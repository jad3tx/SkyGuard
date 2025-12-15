"""
Configuration Manager for SkyGuard System

Handles loading and managing configuration settings from YAML files.
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigManager:
    """Manages configuration settings for the SkyGuard system."""
    
    def __init__(self, config_path: str):
        """Initialize the configuration manager.
        
        Args:
            config_path: Path to the configuration file
        """
        self.config_path = Path(config_path)
        self.config = {}
        self.logger = logging.getLogger(__name__)
        
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file.
        
        Returns:
            Dictionary containing configuration settings
        """
        try:
            if not self.config_path.exists():
                self.logger.warning(f"Config file not found: {self.config_path}")
                self._create_default_config()
                return self.config
                
            with open(self.config_path, 'r') as file:
                self.config = yaml.safe_load(file)
                
            self.logger.info(f"Configuration loaded from {self.config_path}")
            return self.config
            
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            self._create_default_config()
            return self.config
    
    def get_config(self) -> Dict[str, Any]:
        """Get the current configuration.
        
        Returns:
            Dictionary containing configuration settings
        """
        if not self.config:
            return self.load_config()
        return self.config
    
    def reload_config(self) -> Dict[str, Any]:
        """Reload configuration from file.
        
        Returns:
            Dictionary containing configuration settings
        """
        return self.load_config()
    
    def save_config(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """Save configuration to file.
        
        Args:
            config: Configuration to save (uses current config if None)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if config is not None:
                self.config = config
                
            # Ensure config directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, 'w') as file:
                yaml.dump(self.config, file, default_flow_style=False, indent=2)
                
            self.logger.info(f"Configuration saved to {self.config_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            return False
    
    def update_config(self, new_config: Dict[str, Any]) -> bool:
        """Update configuration with new values.
        
        Args:
            new_config: Dictionary containing new configuration values
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            # Merge new configuration with existing
            self._merge_config(self.config, new_config)
            
            # Save the updated configuration
            return self.save_config()
            
        except Exception as e:
            self.logger.error(f"Failed to update configuration: {e}")
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
    
    def _create_default_config(self):
        """Create a default configuration."""
        self.config = {
            'system': {
                'detection_interval': 1.0,  # seconds
                'save_detection_frames': True,
                'max_detection_history': 1000,
            },
            'camera': {
                'source': 0,  # Default camera index
                'width': 640,
                'height': 480,
                'fps': 30,
                'rotation': 0,
                'flip_horizontal': False,
                'flip_vertical': False,
                'focus_mode': 'manual',
                'focus_value': 15,
            },
            'ai': {
                'model_path': 'models/yolo11n-seg.pt',
                'model_type': 'yolo',
                'confidence_threshold': 0.5,
                'nms_threshold': 0.4,
                'input_size': [640, 640],
                'classes': ['raptor', 'hawk', 'eagle', 'owl'],
            },
            'notifications': {
                'audio': {
                    'enabled': True,
                    'sound_file': 'sounds/raptor_alert.wav',
                    'volume': 0.8,
                },
                'push': {
                    'enabled': False,
                    'api_key': '',
                    'device_id': '',
                },
                'sms': {
                    'enabled': False,
                    'account_sid': '',
                    'auth_token': '',
                    'from_number': '',
                    'to_numbers': [],
                },
                'email': {
                    'enabled': False,
                    'smtp_server': '',
                    'smtp_port': 587,
                    'username': '',
                    'password': '',
                    'from_email': '',
                    'to_emails': [],
                },
            },
            'storage': {
                'database_path': 'data/skyguard.db',
                'detection_images_path': 'data/detections',
                'log_retention_days': 30,
            },
            'logging': {
                'level': 'INFO',
                'file': 'logs/skyguard.log',
                'max_size_mb': 10,
                'backup_count': 5,
            },
            'hardware': {
                'platform': 'auto',  # 'auto', 'raspberry_pi', 'desktop'
                'gpio_enabled': False,
                'led_pin': 18,
                'buzzer_pin': 19,
            },
        }
        
        self.logger.info("Created default configuration")
        self.save_config()
