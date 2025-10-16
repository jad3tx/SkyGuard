#!/usr/bin/env python3
"""
SkyGuard Configuration Wizard

Interactive setup and configuration tool for the SkyGuard system.
"""

import os
import sys
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from skyguard.core.config_manager import ConfigManager


class SkyGuardConfigurator:
    """Interactive configuration wizard for SkyGuard."""
    
    def __init__(self):
        """Initialize the configurator."""
        self.config_path = "config/skyguard.yaml"
        self.config_manager = ConfigManager(self.config_path)
        self.logger = logging.getLogger(__name__)
        
    def run(self):
        """Run the configuration wizard."""
        print("🦅 SkyGuard Configuration Wizard")
        print("=" * 50)
        print()
        
        # Load existing config or create default
        config = self.config_manager.load_config()
        
        # Run configuration sections
        self._configure_system(config)
        self._configure_camera(config)
        self._configure_ai(config)
        self._configure_notifications(config)
        self._configure_storage(config)
        self._configure_hardware(config)
        
        # Save configuration
        if self.config_manager.save_config(config):
            print("\n✅ Configuration saved successfully!")
            print(f"📁 Config file: {self.config_path}")
        else:
            print("\n❌ Failed to save configuration")
            return False
        
        # Offer to test the configuration
        if self._ask_yes_no("Would you like to test the configuration now?"):
            self._test_configuration(config)
        
        return True
    
    def _configure_system(self, config: Dict[str, Any]):
        """Configure system settings."""
        print("🔧 System Configuration")
        print("-" * 30)
        
        # Detection interval
        current = config['system']['detection_interval']
        new_interval = self._ask_number(
            f"Detection interval (seconds) [{current}]: ",
            default=current,
            min_val=0.1,
            max_val=10.0
        )
        config['system']['detection_interval'] = new_interval
        
        # Save detection frames
        current = config['system']['save_detection_frames']
        config['system']['save_detection_frames'] = self._ask_yes_no(
            f"Save detection frames? [{'Y' if current else 'N'}]: ",
            default=current
        )
        
        print()
    
    def _configure_camera(self, config: Dict[str, Any]):
        """Configure camera settings."""
        print("📷 Camera Configuration")
        print("-" * 30)
        
        # Camera source
        print("Available camera sources:")
        self._list_cameras()
        
        current = config['camera']['source']
        new_source = self._ask_number(
            f"Camera source (0 for default) [{current}]: ",
            default=current,
            min_val=0
        )
        config['camera']['source'] = new_source
        
        # Resolution
        print("\nResolution options:")
        print("1. 640x480 (VGA) - Recommended for performance")
        print("2. 1280x720 (HD) - Better quality, more CPU usage")
        print("3. 1920x1080 (Full HD) - Best quality, high CPU usage")
        
        current_width = config['camera']['width']
        current_height = config['camera']['height']
        
        if current_width == 640 and current_height == 480:
            current_choice = 1
        elif current_width == 1280 and current_height == 720:
            current_choice = 2
        elif current_width == 1920 and current_height == 1080:
            current_choice = 3
        else:
            current_choice = 1
        
        choice = self._ask_number(
            f"Resolution choice [1-3] [{current_choice}]: ",
            default=current_choice,
            min_val=1,
            max_val=3
        )
        
        if choice == 1:
            config['camera']['width'] = 640
            config['camera']['height'] = 480
        elif choice == 2:
            config['camera']['width'] = 1280
            config['camera']['height'] = 720
        elif choice == 3:
            config['camera']['width'] = 1920
            config['camera']['height'] = 1080
        
        # FPS
        current = config['camera']['fps']
        new_fps = self._ask_number(
            f"Frames per second [1-60] [{current}]: ",
            default=current,
            min_val=1,
            max_val=60
        )
        config['camera']['fps'] = new_fps
        
        # Rotation
        current = config['camera']['rotation']
        new_rotation = self._ask_number(
            f"Camera rotation (degrees: 0, 90, 180, 270) [{current}]: ",
            default=current,
            allowed_values=[0, 90, 180, 270]
        )
        config['camera']['rotation'] = new_rotation
        
        print()
    
    def _configure_ai(self, config: Dict[str, Any]):
        """Configure AI model settings."""
        print("🤖 AI Model Configuration")
        print("-" * 30)
        
        # Confidence threshold
        current = config['ai']['confidence_threshold']
        new_threshold = self._ask_number(
            f"Confidence threshold (0.0-1.0) [{current}]: ",
            default=current,
            min_val=0.0,
            max_val=1.0
        )
        config['ai']['confidence_threshold'] = new_threshold
        
        # Model path
        current = config['ai']['model_path']
        print(f"Current model path: {current}")
        
        if not Path(current).exists():
            print("⚠️  Model file not found. Using dummy model for testing.")
            print("   To use a real model, place it in the models/ directory")
        
        print()
    
    def _configure_notifications(self, config: Dict[str, Any]):
        """Configure notification settings."""
        print("🔔 Notification Configuration")
        print("-" * 30)
        
        # Audio alerts
        current = config['notifications']['audio']['enabled']
        config['notifications']['audio']['enabled'] = self._ask_yes_no(
            f"Enable audio alerts? [{'Y' if current else 'N'}]: ",
            default=current
        )
        
        if config['notifications']['audio']['enabled']:
            current_volume = config['notifications']['audio']['volume']
            new_volume = self._ask_number(
                f"Audio volume (0.0-1.0) [{current_volume}]: ",
                default=current_volume,
                min_val=0.0,
                max_val=1.0
            )
            config['notifications']['audio']['volume'] = new_volume
        
        # Push notifications
        current = config['notifications']['push']['enabled']
        config['notifications']['push']['enabled'] = self._ask_yes_no(
            f"Enable push notifications? [{'Y' if current else 'N'}]: ",
            default=current
        )
        
        if config['notifications']['push']['enabled']:
            api_key = self._ask_string("Pushbullet API key: ")
            if api_key:
                config['notifications']['push']['api_key'] = api_key
        
        # SMS notifications
        current = config['notifications']['sms']['enabled']
        config['notifications']['sms']['enabled'] = self._ask_yes_no(
            f"Enable SMS notifications? [{'Y' if current else 'N'}]: ",
            default=current
        )
        
        if config['notifications']['sms']['enabled']:
            print("SMS configuration requires Twilio account setup.")
            print("Please edit config/skyguard.yaml manually for SMS settings.")
        
        # Email notifications
        current = config['notifications']['email']['enabled']
        config['notifications']['email']['enabled'] = self._ask_yes_no(
            f"Enable email notifications? [{'Y' if current else 'N'}]: ",
            default=current
        )
        
        if config['notifications']['email']['enabled']:
            print("Email configuration requires SMTP server setup.")
            print("Please edit config/skyguard.yaml manually for email settings.")
        
        print()
    
    def _configure_storage(self, config: Dict[str, Any]):
        """Configure storage settings."""
        print("💾 Storage Configuration")
        print("-" * 30)
        
        # Database path
        current = config['storage']['database_path']
        print(f"Database path: {current}")
        
        # Image retention
        current = config['storage']['log_retention_days']
        new_retention = self._ask_number(
            f"Log retention (days) [1-365] [{current}]: ",
            default=current,
            min_val=1,
            max_val=365
        )
        config['storage']['log_retention_days'] = new_retention
        
        print()
    
    def _configure_hardware(self, config: Dict[str, Any]):
        """Configure hardware settings."""
        print("🔌 Hardware Configuration")
        print("-" * 30)
        
        # Platform detection
        platform = self._detect_platform()
        print(f"Detected platform: {platform}")
        
        config['hardware']['platform'] = platform
        
        if platform == "raspberry_pi":
            # GPIO settings
            current = config['hardware']['gpio_enabled']
            config['hardware']['gpio_enabled'] = self._ask_yes_no(
                f"Enable GPIO features? [{'Y' if current else 'N'}]: ",
                default=current
            )
            
            if config['hardware']['gpio_enabled']:
                print("GPIO features enabled for LED indicators and buzzers")
        
        print()
    
    def _list_cameras(self):
        """List available cameras."""
        try:
            import cv2
            
            print("Scanning for cameras...")
            for i in range(5):  # Check first 5 camera indices
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret:
                        height, width = frame.shape[:2]
                        print(f"  Camera {i}: {width}x{height}")
                    cap.release()
                else:
                    break
        except ImportError:
            print("  OpenCV not available for camera detection")
        except Exception as e:
            print(f"  Error detecting cameras: {e}")
    
    def _detect_platform(self) -> str:
        """Detect the current platform."""
        try:
            if os.path.exists('/proc/device-tree/model'):
                with open('/proc/device-tree/model', 'r') as f:
                    model = f.read().strip()
                    if 'Raspberry Pi' in model:
                        return 'raspberry_pi'
            
            if os.path.exists('/etc/os-release'):
                with open('/etc/os-release', 'r') as f:
                    content = f.read()
                    if 'raspbian' in content.lower():
                        return 'raspberry_pi'
                    elif 'ubuntu' in content.lower():
                        return 'ubuntu'
                    elif 'debian' in content.lower():
                        return 'debian'
            
            return 'desktop'
        except Exception:
            return 'unknown'
    
    def _test_configuration(self, config: Dict[str, Any]):
        """Test the configuration."""
        print("\n🧪 Testing Configuration")
        print("-" * 30)
        
        # Test camera
        print("Testing camera...")
        try:
            import cv2
            cap = cv2.VideoCapture(config['camera']['source'])
            if cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    print("✅ Camera test: OK")
                else:
                    print("❌ Camera test: Failed to capture frame")
                cap.release()
            else:
                print("❌ Camera test: Failed to open camera")
        except Exception as e:
            print(f"❌ Camera test: Error - {e}")
        
        # Test audio
        if config['notifications']['audio']['enabled']:
            print("Testing audio...")
            try:
                import pygame
                pygame.mixer.init()
                print("✅ Audio test: OK")
            except ImportError:
                print("⚠️  pygame not available - audio notifications disabled")
                print("   Install pygame for audio alerts: pip install pygame")
                config['notifications']['audio']['enabled'] = False
            except Exception as e:
                print(f"❌ Audio test: Error - {e}")
                print("   Audio notifications will be disabled")
                config['notifications']['audio']['enabled'] = False
        
        # Test model
        print("Testing AI model...")
        model_path = config['ai']['model_path']
        if Path(model_path).exists():
            print("✅ Model test: File exists")
        else:
            print("⚠️  Model test: File not found (will use dummy model)")
        
        print("\nConfiguration test completed!")
    
    def _ask_yes_no(self, prompt: str, default: bool = True) -> bool:
        """Ask a yes/no question."""
        default_str = "Y/n" if default else "y/N"
        while True:
            response = input(f"{prompt} [{default_str}]: ").strip().lower()
            if not response:
                return default
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                print("Please enter 'y' or 'n'")
    
    def _ask_number(self, prompt: str, default: float, min_val: Optional[float] = None, 
                   max_val: Optional[float] = None, allowed_values: Optional[list] = None) -> float:
        """Ask for a number input."""
        while True:
            response = input(prompt).strip()
            if not response:
                return default
            
            try:
                value = float(response)
                
                if allowed_values is not None and value not in allowed_values:
                    print(f"Please enter one of: {allowed_values}")
                    continue
                
                if min_val is not None and value < min_val:
                    print(f"Value must be >= {min_val}")
                    continue
                
                if max_val is not None and value > max_val:
                    print(f"Value must be <= {max_val}")
                    continue
                
                return value
            except ValueError:
                print("Please enter a valid number")
    
    def _ask_string(self, prompt: str) -> str:
        """Ask for a string input."""
        return input(prompt).strip()


def main():
    """Main entry point for the configuration wizard."""
    try:
        configurator = SkyGuardConfigurator()
        success = configurator.run()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nConfiguration cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Configuration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
