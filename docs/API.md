# SkyGuard API Documentation

![SkyGuard Logo](../skyGuardShield.png)

The SkyGuard web portal provides a comprehensive REST API for system management, monitoring, and integration.

## 🌐 Base URL

```
http://localhost:8080
```

## 📋 Authentication

Currently, the API does not require authentication for local network access. This is designed for simplicity in local deployments.

## 📊 API Endpoints

### System Status

#### GET /api/status

Get current system status and component information.

**Response:**
```json
{
  "system": {
    "status": "running",
    "uptime": "2024-01-01 12:00:00",
    "last_detection": {
      "timestamp": "2024-01-01T12:00:00",
      "confidence": 0.85,
      "class": "bird"
    },
    "total_detections": 42
  },
  "camera": {
    "connected": true,
    "resolution": 1920,
    "fps": 30
  },
  "ai": {
    "model_loaded": true,
    "confidence_threshold": 0.5,
    "classes": ["bird", "raptor"]
  },
  "notifications": {
    "audio_enabled": true,
    "sms_enabled": false,
    "email_enabled": false
  }
}
```

### Detections

#### GET /api/detections

Get recent detections with optional pagination.

**Parameters:**
- `limit` (optional): Number of detections to return (default: 50)
- `offset` (optional): Number of detections to skip (default: 0)

**Response:**
```json
[
  {
    "id": 1,
    "timestamp": "2024-01-01T12:00:00",
    "confidence": 0.85,
    "class": "bird",
    "bbox": [100, 100, 200, 200]
  }
]
```

#### GET /api/detections/{id}

Get detailed information about a specific detection.

**Response:**
```json
{
  "id": 1,
  "timestamp": "2024-01-01T12:00:00",
  "confidence": 0.85,
  "class": "bird",
  "bbox": [100, 100, 200, 200],
  "image_path": "data/detections/detection_1.jpg"
}
```

#### GET /api/detections/{id}/image

Get the image associated with a detection.

**Response:** Image file (JPEG)

### Configuration

#### GET /api/config

Get current system configuration.

**Response:**
```json
{
  "system": {
    "detection_interval": 1.0,
    "max_detection_history": 1000,
    "debug_mode": false
  },
  "camera": {
    "width": 1920,
    "height": 1080,
    "fps": 30,
    "source": 0
  },
  "ai": {
    "confidence_threshold": 0.5,
    "nms_threshold": 0.4,
    "model_path": "models/raptor_detector.pt"
  },
  "notifications": {
    "audio": {
      "enabled": true,
      "volume": 0.5
    },
    "sms": {
      "enabled": false
    },
    "email": {
      "enabled": false
    }
  }
}
```

#### POST /api/config

Update system configuration.

**Request Body:**
```json
{
  "system": {
    "detection_interval": 2.0,
    "max_detection_history": 2000
  },
  "camera": {
    "width": 1280,
    "height": 720,
    "fps": 30
  },
  "ai": {
    "confidence_threshold": 0.6
  }
}
```

**Response:**
```json
{
  "message": "Configuration updated successfully"
}
```

### System Testing

#### GET /api/camera/test

Test camera connection and functionality.

**Response:**
```json
{
  "message": "Camera test successful"
}
```

#### GET /api/ai/test

Test AI model loading and functionality.

**Response:**
```json
{
  "message": "AI model test successful"
}
```

#### GET /api/alerts/test

Test alert system functionality.

**Response:**
```json
{
  "message": "Alert system test successful"
}
```

### System Control

#### POST /api/system/restart

Restart the SkyGuard system.

**Response:**
```json
{
  "message": "System restart initiated"
}
```

### Logs and Statistics

#### GET /api/logs

Get system logs.

**Parameters:**
- `limit` (optional): Number of log entries to return (default: 100)

**Response:**
```json
[
  {
    "timestamp": "2024-01-01T12:00:00",
    "level": "INFO",
    "message": "System started",
    "module": "skyguard.main"
  }
]
```

#### GET /api/stats

Get system statistics and performance metrics.

**Response:**
```json
{
  "cpu_percent": 25.5,
  "memory_percent": 60.2,
  "disk_percent": 45.8,
  "uptime": 1234567890,
  "processes": 45,
  "detections_today": 5,
  "detections_this_week": 25,
  "detections_this_month": 100
}
```

## 🔧 Error Handling

All API endpoints return appropriate HTTP status codes:

- `200 OK`: Successful request
- `400 Bad Request`: Invalid request parameters
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

Error responses include a descriptive message:

```json
{
  "error": "Camera test failed: Camera not connected"
}
```

## 📱 Usage Examples

### Python

```python
import requests

# Get system status
response = requests.get('http://localhost:8080/api/status')
status = response.json()

# Get recent detections
response = requests.get('http://localhost:8080/api/detections?limit=10')
detections = response.json()

# Update configuration
config = {
    "camera": {
        "width": 1280,
        "height": 720,
        "fps": 30
    }
}
response = requests.post('http://localhost:8080/api/config', json=config)
```

### JavaScript

```javascript
// Get system status
fetch('/api/status')
  .then(response => response.json())
  .then(data => console.log(data));

// Get detections
fetch('/api/detections?limit=5')
  .then(response => response.json())
  .then(detections => console.log(detections));

// Test camera
fetch('/api/camera/test')
  .then(response => response.json())
  .then(result => console.log(result.message));
```

### cURL

```bash
# Get system status
curl http://localhost:8080/api/status

# Get recent detections
curl http://localhost:8080/api/detections?limit=10

# Test camera connection
curl http://localhost:8080/api/camera/test

# Update configuration
curl -X POST http://localhost:8080/api/config \
  -H "Content-Type: application/json" \
  -d '{"camera":{"width":1280,"height":720}}'
```

## 🔄 Real-time Updates

The web portal automatically refreshes data every 5 seconds. For real-time updates, you can:

1. **Poll the API**: Make regular requests to `/api/status` and `/api/detections`
2. **Use WebSocket**: Future enhancement for real-time updates
3. **Webhook Integration**: Future enhancement for external notifications

## 🛡️ Security Considerations

- **Local Network Only**: API is designed for local network access
- **No Authentication**: Simplified for local deployments
- **HTTPS Support**: Can be configured with SSL certificates
- **Firewall**: Ensure proper firewall configuration for production use

## 📊 Rate Limiting

Currently, no rate limiting is implemented. For production deployments, consider:

- Implementing request rate limiting
- Adding authentication
- Using HTTPS
- Implementing proper logging and monitoring

## 🔧 Development

### Testing the API

```bash
# Test all endpoints
pytest tests/test_web_api.py -v

# Test specific endpoint
curl -X GET http://localhost:8080/api/status

# Test with invalid data
curl -X POST http://localhost:8080/api/config \
  -H "Content-Type: application/json" \
  -d '{"invalid": "data"}'
```

### Adding New Endpoints

1. Add route to `skyguard/web/app.py`
2. Implement handler method
3. Add test cases to `tests/test_web_api.py`
4. Update this documentation

## 📚 Integration Examples

### Home Assistant Integration

```yaml
# configuration.yaml
rest:
  - resource: http://localhost:8080/api/status
    scan_interval: 30
    sensor:
      - name: "SkyGuard Status"
        value_template: "{{ value_json.system.status }}"
      - name: "SkyGuard Detections"
        value_template: "{{ value_json.system.total_detections }}"
```

### Node-RED Integration

```javascript
// Get system status
msg.url = "http://localhost:8080/api/status";
msg.method = "GET";
return msg;
```

### Custom Dashboard

```html
<!DOCTYPE html>
<html>
<head>
    <title>SkyGuard Dashboard</title>
</head>
<body>
    <div id="status"></div>
    <div id="detections"></div>
    
    <script>
        async function updateStatus() {
            const response = await fetch('/api/status');
            const data = await response.json();
            document.getElementById('status').innerHTML = 
                `Status: ${data.system.status}`;
        }
        
        setInterval(updateStatus, 5000);
    </script>
</body>
</html>
```

## 🎯 Best Practices

1. **Error Handling**: Always check HTTP status codes
2. **Timeouts**: Set appropriate request timeouts
3. **Retry Logic**: Implement retry logic for failed requests
4. **Caching**: Cache responses when appropriate
5. **Monitoring**: Monitor API usage and performance
6. **Documentation**: Keep API documentation up to date

## 📞 Support

- **Documentation**: Check this file and other docs in `docs/`
- **Issues**: GitHub Issues for bug reports
- **Testing**: Use the comprehensive test suite
- **Logs**: Check `logs/skyguard.log` for debugging

---

**The SkyGuard API provides powerful integration capabilities for monitoring and managing your raptor detection system!** 🦅

