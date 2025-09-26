#!/usr/bin/env python3
"""
SkyGuard Web Portal Application

A Flask-based web interface for managing SkyGuard configuration and monitoring detections.
"""

import os
import sys
import json
import yaml
import base64
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_file
from flask_cors import CORS
import cv2
import numpy as np
from PIL import Image
import io

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from skyguard.core.config_manager import ConfigManager
from skyguard.storage.event_logger import EventLogger
from skyguard.core.detector import RaptorDetector
from skyguard.core.camera import CameraManager
from skyguard.core.alert_system import AlertSystem


class SkyGuardWebPortal:
    """SkyGuard Web Portal for configuration and monitoring."""
    
    def __init__(self, config_path: str = "config/skyguard.yaml"):
        """Initialize the web portal."""
        self.app = Flask(__name__)
        self.app.secret_key = os.urandom(24)
        CORS(self.app)
        
        # Initialize components
        self.config_manager = ConfigManager(config_path)
        self.event_logger = EventLogger()
        self.detector = None
        self.camera = None
        self.alert_system = None
        
        # Load configuration
        self.config = self.config_manager.get_config()
        
        # Setup routes
        self._setup_routes()
        
        # Initialize components
        self._initialize_components()
    
    def _setup_routes(self):
        """Setup Flask routes."""
        
        @self.app.route('/')
        def index():
            """Main dashboard."""
            return render_template('index.html')
        
        @self.app.route('/api/status')
        def api_status():
            """Get system status."""
            try:
                status = {
                    'system': {
                        'status': 'running' if self._is_system_running() else 'stopped',
                        'uptime': self._get_uptime(),
                        'last_detection': self._get_last_detection(),
                        'total_detections': self._get_total_detections(),
                    },
                    'camera': {
                        'connected': self._is_camera_connected(),
                        'resolution': self.config.get('camera', {}).get('width', 0),
                        'fps': self.config.get('camera', {}).get('fps', 0),
                    },
                    'ai': {
                        'model_loaded': self._is_model_loaded(),
                        'confidence_threshold': self.config.get('ai', {}).get('confidence_threshold', 0.5),
                        'classes': self.config.get('ai', {}).get('classes', []),
                    },
                    'notifications': {
                        'audio_enabled': self.config.get('notifications', {}).get('audio', {}).get('enabled', False),
                        'sms_enabled': self.config.get('notifications', {}).get('sms', {}).get('enabled', False),
                        'email_enabled': self.config.get('notifications', {}).get('email', {}).get('enabled', False),
                    }
                }
                return jsonify(status)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/detections')
        def api_detections():
            """Get recent detections."""
            try:
                limit = request.args.get('limit', 50, type=int)
                offset = request.args.get('offset', 0, type=int)
                
                detections = self._get_recent_detections(limit, offset)
                return jsonify(detections)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/detections/<int:detection_id>')
        def api_detection_detail(detection_id):
            """Get detailed information about a specific detection."""
            try:
                detection = self._get_detection_detail(detection_id)
                if detection:
                    return jsonify(detection)
                else:
                    return jsonify({'error': 'Detection not found'}), 404
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/detections/<int:detection_id>/image')
        def api_detection_image(detection_id):
            """Get detection image."""
            try:
                image_path = self._get_detection_image(detection_id)
                if image_path and os.path.exists(image_path):
                    return send_file(image_path, mimetype='image/jpeg')
                else:
                    return jsonify({'error': 'Image not found'}), 404
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/config')
        def api_get_config():
            """Get current configuration."""
            try:
                return jsonify(self.config)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/config', methods=['POST'])
        def api_update_config():
            """Update configuration."""
            try:
                new_config = request.get_json()
                if not new_config:
                    return jsonify({'error': 'No configuration provided'}), 400
                
                # Validate configuration
                if self._validate_config(new_config):
                    # Update configuration
                    self.config_manager.update_config(new_config)
                    self.config = new_config
                    
                    # Restart components if needed
                    self._restart_components()
                    
                    return jsonify({'message': 'Configuration updated successfully'})
                else:
                    return jsonify({'error': 'Invalid configuration'}), 400
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/camera/test')
        def api_test_camera():
            """Test camera connection."""
            try:
                if self._test_camera():
                    return jsonify({'message': 'Camera test successful'})
                else:
                    return jsonify({'error': 'Camera test failed'}), 500
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/ai/test')
        def api_test_ai():
            """Test AI model."""
            try:
                if self._test_ai_model():
                    return jsonify({'message': 'AI model test successful'})
                else:
                    return jsonify({'error': 'AI model test failed'}), 500
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/alerts/test')
        def api_test_alerts():
            """Test alert system."""
            try:
                if self._test_alert_system():
                    return jsonify({'message': 'Alert system test successful'})
                else:
                    return jsonify({'error': 'Alert system test failed'}), 500
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/system/restart')
        def api_restart_system():
            """Restart SkyGuard system."""
            try:
                self._restart_system()
                return jsonify({'message': 'System restart initiated'})
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/logs')
        def api_get_logs():
            """Get system logs."""
            try:
                limit = request.args.get('limit', 100, type=int)
                logs = self._get_system_logs(limit)
                return jsonify(logs)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/stats')
        def api_get_stats():
            """Get system statistics."""
            try:
                stats = self._get_system_stats()
                return jsonify(stats)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
    
    def _initialize_components(self):
        """Initialize SkyGuard components."""
        try:
            # Initialize detector
            self.detector = RaptorDetector(self.config)
            
            # Initialize camera
            self.camera = CameraManager(self.config)
            
            # Initialize alert system
            self.alert_system = AlertSystem(self.config)
            
        except Exception as e:
            print(f"Warning: Failed to initialize components: {e}")
    
    def _is_system_running(self) -> bool:
        """Check if SkyGuard system is running."""
        try:
            # Check if main process is running
            import psutil
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if 'skyguard' in ' '.join(proc.info['cmdline'] or []):
                    return True
            return False
        except:
            return False
    
    def _get_uptime(self) -> str:
        """Get system uptime."""
        try:
            import psutil
            uptime = psutil.boot_time()
            return datetime.fromtimestamp(uptime).strftime('%Y-%m-%d %H:%M:%S')
        except:
            return "Unknown"
    
    def _get_last_detection(self) -> Optional[Dict[str, Any]]:
        """Get last detection information."""
        try:
            # Query event logger for last detection
            events = self.event_logger.get_events(event_type='detection', limit=1)
            if events:
                return events[0]
            return None
        except:
            return None
    
    def _get_total_detections(self) -> int:
        """Get total number of detections."""
        try:
            # Query event logger for total detections
            events = self.event_logger.get_events(event_type='detection')
            return len(events)
        except:
            return 0
    
    def _is_camera_connected(self) -> bool:
        """Check if camera is connected."""
        try:
            if self.camera:
                return self.camera.test_connection()
            return False
        except:
            return False
    
    def _is_model_loaded(self) -> bool:
        """Check if AI model is loaded."""
        try:
            if self.detector:
                return self.detector.model is not None
            return False
        except:
            return False
    
    def _get_recent_detections(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Get recent detections."""
        try:
            events = self.event_logger.get_events(
                event_type='detection', 
                limit=limit, 
                offset=offset
            )
            return events
        except:
            return []
    
    def _get_detection_detail(self, detection_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific detection."""
        try:
            # This would query the database for specific detection details
            # For now, return a placeholder
            return {
                'id': detection_id,
                'timestamp': datetime.now().isoformat(),
                'confidence': 0.85,
                'class': 'bird',
                'bbox': [100, 100, 200, 200],
                'image_path': f'data/detections/detection_{detection_id}.jpg'
            }
        except:
            return None
    
    def _get_detection_image(self, detection_id: int) -> Optional[str]:
        """Get path to detection image."""
        try:
            image_path = f'data/detections/detection_{detection_id}.jpg'
            if os.path.exists(image_path):
                return image_path
            return None
        except:
            return None
    
    def _validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate configuration."""
        try:
            # Basic validation
            required_sections = ['system', 'camera', 'ai', 'notifications']
            for section in required_sections:
                if section not in config:
                    return False
            
            # Validate camera settings
            camera = config.get('camera', {})
            if not isinstance(camera.get('width'), int) or camera.get('width') <= 0:
                return False
            if not isinstance(camera.get('height'), int) or camera.get('height') <= 0:
                return False
            if not isinstance(camera.get('fps'), int) or camera.get('fps') <= 0:
                return False
            
            # Validate AI settings
            ai = config.get('ai', {})
            if not isinstance(ai.get('confidence_threshold'), (int, float)):
                return False
            if not 0 <= ai.get('confidence_threshold', 0) <= 1:
                return False
            
            return True
        except:
            return False
    
    def _restart_components(self):
        """Restart SkyGuard components."""
        try:
            self._initialize_components()
        except Exception as e:
            print(f"Warning: Failed to restart components: {e}")
    
    def _test_camera(self) -> bool:
        """Test camera connection."""
        try:
            if self.camera:
                return self.camera.test_connection()
            return False
        except:
            return False
    
    def _test_ai_model(self) -> bool:
        """Test AI model."""
        try:
            if self.detector:
                return self.detector.load_model()
            return False
        except:
            return False
    
    def _test_alert_system(self) -> bool:
        """Test alert system."""
        try:
            if self.alert_system:
                # Send test alert
                test_detection = {
                    'timestamp': datetime.now().isoformat(),
                    'confidence': 0.9,
                    'class': 'bird',
                    'bbox': [100, 100, 200, 200]
                }
                self.alert_system.send_alert("Test alert from SkyGuard", test_detection)
                return True
            return False
        except:
            return False
    
    def _restart_system(self):
        """Restart SkyGuard system."""
        try:
            # This would restart the main SkyGuard process
            # For now, just restart components
            self._restart_components()
        except Exception as e:
            print(f"Warning: Failed to restart system: {e}")
    
    def _get_system_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get system logs."""
        try:
            # This would read from log files
            # For now, return placeholder
            return [
                {
                    'timestamp': datetime.now().isoformat(),
                    'level': 'INFO',
                    'message': 'System started',
                    'module': 'skyguard.main'
                }
            ]
        except:
            return []
    
    def _get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics."""
        try:
            import psutil
            
            return {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'uptime': psutil.boot_time(),
                'processes': len(psutil.pids()),
                'detections_today': self._get_detections_today(),
                'detections_this_week': self._get_detections_this_week(),
                'detections_this_month': self._get_detections_this_month(),
            }
        except:
            return {}
    
    def _get_detections_today(self) -> int:
        """Get detections today."""
        try:
            today = datetime.now().date()
            events = self.event_logger.get_events(
                event_type='detection',
                start_date=today
            )
            return len(events)
        except:
            return 0
    
    def _get_detections_this_week(self) -> int:
        """Get detections this week."""
        try:
            week_ago = datetime.now() - timedelta(days=7)
            events = self.event_logger.get_events(
                event_type='detection',
                start_date=week_ago.date()
            )
            return len(events)
        except:
            return 0
    
    def _get_detections_this_month(self) -> int:
        """Get detections this month."""
        try:
            month_ago = datetime.now() - timedelta(days=30)
            events = self.event_logger.get_events(
                event_type='detection',
                start_date=month_ago.date()
            )
            return len(events)
        except:
            return 0
    
    def run(self, host: str = '0.0.0.0', port: int = 8080, debug: bool = False):
        """Run the web portal."""
        print(f"🌐 Starting SkyGuard Web Portal on http://{host}:{port}")
        self.app.run(host=host, port=port, debug=debug)


def main():
    """Main function to run the web portal."""
    import argparse
    
    parser = argparse.ArgumentParser(description='SkyGuard Web Portal')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8080, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--config', default='config/skyguard.yaml', help='Configuration file path')
    
    args = parser.parse_args()
    
    # Create web portal
    portal = SkyGuardWebPortal(args.config)
    
    # Run the portal
    portal.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
