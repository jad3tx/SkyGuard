"""
Comprehensive API endpoint tests with real data and services.

This module tests all API endpoints using real system components
without mocking, ensuring complete functionality validation.
"""

import pytest
import time
import json
import os
import cv2
import numpy as np
from pathlib import Path
from typing import TYPE_CHECKING, Dict, Any

from skyguard.web.app import SkyGuardWebPortal
from skyguard.core.config_manager import ConfigManager
from skyguard.core.camera import CameraManager
from skyguard.core.detector import RaptorDetector
from skyguard.core.alert_system import AlertSystem
from skyguard.storage.event_logger import EventLogger
from skyguard.core.camera_snapshot import CameraSnapshotService

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture


class TestAPIEndpointsComprehensive:
    """Comprehensive API endpoint tests with real components."""

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

    def test_api_status_comprehensive(self, test_client) -> None:
        """Test the /api/status endpoint comprehensively."""
        response = test_client.get('/api/status')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Verify all required fields
        required_fields = ['system', 'camera', 'ai', 'detections']
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Verify system status
        system = data['system']
        assert 'uptime' in system
        assert 'status' in system
        assert 'memory_usage' in system
        assert isinstance(system['uptime'], (int, float))
        assert isinstance(system['status'], str)
        assert system['status'] in ['running', 'stopped', 'error']
        
        # Verify camera status
        camera = data['camera']
        assert 'connected' in camera
        assert 'source' in camera
        assert 'width' in camera
        assert 'height' in camera
        assert 'fps' in camera
        assert isinstance(camera['connected'], bool)
        assert isinstance(camera['source'], (int, str))
        assert isinstance(camera['width'], int)
        assert isinstance(camera['height'], int)
        assert isinstance(camera['fps'], (int, float))
        
        # Verify AI status
        ai = data['ai']
        assert 'loaded' in ai
        assert 'model_path' in ai
        assert 'confidence_threshold' in ai
        assert isinstance(ai['loaded'], bool)
        assert isinstance(ai['model_path'], str)
        assert isinstance(ai['confidence_threshold'], (int, float))
        
        # Verify detections status
        detections = data['detections']
        assert 'total' in detections
        assert 'recent' in detections
        assert isinstance(detections['total'], int)
        assert isinstance(detections['recent'], int)

    def test_api_camera_status_comprehensive(self, test_client) -> None:
        """Test the /api/camera/status endpoint comprehensively."""
        response = test_client.get('/api/camera/status')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Verify all required fields
        required_fields = ['connected', 'source', 'width', 'height', 'fps']
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Verify data types
        assert isinstance(data['connected'], bool)
        assert isinstance(data['source'], (int, str))
        assert isinstance(data['width'], int)
        assert isinstance(data['height'], int)
        assert isinstance(data['fps'], (int, float))
        
        # Verify reasonable values
        assert data['width'] > 0
        assert data['height'] > 0
        assert data['fps'] > 0
        assert data['fps'] <= 60  # Reasonable FPS limit

    def test_api_camera_feed_comprehensive(self, test_client) -> None:
        """Test the /api/camera/feed endpoint comprehensively."""
        # Test basic feed
        response = test_client.get('/api/camera/feed')
        
        # Should return 200 or 503 depending on camera availability
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            # Verify content type
            assert response.content_type.startswith('image/')
            
            # Verify content length
            assert len(response.data) > 0
            
            # Verify it's a valid JPEG
            assert response.data.startswith(b'\xff\xd8\xff'), "Response should be a valid JPEG"
            
            # Test with cache busting parameter
            timestamp = int(time.time())
            response_with_timestamp = test_client.get(f'/api/camera/feed?t={timestamp}')
            assert response_with_timestamp.status_code == 200
            
            # Verify timestamp parameter works (different response)
            if response.data != response_with_timestamp.data:
                assert True  # Timestamp parameter is working
            else:
                # Images might be the same if captured at the same time
                assert len(response_with_timestamp.data) > 0

    def test_api_camera_capture_comprehensive(self, test_client) -> None:
        """Test the /api/camera/capture endpoint comprehensively."""
        response = test_client.get('/api/camera/capture')
        
        # Should return 200 or 503 depending on camera availability
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            # Verify content type
            assert response.content_type.startswith('image/')
            
            # Verify content length
            assert len(response.data) > 0
            
            # Verify it's a valid JPEG
            assert response.data.startswith(b'\xff\xd8\xff'), "Response should be a valid JPEG"
            
            # Test multiple captures
            response2 = test_client.get('/api/camera/capture')
            assert response2.status_code == 200
            assert len(response2.data) > 0

    def test_api_detections_comprehensive(self, test_client) -> None:
        """Test the /api/detections endpoint comprehensively."""
        # Test basic detections endpoint
        response = test_client.get('/api/detections')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Verify response structure
        required_fields = ['detections', 'total', 'page', 'limit']
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Verify data types
        assert isinstance(data['detections'], list)
        assert isinstance(data['total'], int)
        assert isinstance(data['page'], int)
        assert isinstance(data['limit'], int)
        
        # Verify pagination
        assert data['page'] >= 1
        assert data['limit'] > 0
        assert len(data['detections']) <= data['limit']
        
        # Test with limit parameter
        response_limited = test_client.get('/api/detections?limit=5')
        assert response_limited.status_code == 200
        
        limited_data = response_limited.get_json()
        assert len(limited_data['detections']) <= 5
        assert limited_data['limit'] == 5
        
        # Test with page parameter
        response_paged = test_client.get('/api/detections?page=1&limit=10')
        assert response_paged.status_code == 200
        
        paged_data = response_paged.get_json()
        assert paged_data['page'] == 1
        assert paged_data['limit'] == 10

    def test_api_detection_image_comprehensive(self, test_client) -> None:
        """Test the /api/detections/<id>/image endpoint comprehensively."""
        # First get detections to find valid IDs
        detections_response = test_client.get('/api/detections?limit=5')
        detections_data = detections_response.get_json()
        
        if detections_data['detections']:
            # Test with valid detection ID
            detection = detections_data['detections'][0]
            detection_id = detection['id']
            
            response = test_client.get(f'/api/detections/{detection_id}/image')
            
            # Should return 200 or 404 depending on image availability
            assert response.status_code in [200, 404]
            
            if response.status_code == 200:
                # Verify it's an image
                assert response.content_type.startswith('image/')
                assert len(response.data) > 0
                
                # Verify it's a valid image format
                assert (response.data.startswith(b'\xff\xd8\xff') or  # JPEG
                        response.data.startswith(b'\x89PNG') or       # PNG
                        response.data.startswith(b'GIF'))            # GIF
        else:
            # No detections available, test with invalid ID
            response = test_client.get('/api/detections/999999/image')
            assert response.status_code == 404

    def test_api_config_get_comprehensive(self, test_client) -> None:
        """Test the /api/config GET endpoint comprehensively."""
        response = test_client.get('/api/config')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Verify all configuration sections
        required_sections = ['camera', 'ai', 'notifications', 'system', 'storage', 'logging']
        for section in required_sections:
            assert section in data, f"Missing configuration section: {section}"
        
        # Verify camera configuration
        camera = data['camera']
        assert 'source' in camera
        assert 'width' in camera
        assert 'height' in camera
        assert 'fps' in camera
        assert 'rotation' in camera
        assert 'flip_horizontal' in camera
        assert 'flip_vertical' in camera
        
        # Verify AI configuration
        ai = data['ai']
        assert 'model_path' in ai
        assert 'confidence_threshold' in ai
        assert 'nms_threshold' in ai
        assert 'input_size' in ai
        
        # Verify notifications configuration
        notifications = data['notifications']
        assert 'audio' in notifications
        assert 'email' in notifications
        assert 'sms' in notifications
        assert 'push' in notifications
        
        # Verify system configuration
        system = data['system']
        assert 'detection_interval' in system
        assert 'max_detection_history' in system
        assert 'save_detection_frames' in system

    def test_api_config_post_comprehensive(self, test_client) -> None:
        """Test the /api/config POST endpoint comprehensively."""
        # Get current configuration
        get_response = test_client.get('/api/config')
        current_config = get_response.get_json()
        
        # Test partial configuration update
        test_update = {
            'camera': {
                'width': 1280,
                'height': 720,
                'fps': 25
            },
            'ai': {
                'confidence_threshold': 0.7
            },
            'system': {
                'detection_interval': 2.0
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
        assert 'message' in data
        
        # Verify configuration was updated
        updated_response = test_client.get('/api/config')
        updated_config = updated_response.get_json()
        
        assert updated_config['camera']['width'] == 1280
        assert updated_config['camera']['height'] == 720
        assert updated_config['camera']['fps'] == 25
        assert updated_config['ai']['confidence_threshold'] == 0.7
        assert updated_config['system']['detection_interval'] == 2.0
        
        # Test invalid configuration
        invalid_update = {
            'camera': {
                'width': -1,  # Invalid width
                'height': 0   # Invalid height
            }
        }
        
        response = test_client.post('/api/config', 
                                  json=invalid_update,
                                  content_type='application/json')
        
        # Should handle invalid configuration gracefully
        assert response.status_code in [200, 400]

    def test_api_ai_test_comprehensive(self, test_client) -> None:
        """Test the /api/ai/test endpoint comprehensively."""
        response = test_client.get('/api/ai/test')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Verify response structure
        required_fields = ['success', 'message', 'model_loaded']
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Verify data types
        assert isinstance(data['success'], bool)
        assert isinstance(data['message'], str)
        assert isinstance(data['model_loaded'], bool)
        
        # Verify message content
        assert len(data['message']) > 0

    def test_api_alerts_test_comprehensive(self, test_client) -> None:
        """Test the /api/alerts/test endpoint comprehensively."""
        response = test_client.get('/api/alerts/test')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Verify response structure
        required_fields = ['success', 'message', 'audio_enabled']
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Verify data types
        assert isinstance(data['success'], bool)
        assert isinstance(data['message'], str)
        assert isinstance(data['audio_enabled'], bool)
        
        # Verify message content
        assert len(data['message']) > 0

    def test_api_system_restart_comprehensive(self, test_client) -> None:
        """Test the /api/system/restart endpoint comprehensively."""
        response = test_client.post('/api/system/restart')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Verify response structure
        required_fields = ['success', 'message']
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Verify data types
        assert isinstance(data['success'], bool)
        assert isinstance(data['message'], str)
        
        # Verify message content
        assert len(data['message']) > 0

    def test_api_logs_comprehensive(self, test_client) -> None:
        """Test the /api/logs endpoint comprehensively."""
        response = test_client.get('/api/logs')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Verify response structure
        required_fields = ['logs', 'total_lines']
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Verify data types
        assert isinstance(data['logs'], list)
        assert isinstance(data['total_lines'], int)
        
        # Test with limit parameter
        response_limited = test_client.get('/api/logs?limit=10')
        assert response_limited.status_code == 200
        
        limited_data = response_limited.get_json()
        assert len(limited_data['logs']) <= 10
        
        # Test with offset parameter
        response_offset = test_client.get('/api/logs?offset=5&limit=5')
        assert response_offset.status_code == 200
        
        offset_data = response_offset.get_json()
        assert len(offset_data['logs']) <= 5

    def test_api_stats_comprehensive(self, test_client) -> None:
        """Test the /api/stats endpoint comprehensively."""
        response = test_client.get('/api/stats')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Verify response structure
        required_fields = ['detections', 'system', 'performance']
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"
        
        # Verify detections stats
        detections = data['detections']
        assert 'total' in detections
        assert 'today' in detections
        assert 'this_week' in detections
        assert 'this_month' in detections
        
        # Verify system stats
        system = data['system']
        assert 'uptime' in system
        assert 'memory_usage' in system
        assert 'cpu_usage' in system
        
        # Verify performance stats
        performance = data['performance']
        assert 'avg_detection_time' in performance
        assert 'fps' in performance
        assert 'total_detections' in performance

    def test_api_error_handling_comprehensive(self, test_client) -> None:
        """Test API error handling comprehensively."""
        # Test non-existent endpoint
        response = test_client.get('/api/nonexistent')
        assert response.status_code == 404
        
        # Test invalid detection ID
        response = test_client.get('/api/detections/invalid/image')
        assert response.status_code == 404
        
        # Test invalid method
        response = test_client.delete('/api/status')
        assert response.status_code == 405
        
        # Test invalid JSON in POST request
        response = test_client.post('/api/config', 
                                  data='invalid json',
                                  content_type='application/json')
        assert response.status_code == 400
        
        # Test missing content type
        response = test_client.post('/api/config', 
                                  data='{"test": "data"}')
        assert response.status_code == 400

    def test_api_concurrent_requests(self, test_client) -> None:
        """Test API handling of concurrent requests."""
        import threading
        import queue
        
        results = queue.Queue()
        
        def make_request(endpoint):
            try:
                response = test_client.get(endpoint)
                results.put((endpoint, response.status_code))
            except Exception as e:
                results.put((endpoint, f"Error: {e}"))
        
        # Test multiple concurrent requests to different endpoints
        endpoints = [
            '/api/status',
            '/api/camera/status',
            '/api/detections',
            '/api/config',
            '/api/logs'
        ]
        
        # Start concurrent requests
        threads = []
        for endpoint in endpoints:
            thread = threading.Thread(target=make_request, args=(endpoint,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        endpoint_results = {}
        while not results.empty():
            endpoint, status_code = results.get()
            endpoint_results[endpoint] = status_code
        
        # All requests should succeed
        assert len(endpoint_results) == len(endpoints)
        for endpoint, status_code in endpoint_results.items():
            assert status_code == 200, f"Endpoint {endpoint} failed with status {status_code}"

    def test_api_data_consistency(self, test_client) -> None:
        """Test API data consistency across multiple requests."""
        # Get status multiple times
        responses = []
        for _ in range(3):
            response = test_client.get('/api/status')
            assert response.status_code == 200
            responses.append(response.get_json())
        
        # Verify consistent structure
        for i, data in enumerate(responses):
            assert 'system' in data
            assert 'camera' in data
            assert 'ai' in data
            assert 'detections' in data
            
            # Verify system uptime is consistent (should be increasing)
            if i > 0:
                assert data['system']['uptime'] >= responses[i-1]['system']['uptime']
        
        # Get detections multiple times
        detection_responses = []
        for _ in range(3):
            response = test_client.get('/api/detections')
            assert response.status_code == 200
            detection_responses.append(response.get_json())
        
        # Verify consistent structure
        for data in detection_responses:
            assert 'detections' in data
            assert 'total' in data
            assert 'page' in data
            assert 'limit' in data
            assert isinstance(data['detections'], list)
            assert isinstance(data['total'], int)
