"""
Alert System for SkyGuard

Handles various types of alerts including audio, push notifications, SMS, and email.
"""

import logging
import time
import threading
from typing import Dict, Any, List, Optional
from pathlib import Path
import pygame
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

# Try to import Twilio, but don't fail if not available
try:
    from twilio.rest import Client as TwilioClient
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    TwilioClient = None


class AlertSystem:
    """Manages alert notifications for raptor detections."""
    
    def __init__(self, config: dict):
        """Initialize the alert system.
        
        Args:
            config: Notification configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.alert_count = 0
        self.last_alert_time = 0
        
        # Initialize components
        self.audio_enabled = False
        self.push_enabled = False
        self.sms_enabled = False
        self.email_enabled = False
        
        # Rate limiting
        self.min_alert_interval = 30  # seconds between alerts
        self.last_alert_times = {}
        
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
            
            self.logger.info("Alert system initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize alert system: {e}")
            return False
    
    def _initialize_audio(self):
        """Initialize audio alert system."""
        try:
            pygame.mixer.init()
            self.audio_enabled = True
            self.logger.info("Audio alerts enabled")
        except Exception as e:
            self.logger.warning(f"Failed to initialize audio: {e}")
    
    def _initialize_push(self):
        """Initialize push notification system."""
        try:
            api_key = self.config['push'].get('api_key')
            if api_key:
                self.push_enabled = True
                self.logger.info("Push notifications enabled")
            else:
                self.logger.warning("Push notifications disabled - no API key")
        except Exception as e:
            self.logger.warning(f"Failed to initialize push notifications: {e}")
    
    def _initialize_sms(self):
        """Initialize SMS notification system."""
        try:
            if not TWILIO_AVAILABLE:
                self.logger.warning("SMS notifications disabled - Twilio not available")
                return
                
            sms_config = self.config['sms']
            if all(sms_config.get(key) for key in ['account_sid', 'auth_token', 'from_number']):
                self.sms_client = TwilioClient(sms_config['account_sid'], sms_config['auth_token'])
                self.sms_enabled = True
                self.logger.info("SMS notifications enabled")
            else:
                self.logger.warning("SMS notifications disabled - missing credentials")
        except Exception as e:
            self.logger.warning(f"Failed to initialize SMS: {e}")
    
    def _initialize_email(self):
        """Initialize email notification system."""
        try:
            if not EMAIL_AVAILABLE:
                self.logger.warning("Email notifications disabled - email modules not available")
                return
                
            email_config = self.config['email']
            if all(email_config.get(key) for key in ['smtp_server', 'username', 'password']):
                self.email_enabled = True
                self.logger.info("Email notifications enabled")
            else:
                self.logger.warning("Email notifications disabled - missing credentials")
        except Exception as e:
            self.logger.warning(f"Failed to initialize email: {e}")
    
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
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join(timeout=10)  # 10 second timeout
            
            # Update statistics
            self.alert_count += 1
            self.last_alert_time = time.time()
            
            self.logger.info(f"Raptor alert sent: {detection['class_name']} (confidence: {detection['confidence']:.2f})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send raptor alert: {e}")
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
    
    def _send_audio_alert(self):
        """Send audio alert."""
        try:
            audio_config = self.config['audio']
            sound_file = audio_config.get('sound_file', 'sounds/raptor_alert.wav')
            volume = audio_config.get('volume', 0.8)
            
            # Check if sound file exists
            if not Path(sound_file).exists():
                # Generate a simple beep sound
                self._generate_beep_sound()
                return
            
            # Play sound file
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.load(sound_file)
            pygame.mixer.music.play()
            
            self.logger.debug("Audio alert sent")
            
        except Exception as e:
            self.logger.error(f"Failed to send audio alert: {e}")
    
    def _generate_beep_sound(self):
        """Generate a simple beep sound."""
        try:
            # Create a simple beep using pygame
            sample_rate = 22050
            duration = 0.5
            frequency = 800
            
            frames = int(duration * sample_rate)
            arr = np.zeros((frames, 2))
            
            for i in range(frames):
                arr[i][0] = 32767 * np.sin(2 * np.pi * frequency * i / sample_rate)
                arr[i][1] = arr[i][0]
            
            sound = pygame.sndarray.make_sound(arr.astype(np.int16))
            sound.play()
            
        except Exception as e:
            self.logger.error(f"Failed to generate beep sound: {e}")
    
    def _send_push_alert(self, message: str):
        """Send push notification."""
        try:
            push_config = self.config['push']
            api_key = push_config['api_key']
            device_id = push_config['device_id']
            
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
            
        except Exception as e:
            self.logger.error(f"Failed to send push notification: {e}")
    
    def _send_sms_alert(self, message: str):
        """Send SMS alert."""
        try:
            sms_config = self.config['sms']
            to_numbers = sms_config.get('to_numbers', [])
            
            for to_number in to_numbers:
                self.sms_client.messages.create(
                    body=message,
                    from_=sms_config['from_number'],
                    to=to_number
                )
            
            self.logger.debug(f"SMS alert sent to {len(to_numbers)} numbers")
            
        except Exception as e:
            self.logger.error(f"Failed to send SMS alert: {e}")
    
    def _send_email_alert(self, message: str, detection: Dict[str, Any]):
        """Send email alert."""
        try:
            if not EMAIL_AVAILABLE:
                self.logger.warning("Email not available - skipping email alert")
                return
                
            email_config = self.config['email']
            to_emails = email_config.get('to_emails', [])
            
            if not to_emails:
                return
            
            # Create email
            msg = MimeMultipart()
            msg['From'] = email_config['from_email']
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = "SkyGuard Raptor Alert"
            
            # Add body
            msg.attach(MimeText(message, 'plain'))
            
            # Send email
            server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
            server.starttls()
            server.login(email_config['username'], email_config['password'])
            server.send_message(msg)
            server.quit()
            
            self.logger.debug(f"Email alert sent to {len(to_emails)} addresses")
            
        except Exception as e:
            self.logger.error(f"Failed to send email alert: {e}")
    
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
                else:
                    self.logger.warning(f"Unknown alert type or not enabled: {alert_type}")
                    return False
                
                return True
            
        except Exception as e:
            self.logger.error(f"Failed to send test alert: {e}")
            return False
    
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
            'min_alert_interval': self.min_alert_interval,
        }
