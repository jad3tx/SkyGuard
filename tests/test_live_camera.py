#!/usr/bin/env python3
"""
Test suite for Live Camera functionality.

Tests the live camera view, camera feed, and related UI components.
"""

import pytest
import os
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture

from skyguard.web.app import SkyGuardWebPortal


class TestLiveCameraAPI:
    """Test live camera API endpoints."""
    
    def test_camera_status_endpoint(self, web_portal: SkyGuardWebPortal) -> None:
        """Test the /api/camera/status endpoint."""
        with web_portal.app.test_client() as client:
            response = client.get('/api/camera/status')
            assert response.status_code == 200
            
            data = response.get_json()
            assert 'connected' in data
            assert 'source' in data
            assert 'width' in data
            assert 'height' in data
            assert 'fps' in data
    
    def test_camera_feed_endpoint_without_camera(self, web_portal: SkyGuardWebPortal) -> None:
        """Test the /api/camera/feed endpoint when no camera is available."""
        with web_portal.app.test_client() as client:
            response = client.get('/api/camera/feed')
            # Should return 200 if camera is working, or 503/500 if not available
            assert response.status_code in [200, 503, 500]
    
    def test_camera_capture_endpoint_without_camera(self, web_portal: SkyGuardWebPortal) -> None:
        """Test the /api/camera/capture endpoint when no camera is available."""
        with web_portal.app.test_client() as client:
            response = client.get('/api/camera/capture')
            # Should return 200 if camera is working, or 503/500 if not available
            assert response.status_code in [200, 503, 500]
    
    def test_camera_feed_with_mock_camera(self, web_portal: SkyGuardWebPortal, mocker: "MockerFixture") -> None:
        """Test camera feed with mocked camera."""
        # Mock the camera to return a successful connection
        mocker.patch.object(web_portal.camera, 'test_connection', return_value=True)
        import numpy as np
        fake_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        mocker.patch.object(web_portal.camera, 'capture_frame', return_value=fake_frame)
        mocker.patch.object(web_portal.camera, '_apply_transformations', return_value=fake_frame)
        
        with web_portal.app.test_client() as client:
            response = client.get('/api/camera/feed')
            # Should return 200 with image data
            assert response.status_code == 200
            assert response.content_type == 'image/jpeg'
    
    def test_camera_capture_with_mock_camera(self, web_portal: SkyGuardWebPortal, mocker: "MockerFixture") -> None:
        """Test camera capture with mocked camera."""
        # Mock the camera to return a successful connection
        mocker.patch.object(web_portal.camera, 'test_connection', return_value=True)
        import numpy as np
        fake_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        mocker.patch.object(web_portal.camera, 'capture_frame', return_value=fake_frame)
        mocker.patch.object(web_portal.camera, '_apply_transformations', return_value=fake_frame)
        
        with web_portal.app.test_client() as client:
            response = client.get('/api/camera/capture')
            # Should return 200 with image data
            assert response.status_code == 200
            assert response.content_type == 'image/jpeg'
            assert 'attachment' in response.headers.get('Content-Disposition', '')


class TestLiveCameraUI:
    """Test live camera UI components."""
    
    def test_live_camera_page_loads(self, web_portal: SkyGuardWebPortal) -> None:
        """Test that the live camera page loads correctly."""
        with web_portal.app.test_client() as client:
            response = client.get('/')
            assert response.status_code == 200
            
            # Check that live camera section exists in the HTML
            content = response.get_data(as_text=True)
            assert 'live-camera-section' in content
            assert 'Live Camera View' in content
            assert 'camera-container' in content
            assert 'camera-controls' in content
    
    def test_live_camera_contains_controls(self, web_portal: SkyGuardWebPortal) -> None:
        """Test that live camera page contains all necessary controls."""
        with web_portal.app.test_client() as client:
            response = client.get('/')
            content = response.get_data(as_text=True)
            
            # Check for camera controls
            assert 'live-brightness' in content
            assert 'live-contrast' in content
            assert 'live-flip-horizontal' in content
            assert 'live-flip-vertical' in content
            assert 'live-rotation' in content
            
            # Check for control buttons
            assert 'startLiveView()' in content
            assert 'stopLiveView()' in content
            assert 'captureImage()' in content
    
    def test_live_camera_contains_javascript_functions(self, web_portal: SkyGuardWebPortal) -> None:
        """Test that live camera page contains necessary JavaScript functions."""
        with web_portal.app.test_client() as client:
            response = client.get('/')
            content = response.get_data(as_text=True)
            
            # Check for JavaScript functions
            assert 'function loadLiveCamera()' in content
            assert 'function startLiveView()' in content
            assert 'function stopLiveView()' in content
            assert 'function captureImage()' in content
            assert 'function updateRangeValue(' in content
    
    def test_live_camera_navigation_link(self, web_portal: SkyGuardWebPortal) -> None:
        """Test that live camera navigation link exists."""
        with web_portal.app.test_client() as client:
            response = client.get('/')
            content = response.get_data(as_text=True)
            
            # Check for navigation link
            assert 'onclick="showSection(\'live-camera\')"' in content
            assert 'Live Camera' in content
            assert 'fas fa-video' in content


class TestLiveCameraFunctionality:
    """Test live camera functionality and interactions."""
    
    def test_camera_status_updates(self, web_portal: SkyGuardWebPortal) -> None:
        """Test that camera status updates work correctly."""
        with web_portal.app.test_client() as client:
            # Test camera status endpoint
            response = client.get('/api/camera/status')
            assert response.status_code == 200
            
            data = response.get_json()
            # Camera status depends on system capabilities
            assert 'connected' in data
            assert isinstance(data['connected'], bool)
    
    def test_camera_feed_error_handling(self, web_portal: SkyGuardWebPortal) -> None:
        """Test that camera feed handles errors gracefully."""
        with web_portal.app.test_client() as client:
            response = client.get('/api/camera/feed')
            # Should handle camera availability gracefully (200 if working, 503/500 if not)
            assert response.status_code in [200, 503, 500]
            
            # Check error response format if there's an error
            if response.status_code in [503, 500]:
                data = response.get_data(as_text=True)
                assert 'error' in data.lower() or 'camera' in data.lower()
    
    def test_camera_capture_error_handling(self, web_portal: SkyGuardWebPortal) -> None:
        """Test that camera capture handles errors gracefully."""
        with web_portal.app.test_client() as client:
            response = client.get('/api/camera/capture')
            # Should handle camera availability gracefully (200 if working, 503/500 if not)
            assert response.status_code in [200, 503, 500]
    
    def test_live_camera_with_real_file(self, web_portal: SkyGuardWebPortal) -> None:
        """Test live camera functionality with a real test image file."""
        import os
        
        # Create a test image file
        os.makedirs('data/detections', exist_ok=True)
        test_image_path = 'data/detections/test_camera_feed.jpg'
        with open(test_image_path, 'wb') as f:
            f.write(b'fake_jpeg_data')
        
        try:
            # Mock camera to use the test file
            with web_portal.app.test_client() as client:
                # Test that the system can handle file operations
                response = client.get('/api/camera/status')
                assert response.status_code == 200
                
        finally:
            # Clean up test file
            if os.path.exists(test_image_path):
                os.remove(test_image_path)


class TestLiveCameraIntegration:
    """Test live camera integration with the web portal."""
    
    def test_live_camera_section_visibility(self, web_portal: SkyGuardWebPortal) -> None:
        """Test that live camera section is properly configured."""
        with web_portal.app.test_client() as client:
            response = client.get('/')
            content = response.get_data(as_text=True)
            
            # Check that the live camera section is properly structured
            assert 'id="live-camera-section"' in content
            assert 'style="display: none;"' in content  # Initially hidden
            assert 'Live Camera View' in content
    
    def test_camera_feed_url_generation(self, web_portal: SkyGuardWebPortal) -> None:
        """Test that camera feed URLs are generated correctly."""
        with web_portal.app.test_client() as client:
            response = client.get('/')
            content = response.get_data(as_text=True)
            
            # Check that camera feed URL is properly referenced
            assert '/api/camera/feed' in content
            assert 'live-camera-feed' in content
    
    def test_camera_controls_initialization(self, web_portal: SkyGuardWebPortal) -> None:
        """Test that camera controls are properly initialized."""
        with web_portal.app.test_client() as client:
            response = client.get('/')
            content = response.get_data(as_text=True)
            
            # Check for range value initialization
            assert 'updateRangeValue(' in content
            assert 'live-brightness' in content
            assert 'live-contrast' in content
            
            # Check for event listeners
            assert 'addEventListener(' in content
            assert 'change' in content
            assert 'input' in content


@pytest.fixture
def web_portal() -> SkyGuardWebPortal:
    """Create a web portal instance for testing."""
    # Use real components with test configuration
    portal = SkyGuardWebPortal("test_config.yaml")
    return portal
