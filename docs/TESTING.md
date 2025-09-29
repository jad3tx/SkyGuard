# SkyGuard Testing Guide

This guide covers the comprehensive testing suite for SkyGuard, including unit tests, integration tests, and UI regression tests.

## 🧪 Test Suite Overview

SkyGuard includes a comprehensive test suite with the following components:

- **Core Component Tests**: Tests for core SkyGuard functionality
- **Web API Tests**: Tests for all REST API endpoints
- **Web UI Tests**: Tests for web interface functionality
- **Camera Connection Tests**: Tests for camera functionality and connection issues
- **Integration Tests**: Tests for component integration

## 📁 Test Structure

```
tests/
├── __init__.py                    # Test package initialization
├── test_core.py                   # Core component tests
├── test_web_api.py                # Web API endpoint tests
├── test_web_ui.py                 # Web UI functionality tests
├── test_camera_connection.py      # Camera connection tests
└── README.md                      # Test documentation
```

## 🚀 Running Tests

### Prerequisites

```bash
# Install test dependencies
pip install pytest pytest-cov pytest-mock

# Install SkyGuard in development mode
pip install -e .
```

### Basic Test Execution

```bash
# Run all tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ --cov=skyguard --cov-report=html

# Run specific test file
pytest tests/test_web_api.py -v

# Run specific test class
pytest tests/test_web_api.py::TestSkyGuardWebPortalAPI -v

# Run specific test method
pytest tests/test_web_api.py::TestSkyGuardWebPortalAPI::test_api_status_success -v
```

### Test Categories

```bash
# API tests only
pytest tests/test_web_api.py -v

# UI tests only
pytest tests/test_web_ui.py -v

# Camera tests only
pytest tests/test_camera_connection.py -v

# Core component tests only
pytest tests/test_core.py -v
```

## 🔧 Test Components

### Core Component Tests (`test_core.py`)

Tests the fundamental SkyGuard components:

- **ConfigManager**: Configuration loading, saving, and validation
- **CameraManager**: Camera initialization, frame capture, and cleanup
- **RaptorDetector**: AI model loading, detection, and drawing
- **AlertSystem**: Alert creation, rate limiting, and statistics

**Key Test Cases:**
- Configuration file handling
- Camera initialization success/failure
- AI model loading and detection
- Alert system functionality
- Error handling and edge cases

### Web API Tests (`test_web_api.py`)

Tests all REST API endpoints:

- **System Status**: `/api/status` endpoint
- **Detections**: `/api/detections` endpoints
- **Configuration**: `/api/config` endpoints
- **System Testing**: Camera, AI, and alert test endpoints
- **System Control**: Restart and monitoring endpoints
- **Logs and Statistics**: Log and stats endpoints

**Key Test Cases:**
- Successful API responses
- Error handling and status codes
- Request parameter validation
- JSON response format validation
- Integration with core components

### Web UI Tests (`test_web_ui.py`)

Tests web interface functionality:

- **Dashboard Loading**: Page elements and JavaScript
- **Button Functionality**: All interactive elements
- **Form Handling**: Configuration forms
- **API Integration**: Frontend-backend communication
- **Responsive Design**: UI elements and styling

**Key Test Cases:**
- Dashboard page loading
- Navigation menu functionality
- Statistics display
- Quick action buttons
- Configuration form handling
- JavaScript functionality

### Camera Connection Tests (`test_camera_connection.py`)

Tests camera functionality and connection issues:

- **Camera Initialization**: Success and failure scenarios
- **Connection Testing**: The `test_connection()` method
- **Auto-initialization**: Automatic camera setup
- **Error Handling**: Connection failures and exceptions
- **Cleanup**: Proper resource cleanup

**Key Test Cases:**
- Camera initialization success/failure
- Connection test functionality
- Auto-initialization when not connected
- Re-initialization when connection lost
- Cleanup with exceptions
- Integration with web portal

## 🎯 Test Coverage

### API Endpoints Covered

- ✅ `GET /` - Main dashboard page
- ✅ `GET /api/status` - System status
- ✅ `GET /api/detections` - Recent detections
- ✅ `GET /api/detections/{id}` - Specific detection
- ✅ `GET /api/detections/{id}/image` - Detection image
- ✅ `GET /api/config` - Configuration retrieval
- ✅ `POST /api/config` - Configuration updates
- ✅ `GET /api/camera/test` - Camera connection test
- ✅ `GET /api/ai/test` - AI model test
- ✅ `GET /api/alerts/test` - Alert system test
- ✅ `POST /api/system/restart` - System restart
- ✅ `GET /api/logs` - System logs
- ✅ `GET /api/stats` - System statistics

### UI Elements Covered

- ✅ Dashboard page loading
- ✅ Navigation menu
- ✅ Statistics cards
- ✅ Status indicators
- ✅ Quick action buttons
- ✅ Refresh button functionality
- ✅ Export button
- ✅ Restart system button
- ✅ Test camera button
- ✅ Test AI button
- ✅ Test alerts button
- ✅ Configuration form
- ✅ Recent detections section
- ✅ Detection chart
- ✅ System information
- ✅ Responsive design elements
- ✅ JavaScript functionality
- ✅ Error handling
- ✅ Loading indicators

### Camera Functionality Covered

- ✅ Camera initialization
- ✅ Connection testing
- ✅ Auto-initialization
- ✅ Re-initialization
- ✅ Cleanup functionality
- ✅ Error handling
- ✅ Integration with web portal

## 🔍 Test Data and Mocking

### Mocking Strategy

Tests use comprehensive mocking to avoid:
- **Hardware Dependencies**: No actual camera hardware required
- **Database Dependencies**: Mocked data storage
- **External Services**: Mocked notification services
- **File System Dependencies**: Mocked file operations

### Test Data

```python
# Example test data for detections
mock_detections = [
    {
        'id': 1,
        'timestamp': '2024-01-01T12:00:00',
        'confidence': 0.85,
        'class': 'bird',
        'bbox': [100, 100, 200, 200]
    }
]

# Example test data for system status
mock_status = {
    'system': {
        'status': 'running',
        'uptime': '2024-01-01 12:00:00',
        'total_detections': 5
    },
    'camera': {
        'connected': True,
        'resolution': 1920,
        'fps': 30
    }
}
```

## 🚨 Common Test Issues

### Camera Connection Issues

**Problem**: Camera tests failing due to hardware dependencies
**Solution**: Use comprehensive mocking for camera functionality

```python
@patch('cv2.VideoCapture')
def test_camera_initialization(self, mock_video_capture):
    # Mock successful camera
    mock_cap = Mock()
    mock_cap.isOpened.return_value = True
    mock_cap.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
    mock_video_capture.return_value = mock_cap
```

### Web Portal Initialization

**Problem**: Web portal tests failing due to component dependencies
**Solution**: Mock all external dependencies

```python
def test_web_portal_initialization(self, mocker):
    mocker.patch('skyguard.core.config_manager.ConfigManager')
    mocker.patch('skyguard.storage.event_logger.EventLogger')
    mocker.patch('skyguard.core.detector.RaptorDetector')
    mocker.patch('skyguard.core.camera.CameraManager')
    mocker.patch('skyguard.core.alert_system.AlertSystem')
```

### API Response Validation

**Problem**: API tests failing due to response format changes
**Solution**: Use comprehensive response validation

```python
def test_api_status_response(self):
    response = client.get('/api/status')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'system' in data
    assert 'camera' in data
    assert 'ai' in data
    assert 'notifications' in data
```

## 🔧 Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, 3.10, 3.11]

    steps:
    - uses: actions/checkout@v3
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        pytest tests/ --cov=skyguard --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true
        args: [tests/, -v]
```

## 📊 Test Metrics

### Coverage Goals

- **Overall Coverage**: >90%
- **API Coverage**: >95%
- **Core Components**: >90%
- **UI Functionality**: >85%

### Performance Targets

- **Test Execution Time**: <30 seconds
- **API Response Time**: <100ms
- **UI Load Time**: <2 seconds
- **Camera Test Time**: <5 seconds

## 🎯 Best Practices

### Test Writing

1. **Descriptive Names**: Use clear, descriptive test names
2. **Single Responsibility**: Each test should test one thing
3. **Arrange-Act-Assert**: Structure tests clearly
4. **Mocking**: Mock external dependencies
5. **Error Cases**: Test both success and failure scenarios

### Test Organization

1. **Group Related Tests**: Use test classes for related functionality
2. **Setup and Teardown**: Use fixtures for common setup
3. **Test Data**: Use consistent test data
4. **Documentation**: Document complex test scenarios

### Maintenance

1. **Regular Updates**: Update tests when functionality changes
2. **Coverage Monitoring**: Monitor test coverage trends
3. **Performance**: Monitor test execution time
4. **Documentation**: Keep test documentation current

## 🚀 Advanced Testing

### Load Testing

```python
# Example load test for API
import concurrent.futures
import requests

def test_api_load():
    def make_request():
        response = requests.get('http://localhost:8080/api/status')
        return response.status_code == 200
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_request) for _ in range(100)]
        results = [future.result() for future in futures]
    
    assert all(results)
```

### Integration Testing

```python
# Example integration test
def test_full_system_integration():
    # Start web portal
    portal = SkyGuardWebPortal("test_config.yaml")
    
    # Test camera connection
    assert portal._is_camera_connected()
    
    # Test API endpoints
    with portal.app.test_client() as client:
        response = client.get('/api/status')
        assert response.status_code == 200
```

## 📞 Support

### Getting Help

1. **Test Documentation**: Check `tests/README.md`
2. **Test Issues**: Check test output and logs
3. **Coverage Reports**: Review HTML coverage reports
4. **GitHub Issues**: Report test-related issues

### Debugging Tests

```bash
# Run tests with verbose output
pytest tests/ -v -s

# Run specific test with debugging
pytest tests/test_camera_connection.py::TestCameraConnection::test_camera_initialization -v -s

# Run tests with coverage and HTML report
pytest tests/ --cov=skyguard --cov-report=html
```

---

**The SkyGuard test suite ensures reliable, maintainable, and comprehensive testing of all system components!** 🧪✅

