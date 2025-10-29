# SkyGuard Installation Guide

![SkyGuard Logo](../skyGuardShield.png)

This guide provides an overview of installation options for SkyGuard. **SkyGuard is currently optimized for Raspberry Pi 5.**

## Quick Start

**For Raspberry Pi 5 installation, see: [Raspberry Pi 5 Setup Guide](RASPBERRY_PI_SETUP.md)**

This is the recommended installation path and includes:
- Complete step-by-step setup from OS imaging to deployment
- Pi 5 optimizations and performance tuning
- Auto-startup configuration
- Troubleshooting guide

## Prerequisites

### Hardware Requirements

**Minimum Requirements:**
- Raspberry Pi 5 (4GB RAM)
- USB webcam or Raspberry Pi camera module
- 32GB+ microSD card (Class 10 or better)
- 5V/3A power supply

**Recommended Setup:**
- Raspberry Pi 5 (8GB RAM)
- High-quality USB webcam (1080p, 30fps)
- 64GB+ microSD card
- Weatherproof enclosure

### Software Requirements

- Raspberry Pi OS (64-bit)
- Python 3.8 or higher
- Internet connection for initial setup

## Installation Methods

### Method 1: Raspberry Pi 5 (Recommended)

**See [Raspberry Pi 5 Setup Guide](RASPBERRY_PI_SETUP.md) for complete instructions.**

Quick overview:
1. **Image SD card** with Raspberry Pi OS Lite (64-bit)
2. **Clone repository** and run installer
3. **Configure** camera and settings
4. **Enable auto-start** services

### Method 2: Other Platforms

SkyGuard is optimized for Raspberry Pi 5. For other platforms, you may need to:

1. **Install system dependencies**
   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo apt install python3-pip python3-venv python3-dev -y
   sudo apt install libopencv-dev python3-opencv -y
   ```

2. **Clone and setup**
   ```bash
   git clone https://github.com/jad3tx/SkyGuard.git
   cd SkyGuard
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configure and test**
   - Edit `config/skyguard.yaml`
   - Test camera connection
   - Run detection system

## Verification and Testing

See the [Raspberry Pi 5 Setup Guide](RASPBERRY_PI_SETUP.md) for detailed testing instructions.

### Quick Tests

```bash
# Test camera
python3 -c "import cv2; cap = cv2.VideoCapture(0); print('OK' if cap.isOpened() else 'Failed')"

# Test SkyGuard
source venv/bin/activate
python3 skyguard/main.py

# Test web portal
python3 scripts/start_web_portal.py
curl http://localhost:8080/api/status
```

### Run Test Suite
```bash
# Run all tests
pytest tests/ -v

# Run specific test suites
pytest tests/test_web_api.py -v      # API tests
pytest tests/test_web_ui.py -v      # UI tests
pytest tests/test_camera_connection.py -v  # Camera tests
```

## Troubleshooting

For comprehensive troubleshooting, see the [Raspberry Pi 5 Setup Guide](RASPBERRY_PI_SETUP.md) which includes:

- Common issues and solutions
- Performance optimization
- Service management
- Log analysis

### Quick Troubleshooting

**Camera not detected:**
```bash
# Check USB devices
lsusb

# Check video devices
ls /dev/video*

# Test with simple capture
python -c "import cv2; cap = cv2.VideoCapture(0); print('Camera OK' if cap.isOpened() else 'Camera Failed')"
```

**Permission errors:**
```bash
# Add user to video group
sudo usermod -a -G video $USER

# Reboot or logout/login
```

**Check logs:**
```bash
# Application logs
tail -f logs/skyguard.log

# Service logs
journalctl -u skyguard.service -f
```

### Getting Help

1. Review the [Raspberry Pi 5 Setup Guide](RASPBERRY_PI_SETUP.md) troubleshooting section
2. Check logs: `journalctl -u skyguard.service -f`
3. Submit issue on GitHub with system information

## Next Steps

After successful installation:

1. **Configure notifications** - Set up SMS, email, or push notifications
2. **Position camera** - Mount camera with good view of poultry area
3. **Test detection** - Verify system detects objects correctly
4. **Monitor performance** - Check detection accuracy and response times
5. **Customize settings** - Adjust confidence thresholds and alert preferences

See the [Raspberry Pi 5 Setup Guide](RASPBERRY_PI_SETUP.md) for detailed next steps.

## Additional Resources

- **[Raspberry Pi 5 Setup Guide](RASPBERRY_PI_SETUP.md)** - Complete Pi 5 installation guide
- **[API Documentation](API.md)** - REST API reference
- **[Web Portal Guide](WEB_PORTAL.md)** - Web interface documentation
- **[Hardware Guide](HARDWARE.md)** - Hardware recommendations
