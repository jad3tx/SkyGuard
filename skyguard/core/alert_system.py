"""
Alert System for SkyGuard

Handles various types of alerts including audio, push notifications, SMS, email, and Discord webhooks.
"""

import logging
import time
import threading
from typing import Dict, Any, List, Optional
from pathlib import Path
import requests
import smtplib
try:
    from email.mime.text import MimeText
    from email.mime.multipart import MimeMultipart
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False
    MimeText = None
    MimeMultipart = None

# Try to import numpy, but don't fail if not available
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None

# Try to import pygame, but don't fail if not available
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    pygame = None

# Try to import Twilio, but don't fail if not available
try:
    from twilio.rest import Client as TwilioClient
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    TwilioClient = None


class AlertSystem:
    """Manages alert notifications for raptor detections."""
    
    def __init__(self, config: Dict[str, Any], rate_limiting_config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the alert system.
        
        Args:
            config: Notification configuration dictionary
            rate_limiting_config: Optional rate limiting configuration dictionary
        """
        self.config: Dict[str, Any] = config
        self.logger: logging.Logger = logging.getLogger(__name__)
        self.alert_count: int = 0
        self.last_alert_time: float = 0.0
        
        # Initialize components
        self.audio_enabled: bool = False
        self.push_enabled: bool = False
        self.sms_enabled: bool = False
        self.email_enabled: bool = False
        self.discord_enabled: bool = False
        
        # SMS client (initialized if SMS is enabled)
        self.sms_client: Optional[Any] = None
        
        # Rate limiting - use provided config or default
        if rate_limiting_config:
            self.min_alert_interval: float = float(rate_limiting_config.get('min_alert_interval', 30))
        else:
            self.min_alert_interval: float = 30.0  # seconds between alerts
        self.last_alert_times: Dict[str, float] = {}
        
    def initialize(self) -> bool:
        """Initialize the alert system.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Initialize audio
            if self.config.get('audio', {}).get('enabled', False):
                self._initialize_audio()
            
            # Initialize push notifications
            if self.config.get('push', {}).get('enabled', False):
                self._initialize_push()
            
            # Initialize SMS
            if self.config.get('sms', {}).get('enabled', False):
                self._initialize_sms()
            
            # Initialize email
            if self.config.get('email', {}).get('enabled', False):
                self._initialize_email()
            
            # Initialize Discord
            if self.config.get('discord', {}).get('enabled', False):
                self._initialize_discord()
            
            self.logger.info("Alert system initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize alert system: {e}")
            return False
    
    def _initialize_audio(self) -> None:
        """Initialize audio alert system."""
        try:
            if not PYGAME_AVAILABLE or pygame is None:
                self.logger.warning("Audio alerts disabled - pygame not available")
                return
                
            pygame.mixer.init()
            self.audio_enabled = True
            self.logger.info("Audio alerts enabled")
        except Exception as e:
            self.logger.warning(f"Failed to initialize audio: {e}")
            self.audio_enabled = False
    
    def _initialize_push(self) -> None:
        """Initialize push notification system."""
        try:
            push_config = self.config.get('push', {})
            api_key = push_config.get('api_key', '')
            device_id = push_config.get('device_id', '')
            
            if api_key and device_id:
                self.push_enabled = True
                self.logger.info("Push notifications enabled")
            elif not api_key:
                self.logger.warning("Push notifications disabled - no API key")
            elif not device_id:
                self.logger.warning("Push notifications disabled - no device ID")
        except Exception as e:
            self.logger.warning(f"Failed to initialize push notifications: {e}")
            self.push_enabled = False
    
    def _initialize_sms(self) -> None:
        """Initialize SMS notification system."""
        try:
            if not TWILIO_AVAILABLE or TwilioClient is None:
                self.logger.warning("SMS notifications disabled - Twilio not available")
                return
                
            sms_config = self.config.get('sms', {})
            required_keys = ['account_sid', 'auth_token', 'from_number']
            if all(sms_config.get(key) for key in required_keys):
                self.sms_client = TwilioClient(
                    sms_config['account_sid'],
                    sms_config['auth_token']
                )
                self.sms_enabled = True
                self.logger.info("SMS notifications enabled")
            else:
                missing = [key for key in required_keys if not sms_config.get(key)]
                self.logger.warning(f"SMS notifications disabled - missing credentials: {', '.join(missing)}")
        except Exception as e:
            self.logger.warning(f"Failed to initialize SMS: {e}")
            self.sms_enabled = False
            self.sms_client = None
    
    def _initialize_email(self) -> None:
        """Initialize email notification system."""
        try:
            if not EMAIL_AVAILABLE:
                self.logger.warning("Email notifications disabled - email modules not available")
                return
                
            email_config = self.config.get('email', {})
            required_keys = ['smtp_server', 'username', 'password', 'from_email']
            if all(email_config.get(key) for key in required_keys):
                to_emails = email_config.get('to_emails', [])
                if to_emails:
                    self.email_enabled = True
                    self.logger.info("Email notifications enabled")
                else:
                    self.logger.warning("Email notifications disabled - no recipient emails configured")
            else:
                missing = [key for key in required_keys if not email_config.get(key)]
                self.logger.warning(f"Email notifications disabled - missing credentials: {', '.join(missing)}")
        except Exception as e:
            self.logger.warning(f"Failed to initialize email: {e}")
            self.email_enabled = False
    
    def _initialize_discord(self) -> None:
        """Initialize Discord webhook notification system."""
        try:
            discord_config = self.config.get('discord', {})
            webhook_url = discord_config.get('webhook_url', '')
            
            if webhook_url:
                # Validate webhook URL format
                if not webhook_url.startswith('https://discord.com/api/webhooks/') and \
                   not webhook_url.startswith('https://discordapp.com/api/webhooks/'):
                    self.logger.warning("Discord webhook URL format invalid")
                    self.discord_enabled = False
                    return
                
                self.discord_enabled = True
                self.logger.info("Discord notifications enabled")
            else:
                self.logger.warning("Discord notifications disabled - no webhook URL configured")
                self.discord_enabled = False
        except Exception as e:
            self.logger.warning(f"Failed to initialize Discord: {e}")
            self.discord_enabled = False
    
    def send_raptor_alert(self, detection: Dict[str, Any]) -> bool:
        """Send raptor detection alert.
        
        Args:
            detection: Detection information dictionary
            
        Returns:
            True if at least one alert was sent successfully
        """
        try:
            # Check rate limiting
            if not self._check_rate_limit('raptor_alert'):
                self.logger.debug("Alert rate limited, skipping")
                return False
            
            # Create alert message
            message = self._create_alert_message(detection)
            
            # Send alerts in parallel
            threads = []
            success_count = 0
            
            if self.audio_enabled:
                thread = threading.Thread(target=self._send_audio_alert)
                threads.append(thread)
                thread.start()
            
            if self.push_enabled:
                thread = threading.Thread(target=self._send_push_alert, args=(message,))
                threads.append(thread)
                thread.start()
            
            if self.sms_enabled:
                thread = threading.Thread(target=self._send_sms_alert, args=(message,))
                threads.append(thread)
                thread.start()
            
            if self.email_enabled:
                thread = threading.Thread(target=self._send_email_alert, args=(message, detection))
                threads.append(thread)
                thread.start()
            
            if self.discord_enabled:
                thread = threading.Thread(target=self._send_discord_alert, args=(message, detection))
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join(timeout=10)  # 10 second timeout
            
            # Update statistics
            self.alert_count += 1
            self.last_alert_time = time.time()
            
            self.logger.info(f"Raptor alert sent: {detection['class_name']} (confidence: {detection['confidence']:.2f})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send raptor alert: {e}", exc_info=True)
            return False
    
    def _check_rate_limit(self, alert_type: str) -> bool:
        """Check if alert should be rate limited.
        
        Args:
            alert_type: Type of alert
            
        Returns:
            True if alert should be sent, False if rate limited
        """
        current_time = time.time()
        last_time = self.last_alert_times.get(alert_type, 0)
        
        if current_time - last_time < self.min_alert_interval:
            return False
        
        self.last_alert_times[alert_type] = current_time
        return True
    
    def _create_alert_message(self, detection: Dict[str, Any]) -> str:
        """Create alert message from detection.
        
        Args:
            detection: Detection information
            
        Returns:
            Formatted alert message
        """
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        confidence = detection['confidence']
        class_name = detection['class_name']
        
        message = f"🚨 SKYGUARD ALERT 🚨\n"
        message += f"Raptor detected: {class_name.upper()}\n"
        message += f"Confidence: {confidence:.1%}\n"
        message += f"Time: {timestamp}\n"
        message += f"Location: Your poultry area\n"
        message += f"\nPlease check your flock immediately!"
        
        return message
    
    def create_alert_message(self, detection: Dict[str, Any]) -> str:
        """Create alert message from detection (public method).
        
        Args:
            detection: Detection information
            
        Returns:
            Formatted alert message
        """
        return self._create_alert_message(detection)
    
    def _send_audio_alert(self) -> None:
        """Send audio alert."""
        try:
            if not PYGAME_AVAILABLE or pygame is None:
                self.logger.warning("Cannot send audio alert - pygame not available")
                return
                
            audio_config = self.config.get('audio', {})
            sound_file = audio_config.get('sound_file', 'sounds/raptor_alert.wav')
            volume = float(audio_config.get('volume', 0.8))
            repeat_count = int(audio_config.get('repeat_count', 1))
            repeat_interval = float(audio_config.get('repeat_interval', 2.0))
            
            # Check if sound file exists
            sound_path = Path(sound_file)
            if not sound_path.exists():
                # Generate a simple beep sound
                self.logger.debug(f"Sound file not found: {sound_file}, generating beep")
                self._generate_beep_sound()
                return
            
            # Play sound file with optional repeats
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.load(str(sound_path))
            
            for _ in range(repeat_count):
                pygame.mixer.music.play()
                # Wait for the sound to finish playing
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                if repeat_count > 1:
                    time.sleep(repeat_interval)
            
            self.logger.debug("Audio alert sent")
            
        except Exception as e:
            self.logger.error(f"Failed to send audio alert: {e}", exc_info=True)
    
    def _generate_beep_sound(self) -> None:
        """Generate a simple beep sound."""
        try:
            if not PYGAME_AVAILABLE or pygame is None:
                self.logger.warning("Cannot generate beep sound - pygame not available")
                return
                
            if not NUMPY_AVAILABLE or np is None:
                self.logger.warning("Cannot generate beep sound - numpy not available")
                return
            
            # Create a simple beep using pygame
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
    
    def _send_push_alert(self, message: str) -> None:
        """Send push notification.
        
        Args:
            message: Alert message to send
        """
        try:
            push_config = self.config.get('push', {})
            api_key = push_config.get('api_key', '')
            device_id = push_config.get('device_id', '')
            
            if not api_key:
                self.logger.warning("Push notification skipped - no API key")
                return
                
            if not device_id:
                self.logger.warning("Push notification skipped - no device ID")
                return
            
            url = "https://api.pushbullet.com/v2/pushes"
            headers = {
                "Access-Token": api_key,
                "Content-Type": "application/json"
            }
            data = {
                "type": "note",
                "title": "SkyGuard Alert",
                "body": message,
                "device_iden": device_id
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=10)
            response.raise_for_status()
            
            self.logger.debug("Push notification sent")
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to send push notification (network error): {e}", exc_info=True)
        except Exception as e:
            self.logger.error(f"Failed to send push notification: {e}", exc_info=True)
    
    def _send_sms_alert(self, message: str) -> None:
        """Send SMS alert.
        
        Args:
            message: Alert message to send
        """
        try:
            if self.sms_client is None:
                self.logger.warning("SMS alert skipped - SMS client not initialized")
                return
                
            sms_config = self.config.get('sms', {})
            to_numbers = sms_config.get('to_numbers', [])
            
            if not to_numbers:
                self.logger.warning("SMS alert skipped - no recipient numbers configured")
                return
            
            for to_number in to_numbers:
                try:
                    self.sms_client.messages.create(
                        body=message,
                        from_=sms_config['from_number'],
                        to=to_number
                    )
                    self.logger.debug(f"SMS alert sent to {to_number}")
                except Exception as e:
                    self.logger.error(f"Failed to send SMS to {to_number}: {e}", exc_info=True)
            
            self.logger.debug(f"SMS alert sent to {len(to_numbers)} numbers")
            
        except Exception as e:
            self.logger.error(f"Failed to send SMS alert: {e}", exc_info=True)
    
    def _send_email_alert(self, message: str, detection: Dict[str, Any]) -> None:
        """Send email alert.
        
        Args:
            message: Alert message to send
            detection: Detection information dictionary
        """
        try:
            if not EMAIL_AVAILABLE or MimeMultipart is None or MimeText is None:
                self.logger.warning("Email not available - skipping email alert")
                return
                
            email_config = self.config.get('email', {})
            to_emails = email_config.get('to_emails', [])
            
            if not to_emails:
                self.logger.warning("Email alert skipped - no recipient emails configured")
                return
            
            # Create email
            msg = MimeMultipart()
            msg['From'] = email_config['from_email']
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = "SkyGuard Raptor Alert"
            
            # Add body
            msg.attach(MimeText(message, 'plain'))
            
            # Send email
            smtp_server = email_config['smtp_server']
            smtp_port = int(email_config.get('smtp_port', 587))
            
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(email_config['username'], email_config['password'])
            server.send_message(msg)
            server.quit()
            
            self.logger.debug(f"Email alert sent to {len(to_emails)} addresses")
            
        except smtplib.SMTPException as e:
            self.logger.error(f"Failed to send email alert (SMTP error): {e}", exc_info=True)
        except Exception as e:
            self.logger.error(f"Failed to send email alert: {e}", exc_info=True)
    
    def _send_discord_alert(self, message: str, detection: Dict[str, Any]) -> None:
        """Send Discord webhook alert.
        
        Args:
            message: Alert message to send
            detection: Detection information dictionary
        """
        try:
            discord_config = self.config.get('discord', {})
            webhook_url = discord_config.get('webhook_url', '')
            
            if not webhook_url:
                self.logger.warning("Discord alert skipped - no webhook URL configured")
                return
            
            # Create Discord embed for rich formatting
            from datetime import datetime
            timestamp_iso = datetime.utcnow().isoformat()
            timestamp_display = time.strftime("%Y-%m-%d %H:%M:%S")
            confidence = detection.get('confidence', 0.0)
            class_name = detection.get('class_name', 'Unknown')
            
            # Discord embed color: Red for alerts
            embed = {
                "title": "🚨 SkyGuard Raptor Alert",
                "description": f"**{class_name.upper()}** detected with {confidence:.1%} confidence",
                "color": 15158332,  # Red color
                "fields": [
                    {
                        "name": "Confidence",
                        "value": f"{confidence:.1%}",
                        "inline": True
                    },
                    {
                        "name": "Time",
                        "value": timestamp_display,
                        "inline": True
                    },
                    {
                        "name": "Location",
                        "value": "Your poultry area",
                        "inline": False
                    }
                ],
                "footer": {
                    "text": "SkyGuard Detection System"
                },
                "timestamp": timestamp_iso
            }
            
            # Build payload
            payload = {
                "embeds": [embed]
            }
            
            # Add username if configured
            username = discord_config.get('username', 'SkyGuard')
            if username:
                payload["username"] = username
            
            # Add avatar URL if configured
            avatar_url = discord_config.get('avatar_url', '')
            if avatar_url:
                payload["avatar_url"] = avatar_url
            
            # Send webhook
            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()
            
            self.logger.debug("Discord alert sent successfully")
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to send Discord alert (network error): {e}", exc_info=True)
        except Exception as e:
            self.logger.error(f"Failed to send Discord alert: {e}", exc_info=True)
    
    def test_alert(self, alert_type: str = "all") -> bool:
        """Send a test alert.
        
        Args:
            alert_type: Type of alert to test ("audio", "push", "sms", "email", "all")
            
        Returns:
            True if successful, False otherwise
        """
        try:
            test_detection = {
                'class_name': 'test_raptor',
                'confidence': 0.95,
                'timestamp': time.time(),
                'bbox': [100, 100, 200, 200],
                'center': [150, 150],
                'area': 10000,
            }
            
            if alert_type == "all":
                return self.send_raptor_alert(test_detection)
            else:
                # Send specific alert type
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
                    self.logger.warning(f"Unknown alert type or not enabled: {alert_type}")
                    return False
                
                return True
            
        except Exception as e:
            self.logger.error(f"Failed to send test alert: {e}")
            return False
    
    def update_config(self, new_config: Dict[str, Any], rate_limiting_config: Optional[Dict[str, Any]] = None) -> bool:
        """Update notification configuration dynamically.
        
        Args:
            new_config: New notification configuration dictionary
            rate_limiting_config: Optional rate limiting configuration dictionary
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            # Merge new configuration with existing
            self._merge_config(self.config, new_config)
            
            # Update rate limiting if provided
            if rate_limiting_config:
                if 'min_alert_interval' in rate_limiting_config:
                    self.min_alert_interval = float(rate_limiting_config['min_alert_interval'])
            
            # Re-initialize components that may have changed
            # Disable all first
            self.audio_enabled = False
            self.push_enabled = False
            self.sms_enabled = False
            self.email_enabled = False
            self.discord_enabled = False
            self.sms_client = None
            
            # Re-initialize based on new config
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
            self.logger.error(f"Failed to update alert system configuration: {e}", exc_info=True)
            return False
    
    def _merge_config(self, base_config: Dict[str, Any], new_config: Dict[str, Any]) -> None:
        """Recursively merge new configuration into base configuration.
        
        Args:
            base_config: Base configuration dictionary
            new_config: New configuration values to merge
        """
        for key, value in new_config.items():
            if key in base_config and isinstance(base_config[key], dict) and isinstance(value, dict):
                # Recursively merge nested dictionaries
                self._merge_config(base_config[key], value)
            else:
                # Update or add the value
                base_config[key] = value
    
    def get_alert_stats(self) -> Dict[str, Any]:
        """Get alert system statistics.
        
        Returns:
            Dictionary with alert statistics
        """
        return {
            'total_alerts': self.alert_count,
            'last_alert_time': self.last_alert_time,
            'audio_enabled': self.audio_enabled,
            'push_enabled': self.push_enabled,
            'sms_enabled': self.sms_enabled,
            'email_enabled': self.email_enabled,
            'discord_enabled': self.discord_enabled,
            'min_alert_interval': self.min_alert_interval,
        }
