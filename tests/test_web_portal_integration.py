"""
Integration tests for the web portal with real services and data.

This module tests the web portal API endpoints using real system components
without mocking, ensuring end-to-end functionality.
"""

import pytest
import time
import os
import json
import requests
from pathlib import Path
from typing import TYPE_CHECKING, Dict, Any

from skyguard.web.app import SkyGuardWebPortal
from skyguard.core.config_manager import ConfigManager
from skyguard.core.camera import CameraManager
from skyguard.core.detector import RaptorDetector
from skyguard.core.alert_system import AlertSystem
from skyguard.storage.event_logger import EventLogger

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture


class TestWebPortalIntegration:
    """Integration tests for the web portal with real components."""

    @pytest.fixture
    def config_manager(self) -> ConfigManager:
        """Create a real ConfigManager instance."""
        return ConfigManager("config/skyguard.yaml")

    @pytest.fixture
    def web_portal(self, config_manager: ConfigManager) -> SkyGuardWebPortal:
        """Create a real SkyGuardWebPortal instance."""
        return SkyGuardWebPortal("config/skyguard.yaml")

    @pytest.fixture
    def test_client(self, web_portal: SkyGuardWebPortal):
        """Create a test client for the web portal."""
        return web_portal.app.test_client()

    def test_web_portal_initialization(self, web_portal: SkyGuardWebPortal) -> None:
        """Test that the web portal initializes correctly with real components."""
        assert web_portal is not None
        assert web_portal.app is not None
        assert web_portal.config is not None
        assert web_portal.detector is not None
        assert web_portal.alert_system is not None
        assert web_portal.event_logger is not None

    def test_api_status_endpoint(self, test_client) -> None:
        """Test the /api/status endpoint with real data."""
        response = test_client.get('/api/status')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Verify response structure
        assert 'system' in data
        assert 'camera' in data
        assert 'ai' in data
        assert 'detections' in data
        
        # Verify system status
        assert 'uptime' in data['system']
        assert 'status' in data['system']
        
        # Verify camera status
        assert 'connected' in data['camera']
        assert 'source' in data['camera']
        
        # Verify AI status
        assert 'loaded' in data['ai']
        assert 'model_path' in data['ai']

    def test_api_camera_status_endpoint(self, test_client) -> None:
        """Test the /api/camera/status endpoint with real camera data."""
        response = test_client.get('/api/camera/status')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Verify response structure
        assert 'connected' in data
        assert 'source' in data
        assert 'width' in data
        assert 'height' in data
        assert 'fps' in data
        
        # Verify data types
        assert isinstance(data['connected'], bool)
        assert isinstance(data['source'], (int, str))
        assert isinstance(data['width'], int)
        assert isinstance(data['height'], int)
        assert isinstance(data['fps'], (int, float))

    def test_api_camera_feed_endpoint(self, test_client) -> None:
        """Test the /api/camera/feed endpoint with real camera data."""
        response = test_client.get('/api/camera/feed')
        
        # Should return 200 or 503 depending on camera availability
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            # Verify it's an image
            assert response.content_type.startswith('image/')
            assert len(response.data) > 0
            
            # Verify it's a valid JPEG
            assert response.data.startswith(b'\xff\xd8\xff'), "Response should be a valid JPEG"

    def test_api_camera_capture_endpoint(self, test_client) -> None:
        """Test the /api/camera/capture endpoint with real camera data."""
        response = test_client.get('/api/camera/capture')
        
        # Should return 200 or 503 depending on camera availability
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            # Verify it's an image
            assert response.content_type.startswith('image/')
            assert len(response.data) > 0
            
            # Verify it's a valid JPEG
            assert response.data.startswith(b'\xff\xd8\xff'), "Response should be a valid JPEG"

    def test_api_detections_endpoint(self, test_client) -> None:
        """Test the /api/detections endpoint with real detection data."""
        response = test_client.get('/api/detections')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Verify response structure
        assert 'detections' in data
        assert 'total' in data
        assert 'page' in data
        assert 'limit' in data
        
        # Verify data types
        assert isinstance(data['detections'], list)
        assert isinstance(data['total'], int)
        assert isinstance(data['page'], int)
        assert isinstance(data['limit'], int)

    def test_api_detections_with_limit(self, test_client) -> None:
        """Test the /api/detections endpoint with limit parameter."""
        response = test_client.get('/api/detections?limit=5')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Verify limit is respected
        assert len(data['detections']) <= 5
        assert data['limit'] == 5

    def test_api_detection_image_endpoint(self, test_client) -> None:
        """Test the /api/detections/<id>/image endpoint with real detection data."""
        # First get detections to find a valid ID
        detections_response = test_client.get('/api/detections?limit=1')
        detections_data = detections_response.get_json()
        
        if detections_data['detections']:
            detection_id = detections_data['detections'][0]['id']
            
            # Test getting the image
            response = test_client.get(f'/api/detections/{detection_id}/image')
            
            # Should return 200 or 404 depending on image availability
            assert response.status_code in [200, 404]
            
            if response.status_code == 200:
                # Verify it's an image
                assert response.content_type.startswith('image/')
                assert len(response.data) > 0
        else:
            # No detections available, test with invalid ID
            response = test_client.get('/api/detections/999999/image')
            assert response.status_code == 404

    def test_api_config_get_endpoint(self, test_client) -> None:
        """Test the /api/config GET endpoint with real configuration data."""
        response = test_client.get('/api/config')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Verify response structure
        assert 'camera' in data
        assert 'ai' in data
        assert 'notifications' in data
        assert 'system' in data
        
        # Verify camera config
        assert 'source' in data['camera']
        assert 'width' in data['camera']
        assert 'height' in data['camera']
        assert 'fps' in data['camera']
        
        # Verify AI config
        assert 'model_path' in data['ai']
        assert 'confidence_threshold' in data['ai']
        
        # Verify notifications config
        assert 'audio' in data['notifications']
        assert 'email' in data['notifications']

    def test_api_config_post_endpoint(self, test_client) -> None:
        """Test the /api/config POST endpoint with real configuration updates."""
        # Get current config
        get_response = test_client.get('/api/config')
        current_config = get_response.get_json()
        
        # Create test update
        test_update = {
            'camera': {
                'width': 1280,
                'height': 720
            },
            'ai': {
                'confidence_threshold': 0.6
            }
        }
        
        # Send update
        response = test_client.post('/api/config', 
                                  json=test_update,
                                  content_type='application/json')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Verify response
        assert 'success' in data
        assert data['success'] is True
        
        # Verify config was updated
        updated_response = test_client.get('/api/config')
        updated_config = updated_response.get_json()
        
        assert updated_config['camera']['width'] == 1280
        assert updated_config['camera']['height'] == 720
        assert updated_config['ai']['confidence_threshold'] == 0.6

    def test_api_config_post_invalid_data(self, test_client) -> None:
        """Test the /api/config POST endpoint with invalid data."""
        # Test with invalid JSON
        response = test_client.post('/api/config', 
                                  data='invalid json',
                                  content_type='application/json')
        
        assert response.status_code == 400
        
        # Test with missing content type
        response = test_client.post('/api/config', 
                                  data='{"test": "data"}')
        
        assert response.status_code == 400

    def test_api_ai_test_endpoint(self, test_client) -> None:
        """Test the /api/ai/test endpoint with real AI model."""
        response = test_client.get('/api/ai/test')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Verify response structure
        assert 'success' in data
        assert 'message' in data
        assert 'model_loaded' in data
        
        # Verify data types
        assert isinstance(data['success'], bool)
        assert isinstance(data['message'], str)
        assert isinstance(data['model_loaded'], bool)

    def test_api_alerts_test_endpoint(self, test_client) -> None:
        """Test the /api/alerts/test endpoint with real alert system."""
        response = test_client.get('/api/alerts/test')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Verify response structure
        assert 'success' in data
        assert 'message' in data
        assert 'audio_enabled' in data
        
        # Verify data types
        assert isinstance(data['success'], bool)
        assert isinstance(data['message'], str)
        assert isinstance(data['audio_enabled'], bool)

    def test_api_system_restart_endpoint(self, test_client) -> None:
        """Test the /api/system/restart endpoint with real system components."""
        response = test_client.post('/api/system/restart')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Verify response structure
        assert 'success' in data
        assert 'message' in data
        
        # Verify data types
        assert isinstance(data['success'], bool)
        assert isinstance(data['message'], str)

    def test_api_logs_endpoint(self, test_client) -> None:
        """Test the /api/logs endpoint with real log data."""
        response = test_client.get('/api/logs')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Verify response structure
        assert 'logs' in data
        assert 'total_lines' in data
        
        # Verify data types
        assert isinstance(data['logs'], list)
        assert isinstance(data['total_lines'], int)

    def test_api_logs_with_limit(self, test_client) -> None:
        """Test the /api/logs endpoint with limit parameter."""
        response = test_client.get('/api/logs?limit=10')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Verify limit is respected
        assert len(data['logs']) <= 10

    def test_api_stats_endpoint(self, test_client) -> None:
        """Test the /api/stats endpoint with real system statistics."""
        response = test_client.get('/api/stats')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Verify response structure
        assert 'detections' in data
        assert 'system' in data
        assert 'performance' in data
        
        # Verify detections stats
        assert 'total' in data['detections']
        assert 'today' in data['detections']
        assert 'this_week' in data['detections']
        
        # Verify system stats
        assert 'uptime' in data['system']
        assert 'memory_usage' in data['system']
        
        # Verify performance stats
        assert 'avg_detection_time' in data['performance']
        assert 'fps' in data['performance']

    def test_web_portal_home_page(self, test_client) -> None:
        """Test the home page loads correctly."""
        response = test_client.get('/')
        
        assert response.status_code == 200
        assert b'SkyGuard' in response.data
        assert b'Dashboard' in response.data

    def test_web_portal_camera_feed_integration(self, test_client) -> None:
        """Test camera feed integration with real camera system."""
        # Test camera feed endpoint
        response = test_client.get('/api/camera/feed')
        
        # Should return 200 or 503 depending on camera availability
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            # Verify it's a valid image
            assert response.content_type.startswith('image/')
            assert len(response.data) > 0
            
            # Test with timestamp parameter (cache busting)
            timestamp = int(time.time())
            response_with_timestamp = test_client.get(f'/api/camera/feed?t={timestamp}')
            assert response_with_timestamp.status_code == 200

    def test_web_portal_error_handling(self, test_client) -> None:
        """Test web portal error handling with invalid requests."""
        # Test non-existent endpoint
        response = test_client.get('/api/nonexistent')
        assert response.status_code == 404
        
        # Test invalid detection ID
        response = test_client.get('/api/detections/invalid/image')
        assert response.status_code == 404
        
        # Test invalid method
        response = test_client.delete('/api/status')
        assert response.status_code == 405

    def test_web_portal_concurrent_requests(self, test_client) -> None:
        """Test web portal handling of concurrent requests."""
        import threading
        import queue
        
        results = queue.Queue()
        
        def make_request():
            try:
                response = test_client.get('/api/status')
                results.put(response.status_code)
            except Exception as e:
                results.put(f"Error: {e}")
        
        # Start multiple concurrent requests
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        status_codes = []
        while not results.empty():
            result = results.get()
            if isinstance(result, int):
                status_codes.append(result)
        
        # All requests should succeed
        assert len(status_codes) == 5
        assert all(code == 200 for code in status_codes)

    def test_web_portal_configuration_persistence(self, test_client) -> None:
        """Test that configuration changes persist across requests."""
        # Get initial config
        initial_response = test_client.get('/api/config')
        initial_config = initial_response.get_json()
        
        # Make a configuration change
        test_update = {
            'camera': {
                'width': 1920,
                'height': 1080
            }
        }
        
        update_response = test_client.post('/api/config', 
                                         json=test_update,
                                         content_type='application/json')
        assert update_response.status_code == 200
        
        # Verify the change persisted
        updated_response = test_client.get('/api/config')
        updated_config = updated_response.get_json()
        
        assert updated_config['camera']['width'] == 1920
        assert updated_config['camera']['height'] == 1080
        
        # Make another request to ensure persistence
        final_response = test_client.get('/api/config')
        final_config = final_response.get_json()
        
        assert final_config['camera']['width'] == 1920
        assert final_config['camera']['height'] == 1080
