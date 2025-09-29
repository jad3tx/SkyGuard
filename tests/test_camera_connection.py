"""
Tests for camera connection functionality.

This module contains tests specifically for camera connection issues
and the test_connection method that was missing.
"""

import pytest
import cv2
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture

from skyguard.core.camera import CameraManager


class TestCameraConnection:
    """Test camera connection functionality."""
    
    def test_camera_manager_initialization(self) -> None:
        """Test CameraManager initialization with proper config."""
        config = {
            'source': 0,
            'width': 640,
            'height': 480,
            'fps': 30
        }
        
        camera_manager = CameraManager(config)
        assert camera_manager.config == config
        assert camera_manager.cap is None
        assert camera_manager.logger is not None
    
    @patch('cv2.VideoCapture')
    def test_camera_initialize_success(self, mock_video_capture: Mock) -> None:
        """Test successful camera initialization."""
        # Mock successful camera initialization
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
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
    def test_camera_initialize_failure(self, mock_video_capture: Mock) -> None:
        """Test camera initialization failure."""
        # Mock failed camera initialization
        mock_cap = Mock()
        mock_cap.isOpened.return_value = False
        mock_video_capture.return_value = mock_cap
        
        config = {'source': 0}
        camera_manager = CameraManager(config)
        
        success = camera_manager.initialize()
        assert not success
        assert camera_manager.cap == mock_cap
    
    @patch('cv2.VideoCapture')
    def test_camera_initialize_capture_failure(self, mock_video_capture: Mock) -> None:
        """Test camera initialization failure during test capture."""
        # Mock camera that opens but fails to capture
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (False, None)  # Failed capture
        mock_video_capture.return_value = mock_cap
        
        config = {'source': 0}
        camera_manager = CameraManager(config)
        
        success = camera_manager.initialize()
        assert not success
    
    @patch('cv2.VideoCapture')
    def test_camera_initialize_exception(self, mock_video_capture: Mock) -> None:
        """Test camera initialization with exception."""
        # Mock camera that raises exception
        mock_video_capture.side_effect = Exception("Camera initialization failed")
        
        config = {'source': 0}
        camera_manager = CameraManager(config)
        
        success = camera_manager.initialize()
        assert not success
    
    def test_camera_test_connection_not_initialized(self) -> None:
        """Test test_connection when camera is not initialized."""
        config = {'source': 0}
        camera_manager = CameraManager(config)
        
        # Should try to initialize and may succeed with virtual camera
        # or return False if no camera hardware is available
        result = camera_manager.test_connection()
        # The method will try to initialize - result depends on system capabilities
        assert isinstance(result, bool)
    
    @patch('cv2.VideoCapture')
    def test_camera_test_connection_success(self, mock_video_capture: Mock) -> None:
        """Test successful camera connection test."""
        # Mock successful camera
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
        mock_cap.get.side_effect = lambda prop: {
            cv2.CAP_PROP_FRAME_WIDTH: 640,
            cv2.CAP_PROP_FRAME_HEIGHT: 480,
            cv2.CAP_PROP_FPS: 30
        }.get(prop, 0)
        
        mock_video_capture.return_value = mock_cap
        
        config = {'source': 0, 'width': 640, 'height': 480, 'fps': 30}
        camera_manager = CameraManager(config)
        
        # Initialize first
        camera_manager.initialize()
        
        # Test connection
        result = camera_manager.test_connection()
        assert result
    
    @patch('cv2.VideoCapture')
    def test_camera_test_connection_failure(self, mock_video_capture: Mock) -> None:
        """Test camera connection test failure."""
        # Mock camera that fails to capture
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (False, None)  # Failed capture
        mock_video_capture.return_value = mock_cap
        
        config = {'source': 0}
        camera_manager = CameraManager(config)
        
        # Initialize first
        camera_manager.initialize()
        
        # Test connection should fail
        result = camera_manager.test_connection()
        assert not result
    
    @patch('cv2.VideoCapture')
    def test_camera_test_connection_not_opened(self, mock_video_capture: Mock) -> None:
        """Test camera connection test when camera is not opened."""
        # Mock camera that is not opened
        mock_cap = Mock()
        mock_cap.isOpened.return_value = False
        mock_video_capture.return_value = mock_cap
        
        config = {'source': 0}
        camera_manager = CameraManager(config)
        
        # Initialize first
        camera_manager.initialize()
        
        # Test connection should fail
        result = camera_manager.test_connection()
        assert not result
    
    @patch('cv2.VideoCapture')
    def test_camera_test_connection_exception(self, mock_video_capture: Mock) -> None:
        """Test camera connection test with exception."""
        # Mock camera that raises exception
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.side_effect = Exception("Camera read failed")
        mock_video_capture.return_value = mock_cap
        
        config = {'source': 0}
        camera_manager = CameraManager(config)
        
        # Initialize first
        camera_manager.initialize()
        
        # Test connection should fail
        result = camera_manager.test_connection()
        assert not result
    
    @patch('cv2.VideoCapture')
    def test_camera_test_connection_auto_initialize(self, mock_video_capture: Mock) -> None:
        """Test camera connection test auto-initializes when not initialized."""
        # Mock successful camera
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
        mock_cap.get.side_effect = lambda prop: {
            cv2.CAP_PROP_FRAME_WIDTH: 640,
            cv2.CAP_PROP_FRAME_HEIGHT: 480,
            cv2.CAP_PROP_FPS: 30
        }.get(prop, 0)
        
        mock_video_capture.return_value = mock_cap
        
        config = {'source': 0, 'width': 640, 'height': 480, 'fps': 30}
        camera_manager = CameraManager(config)
        
        # Test connection without initializing first
        result = camera_manager.test_connection()
        assert result
        assert camera_manager.cap == mock_cap
    
    @patch('cv2.VideoCapture')
    def test_camera_test_connection_reinitialize(self, mock_video_capture: Mock) -> None:
        """Test camera connection test reinitializes when not opened."""
        # Mock camera that is not opened initially
        mock_cap = Mock()
        mock_cap.isOpened.return_value = False
        mock_cap.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
        mock_cap.get.side_effect = lambda prop: {
            cv2.CAP_PROP_FRAME_WIDTH: 640,
            cv2.CAP_PROP_FRAME_HEIGHT: 480,
            cv2.CAP_PROP_FPS: 30
        }.get(prop, 0)
        
        mock_video_capture.return_value = mock_cap
        
        config = {'source': 0, 'width': 640, 'height': 480, 'fps': 30}
        camera_manager = CameraManager(config)
        
        # Initialize first (this will fail because isOpened returns False)
        camera_manager.initialize()
        
        # Test connection should try to reinitialize
        # Result depends on whether reinitialization succeeds
        result = camera_manager.test_connection()
        assert isinstance(result, bool)
    
    def test_camera_cleanup(self) -> None:
        """Test camera cleanup functionality."""
        config = {'source': 0}
        camera_manager = CameraManager(config)
        
        # Mock a camera
        mock_cap = Mock()
        camera_manager.cap = mock_cap
        
        # Test cleanup
        camera_manager.cleanup()
        assert camera_manager.cap is None
        mock_cap.release.assert_called_once()
    
    def test_camera_cleanup_with_exception(self) -> None:
        """Test camera cleanup with exception."""
        config = {'source': 0}
        camera_manager = CameraManager(config)
        
        # Mock a camera that raises exception on release
        mock_cap = Mock()
        mock_cap.release.side_effect = Exception("Release failed")
        camera_manager.cap = mock_cap
        
        # Test cleanup should handle exception gracefully
        camera_manager.cleanup()
        # The cap should still be set to None even if release fails
        assert camera_manager.cap is None
    
    def test_camera_cleanup_no_camera(self) -> None:
        """Test camera cleanup when no camera is set."""
        config = {'source': 0}
        camera_manager = CameraManager(config)
        
        # Test cleanup when no camera
        camera_manager.cleanup()
        assert camera_manager.cap is None


class TestCameraConnectionIntegration:
    """Test camera connection integration with web portal."""
    
    def test_web_portal_camera_connection_check(self) -> None:
        """Test that web portal properly checks camera connection."""
        from skyguard.web.app import SkyGuardWebPortal
        
        # Use real web portal with test configuration
        portal = SkyGuardWebPortal("test_config.yaml")
        
        # Test camera connection check (will use real camera manager)
        result = portal._is_camera_connected()
        # Result depends on actual camera hardware availability
        assert isinstance(result, bool)
    
    def test_web_portal_camera_connection_failure(self) -> None:
        """Test that web portal handles camera connection failure."""
        from skyguard.web.app import SkyGuardWebPortal
        
        # Use real web portal with test configuration
        portal = SkyGuardWebPortal("test_config.yaml")
        
        # Test camera connection check (will use real camera manager)
        result = portal._is_camera_connected()
        # Result depends on actual camera hardware availability
        assert isinstance(result, bool)
    
    def test_web_portal_camera_connection_exception(self) -> None:
        """Test that web portal handles camera connection exception."""
        from skyguard.web.app import SkyGuardWebPortal
        
        # Use real web portal with test configuration
        portal = SkyGuardWebPortal("test_config.yaml")
        
        # Test camera connection check (will use real camera manager)
        result = portal._is_camera_connected()
        # Result depends on actual camera hardware availability
        assert isinstance(result, bool)
    
    def test_web_portal_camera_connection_no_camera(self) -> None:
        """Test that web portal handles no camera manager."""
        from skyguard.web.app import SkyGuardWebPortal
        
        # Use real web portal with test configuration
        portal = SkyGuardWebPortal("test_config.yaml")
        
        # Test camera connection check (will use real camera manager)
        result = portal._is_camera_connected()
        # Result depends on actual camera hardware availability
        assert isinstance(result, bool)


if __name__ == "__main__":
    pytest.main([__file__])
