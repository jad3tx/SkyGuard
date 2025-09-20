"""
Tests for SkyGuard core components.
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from skyguard.core.config_manager import ConfigManager
from skyguard.core.camera import CameraManager
from skyguard.core.detector import RaptorDetector
from skyguard.core.alert_system import AlertSystem


class TestConfigManager:
    """Test the configuration manager."""
    
    def test_init(self):
        """Test ConfigManager initialization."""
        config_manager = ConfigManager("test_config.yaml")
        assert config_manager.config_path == Path("test_config.yaml")
        assert config_manager.config == {}
    
    def test_create_default_config(self):
        """Test default configuration creation."""
        config_manager = ConfigManager("test_config.yaml")
        config_manager._create_default_config()
        
        assert 'system' in config_manager.config
        assert 'camera' in config_manager.config
        assert 'ai' in config_manager.config
        assert 'notifications' in config_manager.config
        assert 'storage' in config_manager.config
    
    def test_load_config_file_not_found(self):
        """Test loading config when file doesn't exist."""
        config_manager = ConfigManager("nonexistent.yaml")
        config = config_manager.load_config()
        
        # Should create default config
        assert 'system' in config
        assert config['system']['detection_interval'] == 1.0
    
    def test_save_config(self):
        """Test saving configuration."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = f.name
        
        try:
            config_manager = ConfigManager(temp_path)
            config_manager._create_default_config()
            
            success = config_manager.save_config()
            assert success
            
            # Verify file was created and contains valid YAML
            with open(temp_path, 'r') as f:
                saved_config = yaml.safe_load(f)
            
            assert 'system' in saved_config
            assert saved_config['system']['detection_interval'] == 1.0
            
        finally:
            Path(temp_path).unlink(missing_ok=True)


class TestCameraManager:
    """Test the camera manager."""
    
    def test_init(self):
        """Test CameraManager initialization."""
        config = {
            'source': 0,
            'width': 640,
            'height': 480,
            'fps': 30
        }
        
        camera_manager = CameraManager(config)
        assert camera_manager.config == config
        assert camera_manager.cap is None
    
    @patch('cv2.VideoCapture')
    def test_initialize_success(self, mock_video_capture):
        """Test successful camera initialization."""
        # Mock successful camera initialization
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, Mock())  # (ret, frame)
        mock_cap.get.side_effect = lambda prop: {
            cv2.CAP_PROP_FRAME_WIDTH: 640,
            cv2.CAP_PROP_FRAME_HEIGHT: 480,
            cv2.CAP_PROP_FPS: 30
        }.get(prop, 0)
        
        mock_video_capture.return_value = mock_cap
        
        config = {'source': 0, 'width': 640, 'height': 480, 'fps': 30}
        camera_manager = CameraManager(config)
        
        success = camera_manager.initialize()
        assert success
        assert camera_manager.cap == mock_cap
    
    @patch('cv2.VideoCapture')
    def test_initialize_failure(self, mock_video_capture):
        """Test camera initialization failure."""
        # Mock failed camera initialization
        mock_cap = Mock()
        mock_cap.isOpened.return_value = False
        mock_video_capture.return_value = mock_cap
        
        config = {'source': 0}
        camera_manager = CameraManager(config)
        
        success = camera_manager.initialize()
        assert not success
    
    def test_apply_transformations(self):
        """Test frame transformations."""
        import numpy as np
        
        config = {
            'rotation': 0,
            'flip_horizontal': False,
            'flip_vertical': False
        }
        
        camera_manager = CameraManager(config)
        
        # Create test frame
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        
        # Test no transformations
        result = camera_manager._apply_transformations(frame)
        assert np.array_equal(result, frame)
        
        # Test horizontal flip
        config['flip_horizontal'] = True
        camera_manager.config = config
        result = camera_manager._apply_transformations(frame)
        # Should be different from original
        assert not np.array_equal(result, frame)


class TestRaptorDetector:
    """Test the raptor detector."""
    
    def test_init(self):
        """Test RaptorDetector initialization."""
        config = {
            'model_path': 'test_model.pt',
            'confidence_threshold': 0.5,
            'classes': ['raptor', 'hawk']
        }
        
        detector = RaptorDetector(config)
        assert detector.confidence_threshold == 0.5
        assert detector.classes == ['raptor', 'hawk']
        assert detector.model is None
    
    def test_create_dummy_model(self):
        """Test dummy model creation."""
        config = {'model_path': 'nonexistent.pt'}
        detector = RaptorDetector(config)
        detector._create_dummy_model()
        
        assert detector.model == "dummy"
    
    def test_dummy_detection(self):
        """Test dummy detection functionality."""
        import numpy as np
        
        config = {'model_path': 'nonexistent.pt'}
        detector = RaptorDetector(config)
        detector.model = "dummy"
        
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        
        # Test multiple times to get a detection (5% chance)
        detections = []
        for _ in range(100):
            result = detector.detect(frame)
            detections.extend(result)
        
        # Should get at least one detection with high probability
        assert len(detections) > 0
        
        # Check detection structure
        detection = detections[0]
        assert 'bbox' in detection
        assert 'confidence' in detection
        assert 'class_name' in detection
        assert 'timestamp' in detection
    
    def test_draw_detections(self):
        """Test detection drawing."""
        import numpy as np
        
        config = {'model_path': 'test.pt'}
        detector = RaptorDetector(config)
        
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        detections = [{
            'bbox': [10, 10, 50, 50],
            'confidence': 0.8,
            'class_name': 'raptor'
        }]
        
        result = detector.draw_detections(frame, detections)
        
        # Should return a frame (numpy array)
        assert isinstance(result, np.ndarray)
        assert result.shape == frame.shape


class TestAlertSystem:
    """Test the alert system."""
    
    def test_init(self):
        """Test AlertSystem initialization."""
        config = {
            'audio': {'enabled': False},
            'push': {'enabled': False},
            'sms': {'enabled': False},
            'email': {'enabled': False}
        }
        
        alert_system = AlertSystem(config)
        assert alert_system.config == config
        assert alert_system.alert_count == 0
    
    def test_create_alert_message(self):
        """Test alert message creation."""
        config = {'audio': {'enabled': False}}
        alert_system = AlertSystem(config)
        
        detection = {
            'confidence': 0.85,
            'class_name': 'hawk',
            'timestamp': 1234567890
        }
        
        message = alert_system._create_alert_message(detection)
        
        assert 'SKYGUARD ALERT' in message
        assert 'hawk' in message
        assert '85%' in message or '0.85' in message
    
    def test_check_rate_limit(self):
        """Test rate limiting functionality."""
        config = {'audio': {'enabled': False}}
        alert_system = AlertSystem(config)
        
        # First call should pass
        assert alert_system._check_rate_limit('test_alert')
        
        # Immediate second call should be rate limited
        assert not alert_system._check_rate_limit('test_alert')
    
    def test_get_alert_stats(self):
        """Test alert statistics."""
        config = {'audio': {'enabled': False}}
        alert_system = AlertSystem(config)
        
        stats = alert_system.get_alert_stats()
        
        assert 'total_alerts' in stats
        assert 'last_alert_time' in stats
        assert 'audio_enabled' in stats
        assert stats['total_alerts'] == 0


if __name__ == "__main__":
    pytest.main([__file__])
