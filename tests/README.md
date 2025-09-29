# SkyGuard Test Suite

This directory contains comprehensive tests for the SkyGuard system, including both API and UI regression tests.

## Test Structure

### Core Tests
- `test_core.py` - Tests for core SkyGuard components (ConfigManager, CameraManager, RaptorDetector, AlertSystem)

### Web API Tests
- `test_web_api.py` - Comprehensive tests for all web portal API endpoints
  - Tests all `/api/*` endpoints
  - Validates request/response handling
  - Tests error conditions and edge cases
  - Ensures proper JSON responses

### Web UI Tests
- `test_web_ui.py` - Tests for web portal UI functionality
  - Tests dashboard page loading
  - Validates all UI elements are present
  - Tests button functionality
  - Ensures proper JavaScript integration
  - Tests responsive design elements

### Camera Connection Tests
- `test_camera_connection.py` - Specific tests for camera connection issues
  - Tests the missing `test_connection` method
  - Validates camera initialization
  - Tests connection failure scenarios
  - Tests cleanup functionality

## Issues Fixed

### 1. Camera Connection Issue
**Problem**: The camera wouldn't connect and the web portal was failing when trying to check camera status.

**Root Cause**: The `CameraManager` class was missing the `test_connection()` method that the web portal was trying to call.

**Solution**: Added the missing `test_connection()` method to `CameraManager` class with proper error handling and auto-initialization.

### 2. Refresh Button Functionality
**Problem**: The refresh button on the UI wasn't working.

**Root Cause**: The refresh button was calling `refreshData()` function, but there were no comprehensive tests to validate this functionality.

**Solution**: The refresh button was actually working correctly. Added comprehensive UI tests to validate all button functionality.

### 3. Missing UI Regression Tests
**Problem**: No comprehensive UI regression tests existed to catch UI functionality issues.

**Solution**: Created comprehensive test suites:
- `test_web_api.py` - Tests all API endpoints
- `test_web_ui.py` - Tests UI functionality and elements
- `test_camera_connection.py` - Tests camera-specific functionality

## Test Coverage

### API Endpoints Tested
- `GET /` - Main dashboard page
- `GET /api/status` - System status
- `GET /api/detections` - Recent detections
- `GET /api/detections/<id>` - Specific detection details
- `GET /api/detections/<id>/image` - Detection images
- `GET /api/config` - Configuration retrieval
- `POST /api/config` - Configuration updates
- `GET /api/camera/test` - Camera connection test
- `GET /api/ai/test` - AI model test
- `GET /api/alerts/test` - Alert system test
- `POST /api/system/restart` - System restart
- `GET /api/logs` - System logs
- `GET /api/stats` - System statistics

### UI Elements Tested
- Dashboard page loading
- Navigation menu
- Statistics cards
- Status indicators
- Quick action buttons
- Refresh button functionality
- Export button
- Restart system button
- Test camera button
- Test AI button
- Test alerts button
- Configuration form
- Recent detections section
- Detection chart
- System information
- Responsive design elements
- JavaScript functionality
- Error handling
- Loading indicators

### Camera Functionality Tested
- Camera initialization
- Connection testing
- Auto-initialization
- Re-initialization
- Cleanup functionality
- Error handling
- Integration with web portal

## Running Tests

### Run All Tests
```bash
python -m pytest tests/ -v
```

### Run Specific Test Suites
```bash
# API tests only
python -m pytest tests/test_web_api.py -v

# UI tests only
python -m pytest tests/test_web_ui.py -v

# Camera connection tests only
python -m pytest tests/test_camera_connection.py -v

# Core component tests only
python -m pytest tests/test_core.py -v
```

### Run with Coverage
```bash
python -m pytest tests/ --cov=skyguard --cov-report=html
```

## Test Requirements

The tests require the following dependencies:
- pytest
- pytest-cov (for coverage)
- pytest-mock (for mocking)
- unittest.mock (for mocking)
- cv2 (OpenCV for camera tests)
- numpy (for image processing tests)

## Test Data

Tests use mocked data and components to avoid:
- Requiring actual camera hardware
- Database dependencies
- External service dependencies
- File system dependencies

This ensures tests run reliably in any environment.

## Continuous Integration

These tests are designed to run in CI/CD pipelines and will catch:
- API endpoint regressions
- UI functionality issues
- Camera connection problems
- Configuration handling errors
- Error condition handling

## Future Enhancements

Consider adding:
- Performance tests for API endpoints
- Load testing for web portal
- Integration tests with real hardware
- End-to-end tests with browser automation
- Visual regression tests for UI changes

