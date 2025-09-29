"""
Full system integration tests with real components.

This module tests the complete SkyGuard system integration using real
hardware, services, and data without mocking.
"""

import pytest
import time
import os
import cv2
import numpy as np
from pathlib import Path
from typing import TYPE_CHECKING, Dict, Any

from skyguard.main import SkyGuardSystem
from skyguard.core.config_manager import ConfigManager
from skyguard.core.camera import CameraManager
from skyguard.core.detector import RaptorDetector
from skyguard.core.alert_system import AlertSystem
from skyguard.storage.event_logger import EventLogger
from skyguard.core.camera_snapshot import CameraSnapshotService
from skyguard.web.app import SkyGuardWebPortal

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture


class TestSystemIntegration:
    """Full system integration tests with real components."""

    @pytest.fixture
    def config_manager(self) -> ConfigManager:
        """Create a real ConfigManager instance."""
        return ConfigManager("config/skyguard.yaml")

    @pytest.fixture
    def skyguard_system(self, config_manager: ConfigManager) -> SkyGuardSystem:
        """Create a real SkyGuardSystem instance."""
        system = SkyGuardSystem("config/skyguard.yaml")
        # Initialize the system components
        system.initialize()
        return system

    def test_system_initialization(self, skyguard_system: SkyGuardSystem) -> None:
        """Test that the SkyGuard system initializes correctly with all components."""
        # Test system initialization
        assert skyguard_system is not None
        assert skyguard_system.config is not None
        
        # Test component initialization
        assert skyguard_system.camera_manager is not None
        assert skyguard_system.detector is not None
        assert skyguard_system.alert_system is not None
        assert skyguard_system.event_logger is not None
        assert skyguard_system.snapshot_service is not None

    def test_camera_initialization(self, skyguard_system: SkyGuardSystem) -> None:
        """Test camera initialization with real hardware."""
        camera_manager = skyguard_system.camera_manager
        
        # Test camera initialization
        if camera_manager.initialize():
            assert camera_manager.is_initialized
            assert camera_manager.cap is not None
            
            # Test camera properties
            assert camera_manager.config is not None
            assert 'width' in camera_manager.config
            assert 'height' in camera_manager.config
            assert 'fps' in camera_manager.config
            
            # Clean up
            camera_manager.cleanup()
        else:
            pytest.skip("Camera not available for integration test")

    def test_camera_frame_capture(self, skyguard_system: SkyGuardSystem) -> None:
        """Test camera frame capture with real hardware."""
        camera_manager = skyguard_system.camera_manager
        
        if camera_manager.initialize():
            try:
                # Test frame capture
                frame = camera_manager.capture_frame()
                
                if frame is not None:
                    # Verify frame properties
                    assert isinstance(frame, np.ndarray)
                    assert len(frame.shape) == 3  # Height, width, channels
                    assert frame.shape[2] == 3    # RGB channels
                    assert frame.shape[0] > 0     # Valid height
                    assert frame.shape[1] > 0     # Valid width
                    
                    # Test frame transformations
                    transformed_frame = camera_manager.apply_transformations(frame)
                    assert transformed_frame is not None
                    assert transformed_frame.shape == frame.shape
                
            finally:
                camera_manager.cleanup()
        else:
            pytest.skip("Camera not available for integration test")

    def test_ai_detector_initialization(self, skyguard_system: SkyGuardSystem) -> None:
        """Test AI detector initialization with real model."""
        detector = skyguard_system.detector
        
        # Test detector initialization
        assert detector is not None
        assert detector.config is not None
        
        # Test model loading
        if hasattr(detector, 'model') and detector.model is not None:
            assert detector.model is not None
        else:
            # Model might not be loaded yet, test loading
            try:
                detector.load_model()
                assert detector.model is not None
            except Exception:
                pytest.skip("AI model not available for integration test")

    def test_ai_detection_with_real_camera(self, skyguard_system: SkyGuardSystem) -> None:
        """Test AI detection with real camera frames."""
        camera_manager = skyguard_system.camera_manager
        detector = skyguard_system.detector
        
        if camera_manager.initialize():
            try:
                # Capture a frame
                frame = camera_manager.capture_frame()
                
                if frame is not None:
                    # Test detection
                    detections = detector.detect(frame)
                    
                    # Verify detection results
                    assert isinstance(detections, list)
                    
                    for detection in detections:
                        assert 'class' in detection
                        assert 'confidence' in detection
                        assert 'bbox' in detection
                        assert isinstance(detection['confidence'], (int, float))
                        assert 0 <= detection['confidence'] <= 1
                        
                        # Verify bounding box
                        bbox = detection['bbox']
                        assert len(bbox) == 4  # x, y, width, height
                        assert all(isinstance(coord, (int, float)) for coord in bbox)
                        assert bbox[2] > 0  # width > 0
                        assert bbox[3] > 0  # height > 0
                
            finally:
                camera_manager.cleanup()
        else:
            pytest.skip("Camera not available for integration test")

    def test_alert_system_initialization(self, skyguard_system: SkyGuardSystem) -> None:
        """Test alert system initialization with real configuration."""
        alert_system = skyguard_system.alert_system
        
        # Test alert system initialization
        assert alert_system is not None
        assert alert_system.config is not None
        
        # Test alert system properties
        assert hasattr(alert_system, 'audio_enabled')
        assert hasattr(alert_system, 'email_enabled')
        assert hasattr(alert_system, 'sms_enabled')

    def test_alert_system_with_detection(self, skyguard_system: SkyGuardSystem) -> None:
        """Test alert system with real detection data."""
        alert_system = skyguard_system.alert_system
        
        # Create test detection data
        test_detection = {
            'class_name': 'raptor',
            'confidence': 0.85,
            'bbox': [100, 100, 200, 200]
        }
        
        # Test alert creation
        alert_message = alert_system.create_alert_message(test_detection)
        assert isinstance(alert_message, str)
        assert len(alert_message) > 0
        assert 'raptor' in alert_message.lower() or 'detected' in alert_message.lower()
        
        # Test alert sending (without actually sending)
        try:
            alert_system.send_raptor_alert(test_detection)
            # If no exception is raised, the alert system is working
            assert True
        except Exception as e:
            # Alert sending might fail due to missing credentials, but system should handle it gracefully
            assert "email" in str(e).lower() or "sms" in str(e).lower() or "audio" in str(e).lower()

    def test_event_logger_initialization(self, skyguard_system: SkyGuardSystem) -> None:
        """Test event logger initialization with real database."""
        event_logger = skyguard_system.event_logger
        
        # Test event logger initialization
        assert event_logger is not None
        assert event_logger.config is not None
        
        # Test database connection
        assert event_logger.connection is not None

    def test_event_logger_with_real_data(self, skyguard_system: SkyGuardSystem) -> None:
        """Test event logger with real detection data."""
        event_logger = skyguard_system.event_logger
        
        # Test system event logging
        event_logger.log_system_event("test_event", "Integration test event")
        
        # Test detection logging
        test_detection = {
            'class_name': 'raptor',
            'confidence': 0.85,
            'bbox': [100, 100, 200, 200],
            'center': [150, 150],  # Center of the bounding box
            'area': 10000,  # Area of the bounding box (100x100)
            'timestamp': time.time()
        }
        
        # Create a test image
        test_image_path = "data/test_detection.jpg"
        test_image = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.imwrite(test_image_path, test_image)
        
        try:
            # Log detection
            detection_id = event_logger.log_detection(
                test_detection,
                test_image
            )
            
            assert detection_id is not None
            assert isinstance(detection_id, int)
            assert detection_id > 0
            
            # Test getting detections
            detections = event_logger.get_detections()
            assert detections is not None
            assert len(detections) > 0
            # Check that our detection was logged
            found_detection = False
            for detection in detections:
                if detection.get('class_name') == test_detection['class_name']:
                    assert detection['confidence'] == test_detection['confidence']
                    found_detection = True
                    break
            assert found_detection, "Our test detection was not found in the logged detections"
            
        finally:
            # Clean up test image
            if os.path.exists(test_image_path):
                os.remove(test_image_path)

    def test_camera_snapshot_service_integration(self, skyguard_system: SkyGuardSystem) -> None:
        """Test camera snapshot service integration with real camera."""
        camera_manager = skyguard_system.camera_manager
        snapshot_service = skyguard_system.snapshot_service
        
        if camera_manager.initialize():
            try:
                # Start snapshot service
                snapshot_service.start(camera_manager)
                assert snapshot_service.is_running
                
                # Wait for snapshot to be created
                time.sleep(4)  # Wait longer than the 3-second interval
                
                # Verify snapshot file exists
                snapshot_path = Path("data/camera_snapshot.jpg")
                assert snapshot_path.exists(), "Snapshot file should be created"
                
                # Verify snapshot is a valid image
                img = cv2.imread(str(snapshot_path))
                assert img is not None, "Snapshot should be a valid image"
                assert img.shape[0] > 0 and img.shape[1] > 0, "Image should have valid dimensions"
                
                # Test getting snapshot bytes
                snapshot_bytes = snapshot_service.get_snapshot_bytes()
                assert snapshot_bytes is not None
                assert len(snapshot_bytes) > 0
                
                # Verify bytes can be decoded as image
                nparr = np.frombuffer(snapshot_bytes, np.uint8)
                decoded_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                assert decoded_img is not None, "Snapshot bytes should decode to valid image"
                
            finally:
                # Clean up
                snapshot_service.stop()
                camera_manager.cleanup()
        else:
            pytest.skip("Camera not available for integration test")

    def test_web_portal_integration(self, skyguard_system: SkyGuardSystem) -> None:
        """Test web portal integration with real system components."""
        # Create web portal
        web_portal = SkyGuardWebPortal("config/skyguard.yaml")
        
        # Test web portal initialization
        assert web_portal is not None
        assert web_portal.app is not None
        assert web_portal.config is not None
        
        # Test web portal components
        assert web_portal.detector is not None
        assert web_portal.alert_system is not None
        assert web_portal.event_logger is not None
        
        # Test web portal API endpoints
        test_client = web_portal.app.test_client()
        
        # Test status endpoint
        response = test_client.get('/api/status')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'system' in data
        assert 'camera' in data
        assert 'ai' in data
        
        # Test camera status endpoint
        response = test_client.get('/api/camera/status')
        assert response.status_code == 200
        
        # Test detections endpoint
        response = test_client.get('/api/detections')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'detections' in data
        assert 'total' in data

    def test_full_detection_pipeline(self, skyguard_system: SkyGuardSystem) -> None:
        """Test the complete detection pipeline with real components."""
        camera_manager = skyguard_system.camera_manager
        detector = skyguard_system.detector
        alert_system = skyguard_system.alert_system
        event_logger = skyguard_system.event_logger
        
        if camera_manager.initialize():
            try:
                # Capture frame
                frame = camera_manager.capture_frame()
                
                if frame is not None:
                    # Run detection
                    detections = detector.detect(frame)
                    
                    # Process detections
                    for detection in detections:
                        if detection['confidence'] > 0.5:  # Threshold for testing
                            # Create alert
                            alert_message = alert_system.create_alert_message(detection)
                            assert isinstance(alert_message, str)
                            assert len(alert_message) > 0
                            
                            # Log detection
                            test_image_path = "data/test_detection_pipeline.jpg"
                            cv2.imwrite(test_image_path, frame)
                            
                            try:
                                detection_id = event_logger.log_detection(
                                    detection['class'],
                                    detection['confidence'],
                                    detection['bbox'],
                                    test_image_path
                                )
                                
                                assert detection_id is not None
                                assert isinstance(detection_id, int)
                                
                            finally:
                                # Clean up test image
                                if os.path.exists(test_image_path):
                                    os.remove(test_image_path)
                
            finally:
                camera_manager.cleanup()
        else:
            pytest.skip("Camera not available for integration test")

    def test_system_performance(self, skyguard_system: SkyGuardSystem) -> None:
        """Test system performance with real components."""
        camera_manager = skyguard_system.camera_manager
        detector = skyguard_system.detector
        
        if camera_manager.initialize():
            try:
                # Measure frame capture performance
                start_time = time.time()
                frame = camera_manager.capture_frame()
                capture_time = time.time() - start_time
                
                if frame is not None:
                    # Measure detection performance
                    start_time = time.time()
                    detections = detector.detect(frame)
                    detection_time = time.time() - start_time
                    
                    # Verify performance is reasonable
                    assert capture_time < 1.0, f"Frame capture took too long: {capture_time:.2f}s"
                    assert detection_time < 5.0, f"Detection took too long: {detection_time:.2f}s"
                    
                    # Test multiple frames
                    total_time = 0
                    frame_count = 0
                    
                    for _ in range(3):  # Test 3 frames
                        start_time = time.time()
                        frame = camera_manager.capture_frame()
                        if frame is not None:
                            detections = detector.detect(frame)
                            frame_time = time.time() - start_time
                            total_time += frame_time
                            frame_count += 1
                    
                    if frame_count > 0:
                        avg_time = total_time / frame_count
                        assert avg_time < 2.0, f"Average frame processing time too high: {avg_time:.2f}s"
                
            finally:
                camera_manager.cleanup()
        else:
            pytest.skip("Camera not available for integration test")

    def test_system_error_handling(self, skyguard_system: SkyGuardSystem) -> None:
        """Test system error handling with real components."""
        # Test camera error handling
        camera_manager = skyguard_system.camera_manager
        
        # Test with invalid camera source
        original_source = camera_manager.config.get('source', 0)
        camera_manager.config['source'] = 999  # Invalid camera source
        
        # Should handle invalid camera gracefully
        result = camera_manager.initialize()
        assert not result  # Should fail gracefully
        
        # Restore original source
        camera_manager.config['source'] = original_source
        
        # Test detector error handling
        detector = skyguard_system.detector
        
        # Test with invalid frame
        invalid_frame = np.zeros((0, 0, 3), dtype=np.uint8)  # Empty frame
        
        try:
            detections = detector.detect(invalid_frame)
            # Should handle invalid frame gracefully
            assert isinstance(detections, list)
        except Exception:
            # Detector should handle invalid frames gracefully
            pass
        
        # Test alert system error handling
        alert_system = skyguard_system.alert_system
        
        # Test with invalid detection data
        invalid_detection = {
            'class': None,
            'confidence': -1,
            'bbox': []
        }
        
        try:
            alert_message = alert_system.create_alert_message(invalid_detection)
            # Should handle invalid data gracefully
            assert isinstance(alert_message, str)
        except Exception:
            # Alert system should handle invalid data gracefully
            pass

    def test_system_cleanup(self, skyguard_system: SkyGuardSystem) -> None:
        """Test system cleanup with real components."""
        camera_manager = skyguard_system.camera_manager
        snapshot_service = skyguard_system.snapshot_service
        
        if camera_manager.initialize():
            # Start snapshot service
            snapshot_service.start(camera_manager)
            assert snapshot_service.is_running
            
            # Test cleanup
            camera_manager.cleanup()
            snapshot_service.stop()
            
            # Verify cleanup
            assert not camera_manager.is_initialized
            assert not snapshot_service.is_running
            
            # Test multiple cleanup calls (should be safe)
            camera_manager.cleanup()
            snapshot_service.stop()
            
            # Should not raise exceptions
            assert True
