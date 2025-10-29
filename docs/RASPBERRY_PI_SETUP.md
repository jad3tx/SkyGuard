# SkyGuard Raspberry Pi 5 Installation Guide

This comprehensive guide covers the complete setup process for SkyGuard on Raspberry Pi 5, including initial system preparation, installation, configuration, and deployment.

## Prerequisites

### Hardware Requirements

- **Raspberry Pi 5** (4GB+ RAM recommended, 8GB optimal)
- **MicroSD card** (32GB+ recommended, Class 10 or better)
- **Camera module** or USB webcam (1080p, 30fps recommended)
- **Power supply** (5V, 3A+ recommended, 5A for optimal performance)
- **Network connection** (WiFi or Ethernet)

### Software Requirements

- Raspberry Pi OS (64-bit) - Lite version recommended for headless operation
- Internet connection for initial setup

## Step 1: Prepare Raspberry Pi OS

### 1.1 Image the SD Card

1. Download and install [Raspberry Pi Imager](https://www.raspberrypi.org/downloads/)
2. Insert your microSD card
3. Open Raspberry Pi Imager
4. Click "Choose OS" and select:
   - **Raspberry Pi OS Lite (64-bit)** - Recommended for headless operation
   - Or **Raspberry Pi OS (64-bit)** - If you need desktop access
5. Click "Choose Storage" and select your microSD card
6. Click the gear icon (⚙️) to configure advanced options:
   - **Enable SSH**: Set a password for the `pi` user
   - **Set username and password**: Use `pi` as username (or create a custom user)
   - **Configure WiFi**: Enter your network credentials (if using WiFi)
   - **Set locale settings**: Choose your timezone and keyboard layout
7. Click "Write" to image the card

### 1.2 Boot and Connect

1. Insert the SD card into your Raspberry Pi 5
2. Connect power and boot the Pi
3. Find your Pi's IP address:
   - Check your router's admin panel
   - Use a network scanner like `nmap`
   - Use `arp -a` on your computer
   - Use `ping raspberrypi.local` (if mDNS is enabled)
4. SSH into your Pi:
   ```bash
   ssh pi@<PI_IP_ADDRESS>
   ```
   Default password is usually `raspberry` (unless you changed it during imaging)

## Step 2: Initial System Setup

### 2.1 Update System

```bash
sudo apt update && sudo apt upgrade -y
```

### 2.2 Install Git and GitHub CLI

```bash
# Install git
sudo apt install git -y

# Install GitHub CLI
sudo apt install gh -y
```

### 2.3 Configure Git

```bash
# Set your Git username and email
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

### 2.4 Setup SSH Keys for GitHub

```bash
# Generate SSH key
ssh-keygen -t ed25519 -C "your.email@example.com"
# Press Enter to accept default location and optional passphrase

# Start SSH agent
eval "$(ssh-agent -s)"

# Add key to SSH agent
ssh-add ~/.ssh/id_ed25519

# Display public key
cat ~/.ssh/id_ed25519.pub
```

### 2.5 Add SSH Key to GitHub using GitHub CLI

Since Raspberry Pi OS Lite doesn't have a web browser, use the GitHub CLI to upload your SSH key:

```bash
# Authenticate with GitHub CLI
gh auth login

# Follow the prompts:
# - Choose "GitHub.com"
# - Choose "SSH" for protocol
# - Choose "Yes" to authenticate Git with your GitHub credentials
# - Choose "Login with a web browser"
# - Copy the one-time code provided
# - Open the URL in a browser on another device (phone, computer, etc.)
# - Enter the one-time code when prompted
```

**Alternative method if you have access to another device:**
```bash
# Copy the public key to clipboard (if you have access to another device)
cat ~/.ssh/id_ed25519.pub

# Then manually add it via GitHub web interface on another device:
# 1. Go to GitHub.com → Settings → SSH and GPG keys
# 2. Click "New SSH key"
# 3. Paste your public key and save
```

### 2.6 Test GitHub Connection

```bash
# Test SSH connection to GitHub
ssh -T git@github.com

# You should see: "Hi username! You've successfully authenticated..."

# Test GitHub CLI access
gh auth status
```

## Step 3: Clone SkyGuard Repository

```bash
# Clone the repository
git clone https://github.com/jad3tx/SkyGuard.git
cd SkyGuard

# Make install script executable
chmod +x scripts/install.sh
```

## Step 4: Run Installation

### 4.1 Automated Installation (Recommended)

The main installation script automatically detects your Raspberry Pi platform and installs the appropriate dependencies:

```bash
# Run the installation script
./scripts/install.sh
```

**Note:** The installer will automatically detect Raspberry Pi 5 and apply Pi 5 optimizations. If you need manual control, you can use `deployment/install_pi5_unified.sh` instead, but the main script is recommended.

The script will:
- Detect your Raspberry Pi platform
- Install system dependencies
- Handle package availability issues gracefully
- Set up Python virtual environment
- Install Python packages optimized for Pi 5
- Configure the system
- Set up systemd services for auto-startup

### 4.2 Manual Package Installation (if needed)

If you encounter package issues, you can install dependencies manually:

```bash
# Install core packages
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    python3-opencv \
    libopencv-dev \
    git \
    wget \
    curl \
    build-essential \
    cmake \
    pkg-config \
    libjpeg-dev \
    libtiff5-dev \
    libpng-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    libgtk-3-dev \
    libcanberra-gtk3-dev \
    libcanberra-gtk3-module \
    libcanberra-gtk-dev \
    libcanberra-gtk-module

# Try to install BLAS/LAPACK libraries
sudo apt install -y libatlas-base-dev || sudo apt install -y libopenblas-dev
```

## Step 5: Configure SkyGuard

### 5.1 Camera Setup

**For Raspberry Pi Camera Module:**
```bash
# Enable camera interface
sudo raspi-config
# Navigate to: Interface Options → Camera → Enable

# Test camera
libcamera-hello --list-cameras
```

**For USB Camera:**
```bash
# List available cameras
ls /dev/video*

# Test camera
v4l2-ctl --list-devices

# Check USB devices
lsusb | grep -i camera
```

### 5.2 Configuration

```bash
# Edit configuration file
nano config/skyguard.yaml

# Key settings to configure:
# - Camera source (0 for USB, /dev/video0 for specific device)
# - AI model path
# - Detection thresholds
# - Notification settings
```

**Recommended Pi 5 Configuration:**
```yaml
# Camera settings optimized for Pi 5
camera:
  source: 0
  width: 1280      # HD resolution
  height: 720
  fps: 30          # Smooth video
  rotation: 0

# AI model settings
ai:
  model_path: 'models/airbirds_raptor_detector.pt'
  confidence_threshold: 0.5  # Higher confidence for Pi 5
  input_size: [640, 640]
  classes: ['bird']

# System settings
system:
  detection_interval: 1.0    # Faster detection on Pi 5
  max_detection_history: 1000  # More history
  debug_mode: false
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

### 5.3 Pi 5 Performance Optimizations

The installer automatically applies Pi 5 optimizations, but you can verify/configure manually:

```bash
# Check GPU memory (should be 256MB)
vcgencmd get_mem gpu

# Edit boot config for optimal settings
sudo nano /boot/config.txt
```

Add or verify these settings:
```
gpu_mem=256
dtoverlay=vc4-kms-v3d
dtoverlay=vc4-kms-v3d-pi5
```

Reboot after making changes:
```bash
sudo reboot
```

## Step 6: Test Installation

### 6.1 Test Camera

```bash
# Activate virtual environment
source venv/bin/activate

# Test camera capture
python3 -c "
import cv2
cap = cv2.VideoCapture(0)
ret, frame = cap.read()
if ret:
    print('Camera working!')
    cv2.imwrite('test_image.jpg', frame)
else:
    print('Camera not working')
cap.release()
"
```

### 6.2 Test SkyGuard

```bash
# Activate virtual environment
source venv/bin/activate

# Run SkyGuard
python3 skyguard/main.py
```

### 6.3 Test Web Portal

```bash
# Start web portal
python3 scripts/start_web_portal.py

# In another terminal, test API
curl http://localhost:8080/api/status
```

Access the web interface at: `http://<PI_IP_ADDRESS>:8080`

## Step 7: Enable Auto-Start (Recommended)

### 7.1 Service Installation

The installation script should have already set up systemd services. Verify they exist:

```bash
# Check if services are installed
ls /etc/systemd/system/skyguard*.service

# If not installed, install them manually:
sudo cp deployment/systemd/skyguard.service /etc/systemd/system/
sudo cp deployment/systemd/skyguard-web.service /etc/systemd/system/
sudo systemctl daemon-reload
```

### 7.2 Service Configuration

**skyguard.service:**
```ini
[Unit]
Description=SkyGuard Raptor Detection System
After=network-online.target
Before=skyguard-web.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/SkyGuard
Environment=PATH=/home/pi/SkyGuard/venv/bin
ExecStart=/home/pi/SkyGuard/venv/bin/python -m skyguard.main
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**skyguard-web.service:**
```ini
[Unit]
Description=SkyGuard Web Portal
After=skyguard.service
BindsTo=skyguard.service

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/SkyGuard
Environment=PATH=/home/pi/SkyGuard/venv/bin
ExecStart=/home/pi/SkyGuard/venv/bin/python scripts/start_web_portal.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

**Note:** Update `/home/pi/SkyGuard` paths if your installation location differs.

### 7.3 Enable and Start Services

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable services (auto-start on boot)
sudo systemctl enable skyguard.service
sudo systemctl enable skyguard-web.service

# Start services
sudo systemctl start skyguard.service
sudo systemctl start skyguard-web.service

# Check status
sudo systemctl status skyguard.service
sudo systemctl status skyguard-web.service
```

## Service Management

### Using Control Scripts

If control scripts are available:

```bash
# Start all services
./deployment/scripts/skyguard-control.sh start

# Stop all services
./deployment/scripts/skyguard-control.sh stop

# Restart all services
./deployment/scripts/skyguard-control.sh restart

# Check status
./deployment/scripts/skyguard-control.sh status

# View logs
./deployment/scripts/skyguard-control.sh logs

# Run health check
./deployment/scripts/health_check.sh
```

### Using Systemd Directly

```bash
# Start services
sudo systemctl start skyguard.service
sudo systemctl start skyguard-web.service

# Check status
sudo systemctl status skyguard.service
sudo systemctl status skyguard-web.service

# Stop services
sudo systemctl stop skyguard.service
sudo systemctl stop skyguard-web.service

# Enable/disable auto-start
sudo systemctl enable skyguard.service
sudo systemctl disable skyguard.service

# View logs
journalctl -u skyguard.service -f
journalctl -u skyguard-web.service -f
journalctl -u skyguard* -f
```

### Cleanup Services

If you need to remove all SkyGuard services for testing or reinstallation:

```bash
# Use the cleanup script
./scripts/cleanup_skyguard.sh

# Or manually remove services
sudo systemctl stop skyguard.service
sudo systemctl stop skyguard-web.service
sudo systemctl disable skyguard.service
sudo systemctl disable skyguard-web.service
sudo rm /etc/systemd/system/skyguard.service
sudo rm /etc/systemd/system/skyguard-web.service
sudo systemctl daemon-reload
```

## Monitoring and Performance

### System Resources

```bash
# Check CPU usage
htop

# Check memory usage
free -h

# Check disk usage
df -h

# Check GPU memory
vcgencmd get_mem gpu

# Check temperature
vcgencmd measure_temp
```

### SkyGuard Performance

```bash
# Check service status
sudo systemctl status skyguard.service skyguard-web.service

# View logs
journalctl -u skyguard.service -f
tail -f logs/skyguard.log

# Check detection rate
tail -f logs/skyguard.log | grep "Detection"
```

### Web Portal Access

- **Local**: http://localhost:8080
- **Remote**: http://<PI_IP_ADDRESS>:8080

## Troubleshooting

### Common Issues

1. **GitHub CLI authentication fails:**
   ```bash
   # Check if gh is installed
   gh --version
   
   # If not installed, install it
   sudo apt install gh -y
   
   # Try authentication again
   gh auth login
   
   # If browser method fails, try token method
   gh auth login --with-token
   # Then paste a GitHub personal access token
   ```

2. **SSH key not working:**
   ```bash
   # Check if SSH agent is running
   eval "$(ssh-agent -s)"
   
   # Add key to SSH agent
   ssh-add ~/.ssh/id_ed25519
   
   # Test connection
   ssh -T git@github.com
   
   # If still failing, try generating a new key
   ssh-keygen -t ed25519 -C "your.email@example.com"
   ```

3. **Camera not detected:**
   ```bash
   # Check camera permissions
   sudo usermod -a -G video pi
   
   # For USB camera, check devices
   ls /dev/video*
   lsusb | grep -i camera
   
   # For Pi camera, enable interface
   sudo raspi-config
   # Navigate to: Interface Options → Camera → Enable
   
   # Reboot and try again
   sudo reboot
   ```

4. **Package installation fails:**
   ```bash
   # Update package lists
   sudo apt update
   
   # Try alternative packages for BLAS/LAPACK
   sudo apt install -y libopenblas-dev
   
   # Try alternative packages for GTK/Canberra
   sudo apt install -y libcanberra-gtk3-dev libcanberra-gtk3-module
   
   # If specific packages fail, continue without them
   # The install script will handle missing packages gracefully
   ```

5. **Permission issues:**
   ```bash
   # Fix ownership
   sudo chown -R pi:pi /home/pi/SkyGuard
   
   # Fix permissions
   chmod +x scripts/*.sh
   ```

6. **Services won't start:**
   ```bash
   # Check service status
   sudo systemctl status skyguard.service skyguard-web.service
   
   # Check logs for errors
   journalctl -u skyguard.service --since "1 hour ago"
   
   # Check configuration paths
   # Verify WorkingDirectory and ExecStart paths are correct
   # Update User= if using a different username
   ```

7. **Web portal not accessible:**
   ```bash
   # Check web service status
   sudo systemctl status skyguard-web.service
   
   # Test locally
   curl http://localhost:8080/api/status
   
   # Check firewall
   sudo ufw status
   
   # If firewall blocks, allow port 8080
   sudo ufw allow 8080
   ```

8. **Network issues:**
   ```bash
   # Check network connectivity
   ping google.com
   
   # Check DNS
   nslookup github.com
   
   # Check IP address
   hostname -I
   ```

9. **High memory usage:**
   ```bash
   # Check memory usage
   free -h
   htop
   
   # Restart services to free memory
   sudo systemctl restart skyguard.service skyguard-web.service
   
   # Increase swap if needed
   sudo dphys-swapfile swapoff
   sudo nano /etc/dphys-swapfile
   # Set CONF_SWAPSIZE=4096
   sudo dphys-swapfile setup
   sudo dphys-swapfile swapon
   ```

10. **Model loading errors:**
    ```bash
    # Check model file exists
    ls -la models/
    
    # Test model loading
    source venv/bin/activate
    python3 -c "from ultralytics import YOLO; model = YOLO('models/airbirds_raptor_detector.pt'); print('Model loaded successfully')"
    ```

### Performance Optimization

1. **Increase GPU memory split:**
   ```bash
   sudo raspi-config
   # Navigate to: Advanced Options → Memory Split → 256
   ```

2. **Enable hardware acceleration:**
   ```bash
   # Enable camera interface
   sudo raspi-config
   # Navigate to: Interface Options → Camera → Enable
   ```

3. **Set CPU governor to performance:**
   ```bash
   echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
   ```

4. **Optimize camera settings:**
   - Use HD resolution (1280x720) instead of Full HD (1920x1080)
   - Adjust FPS based on your needs (30fps recommended)
   - Lower detection interval for faster response

## Updates and Maintenance

### Updating SkyGuard

```bash
# Stop services
sudo systemctl stop skyguard.service skyguard-web.service

# Update code
cd /home/pi/SkyGuard
git pull origin main

# Update dependencies
source venv/bin/activate
pip install -r requirements-pi5.txt --upgrade

# Restart services
sudo systemctl start skyguard.service
sudo systemctl start skyguard-web.service
```

### System Maintenance

```bash
# Clean old logs
sudo journalctl --vacuum-time=7d

# Clean old detection images (older than 7 days)
find /home/pi/SkyGuard/data/detections -name "*.jpg" -mtime +7 -delete

# Update system
sudo apt update && sudo apt upgrade -y
```

### Log Rotation

Logs are automatically rotated:
- **Frequency**: Daily
- **Retention**: 7 days
- **Compression**: Enabled
- **Location**: `/etc/logrotate.d/skyguard` (if configured)

## Security

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

## Next Steps

1. **Configure detection parameters** in `config/skyguard.yaml`
2. **Set up notifications** (email, SMS, etc.)
3. **Test with real camera** and adjust settings
4. **Monitor system performance** and optimize as needed
5. **Set up remote monitoring** via web portal
6. **Position camera** for optimal detection coverage

## Support

If you encounter issues:

1. Check the logs: `journalctl -u skyguard.service -f`
2. Verify camera permissions: `ls -la /dev/video*`
3. Test camera manually: `libcamera-hello` (Pi camera) or `v4l2-ctl --list-devices` (USB)
4. Check system resources: `htop` and `free -h`
5. Review configuration: `cat config/skyguard.yaml`
6. Run health check: `./deployment/scripts/health_check.sh`

For additional help, check the main documentation or create an issue on GitHub.

---

**Congratulations!** Your SkyGuard system is now installed and configured on Raspberry Pi 5! 🦅
