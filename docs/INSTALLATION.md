# SkyGuard Installation Guide

This guide will walk you through installing and setting up the SkyGuard raptor alert system.

## Prerequisites

### Hardware Requirements

**Minimum Requirements:**
- Raspberry Pi 4 (4GB RAM) or equivalent single-board computer
- USB webcam or Raspberry Pi camera module
- 32GB+ microSD card (Class 10 or better)
- 5V/3A power supply
- Ethernet cable or WiFi connection

**Recommended Setup:**
- Raspberry Pi 4 (8GB RAM)
- High-quality USB webcam (1080p, 30fps)
- 64GB+ microSD card
- Weatherproof enclosure
- Optional: LED indicators, buzzer, motion sensors

### Software Requirements

- Raspberry Pi OS (64-bit) or Ubuntu 20.04+
- Python 3.8 or higher
- Internet connection for initial setup

## Installation Methods

### Method 1: Automated Installation (Recommended)

1. **Download the installation script**
   ```bash
   wget https://raw.githubusercontent.com/johndaughtridge/skyguard/main/scripts/install.sh
   chmod +x install.sh
   ```

2. **Run the installation script**
   ```bash
   ./install.sh
   ```

3. **Follow the interactive prompts**
   - Select your hardware platform
   - Configure camera settings
   - Set up notification preferences
   - Test the installation

### Method 2: Manual Installation

#### Step 1: System Setup

1. **Install Raspberry Pi OS**
   - Download Raspberry Pi Imager
   - Flash OS to microSD card
   - Enable SSH and WiFi (if needed)
   - Boot the system

2. **Update system packages**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

3. **Install Python dependencies**
   ```bash
   sudo apt install python3-pip python3-venv python3-dev -y
   sudo apt install libopencv-dev python3-opencv -y
   sudo apt install libatlas-base-dev -y
   ```

#### Step 2: Install SkyGuard

1. **Clone the repository**
   ```bash
   git clone https://github.com/johndaughtridge/skyguard.git
   cd skyguard
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Python packages**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Install SkyGuard**
   ```bash
   pip install -e .
   ```

#### Step 3: Hardware Configuration

1. **Enable camera interface (Raspberry Pi)**
   ```bash
   sudo raspi-config
   # Navigate to Interface Options > Camera > Enable
   ```

2. **Test camera**
   ```bash
   # For USB webcam
   lsusb | grep -i camera
   
   # For Raspberry Pi camera
   libcamera-hello --list-cameras
   ```

3. **Configure GPIO (optional)**
   ```bash
   # Add user to gpio group
   sudo usermod -a -G gpio $USER
   ```

#### Step 4: Initial Configuration

1. **Run configuration wizard**
   ```bash
   skyguard-setup
   ```

2. **Edit configuration file**
   ```bash
   nano config/skyguard.yaml
   ```

3. **Test the system**
   ```bash
   skyguard --test-camera
   skyguard --test-alerts
   ```

## Platform-Specific Instructions

### Raspberry Pi Setup

1. **Enable required interfaces**
   ```bash
   sudo raspi-config
   ```
   - Enable Camera
   - Enable SSH
   - Enable I2C (if using sensors)
   - Enable SPI (if using sensors)

2. **Optimize for performance**
   ```bash
   # Increase GPU memory split
   echo "gpu_mem=128" | sudo tee -a /boot/config.txt
   
   # Disable unnecessary services
   sudo systemctl disable bluetooth
   sudo systemctl disable hciuart
   ```

3. **Set up auto-start**
   ```bash
   # Create systemd service
   sudo nano /etc/systemd/system/skyguard.service
   ```
   
   Add the following content:
   ```ini
   [Unit]
   Description=SkyGuard Raptor Alert System
   After=network.target
   
   [Service]
   Type=simple
   User=pi
   WorkingDirectory=/home/pi/skyguard
   Environment=PATH=/home/pi/skyguard/venv/bin
   ExecStart=/home/pi/skyguard/venv/bin/python -m skyguard.main
   Restart=always
   RestartSec=10
   
   [Install]
   WantedBy=multi-user.target
   ```
   
   Enable the service:
   ```bash
   sudo systemctl enable skyguard.service
   sudo systemctl start skyguard.service
   ```

### Desktop/Laptop Setup

1. **Install OpenCV dependencies**
   ```bash
   # Ubuntu/Debian
   sudo apt install libopencv-dev python3-opencv
   
   # macOS
   brew install opencv
   
   # Windows
   pip install opencv-python
   ```

2. **Configure for desktop use**
   - Set `platform: "desktop"` in config
   - Disable GPIO features
   - Use USB webcam

## Verification and Testing

### Camera Test
```bash
skyguard --test-camera
```

### Alert Test
```bash
skyguard --test-alerts
```

### Full System Test
```bash
skyguard --test-system
```

### Check System Status
```bash
skyguard --status
```

## Troubleshooting

### Common Issues

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

**Memory issues:**
```bash
# Check memory usage
free -h

# Increase swap space
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Set CONF_SWAPSIZE=2048
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

**Model loading errors:**
```bash
# Check model file exists
ls -la models/

# Download default model
wget https://github.com/johndaughtridge/skyguard/releases/download/v0.1.0/raptor_detector.pt -O models/raptor_detector.pt
```

### Getting Help

1. **Check logs**
   ```bash
   tail -f logs/skyguard.log
   ```

2. **Run in debug mode**
   ```bash
   skyguard --verbose
   ```

3. **Submit issue**
   - Check existing issues on GitHub
   - Create new issue with system information
   - Include log files and error messages

## Next Steps

After successful installation:

1. **Configure notifications** - Set up SMS, email, or push notifications
2. **Position camera** - Mount camera with good view of poultry area
3. **Test detection** - Verify system detects objects correctly
4. **Monitor performance** - Check detection accuracy and response times
5. **Customize settings** - Adjust confidence thresholds and alert preferences

## Uninstallation

To remove SkyGuard:

```bash
# Stop service
sudo systemctl stop skyguard.service
sudo systemctl disable skyguard.service

# Remove service file
sudo rm /etc/systemd/system/skyguard.service

# Remove application
cd skyguard
pip uninstall skyguard
cd ..
rm -rf skyguard

# Remove data (optional)
rm -rf data/
rm -rf logs/
```
