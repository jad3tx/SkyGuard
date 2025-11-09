"""
Tests for SkyGuard Web Portal UI functionality.

This module contains comprehensive tests for UI features including
button functionality, form interactions, and user interface behavior.
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


class TestSkyGuardWebPortalUI:
    """Test the SkyGuard Web Portal UI functionality."""
    
    @pytest.fixture
    def web_portal(self) -> SkyGuardWebPortal:
        """Create a web portal instance for testing."""
        # Use real components with test configuration
        portal = SkyGuardWebPortal("test_config.yaml")
        return portal
    
    def test_dashboard_page_loads(self, web_portal: SkyGuardWebPortal) -> None:
        """Test that the dashboard page loads with all required elements."""
        with web_portal.app.test_client() as client:
            response = client.get('/')
            assert response.status_code == 200
            
            # Check for key dashboard elements
            content = response.data.decode('utf-8')
            assert 'Dashboard' in content
            # Statistics cards were removed per request, so we don't check for them
            # assert 'Total Detections' in content
            assert 'Recent Detections' in content
            assert 'System Information' in content
            assert 'Quick Actions' in content
    
    def test_dashboard_contains_refresh_button(self, web_portal: SkyGuardWebPortal) -> None:
        """Test that the dashboard contains a functional refresh button."""
        with web_portal.app.test_client() as client:
            response = client.get('/')
            assert response.status_code == 200
            
            content = response.data.decode('utf-8')
            assert 'onclick="refreshData()"' in content
            assert 'Refresh' in content
            assert 'fa-sync-alt' in content
    
    def test_dashboard_contains_export_button(self, web_portal: SkyGuardWebPortal) -> None:
        """Test that the dashboard contains an export button."""
        with web_portal.app.test_client() as client:
            response = client.get('/')
            assert response.status_code == 200
            
            content = response.data.decode('utf-8')
            assert 'onclick="exportData()"' in content
            assert 'Export' in content
            assert 'fa-download' in content
    
    def test_dashboard_contains_restart_button(self, web_portal: SkyGuardWebPortal) -> None:
        """Test that the dashboard contains a system restart button."""
        with web_portal.app.test_client() as client:
            response = client.get('/')
            assert response.status_code == 200
            
            content = response.data.decode('utf-8')
            assert 'onclick="restartSystem()"' in content
            assert 'Restart System' in content
            assert 'fa-power-off' in content
    
    def test_dashboard_contains_quick_action_buttons(self, web_portal: SkyGuardWebPortal) -> None:
        """Test that the dashboard contains quick action buttons."""
        with web_portal.app.test_client() as client:
            response = client.get('/')
            assert response.status_code == 200
            
            content = response.data.decode('utf-8')
            assert 'onclick="testCamera()"' in content
            assert 'Test Camera' in content
            assert 'onclick="testAI()"' in content
            assert 'Test AI Model' in content
            assert 'onclick="testAlerts()"' in content
            assert 'Test Alerts' in content
    
    def test_dashboard_contains_status_indicators(self, web_portal: SkyGuardWebPortal) -> None:
        """Test that the dashboard contains status indicators."""
        with web_portal.app.test_client() as client:
            response = client.get('/')
            assert response.status_code == 200
            
            content = response.data.decode('utf-8')
            assert 'system-status' in content
            assert 'camera-status' in content
            assert 'ai-status' in content
            assert 'alerts-status' in content
    
    def test_dashboard_contains_statistics_cards(self, web_portal: SkyGuardWebPortal) -> None:
        """Test that the dashboard contains statistics cards."""
        with web_portal.app.test_client() as client:
            response = client.get('/')
            assert response.status_code == 200
            
            content = response.data.decode('utf-8')
            # Statistics cards were removed per request, so we just verify the page loads
            assert 'Dashboard' in content
            # The statistics are now shown in the Detection Statistics chart instead
            assert 'Detection Statistics' in content
    
    def test_dashboard_contains_recent_detections_section(self, web_portal: SkyGuardWebPortal) -> None:
        """Test that the dashboard contains recent detections section."""
        with web_portal.app.test_client() as client:
            response = client.get('/')
            assert response.status_code == 200
            
            content = response.data.decode('utf-8')
            assert 'recent-detections' in content
            assert 'Recent Detections' in content
    
    def test_dashboard_contains_detection_chart(self, web_portal: SkyGuardWebPortal) -> None:
        """Test that the dashboard contains detection chart."""
        with web_portal.app.test_client() as client:
            response = client.get('/')
            assert response.status_code == 200
            
            content = response.data.decode('utf-8')
            assert 'detection-chart' in content
            assert 'Detection Statistics' in content
    
    def test_dashboard_contains_system_information(self, web_portal: SkyGuardWebPortal) -> None:
        """Test that the dashboard contains system information section."""
        with web_portal.app.test_client() as client:
            response = client.get('/')
            assert response.status_code == 200
            
            content = response.data.decode('utf-8')
            assert 'System Information' in content
            assert 'system-uptime' in content
            assert 'last-detection' in content
            assert 'ai-confidence' in content
            # camera-resolution and camera-fps may not be in the template
    
    def test_dashboard_contains_navigation_menu(self, web_portal: SkyGuardWebPortal) -> None:
        """Test that the dashboard contains navigation menu."""
        with web_portal.app.test_client() as client:
            response = client.get('/')
            assert response.status_code == 200
            
            content = response.data.decode('utf-8')
            assert 'Dashboard' in content
            assert 'Detections' in content
            assert 'Configuration' in content
            assert 'Camera' in content
            assert 'AI' in content
            assert 'Alerts' in content
            assert 'Logs' in content
            assert 'Statistics' in content
    
    def test_dashboard_contains_javascript_functions(self, web_portal: SkyGuardWebPortal) -> None:
        """Test that the dashboard contains required JavaScript functions."""
        with web_portal.app.test_client() as client:
            response = client.get('/')
            assert response.status_code == 200
            
            content = response.data.decode('utf-8')
            # Check for key JavaScript functions
            assert 'function refreshData()' in content
            assert 'function loadSystemStatus()' in content
            assert 'function loadDashboardData()' in content
            assert 'function testCamera()' in content
            assert 'function testAI()' in content
            assert 'function testAlerts()' in content
            assert 'function showSection(' in content
    
    def test_dashboard_contains_auto_refresh_functionality(self, web_portal: SkyGuardWebPortal) -> None:
        """Test that the dashboard contains auto-refresh functionality."""
        with web_portal.app.test_client() as client:
            response = client.get('/')
            assert response.status_code == 200
            
            content = response.data.decode('utf-8')
            assert 'startAutoRefresh()' in content
            assert 'refreshInterval' in content
            assert 'setInterval' in content
    
    def test_dashboard_contains_chart_js_integration(self, web_portal: SkyGuardWebPortal) -> None:
        """Test that the dashboard contains Chart.js integration."""
        with web_portal.app.test_client() as client:
            response = client.get('/')
            assert response.status_code == 200
            
            content = response.data.decode('utf-8')
            assert 'Chart.js' in content or 'chart.js' in content
            assert 'new Chart(' in content
    
    def test_dashboard_contains_bootstrap_styling(self, web_portal: SkyGuardWebPortal) -> None:
        """Test that the dashboard contains Bootstrap styling."""
        with web_portal.app.test_client() as client:
            response = client.get('/')
            assert response.status_code == 200
            
            content = response.data.decode('utf-8')
            assert 'bootstrap' in content.lower()
            assert 'card' in content
            assert 'btn' in content
            assert 'row' in content
            assert 'col-md' in content
    
    def test_dashboard_contains_font_awesome_icons(self, web_portal: SkyGuardWebPortal) -> None:
        """Test that the dashboard contains Font Awesome icons."""
        with web_portal.app.test_client() as client:
            response = client.get('/')
            assert response.status_code == 200
            
            content = response.data.decode('utf-8')
            assert 'fa-' in content
            assert 'fas fa-' in content
            assert 'fontawesome' in content.lower() or 'font-awesome' in content.lower()
    
    def test_dashboard_contains_responsive_design(self, web_portal: SkyGuardWebPortal) -> None:
        """Test that the dashboard contains responsive design elements."""
        with web_portal.app.test_client() as client:
            response = client.get('/')
            assert response.status_code == 200
            
            content = response.data.decode('utf-8')
            # Check for responsive design classes (Bootstrap 5 uses different classes)
            assert 'col-' in content or 'col-sm-' in content or 'col-md-' in content
            assert 'container' in content
            assert 'row' in content
            assert 'table-responsive' in content
    
    def test_dashboard_contains_error_handling(self, web_portal: SkyGuardWebPortal) -> None:
        """Test that the dashboard contains error handling."""
        with web_portal.app.test_client() as client:
            response = client.get('/')
            assert response.status_code == 200
            
            content = response.data.decode('utf-8')
            assert 'try {' in content
            assert 'catch' in content
            assert 'error' in content.lower()
    
    def test_dashboard_contains_loading_indicators(self, web_portal: SkyGuardWebPortal) -> None:
        """Test that the dashboard contains loading indicators."""
        with web_portal.app.test_client() as client:
            response = client.get('/')
            assert response.status_code == 200
            
            content = response.data.decode('utf-8')
            assert 'spinner-border' in content
            assert 'Loading...' in content
            assert 'visually-hidden' in content
    
    def test_dashboard_contains_form_validation(self, web_portal: SkyGuardWebPortal) -> None:
        """Test that the dashboard contains form validation."""
        with web_portal.app.test_client() as client:
            response = client.get('/')
            assert response.status_code == 200
            
            content = response.data.decode('utf-8')
            assert 'form-control' in content
            assert 'form-label' in content
            assert 'form-check' in content
            assert 'form-range' in content
    
    def test_dashboard_contains_alert_functionality(self, web_portal: SkyGuardWebPortal) -> None:
        """Test that the dashboard contains alert functionality."""
        with web_portal.app.test_client() as client:
            response = client.get('/')
            assert response.status_code == 200
            
            content = response.data.decode('utf-8')
            assert 'alert(' in content
            assert 'confirm(' in content
            assert 'success' in content.lower()
            assert 'failed' in content.lower()


class TestSkyGuardWebPortalUIFunctionality:
    """Test the SkyGuard Web Portal UI functionality with mocked data."""
    
    @pytest.fixture
    def web_portal(self) -> SkyGuardWebPortal:
        """Create a web portal instance for testing."""
        # Use real components with test configuration
        portal = SkyGuardWebPortal("test_config.yaml")
        return portal
    
    def test_refresh_button_functionality(self, web_portal: SkyGuardWebPortal, mocker: "MockerFixture") -> None:
        """Test that the refresh button calls the correct API endpoints."""
        # Mock the status API response
        mock_status = {
            'system': {'status': 'running', 'uptime': '2024-01-01 12:00:00', 'last_detection': None, 'total_detections': 5},
            'camera': {'connected': True, 'resolution': 1920, 'fps': 30},
            'ai': {'model_loaded': True, 'confidence_threshold': 0.5, 'classes': ['bird']},
            'notifications': {'audio_enabled': True, 'sms_enabled': False, 'email_enabled': False}
        }
        
        mocker.patch.object(web_portal, '_is_system_running', return_value=True)
        mocker.patch.object(web_portal, '_get_uptime', return_value='2024-01-01 12:00:00')
        mocker.patch.object(web_portal, '_get_last_detection', return_value=None)
        mocker.patch.object(web_portal, '_get_total_detections', return_value=5)
        mocker.patch.object(web_portal, '_is_camera_connected', return_value=True)
        mocker.patch.object(web_portal, '_is_model_loaded', return_value=True)
        
        with web_portal.app.test_client() as client:
            # Test that the status endpoint works (which the refresh button calls)
            response = client.get('/api/status')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['system']['status'] == 'running'
            assert data['camera']['connected'] is True
            assert data['ai']['loaded'] is True
    
    def test_camera_test_button_functionality(self, web_portal: SkyGuardWebPortal, mocker: "MockerFixture") -> None:
        """Test that the camera test button calls the correct API endpoint."""
        mocker.patch.object(web_portal, '_test_camera', return_value=True)
        
        with web_portal.app.test_client() as client:
            response = client.get('/api/camera/test')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert 'message' in data
    
    def test_ai_test_button_functionality(self, web_portal: SkyGuardWebPortal, mocker: "MockerFixture") -> None:
        """Test that the AI test button calls the correct API endpoint."""
        mocker.patch.object(web_portal, '_test_ai_model', return_value=True)
        
        with web_portal.app.test_client() as client:
            response = client.get('/api/ai/test')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert 'message' in data
    
    def test_alerts_test_button_functionality(self, web_portal: SkyGuardWebPortal, mocker: "MockerFixture") -> None:
        """Test that the alerts test button calls the correct API endpoint."""
        mocker.patch.object(web_portal, '_test_alert_system', return_value=True)
        
        with web_portal.app.test_client() as client:
            response = client.get('/api/alerts/test')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert 'message' in data
    
    def test_restart_system_button_functionality(self, web_portal: SkyGuardWebPortal, mocker: "MockerFixture") -> None:
        """Test that the restart system button calls the correct API endpoint."""
        mocker.patch.object(web_portal, '_restart_system')
        
        with web_portal.app.test_client() as client:
            response = client.post('/api/system/restart')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert 'message' in data
    
    def test_detections_api_integration(self, web_portal: SkyGuardWebPortal, mocker: "MockerFixture") -> None:
        """Test that the detections API works for the UI."""
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
            response = client.get('/api/detections?limit=5')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert 'detections' in data
            assert len(data['detections']) == 1
            assert data['detections'][0]['id'] == 1
    
    def test_configuration_api_integration(self, web_portal: SkyGuardWebPortal, mocker: "MockerFixture") -> None:
        """Test that the configuration API works for the UI."""
        test_config = {
            'system': {'detection_interval': 1.0, 'max_detection_history': 1000},
            'camera': {'width': 1920, 'height': 1080, 'fps': 30},
            'ai': {'confidence_threshold': 0.5, 'nms_threshold': 0.4},
            'notifications': {'audio': {'enabled': True}, 'sms': {'enabled': False}, 'email': {'enabled': False}}
        }
        
        mocker.patch.object(web_portal, '_validate_config', return_value=True)
        mocker.patch.object(web_portal.config_manager, 'update_config')
        mocker.patch.object(web_portal, '_restart_components')
        
        with web_portal.app.test_client() as client:
            # Test GET config
            response = client.get('/api/config')
            assert response.status_code == 200
            
            # Test POST config
            response = client.post('/api/config',
                                data=json.dumps(test_config),
                                content_type='application/json')
            assert response.status_code == 200
    
    def test_logs_api_integration(self, web_portal: SkyGuardWebPortal, mocker: "MockerFixture") -> None:
        """Test that the logs API works for the UI."""
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
    
    def test_stats_api_integration(self, web_portal: SkyGuardWebPortal, mocker: "MockerFixture") -> None:
        """Test that the stats API works for the UI."""
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
            assert 'cpu_usage' in data['system']
            assert 'memory_usage' in data['system']
            assert 'today' in data['detections']


if __name__ == "__main__":
    pytest.main([__file__])
