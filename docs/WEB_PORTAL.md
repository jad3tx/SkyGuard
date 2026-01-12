# SkyGuard Web Portal

![SkyGuard Logo](../skyGuardShield.png)

A comprehensive web-based interface for managing and monitoring your SkyGuard raptor detection system.

## 🌐 **Features**

### **Dashboard**
- **Real-time System Status**: Monitor system, camera, AI model, and alert status
- **Detection Statistics**: View total detections, daily/weekly/monthly counts
- **Recent Detections**: Browse latest detections with images and details
- **System Information**: Uptime, last detection, camera specs, AI confidence
- **Quick Actions**: Test camera, AI model, and alert systems

### **Detection Management**
- **Detection History**: Browse all detections with search and filtering
- **Detection Images**: View captured images from detections
- **Detection Details**: Confidence scores, timestamps, bounding boxes
- **Export Functionality**: Download detection data and images

### **Configuration Management**
- **System Settings**: Detection interval, history limits, debug mode
- **Camera Configuration**: Resolution, FPS, rotation, flip settings
- **AI Model Settings**: Confidence thresholds, NMS settings, model selection
- **Notification Settings**: Audio, SMS, email, Discord webhook alert configuration
- **Real-time Updates**: Changes take effect immediately

### **System Monitoring**
- **Camera Management**: Test camera connection, capture test images
- **AI Model Management**: Test model loading, performance monitoring
- **Alert System**: Test notification systems, configure alert settings
- **System Logs**: View real-time logs with filtering and search
- **Statistics**: CPU, memory, disk usage, detection rates

## 🚀 **Quick Start**

### **Installation**

```bash
# Install web portal dependencies
pip install -r requirements-web.txt

# Start the web portal
python scripts/start_web_portal.py
```

### **Access the Portal**

Open your web browser and navigate to:
```
http://localhost:8080
```

### **Default Configuration**

- **Host**: `0.0.0.0` (accessible from any device on the network)
- **Port**: `8080`
- **Debug Mode**: Disabled by default

## ⚙️ **Configuration**

### **Command Line Options**

```bash
python scripts/start_web_portal.py [OPTIONS]

Options:
  --host HOST          Host to bind to (default: 0.0.0.0)
  --port PORT          Port to bind to (default: 8080)
  --debug              Enable debug mode
  --config CONFIG      Configuration file path


### **Environment Variables**

```bash
# Set custom configuration
export SKYGUARD_CONFIG_PATH="config/skyguard.yaml"
export SKYGUARD_WEB_HOST="0.0.0.0"
export SKYGUARD_WEB_PORT="8080"
export SKYGUARD_WEB_DEBUG="false"
```

## 📱 **Web Interface Guide**

### **Dashboard**

The main dashboard provides an overview of your SkyGuard system:

1. **Status Indicators**: 
   - 🟢 **System**: Running/Stopped
   - 🟢 **Camera**: Connected/Disconnected
   - 🟢 **AI Model**: Loaded/Not Loaded
   - 🟢 **Alerts**: Enabled/Disabled

2. **Statistics Cards**:
   - Total detections
   - Today's detections
   - This week's detections
   - This month's detections

3. **Recent Detections**:
   - Latest 5 detections with images
   - Detection details and timestamps
   - Confidence scores

4. **Quick Actions**:
   - Test camera connection
   - Test AI model
   - Test alert system
   - Configure system

### **Detection Management**

Browse and manage all detections:

1. **Search and Filter**:
   - Search by detection ID or class
   - Filter by date range (today, week, month)
   - Sort by timestamp or confidence

2. **Detection Cards**:
   - Detection image thumbnails
   - Class and confidence information
   - Timestamp and bounding box details
   - Click to view full details

3. **Export Options**:
   - Download detection images
   - Export detection data (CSV, JSON)
   - Generate detection reports

### **Configuration Management**

Configure all aspects of your SkyGuard system:

1. **System Settings**:
   - Detection interval (0.1-10 seconds)
   - Maximum detection history (100-10000)
   - Debug mode toggle

2. **Camera Settings**:
   - Resolution (320x240 to 1920x1080)
   - FPS (1-60)
   - Rotation and flip settings

3. **AI Model Settings**:
   - Confidence threshold (0.0-1.0)
   - NMS threshold (0.0-1.0)
   - Model selection

4. **Notification Settings**:
   - Audio alerts (enabled/disabled, volume control)
   - SMS alerts (enabled/disabled, requires Twilio account)
   - Email alerts (enabled/disabled, requires SMTP server)
   - Discord webhook alerts (enabled/disabled, free webhook setup)
   
   **Discord Webhook Setup:**
   1. Open your Discord server
   2. Go to **Server Settings** → **Integrations** → **Webhooks**
   3. Click **New Webhook** or **Create Webhook**
   4. Choose a channel for alerts
   5. Name the webhook (e.g., "SkyGuard Alerts")
   6. Click **Copy Webhook URL**
   7. Paste the URL into the Discord Webhook URL field in the web portal
   8. Optionally set a custom bot username
   9. Enable Discord alerts and save

### **System Monitoring**

Monitor and test system components:

1. **Camera Management**:
   - Test camera connection
   - Capture test images
   - View camera specifications
   - Monitor camera performance

2. **AI Model Management**:
   - Test model loading
   - Monitor model performance
   - View model information
   - Test detection accuracy

3. **Alert System**:
   - Test notification systems
   - Configure alert settings
   - Monitor alert delivery
   - View alert history

4. **System Logs**:
   - Real-time log viewing
   - Log filtering and search
   - Log level filtering
   - Log export

5. **Statistics**:
   - System resource usage
   - Detection statistics
   - Performance metrics
   - Historical data

## 🔧 **Advanced Features**

### **Real-time Updates**

The web portal automatically refreshes every 5 seconds to show:
- Latest system status
- New detections
- Updated statistics
- Current configuration

### **Responsive Design**

The interface is optimized for:
- **Desktop**: Full-featured interface
- **Tablet**: Touch-friendly navigation
- **Mobile**: Compact view with essential features

### **Security Features**

- **Local Network Access**: Only accessible from your local network
- **No Authentication**: Simple setup for local use
- **HTTPS Support**: Can be configured with SSL certificates

### **API Endpoints**

The web portal provides REST API endpoints:

```
GET  /api/status              # System status
GET  /api/detections          # Recent detections
GET  /api/detections/{id}     # Specific detection
GET  /api/detections/{id}/image # Detection image
GET  /api/config              # Current configuration
POST /api/config              # Update configuration
GET  /api/camera/test         # Test camera
GET  /api/ai/test             # Test AI model
GET  /api/alerts/test         # Test alerts
POST /api/system/restart      # Restart system
GET  /api/logs                # System logs
GET  /api/stats               # System statistics
```

## 🚀 **Deployment**

### **Local Development**

```bash
# Start with debug mode
python scripts/start_web_portal.py --debug

# Custom host and port
python scripts/start_web_portal.py --host 192.168.1.100 --port 9000
```

### **Production Deployment**

```bash
# Start as background service
nohup python scripts/start_web_portal.py > web_portal.log 2>&1 &

# Or use systemd service
sudo systemctl start skyguard-web
sudo systemctl enable skyguard-web
```

### **Docker Deployment**

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY . .

RUN pip install -r requirements-web.txt

EXPOSE 8080

CMD ["python", "scripts/start_web_portal.py"]
```

### **Nginx Reverse Proxy**

```nginx
server {
    listen 80;
    server_name skyguard.local;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🔧 **Troubleshooting**

### **Common Issues**

**Web portal won't start:**
```bash
# Check if dependencies are installed
pip install -r requirements-web.txt

# Check if port is available
netstat -tulpn | grep :8080

# Check configuration file
python -c "import yaml; yaml.safe_load(open('config/skyguard.yaml'))"
```

**Can't access from other devices:**
```bash
# Check firewall settings
sudo ufw allow 8080

# Check if binding to 0.0.0.0
python scripts/start_web_portal.py --host 0.0.0.0
```

**Configuration not saving:**
```bash
# Check file permissions
ls -la config/skyguard.yaml

# Check if SkyGuard is running
ps aux | grep skyguard
```

**Images not loading:**
```bash
# Check if detection images exist
ls -la data/detections/

# Check file permissions
chmod 755 data/detections/
```

### **Performance Optimization**

**For Raspberry Pi:**
```bash
# Reduce image quality
# Edit config/skyguard.yaml
camera:
  width: 640
  height: 480
  fps: 15

# Reduce detection history
system:
  max_detection_history: 500
```

**For High-Performance Systems:**
```bash
# Increase image quality
camera:
  width: 1280
  height: 720
  fps: 30

# Increase detection history
system:
  max_detection_history: 5000
```

## 📞 **Support**

- **Documentation**: Check `docs/` directory
- **Issues**: GitHub Issues
- **Logs**: Check `web_portal.log`
- **API**: Use browser developer tools to inspect API calls

## 🎯 **Next Steps**

1. **Start the web portal**: `python scripts/start_web_portal.py`
2. **Access the interface**: Open `http://localhost:8080`
3. **Configure your system**: Use the configuration section
4. **Test all components**: Use the quick actions
5. **Monitor detections**: Check the detection history
6. **Optimize settings**: Adjust based on your needs

---

**Congratulations!** Your SkyGuard system now has a powerful web interface for easy management and monitoring! 🦅
