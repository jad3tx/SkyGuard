"""
Alert System for SkyGuard

Handles various types of alerts including audio, push notifications, SMS, email,
and Discord webhooks.  All channel sends happen in daemon threads so detection
loop latency is not affected.  Delivery outcomes are persisted to the database
via an optional :class:`~skyguard.storage.event_logger.EventLogger` reference.
"""

import logging
import time
import threading
from collections import deque
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional

import requests
import smtplib

# ---------------------------------------------------------------------------
# Optional dependencies — gracefully degraded when unavailable
# ---------------------------------------------------------------------------
try:
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from email.mime.image import MIMEImage
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False
    MIMEText = None       # type: ignore[assignment,misc]
    MIMEMultipart = None  # type: ignore[assignment,misc]
    MIMEImage = None      # type: ignore[assignment,misc]

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None  # type: ignore[assignment]

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    pygame = None  # type: ignore[assignment]

try:
    from twilio.rest import Client as TwilioClient
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    TwilioClient = None  # type: ignore[assignment,misc]

# Sentinel value used in GET /api/config responses for redacted credentials.
_REDACTED = "••••••••"

# Maximum MIME image attachment size (bytes).  Configurable via
# ``storage.max_image_size_mb``; this is the hard-coded default.
_DEFAULT_MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5 MB


class AlertSystem:
    """Manages alert notifications for raptor detections.

    Supports five channels: audio, PushBullet push, SMS (Twilio), email
    (SMTP), and Discord webhook.  Alerts are sent in parallel daemon threads.
    Rate-limiting enforces three constraints:

    1. ``min_alert_interval`` — minimum seconds between consecutive alerts of
       the same type.
    2. ``max_alerts_per_hour`` — rolling 60-minute cap per alert type.
    3. ``cooldown_period`` — once the hourly cap is hit, suppress all further
       sends for this many seconds before resetting the counter.
    """

    def __init__(
        self,
        config: Dict[str, Any],
        rate_limiting_config: Optional[Dict[str, Any]] = None,
        event_logger: Optional[Any] = None,
    ) -> None:
        """Initialise the alert system.

        Args:
            config: Notification configuration dictionary (the
                ``notifications`` key from ``skyguard.yaml``).
            rate_limiting_config: Optional rate-limiting configuration.
                Supported keys: ``min_alert_interval`` (float, seconds),
                ``max_alerts_per_hour`` (int), ``cooldown_period`` (float,
                seconds).
            event_logger: Optional
                :class:`~skyguard.storage.event_logger.EventLogger` instance.
                When supplied, every channel send — success *and* failure — is
                persisted to the ``alert_deliveries`` table.
        """
        self.config: Dict[str, Any] = config
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.event_logger = event_logger

        # In-memory counters (still maintained for backward compatibility)
        self.alert_count: int = 0
        self.last_alert_time: float = 0.0

        # Channel availability flags — set by the _initialize_* methods
        self.audio_enabled: bool = False
        self.push_enabled: bool = False
        self.sms_enabled: bool = False
        self.email_enabled: bool = False
        self.discord_enabled: bool = False

        # SMS client (Twilio); initialised lazily
        self.sms_client: Optional[Any] = None

        # ---- Rate-limiting state -------------------------------------------
        rl = rate_limiting_config or {}
        self.min_alert_interval: float = float(rl.get('min_alert_interval', 30.0))
        self.max_alerts_per_hour: int = int(rl.get('max_alerts_per_hour', 10))
        self.cooldown_period: float = float(rl.get('cooldown_period', 300.0))

        # Per-alert-type last-send timestamps (stage-2 check)
        self.last_alert_times: Dict[str, float] = {}
        # Per-alert-type rolling window of send timestamps (stage-3 check)
        self.alert_send_times: Dict[str, Deque[float]] = {}
        # Per-alert-type cooldown expiry timestamp
        self.cooldown_until: Dict[str, float] = {}
        # Lock protecting all rate-limiting mutable state
        self._rate_limit_lock = threading.Lock()

    # -----------------------------------------------------------------------
    # Initialisation
    # -----------------------------------------------------------------------

    def initialize(self) -> bool:
        """Initialise all enabled alert channels.

        Returns:
            ``True`` if the initialisation completed without exceptions
            (individual channel failures are non-fatal and logged as
            warnings).
        """
        try:
            if self.config.get('audio', {}).get('enabled', False):
                self._initialize_audio()

            if self.config.get('push', {}).get('enabled', False):
                self._initialize_push()

            if self.config.get('sms', {}).get('enabled', False):
                self._initialize_sms()

            if self.config.get('email', {}).get('enabled', False):
                self._initialize_email()

            if self.config.get('discord', {}).get('enabled', False):
                self._initialize_discord()

            self.logger.info("Alert system initialised successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to initialise alert system: {e}", exc_info=True)
            return False

    def _initialize_audio(self) -> None:
        """Initialise pygame mixer for audio alerts."""
        try:
            if not PYGAME_AVAILABLE or pygame is None:
                self.logger.warning("Audio alerts disabled — pygame not available")
                return
            pygame.mixer.init()
            self.audio_enabled = True
            self.logger.info("Audio alerts enabled")
        except Exception as e:
            self.logger.warning(f"Failed to initialise audio: {e}")
            self.audio_enabled = False

    def _initialize_push(self) -> None:
        """Validate PushBullet credentials."""
        try:
            push_config = self.config.get('push', {})
            api_key = push_config.get('api_key', '')
            device_id = push_config.get('device_id', '')

            if api_key and device_id:
                self.push_enabled = True
                self.logger.info("Push notifications enabled")
            elif not api_key:
                self.logger.warning("Push notifications disabled — no API key")
            else:
                self.logger.warning("Push notifications disabled — no device ID")
        except Exception as e:
            self.logger.warning(f"Failed to initialise push notifications: {e}")
            self.push_enabled = False

    def _initialize_sms(self) -> None:
        """Create a Twilio SMS client."""
        try:
            if not TWILIO_AVAILABLE or TwilioClient is None:
                self.logger.warning("SMS notifications disabled — Twilio not available")
                return

            sms_config = self.config.get('sms', {})
            required_keys = ['account_sid', 'auth_token', 'from_number']
            if all(sms_config.get(k) for k in required_keys):
                self.sms_client = TwilioClient(
                    sms_config['account_sid'],
                    sms_config['auth_token'],
                )
                self.sms_enabled = True
                self.logger.info("SMS notifications enabled")
            else:
                missing = [k for k in required_keys if not sms_config.get(k)]
                self.logger.warning(
                    f"SMS notifications disabled — missing credentials: {', '.join(missing)}"
                )
        except Exception as e:
            self.logger.warning(f"Failed to initialise SMS: {e}")
            self.sms_enabled = False
            self.sms_client = None

    def _initialize_email(self) -> None:
        """Validate SMTP credentials."""
        try:
            if not EMAIL_AVAILABLE:
                self.logger.warning(
                    "Email notifications disabled — email.mime modules not available"
                )
                return

            email_config = self.config.get('email', {})
            required_keys = ['smtp_server', 'username', 'password', 'from_email']
            if all(email_config.get(k) for k in required_keys):
                if email_config.get('to_emails'):
                    self.email_enabled = True
                    self.logger.info("Email notifications enabled")
                else:
                    self.logger.warning(
                        "Email notifications disabled — no recipient emails configured"
                    )
            else:
                missing = [k for k in required_keys if not email_config.get(k)]
                self.logger.warning(
                    f"Email notifications disabled — missing credentials: {', '.join(missing)}"
                )
        except Exception as e:
            self.logger.warning(f"Failed to initialise email: {e}")
            self.email_enabled = False

    def _initialize_discord(self) -> None:
        """Validate Discord webhook URL."""
        try:
            discord_config = self.config.get('discord', {})
            webhook_url = discord_config.get('webhook_url', '')

            if not webhook_url:
                self.logger.warning(
                    "Discord notifications disabled — no webhook URL configured"
                )
                self.discord_enabled = False
                return

            valid_prefixes = (
                'https://discord.com/api/webhooks/',
                'https://discordapp.com/api/webhooks/',
            )
            if not webhook_url.startswith(valid_prefixes):
                self.logger.warning("Discord webhook URL format invalid")
                self.discord_enabled = False
                return

            self.discord_enabled = True
            self.logger.info("Discord notifications enabled")
        except Exception as e:
            self.logger.warning(f"Failed to initialise Discord: {e}")
            self.discord_enabled = False

    # -----------------------------------------------------------------------
    # Public alert dispatch
    # -----------------------------------------------------------------------

    def send_raptor_alert(
        self,
        detection: Dict[str, Any],
        detection_id: Optional[int] = None,
    ) -> bool:
        """Send a raptor detection alert on all enabled channels.

        Channel sends run in parallel daemon threads (10-second timeout each).
        Rate-limiting is enforced before thread creation.

        Args:
            detection: Detection information dictionary from the detector.
            detection_id: Optional primary key of the ``detections`` row for
                this event — passed to delivery log records as an FK.

        Returns:
            ``True`` if at least one alert was dispatched successfully (or rate
            limited), ``False`` only on unexpected exceptions.
        """
        try:
            if not self._check_rate_limit('raptor_alert'):
                self.logger.debug("Alert rate-limited — skipping")
                return False

            message = self._create_alert_message(detection)
            threads: List[threading.Thread] = []

            if self.audio_enabled:
                t = threading.Thread(
                    target=self._send_audio_alert,
                    args=(detection_id,),
                    daemon=True,
                )
                threads.append(t)
                t.start()

            if self.push_enabled:
                t = threading.Thread(
                    target=self._send_push_alert,
                    args=(message, detection_id),
                    daemon=True,
                )
                threads.append(t)
                t.start()

            if self.sms_enabled:
                t = threading.Thread(
                    target=self._send_sms_alert,
                    args=(message, detection_id),
                    daemon=True,
                )
                threads.append(t)
                t.start()

            if self.email_enabled:
                t = threading.Thread(
                    target=self._send_email_alert,
                    args=(message, detection, detection_id),
                    daemon=True,
                )
                threads.append(t)
                t.start()

            if self.discord_enabled:
                t = threading.Thread(
                    target=self._send_discord_alert,
                    args=(message, detection, detection_id),
                    daemon=True,
                )
                threads.append(t)
                t.start()

            for t in threads:
                t.join(timeout=10)

            self.alert_count += 1
            self.last_alert_time = time.time()

            self.logger.info(
                f"Raptor alert sent: {detection.get('class_name', 'unknown')} "
                f"(confidence: {detection.get('confidence', 0):.2f})"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to send raptor alert: {e}", exc_info=True)
            return False

    # -----------------------------------------------------------------------
    # Rate limiting
    # -----------------------------------------------------------------------

    def _check_rate_limit(self, alert_type: str) -> bool:
        """Three-stage rate-limit check.

        Stage 1 — Active cooldown:
            If ``max_alerts_per_hour`` was hit recently, block until
            ``cooldown_period`` seconds have elapsed.

        Stage 2 — Minimum interval:
            Reject if the last send of this type was less than
            ``min_alert_interval`` seconds ago.

        Stage 3 — Hourly cap:
            Prune timestamps older than 60 minutes from the rolling window;
            reject if the window already contains ``max_alerts_per_hour`` sends.
            On rejection, activate a cooldown.

        The timestamp of a passing send is appended to the rolling window
        inside this method (not in the caller).

        Args:
            alert_type: Logical alert category (e.g. ``'raptor_alert'``).

        Returns:
            ``True`` if the alert should be sent, ``False`` if rate-limited.
        """
        now = time.time()
        with self._rate_limit_lock:
            # Stage 1: cooldown guard
            if now < self.cooldown_until.get(alert_type, 0.0):
                return False

            # Stage 2: min interval guard
            if now - self.last_alert_times.get(alert_type, 0.0) < self.min_alert_interval:
                return False

            # Stage 3: hourly cap — prune stale entries
            window: Deque[float] = self.alert_send_times.setdefault(
                alert_type, deque()
            )
            cutoff = now - 3600.0
            while window and window[0] < cutoff:
                window.popleft()

            if len(window) >= self.max_alerts_per_hour:
                self.cooldown_until[alert_type] = now + self.cooldown_period
                self.logger.warning(
                    f"Hourly alert cap ({self.max_alerts_per_hour}) reached for "
                    f"'{alert_type}' — cooldown activated for "
                    f"{self.cooldown_period:.0f}s"
                )
                return False

            # Record this send in the rolling window
            window.append(now)
            self.last_alert_times[alert_type] = now
            return True

    # -----------------------------------------------------------------------
    # Message formatting
    # -----------------------------------------------------------------------

    def _create_alert_message(self, detection: Dict[str, Any]) -> str:
        """Build a human-readable alert message from a detection dict.

        When ``detection`` contains species classification data (``species``
        and ``species_confidence``), the species name and confidence are
        included as a dedicated line.  Without species data the format is
        unchanged from the pre-sprint baseline.

        Args:
            detection: Detection information dictionary.

        Returns:
            Multi-line alert message string.
        """
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        confidence: float = detection.get('confidence', 0.0)
        class_name: str = detection.get('class_name', 'unknown')
        species: Optional[str] = detection.get('species')
        species_conf: Optional[float] = detection.get('species_confidence')

        message = "🚨 SKYGUARD ALERT 🚨\n"
        message += f"Raptor detected: {class_name.upper()}\n"
        message += f"Confidence: {confidence:.1%}\n"

        if species and species_conf is not None:
            message += f"Species: {species} ({species_conf:.1%} confidence)\n"

        message += f"Time: {timestamp}\n"
        message += "Location: Your poultry area\n"
        message += "\nPlease check your flock immediately!"

        return message

    def create_alert_message(self, detection: Dict[str, Any]) -> str:
        """Public alias for :meth:`_create_alert_message`.

        Args:
            detection: Detection information dictionary.

        Returns:
            Formatted alert message string.
        """
        return self._create_alert_message(detection)

    def _build_alert_subject(self, detection: Dict[str, Any]) -> str:
        """Build the email subject line, preferring the species name when known.

        Args:
            detection: Detection information dictionary.

        Returns:
            Subject line string.
        """
        species: Optional[str] = detection.get('species')
        if species:
            return f"SkyGuard Alert — {species} detected"
        class_name: str = detection.get('class_name', 'raptor')
        return f"SkyGuard Alert — {class_name.capitalize()} detected"

    # -----------------------------------------------------------------------
    # Channel send methods
    # -----------------------------------------------------------------------

    def _log_delivery(
        self,
        channel: str,
        status: str,
        detection_id: Optional[int],
        error_message: Optional[str] = None,
    ) -> None:
        """Write a delivery record to the database (if event_logger is set).

        Failures inside this helper are logged and swallowed — delivery
        logging must never crash an alert thread.

        Args:
            channel: Channel name.
            status: ``'success'``, ``'failure'``, or ``'skipped'``.
            detection_id: FK to the triggering detection row (may be None).
            error_message: Error description on failure.
        """
        if self.event_logger is None:
            return
        try:
            self.event_logger.log_alert_delivery(
                channel=channel,
                status=status,
                detection_id=detection_id,
                error_message=error_message,
            )
        except Exception as e:
            self.logger.error(
                f"Failed to write delivery log for channel '{channel}': {e}",
                exc_info=True,
            )

    def _send_audio_alert(self, detection_id: Optional[int] = None) -> None:
        """Play an audio alert.

        Args:
            detection_id: Optional FK to the triggering detection.
        """
        try:
            if not PYGAME_AVAILABLE or pygame is None:
                self.logger.warning("Cannot send audio alert — pygame not available")
                self._log_delivery('audio', 'skipped', detection_id,
                                   "pygame not available")
                return

            audio_config = self.config.get('audio', {})
            sound_file = audio_config.get('sound_file', 'sounds/raptor_alert.wav')
            volume = float(audio_config.get('volume', 0.8))
            repeat_count = int(audio_config.get('repeat_count', 1))
            repeat_interval = float(audio_config.get('repeat_interval', 2.0))

            sound_path = Path(sound_file)
            if not sound_path.exists():
                self.logger.debug(f"Sound file not found: {sound_file} — generating beep")
                self._generate_beep_sound()
            else:
                pygame.mixer.music.set_volume(volume)
                pygame.mixer.music.load(str(sound_path))
                for _ in range(repeat_count):
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        time.sleep(0.1)
                    if repeat_count > 1:
                        time.sleep(repeat_interval)

            self.logger.debug("Audio alert sent")
            self._log_delivery('audio', 'success', detection_id)

        except Exception as e:
            self.logger.error(f"Failed to send audio alert: {e}", exc_info=True)
            self._log_delivery('audio', 'failure', detection_id, str(e))

    def _generate_beep_sound(self) -> None:
        """Generate a synthetic beep using pygame and numpy."""
        try:
            if not PYGAME_AVAILABLE or pygame is None:
                self.logger.warning("Cannot generate beep — pygame not available")
                return
            if not NUMPY_AVAILABLE or np is None:
                self.logger.warning("Cannot generate beep — numpy not available")
                return

            sample_rate = 22050
            duration = 0.5
            frequency = 800
            frames = int(duration * sample_rate)
            arr = np.zeros((frames, 2), dtype=np.float32)
            for i in range(frames):
                arr[i][0] = 32767 * np.sin(2 * np.pi * frequency * i / sample_rate)
                arr[i][1] = arr[i][0]
            sound = pygame.sndarray.make_sound(arr.astype(np.int16))
            sound.play()
        except Exception as e:
            self.logger.error(f"Failed to generate beep sound: {e}", exc_info=True)

    def _send_push_alert(
        self, message: str, detection_id: Optional[int] = None
    ) -> None:
        """Send a PushBullet push notification.

        Args:
            message: Alert message body.
            detection_id: Optional FK to the triggering detection.
        """
        try:
            push_config = self.config.get('push', {})
            api_key = push_config.get('api_key', '')
            device_id = push_config.get('device_id', '')

            if not api_key:
                self.logger.warning("Push notification skipped — no API key")
                self._log_delivery('push', 'skipped', detection_id, "no API key")
                return
            if not device_id:
                self.logger.warning("Push notification skipped — no device ID")
                self._log_delivery('push', 'skipped', detection_id, "no device ID")
                return

            url = "https://api.pushbullet.com/v2/pushes"
            headers = {
                "Access-Token": api_key,
                "Content-Type": "application/json",
            }
            payload = {
                "type": "note",
                "title": "SkyGuard Alert",
                "body": message,
                "device_iden": device_id,
            }

            response = requests.post(url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()

            self.logger.debug("Push notification sent")
            self._log_delivery('push', 'success', detection_id)

        except requests.exceptions.RequestException as e:
            self.logger.error(
                f"Failed to send push notification (network error): {e}", exc_info=True
            )
            self._log_delivery('push', 'failure', detection_id, str(e))
        except Exception as e:
            self.logger.error(f"Failed to send push notification: {e}", exc_info=True)
            self._log_delivery('push', 'failure', detection_id, str(e))

    def _send_sms_alert(
        self, message: str, detection_id: Optional[int] = None
    ) -> None:
        """Send an SMS alert via Twilio.

        Args:
            message: Alert message body.
            detection_id: Optional FK to the triggering detection.
        """
        try:
            if self.sms_client is None:
                self.logger.warning("SMS alert skipped — SMS client not initialised")
                self._log_delivery('sms', 'skipped', detection_id,
                                   "SMS client not initialised")
                return

            sms_config = self.config.get('sms', {})
            to_numbers: List[str] = sms_config.get('to_numbers', [])

            if not to_numbers:
                self.logger.warning("SMS alert skipped — no recipient numbers configured")
                self._log_delivery('sms', 'skipped', detection_id,
                                   "no recipient numbers")
                return

            errors: List[str] = []
            for to_number in to_numbers:
                try:
                    self.sms_client.messages.create(
                        body=message,
                        from_=sms_config['from_number'],
                        to=to_number,
                    )
                    self.logger.debug(f"SMS alert sent to {to_number}")
                except Exception as e:
                    self.logger.error(
                        f"Failed to send SMS to {to_number}: {e}", exc_info=True
                    )
                    errors.append(f"{to_number}: {e}")

            if errors:
                self._log_delivery('sms', 'failure', detection_id,
                                   "; ".join(errors))
            else:
                self.logger.debug(f"SMS alert sent to {len(to_numbers)} numbers")
                self._log_delivery('sms', 'success', detection_id)

        except Exception as e:
            self.logger.error(f"Failed to send SMS alert: {e}", exc_info=True)
            self._log_delivery('sms', 'failure', detection_id, str(e))

    def _send_email_alert(
        self,
        message: str,
        detection: Dict[str, Any],
        detection_id: Optional[int] = None,
    ) -> None:
        """Send an email alert with an optional inline JPEG image attachment.

        The detection image (from ``detection['image_path']``) is attached as
        an inline MIME part when all of the following hold:

        * ``email.mime.*`` modules are importable (``EMAIL_AVAILABLE``).
        * The file exists on disk.
        * The file size does not exceed ``storage.max_image_size_mb`` MB.
        * The path resolves within the configured detection images directory
          (path-traversal guard).

        If any condition fails the email is still sent as plain-text only.

        Args:
            message: Plain-text alert body.
            detection: Detection information dict (may contain ``image_path``).
            detection_id: Optional FK to the triggering detection.
        """
        try:
            if not EMAIL_AVAILABLE or MIMEMultipart is None or MIMEText is None:
                self.logger.warning("Email not available — skipping email alert")
                self._log_delivery('email', 'skipped', detection_id,
                                   "email.mime modules not available")
                return

            email_config = self.config.get('email', {})
            to_emails: List[str] = email_config.get('to_emails', [])

            if not to_emails:
                self.logger.warning("Email alert skipped — no recipient emails configured")
                self._log_delivery('email', 'skipped', detection_id,
                                   "no recipient emails")
                return

            # Build the email
            msg = MIMEMultipart()
            msg['From'] = email_config['from_email']
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = self._build_alert_subject(detection)
            msg.attach(MIMEText(message, 'plain'))

            # Optionally attach the detection image
            image_path_str: str = detection.get('image_path') or ''
            if image_path_str:
                self._attach_detection_image(msg, image_path_str)

            # Send via SMTP/TLS
            smtp_server: str = email_config['smtp_server']
            smtp_port: int = int(email_config.get('smtp_port', 587))

            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(email_config['username'], email_config['password'])
            server.send_message(msg)
            server.quit()

            self.logger.debug(f"Email alert sent to {len(to_emails)} addresses")
            self._log_delivery('email', 'success', detection_id)

        except smtplib.SMTPException as e:
            self.logger.error(
                f"Failed to send email alert (SMTP error): {e}", exc_info=True
            )
            self._log_delivery('email', 'failure', detection_id, str(e))
        except Exception as e:
            self.logger.error(f"Failed to send email alert: {e}", exc_info=True)
            self._log_delivery('email', 'failure', detection_id, str(e))

    def _attach_detection_image(
        self, msg: Any, image_path_str: str
    ) -> None:
        """Attach a detection image as an inline JPEG MIME part.

        Validates that the file exists, is within the configured detection
        images directory (path-traversal guard), and does not exceed the
        configured size cap.  Logs a WARNING and returns without attaching if
        any check fails.

        Args:
            msg: The :class:`email.mime.multipart.MIMEMultipart` message to
                attach the image to.
            image_path_str: Filesystem path to the JPEG image file.
        """
        if not image_path_str or MIMEImage is None:
            return

        try:
            image_path = Path(image_path_str).resolve()

            # Path-traversal guard: image must live inside the configured
            # detection images directory.
            storage_config = self.config.get('storage', {})
            images_dir_str: str = storage_config.get(
                'detection_images_path', 'data/detections'
            )
            images_dir = Path(images_dir_str).resolve()
            try:
                image_path.relative_to(images_dir)
            except ValueError:
                self.logger.warning(
                    f"Email attachment rejected — path '{image_path}' is "
                    f"outside detection images directory '{images_dir}'"
                )
                return

            if not image_path.exists():
                self.logger.debug(
                    f"Detection image not found for email attachment: {image_path}"
                )
                return

            # Size cap
            max_bytes_cfg = storage_config.get('max_image_size_mb', 5)
            max_bytes = int(float(max_bytes_cfg) * 1024 * 1024)
            file_size = image_path.stat().st_size
            if file_size > max_bytes:
                self.logger.warning(
                    f"Detection image ({file_size / 1024 / 1024:.1f} MB) exceeds "
                    f"cap ({max_bytes_cfg} MB) — sending email without attachment"
                )
                return

            with open(image_path, 'rb') as fh:
                img_data = fh.read()

            mime_img = MIMEImage(img_data, _subtype='jpeg')
            mime_img.add_header('Content-ID', '<detection_image>')
            mime_img.add_header(
                'Content-Disposition', 'inline', filename='detection.jpg'
            )
            msg.attach(mime_img)
            self.logger.debug(f"Detection image attached to email ({file_size} bytes)")

        except Exception as e:
            self.logger.warning(
                f"Failed to attach detection image to email: {e}", exc_info=True
            )

    def _send_discord_alert(
        self,
        message: str,
        detection: Dict[str, Any],
        detection_id: Optional[int] = None,
    ) -> None:
        """Send a rich Discord embed via webhook.

        The embed includes species classification data (name and confidence)
        when present in the detection dict.

        Args:
            message: Plain-text alert body (used as embed fallback).
            detection: Detection information dict.
            detection_id: Optional FK to the triggering detection.
        """
        try:
            discord_config = self.config.get('discord', {})
            webhook_url: str = discord_config.get('webhook_url', '')

            if not webhook_url:
                self.logger.warning("Discord alert skipped — no webhook URL configured")
                self._log_delivery('discord', 'skipped', detection_id,
                                   "no webhook URL")
                return

            from datetime import datetime
            timestamp_iso = datetime.utcnow().isoformat()
            timestamp_display = time.strftime("%Y-%m-%d %H:%M:%S")
            confidence: float = detection.get('confidence', 0.0)
            class_name: str = detection.get('class_name', 'Unknown')
            species: Optional[str] = detection.get('species')
            species_conf: Optional[float] = detection.get('species_confidence')

            # Build a species-aware description
            if species and species_conf is not None:
                description = (
                    f"**{species}** (bird, {confidence:.0%} detection"
                    f" / {species_conf:.0%} species confidence)"
                )
            else:
                description = (
                    f"**{class_name.upper()}** detected with {confidence:.1%} confidence"
                )

            fields = [
                {"name": "Confidence", "value": f"{confidence:.1%}", "inline": True},
                {"name": "Time", "value": timestamp_display, "inline": True},
            ]
            if species and species_conf is not None:
                fields.insert(
                    1,
                    {
                        "name": "Species Confidence",
                        "value": f"{species_conf:.1%}",
                        "inline": True,
                    },
                )

            fields.append(
                {"name": "Location", "value": "Your poultry area", "inline": False}
            )

            embed = {
                "title": "🚨 SkyGuard Raptor Alert",
                "description": description,
                "color": 15158332,  # Red
                "fields": fields,
                "footer": {"text": "SkyGuard Detection System"},
                "timestamp": timestamp_iso,
            }

            payload: Dict[str, Any] = {"embeds": [embed]}

            username: str = discord_config.get('username', 'SkyGuard')
            if username:
                payload["username"] = username

            avatar_url: str = discord_config.get('avatar_url', '')
            if avatar_url:
                payload["avatar_url"] = avatar_url

            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()

            self.logger.debug("Discord alert sent successfully")
            self._log_delivery('discord', 'success', detection_id)

        except requests.exceptions.RequestException as e:
            self.logger.error(
                f"Failed to send Discord alert (network error): {e}", exc_info=True
            )
            self._log_delivery('discord', 'failure', detection_id, str(e))
        except Exception as e:
            self.logger.error(f"Failed to send Discord alert: {e}", exc_info=True)
            self._log_delivery('discord', 'failure', detection_id, str(e))

    # -----------------------------------------------------------------------
    # Test dispatch
    # -----------------------------------------------------------------------

    def test_alert(self, alert_type: str = "all") -> bool:
        """Send a test alert.

        Test alerts intentionally bypass the rate-limiter and do *not* write
        delivery records to the database.

        Args:
            alert_type: One of ``'audio'``, ``'push'``, ``'sms'``,
                ``'email'``, ``'discord'``, or ``'all'``.

        Returns:
            ``True`` if the requested channel(s) were invoked without raising,
            ``False`` otherwise.
        """
        try:
            test_detection: Dict[str, Any] = {
                'class_name': 'test_raptor',
                'confidence': 0.95,
                'timestamp': time.time(),
                'bbox': [100, 100, 200, 200],
                'center': [150, 150],
                'area': 10000,
            }

            if alert_type == "all":
                return self.send_raptor_alert(test_detection)

            message = self._create_alert_message(test_detection)

            if alert_type == "audio" and self.audio_enabled:
                self._send_audio_alert()
            elif alert_type == "push" and self.push_enabled:
                self._send_push_alert(message)
            elif alert_type == "sms" and self.sms_enabled:
                self._send_sms_alert(message)
            elif alert_type == "email" and self.email_enabled:
                self._send_email_alert(message, test_detection)
            elif alert_type == "discord" and self.discord_enabled:
                self._send_discord_alert(message, test_detection)
            else:
                self.logger.warning(f"Unknown or disabled alert type: {alert_type}")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Failed to send test alert: {e}", exc_info=True)
            return False

    # -----------------------------------------------------------------------
    # Configuration update
    # -----------------------------------------------------------------------

    def update_config(
        self,
        new_config: Dict[str, Any],
        rate_limiting_config: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Apply new notification and rate-limiting configuration at runtime.

        Channels are disabled and re-initialised based on the merged config.

        Args:
            new_config: New notification configuration dictionary.
            rate_limiting_config: Optional rate-limiting configuration.

        Returns:
            ``True`` if the update succeeded, ``False`` on error.
        """
        try:
            self._merge_config(self.config, new_config)

            if rate_limiting_config:
                rl = rate_limiting_config
                if 'min_alert_interval' in rl:
                    self.min_alert_interval = float(rl['min_alert_interval'])
                if 'max_alerts_per_hour' in rl:
                    self.max_alerts_per_hour = int(rl['max_alerts_per_hour'])
                if 'cooldown_period' in rl:
                    self.cooldown_period = float(rl['cooldown_period'])

            # Reset channel flags and re-initialise
            self.audio_enabled = False
            self.push_enabled = False
            self.sms_enabled = False
            self.email_enabled = False
            self.discord_enabled = False
            self.sms_client = None

            if self.config.get('audio', {}).get('enabled', False):
                self._initialize_audio()
            if self.config.get('push', {}).get('enabled', False):
                self._initialize_push()
            if self.config.get('sms', {}).get('enabled', False):
                self._initialize_sms()
            if self.config.get('email', {}).get('enabled', False):
                self._initialize_email()
            if self.config.get('discord', {}).get('enabled', False):
                self._initialize_discord()

            self.logger.info("Alert system configuration updated successfully")
            return True

        except Exception as e:
            self.logger.error(
                f"Failed to update alert system configuration: {e}", exc_info=True
            )
            return False

    def _merge_config(
        self, base_config: Dict[str, Any], new_config: Dict[str, Any]
    ) -> None:
        """Recursively merge ``new_config`` into ``base_config`` in-place.

        Args:
            base_config: Base configuration dictionary (mutated in-place).
            new_config: New values to apply.
        """
        for key, value in new_config.items():
            if (
                key in base_config
                and isinstance(base_config[key], dict)
                and isinstance(value, dict)
            ):
                self._merge_config(base_config[key], value)
            else:
                base_config[key] = value

    # -----------------------------------------------------------------------
    # Statistics
    # -----------------------------------------------------------------------

    def get_alert_stats(self) -> Dict[str, Any]:
        """Return alert system statistics.

        When an :attr:`event_logger` is configured the ``total_alerts``,
        ``failed_alerts``, and ``last_alert_time`` values are sourced from the
        ``alert_deliveries`` table.  Otherwise the in-memory counters are
        used.

        The rate-limiting state (``max_alerts_per_hour``, ``cooldown_period``,
        ``alerts_sent_last_hour``, ``in_cooldown``) is always computed from
        the in-memory rolling window.

        Returns:
            Dictionary with alert statistics.
        """
        # DB-backed totals when available
        total_alerts: int = self.alert_count
        failed_alerts: int = 0
        last_alert_time: float = self.last_alert_time

        if self.event_logger is not None:
            try:
                successes = self.event_logger.get_alert_deliveries(
                    limit=1, status='success'
                )
                if successes:
                    last_alert_time = successes[0]['timestamp']

                # Count totals from DB (up to last 10 000 records for perf)
                all_records = self.event_logger.get_alert_deliveries(limit=10_000)
                total_alerts = len(all_records)
                failed_alerts = sum(
                    1 for r in all_records if r['status'] == 'failure'
                )
            except Exception as e:
                self.logger.debug(f"Failed to fetch DB alert stats: {e}")

        # Rolling window stats
        now = time.time()
        with self._rate_limit_lock:
            window = self.alert_send_times.get('raptor_alert', deque())
            cutoff = now - 3600.0
            alerts_last_hour = sum(1 for ts in window if ts >= cutoff)
            in_cooldown = (
                now < self.cooldown_until.get('raptor_alert', 0.0)
            )

        return {
            'total_alerts': total_alerts,
            'failed_alerts': failed_alerts,
            'last_alert_time': last_alert_time,
            'audio_enabled': self.audio_enabled,
            'push_enabled': self.push_enabled,
            'sms_enabled': self.sms_enabled,
            'email_enabled': self.email_enabled,
            'discord_enabled': self.discord_enabled,
            'min_alert_interval': self.min_alert_interval,
            'max_alerts_per_hour': self.max_alerts_per_hour,
            'cooldown_period': self.cooldown_period,
            'alerts_sent_last_hour': alerts_last_hour,
            'in_cooldown': in_cooldown,
        }
