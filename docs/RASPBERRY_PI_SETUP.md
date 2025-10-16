# SkyGuard Raspberry Pi Setup Guide

This guide covers the complete setup process for SkyGuard on a Raspberry Pi, including manual steps required for initial system preparation.

## Prerequisites

- Raspberry Pi (3B+, 4B, or newer recommended)
- MicroSD card (32GB+ recommended)
- Camera module or USB camera
- Power supply (5V, 3A+ recommended)
- Network connection (WiFi or Ethernet)

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
   - **Set username and password**: Use `pi` as username
   - **Configure WiFi**: Enter your network credentials
   - **Set locale settings**: Choose your timezone and keyboard layout
7. Click "Write" to image the card

### 1.2 Boot and Connect

1. Insert the SD card into your Raspberry Pi
2. Connect power and boot the Pi
3. Find your Pi's IP address:
   - Check your router's admin panel
   - Use a network scanner like `nmap`
   - Use `arp -a` on your computer
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
git clone https://github.com/your-username/SkyGuard.git
cd SkyGuard

# Make install script executable
chmod +x scripts/install.sh
```

## Step 4: Run Installation

### 4.1 Automated Installation

```bash
# Run the installation script
./scripts/install.sh
```

The script will:
- Detect your Raspberry Pi platform
- Install system dependencies
- Handle package availability issues gracefully
- Set up Python virtual environment
- Install Python packages
- Configure the system

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
```

**For USB Camera:**
```bash
# List available cameras
ls /dev/video*
# Test camera
v4l2-ctl --list-devices
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

## Step 6: Test Installation

### 6.1 Test Camera

```bash
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

## Step 7: Enable Auto-Start (Optional)

### 7.1 Create Systemd Service

```bash
# Create service file
sudo nano /etc/systemd/system/skyguard.service
```

Add the following content:
```ini
[Unit]
Description=SkyGuard Raptor Detection System
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/SkyGuard
Environment=PATH=/home/pi/SkyGuard/venv/bin
ExecStart=/home/pi/SkyGuard/venv/bin/python /home/pi/SkyGuard/skyguard/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 7.2 Enable Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable skyguard.service

# Start service
sudo systemctl start skyguard.service

# Check status
sudo systemctl status skyguard.service
```

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
   
   # Reboot and try again
   sudo reboot
   ```

4. **Package installation fails:**
   ```bash
   # Update package lists
   sudo apt update
   
   # Try alternative packages
   sudo apt install -y libopenblas-dev
   ```

5. **Permission issues:**
   ```bash
   # Fix ownership
   sudo chown -R pi:pi /home/pi/SkyGuard
   
   # Fix permissions
   chmod +x scripts/*.sh
   ```

6. **Network issues:**
   ```bash
   # Check network connectivity
   ping google.com
   
   # Check DNS
   nslookup github.com
   ```

7. **GitHub CLI browser authentication issues:**
   ```bash
   # If you can't use browser method, create a personal access token:
   # 1. Go to GitHub.com → Settings → Developer settings → Personal access tokens
   # 2. Generate new token with 'repo' and 'read:org' permissions
   # 3. Use token authentication:
   gh auth login --with-token
   # 4. Paste the token when prompted
   ```

### Performance Optimization

1. **Increase GPU memory split:**
   ```bash
   sudo raspi-config
   # Navigate to: Advanced Options → Memory Split → 128
   ```

2. **Enable hardware acceleration:**
   ```bash
   # Enable camera interface
   sudo raspi-config
   # Navigate to: Interface Options → Camera → Enable
   ```

3. **Monitor system resources:**
   ```bash
   # Check CPU usage
   top
   
   # Check memory usage
   free -h
   
   # Check temperature
   vcgencmd measure_temp
   ```

## Next Steps

1. **Configure detection parameters** in `config/skyguard.yaml`
2. **Set up notifications** (email, SMS, etc.)
3. **Test with real camera** and adjust settings
4. **Monitor system performance** and optimize as needed
5. **Set up remote monitoring** if desired

## Support

If you encounter issues:

1. Check the logs: `tail -f logs/skyguard.log`
2. Verify camera permissions: `ls -la /dev/video*`
3. Test camera manually: `raspistill -o test.jpg`
4. Check system resources: `htop`
5. Review configuration: `cat config/skyguard.yaml`

For additional help, check the main documentation or create an issue on GitHub.
