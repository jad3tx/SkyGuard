#!/usr/bin/env python3
"""
SkyGuard Web Portal Application

A Flask-based web interface for managing SkyGuard configuration and monitoring detections.
"""

import os
import sys
import json
import time
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
        
        # Load configuration first
        self.config = self.config_manager.get_config()
        
        # Initialize event logger with config
        self.event_logger = EventLogger(self.config.get('storage', {}))
        # Ensure database/paths exist for read APIs
        try:
            self.event_logger.initialize()
        except Exception:
            pass
        self.detector = None
        self.camera = None
        self.alert_system = None
        
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
                        'memory_usage': self._get_memory_usage(),
                    },
                    'camera': {
                        'connected': self._is_camera_connected(),
                        'source': self.config.get('camera', {}).get('source', 0),
                        'width': self.config.get('camera', {}).get('width', 640),
                        'height': self.config.get('camera', {}).get('height', 480),
                        'fps': self.config.get('camera', {}).get('fps', 30),
                    },
                    'ai': {
                        'loaded': self._is_model_loaded(),
                        'model_path': self.config.get('ai', {}).get('model_path', 'models/yolo11n-seg.pt'),
                        'confidence_threshold': self.config.get('ai', {}).get('confidence_threshold', 0.5),
                        'classes': self.config.get('ai', {}).get('classes', []),
                    },
                    'detections': {
                        'total': self._get_total_detections(),
                        'recent': len(self._get_recent_detections(limit=5)),
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
                total = self._get_total_detections()
                page = (offset // limit) + 1
                
                return jsonify({
                    'detections': detections,
                    'total': total,
                    'page': page,
                    'limit': limit
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/detections/<int:detection_id>')
        def api_detection_detail(detection_id: int):
            """Get detailed information about a specific detection."""
            try:
                detection = self.event_logger.get_detection_by_id(detection_id)
                if detection:
                    # Normalize response keys for web consumption
                    return jsonify({
                        'id': detection.get('id', 0),
                        'timestamp': detection.get('timestamp', ''),
                        'confidence': detection.get('confidence', 0.0),
                        'class': detection.get('class_name', 'bird'),
                        'bbox': detection.get('bbox', [0, 0, 0, 0]),
                        'image_path': detection.get('image_path', ''),
                        'metadata': detection.get('metadata', {}),
                    })
                return jsonify({'error': 'Detection not found'}), 404
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/detections/<int:detection_id>/image')
        def api_detection_image(detection_id: int):
            """Get detection image."""
            try:
                record = self.event_logger.get_detection_by_id(detection_id)
                image_path = (record or {}).get('image_path')
                if image_path:
                    # Resolve relative paths to absolute within project root
                    abs_path = image_path
                    if not os.path.isabs(abs_path):
                        abs_path = os.path.abspath(os.path.join(project_root, image_path))
                    if os.path.exists(abs_path):
                        return send_file(abs_path, mimetype='image/jpeg')
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
                # Check if request has JSON content
                if not request.is_json:
                    return jsonify({'error': 'Content-Type must be application/json'}), 400
                
                try:
                    new_config = request.get_json()
                except Exception as e:
                    return jsonify({'error': 'Invalid JSON data'}), 400
                
                if not new_config:
                    return jsonify({'error': 'No configuration provided'}), 400
                
                # Validate configuration
                if self._validate_config(new_config):
                    # Update configuration
                    self.config_manager.update_config(new_config)
                    self.config = new_config
                    
                    # Only restart components if camera settings changed
                    if 'camera' in new_config:
                        try:
                            self._restart_components()
                        except Exception as e:
                            print(f"⚠️ Component restart failed: {e}")
                            # Continue anyway - configuration is saved
                    
                    return jsonify({'success': True, 'message': 'Configuration updated successfully'})
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
        
        @self.app.route('/api/camera/status')
        def api_camera_status():
            """Get camera status."""
            try:
                # Check if camera snapshot file exists and is recent
                import os
                import time
                snapshot_file = "data/camera_snapshot.jpg"
                
                if os.path.exists(snapshot_file):
                    # Check if file is recent (within last 10 seconds)
                    file_time = os.path.getmtime(snapshot_file)
                    current_time = time.time()
                    is_recent = (current_time - file_time) < 10
                    
                    return jsonify({
                        'connected': is_recent,
                        'source': self.config.get('camera', {}).get('source', 0),
                        'width': self.config.get('camera', {}).get('width', 640),
                        'height': self.config.get('camera', {}).get('height', 480),
                        'fps': self.config.get('camera', {}).get('fps', 30)
                    })
                else:
                    return jsonify({'connected': False, 'error': 'No camera snapshot available'})
            except Exception as e:
                return jsonify({'connected': False, 'error': str(e)})
        
        @self.app.route('/api/camera/feed')
        def api_camera_feed():
            """Get camera feed frame."""
            try:
                import os
                
                # Read the snapshot file directly
                snapshot_file = "data/camera_snapshot.jpg"
                
                if os.path.exists(snapshot_file):
                    with open(snapshot_file, 'rb') as f:
                        feed_bytes = f.read()
                    
                    from flask import Response
                    return Response(feed_bytes, mimetype='image/jpeg')
                else:
                    # Create a simple test image if no snapshot available
                    import cv2
                    import numpy as np
                    
                    # Create a test image
                    img = np.zeros((480, 640, 3), dtype=np.uint8)
                    
                    # Add a gradient background
                    for y in range(480):
                        for x in range(640):
                            img[y, x] = [int(255 * y / 480), int(255 * x / 640), 100]
                    
                    # Add text
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    cv2.putText(img, 'SkyGuard Camera Feed', (50, 100), font, 1, (255, 255, 255), 2)
                    cv2.putText(img, 'No camera snapshot available', (50, 150), font, 0.7, (200, 200, 200), 2)
                    cv2.putText(img, 'Main process not running', (50, 200), font, 0.7, (200, 200, 200), 2)
                    
                    # Add timestamp
                    import time
                    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                    cv2.putText(img, timestamp, (50, 400), font, 0.5, (150, 150, 150), 1)
                    
                    # Encode as JPEG
                    ret, buffer = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    if ret:
                        from flask import Response
                        return Response(buffer.tobytes(), mimetype='image/jpeg')
                    else:
                        return "Failed to create test image", 500
                
            except Exception as e:
                return f"Camera feed error: {str(e)}", 500
        
        @self.app.route('/api/camera/capture')
        def api_camera_capture():
            """Capture and download image."""
            try:
                import os
                import time
                
                # Read the snapshot file directly
                snapshot_file = "data/camera_snapshot.jpg"
                
                if os.path.exists(snapshot_file):
                    with open(snapshot_file, 'rb') as f:
                        image_data = f.read()
                    
                    from flask import Response
                    return Response(
                        image_data,
                        mimetype='image/jpeg',
                        headers={'Content-Disposition': f'attachment; filename=skyguard_capture_{int(time.time())}.jpg'}
                    )
                else:
                    return "No camera snapshot available", 404
                
            except Exception as e:
                return f"Camera capture error: {str(e)}", 500
        
        @self.app.route('/api/ai/test')
        def api_test_ai():
            """Test AI model."""
            try:
                if self._test_ai_model():
                    return jsonify({
                        'success': True, 
                        'message': 'AI model test successful',
                        'model_loaded': self._is_model_loaded()
                    })
                else:
                    return jsonify({'error': 'AI model test failed'}), 500
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/alerts/test')
        def api_test_alerts():
            """Test alert system."""
            try:
                if self._test_alert_system():
                    return jsonify({
                        'success': True,
                        'message': 'Alert system test successful',
                        'audio_enabled': self.config.get('notifications', {}).get('audio', {}).get('enabled', False),
                        'sms_enabled': self.config.get('notifications', {}).get('sms', {}).get('enabled', False),
                        'email_enabled': self.config.get('notifications', {}).get('email', {}).get('enabled', False)
                    })
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
                return jsonify({
                    'logs': logs,
                    'total_lines': len(logs)
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/stats')
        def api_get_stats():
            """Get system statistics."""
            try:
                stats = self._get_system_stats()
                return jsonify({
                    'detections': {
                        'total': self._get_total_detections(),
                        'today': stats.get('detections_today', 0),
                        'this_week': stats.get('detections_this_week', 0),
                        'this_month': stats.get('detections_this_month', 0)
                    },
                    'system': {
                        'uptime': stats.get('uptime', 0),
                        'memory_usage': stats.get('memory_percent', 0),
                        'cpu_usage': stats.get('cpu_percent', 0),
                        'disk_usage': stats.get('disk_percent', 0),
                        'processes': stats.get('processes', 0)
                    },
                    'performance': {
                        'avg_detection_time': 0.5,  # Placeholder
                        'fps': self.config.get('camera', {}).get('fps', 30),
                        'model_accuracy': 0.85,  # Placeholder
                        'total_detections': self._get_total_detections()
                    }
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/system/restart', methods=['POST'])
        def api_system_restart():
            """Restart the system."""
            try:
                # Log the restart request
                self.event_logger.log_system_event('system_restart', 'System restart requested via web portal', 'INFO', {
                    'timestamp': time.time()
                })
                
                # Return success response
                return jsonify({
                    'success': True,
                    'message': 'System restart initiated',
                    'timestamp': time.time()
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500
    
    def _initialize_components(self):
        """Initialize SkyGuard components."""
        try:
            # Initialize detector with AI config
            ai_config = self.config.get('ai', {})
            self.detector = RaptorDetector(ai_config)
            # Load the model
            if self.detector.load_model():
                print("✅ Detector initialized and model loaded successfully")
            else:
                print("⚠️ Detector initialized but model loading failed")
            
            # Web portal does NOT access camera directly - it only reads snapshots
            # The main SkyGuard system handles all camera operations
            self.camera = None
            print("ℹ️ Web portal configured to read camera snapshots (no direct camera access)")
            
            # Initialize alert system
            self.alert_system = AlertSystem(self.config.get('notifications', {}))
            print("✅ Alert system initialized successfully")
            
        except Exception as e:
            print(f"❌ Failed to initialize components: {e}")
            import traceback
            traceback.print_exc()
    
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
    
    def _get_uptime(self) -> float:
        """Get system uptime in seconds."""
        try:
            import psutil
            import time
            boot_time = psutil.boot_time()
            current_time = time.time()
            return current_time - boot_time
        except:
            return 0.0
    
    def _get_memory_usage(self) -> Dict[str, Any]:
        """Get system memory usage."""
        try:
            import psutil
            memory = psutil.virtual_memory()
            return {
                'total': memory.total,
                'available': memory.available,
                'used': memory.used,
                'percentage': memory.percent
            }
        except:
            return {
                'total': 0,
                'available': 0,
                'used': 0,
                'percentage': 0
            }
    
    def _get_last_detection(self) -> Optional[Dict[str, Any]]:
        """Get last detection information."""
        try:
            # Query event logger for last detection
            detections = self.event_logger.get_detections(limit=1)
            if detections:
                detection = detections[0]
                return {
                    'id': detection.get('id', 0),
                    'timestamp': detection.get('timestamp', ''),
                    'confidence': detection.get('confidence', 0.0),
                    'class': detection.get('class_name', 'bird'),
                    'bbox': detection.get('bbox', [0, 0, 0, 0])
                }
            return None
        except:
            return None
    
    def _get_total_detections(self) -> int:
        """Get total number of detections."""
        try:
            # Query event logger for total detections
            detections = self.event_logger.get_detections(limit=10000)  # Get a large number to count all
            return len(detections)
        except:
            return 0
    
    def _is_camera_connected(self) -> bool:
        """Check if camera is connected in the main system."""
        try:
            # Check if the main system is running by looking for recent camera snapshots
            import os
            import time
            
            snapshot_file = "data/camera_snapshot.jpg"
            if os.path.exists(snapshot_file):
                # Check if file is recent (within last 10 seconds)
                file_time = os.path.getmtime(snapshot_file)
                current_time = time.time()
                is_recent = (current_time - file_time) < 10
                
                if is_recent:
                    # Check if the snapshot file is larger than a placeholder (real camera data)
                    file_size = os.path.getsize(snapshot_file)
                    return file_size > 50000  # Real camera images are typically > 50KB
            
            return False
        except:
            return False
    
    def _is_model_loaded(self) -> bool:
        """Check if AI model is loaded in the web portal's detector."""
        try:
            # Directly check if the detector's model is loaded
            if self.detector:
                # Check if the detector has a loaded model
                return self.detector.model is not None and self.detector.model != "dummy"
            return False
        except:
            return False
    
    def _get_recent_detections(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Get recent detections."""
        try:
            detections = self.event_logger.get_detections(limit=limit)
            # Convert to expected format
            formatted_detections = []
            for detection in detections:
                formatted_detection = {
                    'id': detection.get('id', 0),
                    'timestamp': detection.get('timestamp', ''),
                    'confidence': detection.get('confidence', 0.0),
                    'class': detection.get('class_name', 'bird'),
                    'bbox': detection.get('bbox', [0, 0, 0, 0]),
                    'image_path': detection.get('image_path', '')
                }
                formatted_detections.append(formatted_detection)
            return formatted_detections
        except:
            return []
    
    # Removed placeholder detection detail/image helpers in favor of DB-backed methods
    
    def _validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate configuration."""
        try:
            # More flexible validation - only validate what's provided
            if not config:
                return False
            
            # Validate camera settings if provided
            if 'camera' in config:
                camera = config['camera']
                if 'width' in camera and (not isinstance(camera['width'], int) or camera['width'] <= 0):
                    return False
                if 'height' in camera and (not isinstance(camera['height'], int) or camera['height'] <= 0):
                    return False
                if 'fps' in camera and (not isinstance(camera['fps'], int) or camera['fps'] <= 0):
                    return False
            
            # Validate AI settings if provided
            if 'ai' in config:
                ai = config['ai']
                if 'confidence_threshold' in ai and not isinstance(ai['confidence_threshold'], (int, float)):
                    return False
                if 'confidence_threshold' in ai and not (0 <= ai['confidence_threshold'] <= 1):
                    return False
                if 'nms_threshold' in ai and not isinstance(ai['nms_threshold'], (int, float)):
                    return False
                if 'nms_threshold' in ai and not (0 <= ai['nms_threshold'] <= 1):
                    return False
            
            # Validate system settings if provided
            if 'system' in config:
                system = config['system']
                if 'detection_interval' in system and not isinstance(system['detection_interval'], (int, float)):
                    return False
                if 'max_detection_history' in system and not isinstance(system['max_detection_history'], int):
                    return False
            
            return True
        except:
            return False
    
    def _restart_components(self):
        """Restart SkyGuard components."""
        try:
            print("🔄 Restarting components after configuration update...")
            self._initialize_components()
            print("✅ Components restarted successfully")
        except Exception as e:
            print(f"⚠️ Warning: Failed to restart components: {e}")
            # Don't crash the web portal if component restart fails
    
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
                # Check if model is already loaded
                if self.detector.model is not None:
                    return True
                # Try to load model
                return self.detector.load_model()
            return False
        except Exception as e:
            print(f"AI model test failed: {e}")
            return False
    
    def _test_alert_system(self) -> bool:
        """Test alert system."""
        try:
            if self.alert_system:
                # Send test alert
                test_detection = {
                    'timestamp': time.time(),
                    'confidence': 0.9,
                    'class_name': 'bird',
                    'bbox': [100, 100, 200, 200]
                }
                return self.alert_system.send_raptor_alert(test_detection)
            return False
        except Exception as e:
            print(f"Alert system test failed: {e}")
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
            start_time = datetime.combine(today, datetime.min.time()).timestamp()
            end_time = datetime.combine(today, datetime.max.time()).timestamp()
            
            detections = self.event_logger.get_detections(
                start_time=start_time,
                end_time=end_time
            )
            return len(detections)
        except:
            return 0
    
    def _get_detections_this_week(self) -> int:
        """Get detections this week."""
        try:
            week_ago = datetime.now() - timedelta(days=7)
            start_time = week_ago.timestamp()
            end_time = datetime.now().timestamp()
            
            detections = self.event_logger.get_detections(
                start_time=start_time,
                end_time=end_time
            )
            return len(detections)
        except:
            return 0
    
    def _get_detections_this_month(self) -> int:
        """Get detections this month."""
        try:
            month_ago = datetime.now() - timedelta(days=30)
            start_time = month_ago.timestamp()
            end_time = datetime.now().timestamp()
            
            detections = self.event_logger.get_detections(
                start_time=start_time,
                end_time=end_time
            )
            return len(detections)
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
