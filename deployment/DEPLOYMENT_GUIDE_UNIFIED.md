# SkyGuard Unified Deployment Guide

## 🎯 Overview

This guide covers the unified deployment approach for SkyGuard on Raspberry Pi, using the main codebase with systemd services for automatic startup and monitoring.

## 🏗️ Architecture

### Unified Approach Benefits

- **Single Source of Truth**: Uses main `skyguard/` codebase
- **Automatic Startup**: Systemd services for detection and web portal
- **Health Monitoring**: Comprehensive health checks and auto-recovery
- **Easy Management**: Unified control script for all operations
- **Production Ready**: Log rotation, error handling, and monitoring

### Service Architecture

```
┌─────────────────┐    ┌─────────────────┐
│   Detection     │    │   Web Portal    │
│   System        │    │   (Port 8080)   │
│                 │    │                 │
│ • Camera        │    │ • REST API      │
│ • AI Detection  │    │ • Web Interface │
│ • Alerts        │    │ • Status Page   │
│ • Snapshots     │───▶│ • Config Mgmt   │
└─────────────────┘    └─────────────────┘
         │                       │
         └───────────────────────┘
                   │
            ┌───────────────┐
            │ Health Check │
            │ & Monitoring │
            └───────────────┘
```

## 🚀 Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/jad3tx/SkyGuard.git
cd skyguard
```

### 2. Run Unified Installer

```bash
# Make installer executable
chmod +x deployment/install_pi5_unified.sh

# Run installation
./deployment/install_pi5_unified.sh
```

### 3. Start Services

```bash
# Start all services
skyguard-control start

# Check status
skyguard-control status

# Run health check
skyguard-control health
```

### 4. Access Web Portal

Open your browser to: `http://<PI_IP_ADDRESS>:8080`

## 📦 What's Included

### Core Components

- **Main Detection System** (`skyguard.main`)
- **Web Portal** (`skyguard.web.app`)
- **Camera Management** (`skyguard.core.camera`)
- **AI Detection** (`skyguard.core.detector`)
- **Alert System** (`skyguard.core.alert_system`)
- **Event Logging** (`skyguard.storage.event_logger`)

### Systemd Services

- **skyguard.service**: Main detection system
- **skyguard-web.service**: Web portal
- **Auto-startup**: Enabled by default
- **Health monitoring**: Built-in checks
- **Auto-recovery**: Automatic restart on failure

### Management Tools

- **skyguard-control.sh**: Unified service management
- **health_check.sh**: Comprehensive health monitoring
- **install_pi5_unified.sh**: Complete installation

## ⚙️ Installation Details

### System Requirements

- **Hardware**: Raspberry Pi 5 (recommended) or Pi 4 (8GB RAM)
- **OS**: Raspberry Pi OS or Ubuntu 20.04+
- **Storage**: 32GB+ microSD card
- **Camera**: USB webcam or Pi camera module
- **Network**: Internet connection for setup

### Installation Process

The unified installer performs these steps:

1. **System Updates**: Updates all packages
2. **Dependencies**: Installs Python, OpenCV, and system libraries
3. **Pi 5 Optimizations**: GPU memory, hardware acceleration
4. **Python Environment**: Creates virtual environment with dependencies
5. **Service Installation**: Copies and enables systemd services
6. **Configuration**: Creates default config files
7. **Log Rotation**: Sets up automatic log management
8. **Health Monitoring**: Configures health check system

### Directory Structure

```
/home/pi/skyguard/
├── skyguard/              # Main codebase
├── config/                # Configuration files
├── data/                  # Database and images
├── logs/                  # Log files
├── models/                # AI models
├── deployment/            # Deployment scripts
│   ├── scripts/           # Management scripts
│   └── systemd/           # Service files
└── venv/                  # Python virtual environment
```

## 🔧 Configuration

### Service Configuration

Services are configured in `/etc/systemd/system/`:

**skyguard.service**:
```ini
[Unit]
Description=SkyGuard Raptor Detection System
After=network-online.target
Before=skyguard-web.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/skyguard
ExecStart=/home/pi/skyguard/venv/bin/python -m skyguard.main
Restart=always
RestartSec=10
```

**skyguard-web.service**:
```ini
[Unit]
Description=SkyGuard Web Portal
After=skyguard.service
BindsTo=skyguard.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/skyguard
ExecStart=/home/pi/skyguard/venv/bin/python scripts/start_web_portal.py
Restart=always
RestartSec=10
```

### SkyGuard Configuration

Main configuration in `/home/pi/skyguard/config/skyguard.yaml`:

```yaml
# Camera settings
camera:
  source: 0
  width: 1920
  height: 1080
  fps: 30

# AI model settings
ai:
  model_path: models/yolov8n.pt
  confidence_threshold: 0.48
  classes: ['bird']

# System settings
system:
  detection_interval: 1
  save_detection_frames: true

# Notifications
notifications:
  audio:
    enabled: true
  email:
    enabled: false
  sms:
    enabled: false
```

## 🎮 Service Management

### Control Commands

```bash
# Service management
skyguard-control start          # Start all services
skyguard-control stop           # Stop all services
skyguard-control restart        # Restart all services
skyguard-control status         # Show service status

# Monitoring
skyguard-control health         # Run health check
skyguard-control logs           # View logs
skyguard-control logs --follow  # Follow logs in real-time

# Auto-startup
skyguard-control enable         # Enable auto-start on boot
skyguard-control disable        # Disable auto-start on boot

# Service installation
skyguard-control install        # Install systemd services
skyguard-control uninstall      # Remove systemd services
```

### Health Monitoring

The health check system monitors:

- **Service Status**: Are services running?
- **Camera Snapshot**: Is camera capturing images?
- **Web Portal**: Is web interface responding?
- **System Resources**: Memory and disk usage
- **Auto-Recovery**: Restart failed services

```bash
# Run health check
skyguard-control health

# Run with auto-recovery
skyguard-control health --auto-restart

# View detailed status
skyguard-control status
```

## 📊 Monitoring and Logs

### Log Locations

- **Service Logs**: `journalctl -u skyguard*`
- **Application Logs**: `/home/pi/skyguard/logs/skyguard.log`
- **Health Check Logs**: `/home/pi/skyguard/logs/health_check.log`
- **Control Logs**: `/home/pi/skyguard/logs/control.log`

### Log Management

```bash
# View recent logs
skyguard-control logs

# Follow logs in real-time
skyguard-control logs --follow

# View specific service logs
journalctl -u skyguard.service -f
journalctl -u skyguard-web.service -f

# View all SkyGuard logs
journalctl -u skyguard* -f
```

### Log Rotation

Logs are automatically rotated:

- **Frequency**: Daily
- **Retention**: 7 days
- **Compression**: Enabled
- **Location**: `/etc/logrotate.d/skyguard`

## 🔍 Troubleshooting

### Common Issues

**Services won't start:**
```bash
# Check service status
systemctl status skyguard.service skyguard-web.service

# Check logs for errors
journalctl -u skyguard.service --since "1 hour ago"

# Restart services
skyguard-control restart
```

**Camera not detected:**
```bash
# Check camera devices
ls /dev/video*

# Test camera
python -c "import cv2; cap = cv2.VideoCapture(0); print('OK' if cap.isOpened() else 'Failed')"

# Check permissions
sudo usermod -a -G video pi
```

**Web portal not accessible:**
```bash
# Check web service
systemctl status skyguard-web.service

# Test locally
curl http://localhost:8080/api/status

# Check firewall
sudo ufw status
```

### Debug Mode

Enable debug logging:

```bash
# Edit configuration
nano /home/pi/skyguard/config/skyguard.yaml

# Set debug mode
system:
  debug_mode: true

# Restart services
skyguard-control restart
```

### Service Recovery

If services fail repeatedly:

```bash
# Check system resources
df -h
free -h

# Check for errors
journalctl -u skyguard* --since "1 hour ago"

# Manual restart
sudo systemctl stop skyguard-web.service skyguard.service
sudo systemctl start skyguard.service
sleep 5
sudo systemctl start skyguard-web.service
```

## 🔄 Updates and Maintenance

### Updating SkyGuard

```bash
# Stop services
skyguard-control stop

# Update code
cd /home/pi/skyguard
git pull origin main

# Update dependencies
source venv/bin/activate
pip install -r requirements-pi5.txt

# Restart services
skyguard-control start
```

### System Maintenance

```bash
# Clean old logs
sudo journalctl --vacuum-time=7d

# Clean old detection images
find /home/pi/skyguard/data/detections -name "*.jpg" -mtime +7 -delete

# Update system
sudo apt update && sudo apt upgrade -y
```

## 🔒 Security

### Firewall Configuration

```bash
# Install UFW
sudo apt install ufw

# Configure firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 8080  # Web portal
sudo ufw enable
```

### User Permissions

```bash
# Create dedicated user (optional)
sudo useradd -m -s /bin/bash skyguard
sudo usermod -a -G video,gpio skyguard

# Update service files
sudo nano /etc/systemd/system/skyguard.service
# Change User=pi to User=skyguard
```

## 📱 Remote Access

### SSH Access

```bash
# Enable SSH
sudo systemctl enable ssh
sudo systemctl start ssh

# Connect remotely
ssh pi@<PI_IP_ADDRESS>
```

### Web Portal Access

- **Local**: http://localhost:8080
- **Remote**: http://<PI_IP_ADDRESS>:8080

### Port Configuration

To change the web portal port:

```bash
# Edit service file
sudo nano /etc/systemd/system/skyguard-web.service

# Change port in ExecStart line
ExecStart=/home/pi/skyguard/venv/bin/python scripts/start_web_portal.py --host 0.0.0.0 --port 8080

# Reload and restart
sudo systemctl daemon-reload
skyguard-control restart
```

## 📈 Performance Optimization

### Pi 5 Optimizations

The installer automatically applies:

- GPU memory split: 256MB
- Hardware acceleration enabled
- Optimized camera settings
- Enhanced systemd configuration

### Manual Optimizations

```bash
# Set CPU governor to performance
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# Increase GPU memory
sudo nano /boot/config.txt
# Add: gpu_mem=256

# Optimize camera settings
nano /home/pi/skyguard/config/skyguard.yaml
```

## 📞 Support

### Getting Help

- **Logs**: `skyguard-control logs`
- **Status**: `skyguard-control status`
- **Health**: `skyguard-control health`
- **Documentation**: See `docs/` directory

### Common Commands

```bash
# Full system status
skyguard-control status && skyguard-control health

# View all logs
skyguard-control logs --follow

# Restart everything
skyguard-control restart

# Disable auto-start
skyguard-control disable

# Re-enable auto-start
skyguard-control enable
```

---

**Congratulations!** Your SkyGuard system is now deployed with unified management and automatic startup! 🦅

