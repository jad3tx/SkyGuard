"""
Tests for SkyGuard Web Portal API endpoints.

This module contains comprehensive tests for all API endpoints
to ensure proper functionality and error handling.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture

from skyguard.web.app import SkyGuardWebPortal


class TestSkyGuardWebPortalAPI:
    """Test the SkyGuard Web Portal API endpoints."""
    
    @pytest.fixture
    def web_portal(self) -> SkyGuardWebPortal:
        """Create a web portal instance for testing."""
        # Use real components with test configuration
        portal = SkyGuardWebPortal("test_config.yaml")
        return portal
    
    def test_index_route(self, web_portal: SkyGuardWebPortal) -> None:
        """Test the main index route returns the dashboard page."""
        with web_portal.app.test_client() as client:
            response = client.get('/')
            assert response.status_code == 200
            assert b'Dashboard' in response.data
    
    def test_api_status_success(self, web_portal: SkyGuardWebPortal, mocker: "MockerFixture") -> None:
        """Test the /api/status endpoint returns system status."""
        # Mock the status check methods
        mocker.patch.object(web_portal, '_is_system_running', return_value=True)
        mocker.patch.object(web_portal, '_get_uptime', return_value='2024-01-01 12:00:00')
        mocker.patch.object(web_portal, '_get_last_detection', return_value={'timestamp': '2024-01-01T12:00:00'})
        mocker.patch.object(web_portal, '_get_total_detections', return_value=5)
        mocker.patch.object(web_portal, '_is_camera_connected', return_value=True)
        mocker.patch.object(web_portal, '_is_model_loaded', return_value=True)
        
        with web_portal.app.test_client() as client:
            response = client.get('/api/status')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert 'system' in data
            assert 'camera' in data
            assert 'ai' in data
            assert 'notifications' in data
            assert data['system']['status'] == 'running'
            assert data['camera']['connected'] is True
            assert data['ai']['loaded'] is True
    
    def test_api_status_error_handling(self, web_portal: SkyGuardWebPortal, mocker: "MockerFixture") -> None:
        """Test the /api/status endpoint handles errors gracefully."""
        # Mock an exception in status check
        mocker.patch.object(web_portal, '_is_system_running', side_effect=Exception("Test error"))
        
        with web_portal.app.test_client() as client:
            response = client.get('/api/status')
            assert response.status_code == 500
            
            data = json.loads(response.data)
            assert 'error' in data
    
    def test_api_detections_success(self, web_portal: SkyGuardWebPortal, mocker: "MockerFixture") -> None:
        """Test the /api/detections endpoint returns detection data."""
        mock_detections = [
            {
                'id': 1,
                'timestamp': '2024-01-01T12:00:00',
                'confidence': 0.85,
                'class': 'bird',
                'bbox': [100, 100, 200, 200]
            }
        ]
        mocker.patch.object(web_portal, '_get_recent_detections', return_value=mock_detections)
        
        with web_portal.app.test_client() as client:
            response = client.get('/api/detections?limit=10&offset=0')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert 'detections' in data
            assert len(data['detections']) == 1
            assert data['detections'][0]['id'] == 1
            assert data['detections'][0]['class'] == 'bird'
            assert 'total' in data
            assert 'page' in data
            assert 'limit' in data
    
    def test_api_detections_with_parameters(self, web_portal: SkyGuardWebPortal, mocker: "MockerFixture") -> None:
        """Test the /api/detections endpoint with query parameters."""
        mock_detections = [{'id': i} for i in range(5)]
        mocker.patch.object(web_portal, '_get_recent_detections', return_value=mock_detections)
        
        with web_portal.app.test_client() as client:
            response = client.get('/api/detections?limit=5&offset=10')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert 'detections' in data
            assert len(data['detections']) == 5
            assert data['page'] == 3  # offset=10, limit=5, so page = (10/5)+1 = 3
    
    def test_api_detection_detail_success(self, web_portal: SkyGuardWebPortal, mocker: "MockerFixture") -> None:
        """Test the /api/detections/<id> endpoint returns specific detection."""
        mock_detection = {
            'id': 1,
            'timestamp': '2024-01-01T12:00:00',
            'confidence': 0.85,
            'class_name': 'bird',
            'bbox': [100, 100, 200, 200],
            'image_path': '',
            'metadata': {}
        }
        mocker.patch.object(web_portal.event_logger, 'get_detection_by_id', return_value=mock_detection)
        
        with web_portal.app.test_client() as client:
            response = client.get('/api/detections/1')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['id'] == 1
            assert data['class'] == 'bird'
    
    def test_api_detection_detail_not_found(self, web_portal: SkyGuardWebPortal, mocker: "MockerFixture") -> None:
        """Test the /api/detections/<id> endpoint handles missing detection."""
        mocker.patch.object(web_portal.event_logger, 'get_detection_by_id', return_value=None)
        
        with web_portal.app.test_client() as client:
            response = client.get('/api/detections/999')
            assert response.status_code == 404
            
            data = json.loads(response.data)
            assert 'error' in data
            assert 'not found' in data['error'].lower()
    
    def test_api_detection_image_success(self, web_portal: SkyGuardWebPortal) -> None:
        """Test the /api/detections/<id>/image endpoint returns image."""
        import os
        
        # Create a real test image file
        os.makedirs('data/detections', exist_ok=True)
        test_image_path = 'data/detections/detection_1.jpg'
        with open(test_image_path, 'w') as f:
            f.write('fake image data')
        
        with web_portal.app.test_client() as client:
            response = client.get('/api/detections/1/image')
            assert response.status_code == 200
            assert response.content_type == 'image/jpeg'
    
    def test_api_detection_image_not_found(self, web_portal: SkyGuardWebPortal, mocker: "MockerFixture") -> None:
        """Test the /api/detections/<id>/image endpoint handles missing image."""
        mocker.patch.object(web_portal, '_get_detection_image', return_value=None)
        
        with web_portal.app.test_client() as client:
            response = client.get('/api/detections/1/image')
            assert response.status_code == 404
    
    def test_api_config_get(self, web_portal: SkyGuardWebPortal) -> None:
        """Test the /api/config GET endpoint returns configuration."""
        with web_portal.app.test_client() as client:
            response = client.get('/api/config')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert isinstance(data, dict)
    
    def test_api_config_post_success(self, web_portal: SkyGuardWebPortal, mocker: "MockerFixture") -> None:
        """Test the /api/config POST endpoint updates configuration."""
        test_config = {
            'system': {'detection_interval': 2.0},
            'camera': {'width': 1280, 'height': 720, 'fps': 30},
            'ai': {'confidence_threshold': 0.6},
            'notifications': {'audio': {'enabled': True}}
        }
        
        mocker.patch.object(web_portal, '_validate_config', return_value=True)
        mocker.patch.object(web_portal.config_manager, 'update_config')
        mocker.patch.object(web_portal, '_restart_components')
        
        with web_portal.app.test_client() as client:
            response = client.post('/api/config', 
                                data=json.dumps(test_config),
                                content_type='application/json')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert 'message' in data
    
    def test_api_config_post_invalid_config(self, web_portal: SkyGuardWebPortal, mocker: "MockerFixture") -> None:
        """Test the /api/config POST endpoint handles invalid configuration."""
        invalid_config = {'invalid': 'config'}
        
        mocker.patch.object(web_portal, '_validate_config', return_value=False)
        
        with web_portal.app.test_client() as client:
            response = client.post('/api/config',
                                data=json.dumps(invalid_config),
                                content_type='application/json')
            assert response.status_code == 400
            
            data = json.loads(response.data)
            assert 'error' in data
    
    def test_api_config_post_no_data(self, web_portal: SkyGuardWebPortal) -> None:
        """Test the /api/config POST endpoint handles missing data."""
        with web_portal.app.test_client() as client:
            response = client.post('/api/config')
            assert response.status_code == 400
    
    def test_api_camera_test_success(self, web_portal: SkyGuardWebPortal, mocker: "MockerFixture") -> None:
        """Test the /api/camera/test endpoint."""
        mocker.patch.object(web_portal, '_test_camera', return_value=True)
        
        with web_portal.app.test_client() as client:
            response = client.get('/api/camera/test')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert 'message' in data
    
    def test_api_camera_test_failure(self, web_portal: SkyGuardWebPortal, mocker: "MockerFixture") -> None:
        """Test the /api/camera/test endpoint handles camera test failure."""
        mocker.patch.object(web_portal, '_test_camera', return_value=False)
        
        with web_portal.app.test_client() as client:
            response = client.get('/api/camera/test')
            assert response.status_code == 500
            
            data = json.loads(response.data)
            assert 'error' in data
    
    def test_api_ai_test_success(self, web_portal: SkyGuardWebPortal, mocker: "MockerFixture") -> None:
        """Test the /api/ai/test endpoint."""
        mocker.patch.object(web_portal, '_test_ai_model', return_value=True)
        
        with web_portal.app.test_client() as client:
            response = client.get('/api/ai/test')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert 'message' in data
    
    def test_api_alerts_test_success(self, web_portal: SkyGuardWebPortal, mocker: "MockerFixture") -> None:
        """Test the /api/alerts/test endpoint."""
        mocker.patch.object(web_portal, '_test_alert_system', return_value=True)
        
        with web_portal.app.test_client() as client:
            response = client.get('/api/alerts/test')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert 'message' in data
    
    def test_api_system_restart(self, web_portal: SkyGuardWebPortal, mocker: "MockerFixture") -> None:
        """Test the /api/system/restart endpoint."""
        mocker.patch.object(web_portal, '_restart_system')
        
        with web_portal.app.test_client() as client:
            response = client.post('/api/system/restart')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert 'message' in data
    
    def test_api_logs_success(self, web_portal: SkyGuardWebPortal, mocker: "MockerFixture") -> None:
        """Test the /api/logs endpoint returns system logs."""
        mock_logs = [
            {
                'timestamp': '2024-01-01T12:00:00',
                'level': 'INFO',
                'message': 'System started',
                'module': 'skyguard.main'
            }
        ]
        mocker.patch.object(web_portal, '_get_system_logs', return_value=mock_logs)
        
        with web_portal.app.test_client() as client:
            response = client.get('/api/logs?limit=50')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert 'logs' in data
            assert len(data['logs']) == 1
            assert data['logs'][0]['level'] == 'INFO'
            assert 'total_lines' in data
    
    def test_api_stats_success(self, web_portal: SkyGuardWebPortal, mocker: "MockerFixture") -> None:
        """Test the /api/stats endpoint returns system statistics."""
        mock_stats = {
            'cpu_percent': 25.5,
            'memory_percent': 60.2,
            'disk_percent': 45.8,
            'detections_today': 5,
            'detections_this_week': 25,
            'detections_this_month': 100
        }
        mocker.patch.object(web_portal, '_get_system_stats', return_value=mock_stats)
        
        with web_portal.app.test_client() as client:
            response = client.get('/api/stats')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert 'system' in data
            assert 'detections' in data
            assert 'performance' in data
            assert data['system']['cpu_usage'] == 25.5
            assert data['system']['memory_usage'] == 60.2
            assert data['system']['disk_usage'] == 45.8


if __name__ == "__main__":
    pytest.main([__file__])
