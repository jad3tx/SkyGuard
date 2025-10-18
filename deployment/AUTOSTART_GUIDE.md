# SkyGuard Auto-Startup Guide

## 🚀 Overview

This guide covers setting up SkyGuard to automatically start on Raspberry Pi boot using systemd services. The system includes both the detection system and web portal as separate services with health monitoring and auto-recovery.

## 📋 Prerequisites

- Raspberry Pi 5 (recommended) or Pi 4 (8GB RAM)
- Raspberry Pi OS or Ubuntu 20.04+
- Camera (USB webcam or Pi camera module)
- Internet connection for initial setup

## 🛠️ Installation

### Method 1: Unified Installation (Recommended)

```bash
# Clone the repository
git clone https://github.com/jad3tx/SkyGuard.git
cd skyguard

# Run the unified installer
chmod +x deployment/install_pi5_unified.sh
./deployment/install_pi5_unified.sh
```

### Method 2: Manual Installation

```bash
# 1. Install system dependencies
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv python3-opencv libopencv-dev git

# 2. Setup SkyGuard directory
mkdir -p /home/pi/skyguard
cd /home/pi/skyguard

# 3. Copy SkyGuard code
cp -r /path/to/skyguard/* .

# 4. Create virtual environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-pi5.txt

# 5. Install systemd services
sudo cp deployment/systemd/skyguard.service /etc/systemd/system/
sudo cp deployment/systemd/skyguard-web.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable skyguard.service skyguard-web.service
```

## ⚙️ Service Configuration

### Service Dependencies

- **skyguard.service**: Main detection system (starts first)
- **skyguard-web.service**: Web portal (depends on detection system)

### Service Management

Use the control script for easy management:

```bash
# Start all services
skyguard-control start

# Stop all services
skyguard-control stop

# Restart all services
skyguard-control restart

# Check status
skyguard-control status

# View logs
skyguard-control logs

# Run health check
skyguard-control health

# Enable auto-start on boot
skyguard-control enable

# Disable auto-start on boot
skyguard-control disable
```

## 🔍 Health Monitoring

### Automatic Health Checks

The system includes comprehensive health monitoring:

- **Service Status**: Checks if services are running
- **Camera Snapshot**: Verifies camera is capturing images
- **Web Portal**: Tests web interface availability
- **System Resources**: Monitors memory and disk usage
- **Auto-Recovery**: Automatically restarts failed services

### Manual Health Check

```bash
# Run health check
skyguard-control health

# Run health check with auto-recovery
skyguard-control health --auto-restart

# View detailed status
skyguard-control status
```

### Health Check Features

- ✅ Service process monitoring
- ✅ Camera snapshot freshness (< 10 seconds)
- ✅ Web portal HTTP response
- ✅ System resource monitoring
- ✅ Automatic service restart on failure
- ✅ Log file analysis

## 📊 Service Status

### Check Service Status

```bash
# Quick status
skyguard-control status

# Detailed status with logs
systemctl status skyguard.service skyguard-web.service

# Check if services are enabled
systemctl is-enabled skyguard.service skyguard-web.service
```

### Service Logs

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

## 🔧 Configuration

### Service Configuration

Services are configured in `/etc/systemd/system/`:

- **skyguard.service**: Detection system configuration
- **skyguard-web.service**: Web portal configuration

### SkyGuard Configuration

Main configuration is in `/home/pi/skyguard/config/skyguard.yaml`:

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

# System settings
system:
  detection_interval: 1
  save_detection_frames: true
```

## 🚨 Troubleshooting

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

# Test camera with OpenCV
python -c "import cv2; cap = cv2.VideoCapture(0); print('OK' if cap.isOpened() else 'Failed')"

# Check camera permissions
sudo usermod -a -G video pi
```

**Web portal not accessible:**
```bash
# Check if web service is running
systemctl status skyguard-web.service

# Test web portal locally
curl http://localhost:8080/api/status

# Check firewall
sudo ufw status
```

**High memory usage:**
```bash
# Check memory usage
free -h
htop

# Restart services to free memory
skyguard-control restart
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

## 📈 Performance Optimization

### Pi 5 Optimizations

The installer automatically applies Pi 5 optimizations:

- GPU memory split: 256MB
- Hardware acceleration enabled
- Optimized camera settings
- Enhanced systemd service configuration

### Manual Optimizations

```bash
# Set CPU governor to performance
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# Increase GPU memory (edit /boot/config.txt)
sudo nano /boot/config.txt
# Add: gpu_mem=256

# Optimize camera settings
# Edit config/skyguard.yaml
camera:
  width: 1920
  height: 1080
  fps: 30
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

### Log Rotation

Logs are automatically rotated:

- **Location**: `/home/pi/skyguard/logs/`
- **Rotation**: Daily
- **Retention**: 7 days
- **Compression**: Enabled

### System Maintenance

```bash
# Clean old logs
sudo journalctl --vacuum-time=7d

# Clean old detection images
find /home/pi/skyguard/data/detections -name "*.jpg" -mtime +7 -delete

# Update system
sudo apt update && sudo apt upgrade -y
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

The web portal is available at:
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

# Update service files to use skyguard user
sudo nano /etc/systemd/system/skyguard.service
# Change User=pi to User=skyguard
```

## 📞 Support

### Getting Help

- **Logs**: Check `skyguard-control logs`
- **Status**: Run `skyguard-control status`
- **Health**: Run `skyguard-control health`
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

**Congratulations!** Your SkyGuard system is now configured for automatic startup and monitoring! 🦅

