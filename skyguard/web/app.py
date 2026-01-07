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
        
        # Setup logger
        import logging
        self.logger = logging.getLogger(__name__)
        
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
        
        # Track last reload attempt to prevent excessive reloads
        self._last_reload_attempt = 0
        self._reload_cooldown = 60  # Only attempt reload once per minute
        
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
                        'model_loaded': self._is_model_loaded(),  # Alias for consistency
                        'model_path': self.config.get('ai', {}).get('model_path', 'models/yolo11n-seg.pt'),
                        'confidence_threshold': self.config.get('ai', {}).get('confidence_threshold', 0.5),
                        'detection_log_level': self.config.get('ai', {}).get('detection_log_level', 'standard'),
                        'classes': self.config.get('ai', {}).get('classes', []),
                        'species_model_loaded': self._is_species_model_loaded(),
                    },
                    'detections': {
                        'total': self._get_total_detections(),
                        'recent': len(self._get_recent_detections(limit=5)),
                    },
                    'notifications': {
                        'audio_enabled': self.config.get('notifications', {}).get('audio', {}).get('enabled', False),
                        'sms_enabled': self.config.get('notifications', {}).get('sms', {}).get('enabled', False),
                        'email_enabled': self.config.get('notifications', {}).get('email', {}).get('enabled', False),
                        'discord_enabled': self.config.get('notifications', {}).get('discord', {}).get('enabled', False),
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
                species = request.args.get('species', None, type=str)
                class_name = request.args.get('class', None, type=str)
                
                detections = self._get_recent_detections(limit, offset, species=species, class_name=class_name)
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
                        'species': detection.get('species_name'),
                        'species_confidence': detection.get('species_confidence'),
                        'segmented_image_path': detection.get('segmented_image_path'),
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
        
        @self.app.route('/api/detections/<int:detection_id>/segmented')
        def api_detection_segmented_image(detection_id: int):
            """Get segmented detection image with species annotations."""
            try:
                record = self.event_logger.get_detection_by_id(detection_id)
                segmented_image_path = (record or {}).get('segmented_image_path')
                if segmented_image_path:
                    # Resolve relative paths to absolute within project root
                    abs_path = segmented_image_path
                    if not os.path.isabs(abs_path):
                        abs_path = os.path.abspath(os.path.join(project_root, segmented_image_path))
                    if os.path.exists(abs_path):
                        return send_file(abs_path, mimetype='image/jpeg')
                # Fallback to regular image if segmented not available
                image_path = (record or {}).get('image_path')
                if image_path:
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
                    
                    # Restart components if camera or AI settings changed
                    if 'camera' in new_config or 'ai' in new_config:
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
        
        @self.app.route('/api/ai/stats')
        def api_ai_stats():
            """Get AI model statistics and metrics."""
            try:
                ai_config = self.config.get('ai', {})
                
                # Get detector stats if available
                detector_stats = {}
                if self.detector:
                    try:
                        detector_stats = self.detector.get_detection_stats()
                    except Exception:
                        pass
                
                # Get detection statistics from event logger
                detection_stats = {}
                try:
                    # Get stats for last 7 days
                    detection_stats = self.event_logger.get_detection_stats(days=7)
                except Exception:
                    pass
                
                # Get recent detections for confidence stats
                recent_detections = []
                confidence_stats = {
                    'avg': 0.0,
                    'min': 1.0,
                    'max': 0.0,
                    'count': 0
                }
                species_stats = {
                    'total_classifications': 0,
                    'successful_identifications': 0,
                    'species_breakdown': {}
                }
                
                try:
                    recent_detections = self.event_logger.get_detections(limit=100)
                    if recent_detections:
                        confidences = [d.get('confidence', 0.0) for d in recent_detections if d.get('confidence')]
                        if confidences:
                            confidence_stats = {
                                'avg': sum(confidences) / len(confidences),
                                'min': min(confidences),
                                'max': max(confidences),
                                'count': len(confidences)
                            }
                        
                        # Species statistics
                        species_detections = [d for d in recent_detections if d.get('species')]
                        species_stats['total_classifications'] = len([d for d in recent_detections if d.get('species_confidence')])
                        species_stats['successful_identifications'] = len(species_detections)
                        
                        # Species breakdown
                        for det in species_detections:
                            species = det.get('species', 'Unknown')
                            if species not in species_stats['species_breakdown']:
                                species_stats['species_breakdown'][species] = {
                                    'count': 0,
                                    'avg_confidence': 0.0,
                                    'confidences': []
                                }
                            species_stats['species_breakdown'][species]['count'] += 1
                            if det.get('species_confidence'):
                                species_stats['species_breakdown'][species]['confidences'].append(
                                    det.get('species_confidence')
                                )
                        
                        # Calculate averages
                        for species in species_stats['species_breakdown']:
                            confs = species_stats['species_breakdown'][species]['confidences']
                            if confs:
                                species_stats['species_breakdown'][species]['avg_confidence'] = sum(confs) / len(confs)
                except Exception:
                    pass
                
                # Model information
                model_info = {
                    'model_path': ai_config.get('model_path', 'Not configured'),
                    'model_type': ai_config.get('model_type', 'yolo'),
                    'input_size': ai_config.get('input_size', 1080),
                    'confidence_threshold': ai_config.get('confidence_threshold', 0.6),
                    'nms_threshold': ai_config.get('nms_threshold', 0.5),
                    'detection_log_level': ai_config.get('detection_log_level', 'standard'),
                    'model_loaded': self._is_model_loaded(),
                }
                
                # Species model information
                species_model_loaded = False
                species_model_path = ai_config.get('species_model_path')
                species_model_error = None
                
                if self.detector:
                    try:
                        # YOLO models are callable directly, not via .predict() method
                        # Check if model exists and is callable (or has predict method for compatibility)
                        species_model_loaded = (
                            self.detector.species_model is not None 
                            and self.detector.species_model != "dummy"
                            and (callable(self.detector.species_model) or hasattr(self.detector.species_model, 'predict'))
                        )
                        # If path is configured but model not loaded, try to diagnose
                        if species_model_path and not species_model_loaded:
                            # Check if the model file exists
                            try:
                                from pathlib import Path
                                resolved_path = self.detector._resolve_model_path(species_model_path)
                                if not resolved_path.exists():
                                    species_model_error = f"Model file not found: {resolved_path}"
                                    self.logger.warning(f"Species model path configured but file not found: {resolved_path}")
                            except Exception as path_err:
                                species_model_error = f"Path resolution error: {path_err}"
                                self.logger.warning(f"Failed to resolve species model path: {path_err}")
                    except Exception as e:
                        species_model_error = f"Error checking species model: {e}"
                        self.logger.error(f"Error checking species model status: {e}")
                
                species_model_info = {
                    'enabled': bool(species_model_path),
                    'model_loaded': species_model_loaded,
                    'model_path': species_model_path or 'Not configured',
                    'backend': ai_config.get('species_backend', 'ultralytics'),
                    'input_size': ai_config.get('species_input_size', [224, 224]),
                    'confidence_threshold': ai_config.get('species_confidence_threshold', 0.3),
                    'error': species_model_error,
                }
                
                return jsonify({
                    'model': model_info,
                    'species_model': species_model_info,
                    'detector_stats': detector_stats,
                    'detection_stats': detection_stats,
                    'confidence_stats': confidence_stats,
                    'species_stats': species_stats,
                    'recent_detections_count': len(recent_detections)
                })
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
                        'email_enabled': self.config.get('notifications', {}).get('email', {}).get('enabled', False),
                        'discord_enabled': self.config.get('notifications', {}).get('discord', {}).get('enabled', False)
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
                limit = request.args.get('limit', 500, type=int)
                since = request.args.get('since', None, type=float)  # Unix timestamp
                logs = self._get_system_logs(limit, since)
                return jsonify({
                    'logs': logs,
                    'total_lines': len(logs),
                    'last_timestamp': logs[-1]['timestamp'] if logs else None
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
        
        @self.app.route('/api/species/stats')
        def api_species_stats():
            """Get species detection statistics for reporting."""
            try:
                days = request.args.get('days', None, type=int)
                stats = self.event_logger.get_species_stats(days=days)
                return jsonify(stats)
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/system/restart', methods=['POST'])
        def api_system_restart():
            """Restart the system."""
            try:
                # Attempt to restart the system
                self._restart_system()
                
                # Return success response
                return jsonify({
                    'success': True,
                    'message': 'System restart initiated successfully',
                    'timestamp': time.time()
                })
            except Exception as e:
                self.logger.error(f"Restart failed: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'message': 'System restart failed. Check logs for details.',
                    'timestamp': time.time()
                }), 500
    
    def _initialize_components(self):
        """Initialize SkyGuard components."""
        try:
            # Initialize detector with AI config
            ai_config = self.config.get('ai', {})
            self.detector = RaptorDetector(ai_config)
            # Load the model
            if self.detector.load_model():
                print("✅ Detector initialized and model loaded successfully")
                # Check species model status
                species_path = ai_config.get('species_model_path')
                if species_path:
                    if self.detector.species_model is not None:
                        print(f"✅ Species model loaded: {species_path}")
                    else:
                        print(f"⚠️ Species model path configured ({species_path}) but model not loaded")
                        # Try to diagnose the issue
                        try:
                            from pathlib import Path
                            resolved = self.detector._resolve_model_path(species_path)
                            if resolved.exists():
                                print(f"   Model file exists at: {resolved}")
                                print(f"   Attempting to reload species model...")
                                self.detector._init_species_backend()
                                if self.detector.species_model is not None:
                                    print(f"   ✅ Species model reloaded successfully")
                                else:
                                    print(f"   ❌ Species model still not loaded - check logs for errors")
                            else:
                                print(f"   ❌ Model file not found at: {resolved}")
                                print(f"   Please verify the path in config/skyguard.yaml")
                        except Exception as e:
                            print(f"   ❌ Error checking species model: {e}")
                else:
                    print("ℹ️ Species model not configured (species_model_path not set)")
            else:
                print("⚠️ Detector initialized but model loading failed")
            
            # Web portal does NOT access camera directly - it only reads snapshots
            # The main SkyGuard system handles all camera operations
            self.camera = None
            print("ℹ️ Web portal configured to read camera snapshots (no direct camera access)")
            
            # Initialize alert system
            rate_limiting_config = self.config.get('rate_limiting', {})
            self.alert_system = AlertSystem(
                self.config.get('notifications', {}),
                rate_limiting_config=rate_limiting_config
            )
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
            # Use efficient COUNT query instead of loading all detections
            return self.event_logger.count_detections()
        except Exception as e:
            self.logger.error(f"Failed to get total detections: {e}")
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
        """Check if AI model is loaded in the web portal's detector.
        
        YOLO models from ultralytics are callable directly, not via .predict() method.
        This method checks if the model is callable or has a predict method for compatibility.
        """
        try:
            # Directly check if the detector's model is loaded
            if self.detector:
                # Check if the detector has a loaded model
                # YOLO models are callable directly, not via .predict() method
                # Check if model is callable OR has predict method (for compatibility)
                is_loaded = (
                    self.detector.model is not None 
                    and self.detector.model != "dummy"
                    and (callable(self.detector.model) or hasattr(self.detector.model, 'predict'))
                )
                
                # If model is not loaded but detector exists, try to reload it (with rate limiting)
                if not is_loaded:
                    current_time = time.time()
                    if current_time - self._last_reload_attempt > self._reload_cooldown:
                        self._last_reload_attempt = current_time
                        self.logger.warning("Detection model appears unloaded, attempting to reload...")
                        if self._reload_detector_models():
                            is_loaded = (
                                self.detector.model is not None 
                                and self.detector.model != "dummy"
                                and (callable(self.detector.model) or hasattr(self.detector.model, 'predict'))
                            )
                            if is_loaded:
                                self.logger.info("Detection model reloaded successfully")
                            else:
                                self.logger.error("Failed to reload detection model")
                        else:
                            self.logger.warning("Reload attempt failed, will retry after cooldown")
                    else:
                        # Still in cooldown, just log a debug message
                        self.logger.debug(
                            f"Model unloaded but reload cooldown active "
                            f"({int(self._reload_cooldown - (current_time - self._last_reload_attempt))}s remaining)"
                        )
                
                return is_loaded
            else:
                # Detector doesn't exist, try to reinitialize
                self.logger.warning("Detector instance is None, attempting to reinitialize...")
                self._initialize_components()
                if self.detector:
                    return (
                        self.detector.model is not None 
                        and self.detector.model != "dummy"
                        and (callable(self.detector.model) or hasattr(self.detector.model, 'predict'))
                    )
            return False
        except Exception as e:
            self.logger.error(f"Error checking if model is loaded: {e}")
            # Try to reinitialize on error
            try:
                self._initialize_components()
            except Exception as init_error:
                self.logger.error(f"Failed to reinitialize detector: {init_error}")
            return False
    
    def _is_species_model_loaded(self) -> bool:
        """Check if species classification model is loaded in the web portal's detector."""
        try:
            if self.detector:
                # Check if species model is loaded and functional
                # YOLO models are callable directly, not via .predict() method
                is_loaded = (
                    self.detector.species_model is not None 
                    and self.detector.species_model != "dummy"
                    and (callable(self.detector.species_model) or hasattr(self.detector.species_model, 'predict'))
                )
                
                # If species model is not loaded but detector exists, try to reload it (with rate limiting)
                if not is_loaded and self.detector.model is not None:
                    current_time = time.time()
                    if current_time - self._last_reload_attempt > self._reload_cooldown:
                        self._last_reload_attempt = current_time
                        self.logger.warning("Species model appears unloaded, attempting to reload...")
                        if self._reload_detector_models():
                            is_loaded = (
                                self.detector.species_model is not None 
                                and self.detector.species_model != "dummy"
                                and (callable(self.detector.species_model) or hasattr(self.detector.species_model, 'predict'))
                            )
                            if is_loaded:
                                self.logger.info("Species model reloaded successfully")
                            else:
                                self.logger.error("Failed to reload species model")
                        else:
                            self.logger.warning("Reload attempt failed, will retry after cooldown")
                    else:
                        # Still in cooldown, just log a debug message
                        self.logger.debug(
                            f"Species model unloaded but reload cooldown active "
                            f"({int(self._reload_cooldown - (current_time - self._last_reload_attempt))}s remaining)"
                        )
                
                return is_loaded
            else:
                # Detector doesn't exist, try to reinitialize
                self.logger.warning("Detector instance is None, attempting to reinitialize...")
                self._initialize_components()
                if self.detector:
                    return (
                        self.detector.species_model is not None 
                        and self.detector.species_model != "dummy"
                        and (callable(self.detector.species_model) or hasattr(self.detector.species_model, 'predict'))
                    )
            return False
        except Exception as e:
            self.logger.error(f"Error checking if species model is loaded: {e}")
            # Try to reinitialize on error
            try:
                self._initialize_components()
            except Exception as init_error:
                self.logger.error(f"Failed to reinitialize detector: {init_error}")
            return False
    
    def _reload_detector_models(self) -> bool:
        """Attempt to reload detector models without recreating the detector instance.
        
        Returns:
            True if reload was successful, False otherwise
        """
        try:
            if not self.detector:
                return False
            
            # Reload the main detection model
            ai_config = self.config.get('ai', {})
            model_path_str = ai_config.get('model_path', 'models/yolo11n-seg.pt')
            model_path = self.detector._resolve_model_path(model_path_str)
            
            if model_path.exists():
                from ultralytics import YOLO
                self.detector.model = YOLO(str(model_path))
                self.logger.info(f"Reloaded detection model: {model_path}")
            else:
                self.logger.error(f"Cannot reload detection model: {model_path} not found")
                return False
            
            # Reload species model if configured
            if ai_config.get('species_model_path'):
                self.detector._init_species_backend()
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to reload detector models: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
    
    def _get_recent_detections(self, limit: int = 50, offset: int = 0, 
                               species: Optional[str] = None, class_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get recent detections.
        
        Args:
            limit: Maximum number of detections to return
            offset: Number of detections to skip (for pagination)
            species: Optional species filter
            class_name: Optional class name filter
            
        Returns:
            List of formatted detection dictionaries
        """
        try:
            detections = self.event_logger.get_detections(
                limit=limit, 
                offset=offset,
                species_name=species,
                class_name=class_name
            )
            # Convert to expected format
            formatted_detections = []
            for detection in detections:
                formatted_detection = {
                    'id': detection.get('id', 0),
                    'timestamp': detection.get('timestamp', ''),
                    'confidence': detection.get('confidence', 0.0),
                    'class': detection.get('class_name', 'bird'),
                    'bbox': detection.get('bbox', [0, 0, 0, 0]),
                    'image_path': detection.get('image_path', ''),
                    'species': detection.get('species_name'),
                    'species_confidence': detection.get('species_confidence'),
                    'segmented_image_path': detection.get('segmented_image_path')
                }
                formatted_detections.append(formatted_detection)
            return formatted_detections
        except Exception as e:
            self.logger.error(f"Failed to get recent detections: {e}")
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
                if 'detection_log_level' in ai and ai['detection_log_level'] not in ['minimal', 'standard', 'detailed']:
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
            import subprocess
            import platform
            import sys
            from pathlib import Path
            
            # Get project root
            project_root = Path(__file__).parent.parent.parent
            
            # Log the restart request - use logger which writes to file
            self.logger.info("=" * 60)
            self.logger.info("🔄 SYSTEM RESTART INITIATED via web portal")
            self.logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.logger.info("=" * 60)
            
            # Also log to event logger
            try:
                self.event_logger.log_system_event(
                    'system_restart', 
                    'System restart requested via web portal', 
                    'INFO', 
                    {'timestamp': time.time()}
                )
            except Exception:
                pass  # Don't fail if event logger fails
            
            # Find and stop the main SkyGuard process
            if platform.system() == 'Windows':
                # Windows: Find processes running skyguard.main
                try:
                    result = subprocess.run(
                        ['tasklist', '/FI', 'IMAGENAME eq python.exe', '/FO', 'CSV'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    
                    # Also check for pythonw.exe
                    result2 = subprocess.run(
                        ['tasklist', '/FI', 'IMAGENAME eq pythonw.exe', '/FO', 'CSV'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    
                    # Try to find the process by checking command line
                    # Note: This is a simplified approach - in production you might want
                    # to use psutil or wmic for more reliable process detection
                    import psutil
                    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                        try:
                            cmdline = proc.info.get('cmdline', [])
                            if cmdline and any('skyguard.main' in str(arg) for arg in cmdline):
                                # Found the process - terminate it gracefully
                                pid = proc.info['pid']
                                self.logger.info(f"🛑 Stopping SkyGuard main process (PID: {pid})")
                                proc.terminate()
                                self.logger.info(f"   Sent termination signal to PID {pid}")
                                # Wait a bit for graceful shutdown
                                time.sleep(2)
                                # If still running, force kill
                                if proc.is_running():
                                    proc.kill()
                                    self.logger.info(f"   Force killed process PID {pid}")
                                else:
                                    self.logger.info(f"   Process PID {pid} stopped gracefully")
                        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                            continue
                except ImportError:
                    self.logger.warning("psutil not available, cannot find SkyGuard process")
                except Exception as e:
                    self.logger.warning(f"Could not find/stop SkyGuard process: {e}")
            else:
                # Linux/Mac: Use pkill
                try:
                    subprocess.run(['pkill', '-f', 'skyguard.main'], timeout=5, check=False)
                    time.sleep(2)
                except Exception as e:
                    self.logger.warning(f"Could not stop SkyGuard process: {e}")
            
            # Restart the main system
            # Note: This will start it in the background
            python_exe = sys.executable
            main_script = project_root / "skyguard" / "main.py"
            
            if platform.system() == 'Windows':
                # Windows: Start in background
                # Use DETACHED_PROCESS to run in background without console window
                DETACHED_PROCESS = 0x00000008
                subprocess.Popen(
                    [python_exe, str(main_script)],
                    cwd=str(project_root),
                    creationflags=DETACHED_PROCESS,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            else:
                # Linux/Mac: Start in background using nohup
                subprocess.Popen(
                    [python_exe, str(main_script)],
                    cwd=str(project_root),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
            
            self.logger.info("🚀 Starting SkyGuard main system...")
            self.logger.info(f"   Python: {python_exe}")
            self.logger.info(f"   Script: {main_script}")
            self.logger.info(f"   Working directory: {project_root}")
            
            # Also restart web portal components
            self.logger.info("🔄 Restarting web portal components...")
            self._restart_components()
            
            self.logger.info("=" * 60)
            self.logger.info("✅ SYSTEM RESTART COMPLETE")
            self.logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.logger.info("=" * 60)
            
        except Exception as e:
            self.logger.error(f"Failed to restart system: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            raise
    
    def _get_system_logs(self, limit: int = 500, since: Optional[float] = None) -> List[Dict[str, Any]]:
        """Get system logs from the log file.
        
        Args:
            limit: Maximum number of log lines to return
            since: Optional Unix timestamp - only return logs after this time
            
        Returns:
            List of log entry dictionaries
        """
        try:
            import re
            from pathlib import Path
            
            # Get log file path from config
            log_file = self.config.get('logging', {}).get('file', 'logs/skyguard.log')
            log_path = Path(log_file)
            
            # Resolve relative paths
            if not log_path.is_absolute():
                # Try relative to project root
                project_root = Path(__file__).parent.parent.parent
                log_path = project_root / log_file
            
            if not log_path.exists():
                return []
            
            # Read log file (read last N lines efficiently)
            logs = []
            try:
                # Read file in reverse to get last N lines
                with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                    # Read all lines if file is small, otherwise read last portion
                    lines = f.readlines()
                    
                    # Get last N lines
                    if len(lines) > limit:
                        lines = lines[-limit:]
                    
                    # Parse each line
                    # Format: YYYY-MM-DD HH:MM:SS - module - LEVEL - message
                    log_pattern = re.compile(
                        r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) - ([^-]+) - (\w+) - (.+)$'
                    )
                    
                    for line in lines:
                        line = line.strip()
                        if not line:
                            continue
                        
                        match = log_pattern.match(line)
                        if match:
                            timestamp_str, module, level, message = match.groups()
                            
                            # Parse timestamp
                            try:
                                dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                                timestamp = dt.timestamp()
                                
                                # Filter by 'since' if provided
                                if since and timestamp <= since:
                                    continue
                                
                                logs.append({
                                    'timestamp': timestamp,
                                    'timestamp_str': timestamp_str,
                                    'level': level,
                                    'module': module.strip(),
                                    'message': message,
                                    'raw': line
                                })
                            except ValueError:
                                # If timestamp parsing fails, include as-is
                                logs.append({
                                    'timestamp': time.time(),
                                    'timestamp_str': '',
                                    'level': 'INFO',
                                    'module': 'unknown',
                                    'message': line,
                                    'raw': line
                                })
                        else:
                            # If pattern doesn't match, include as raw log
                            logs.append({
                                'timestamp': time.time(),
                                'timestamp_str': '',
                                'level': 'INFO',
                                'module': 'unknown',
                                'message': line,
                                'raw': line
                            })
                
                # Sort by timestamp (oldest first)
                logs.sort(key=lambda x: x['timestamp'])
                
            except Exception as e:
                self.logger.error(f"Error reading log file: {e}")
                return []
            
            return logs
            
        except Exception as e:
            import traceback
            print(f"Error in _get_system_logs: {e}")
            traceback.print_exc()
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
