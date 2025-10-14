#!/bin/bash
# SkyGuard Raspberry Pi 5 (8GB) Installation Script

set -e

echo "SkyGuard Raspberry Pi 5 Installation"
echo "======================================"

# Update system
echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install system dependencies optimized for Pi 5
echo "Installing system dependencies..."
sudo apt install -y python3 python3-pip python3-venv python3-dev python3-opencv libopencv-dev libatlas-base-dev git wget curl build-essential cmake pkg-config libjpeg-dev libtiff5-dev libpng-dev libavcodec-dev libavformat-dev libswscale-dev libv4l-dev libxvidcore-dev libx264-dev libgtk-3-dev libcanberra-gtk3-dev libcanberra-gtk3-module libcanberra-gtk-dev libcanberra-gtk-module ffmpeg v4l-utils

# Enable camera interface
echo "Enabling camera interface..."
sudo raspi-config nonint do_camera 0

# Enable I2C and SPI
echo "Enabling I2C and SPI..."
sudo raspi-config nonint do_i2c 0
sudo raspi-config nonint do_spi 0

# Optimize Pi 5 settings
echo "Optimizing Pi 5 settings..."
# Increase GPU memory split for Pi 5
echo "gpu_mem=256" | sudo tee -a /boot/config.txt

# Enable hardware acceleration
echo "dtoverlay=vc4-kms-v3d" | sudo tee -a /boot/config.txt
echo "dtoverlay=vc4-kms-v3d-pi5" | sudo tee -a /boot/config.txt

# Set CPU governor to performance for Pi 5
echo "Setting CPU governor to performance..."
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# Optimize swap for Pi 5
echo "Optimizing swap configuration..."
sudo dphys-swapfile swapoff
sudo sed -i 's/CONF_SWAPSIZE=.*/CONF_SWAPSIZE=4096/' /etc/dphys-swapfile
sudo dphys-swapfile setup
sudo dphys-swapfile swapon

# Create virtual environment
echo "Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install requirements optimized for Pi 5
echo "Installing Python packages..."
pip install -r requirements-pi5.txt

# Install SkyGuard
echo "Installing SkyGuard..."
pip install -e .

# Create systemd service
echo "Creating systemd service..."
sudo tee /etc/systemd/system/skyguard.service > /dev/null <<EOF
[Unit]
Description=SkyGuard Raptor Alert System
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=$(pwd)
Environment=PATH=$(pwd)/venv/bin
ExecStart=$(pwd)/venv/bin/python -m skyguard.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable service
sudo systemctl daemon-reload
sudo systemctl enable skyguard.service

echo "Installation complete!"
echo ""
echo "Pi 5 Optimizations Applied:"
echo "- GPU memory split: 256MB"
echo "- Hardware acceleration enabled"
echo "- CPU governor set to performance"
echo "- Swap optimized to 4GB"
echo "- Higher resolution: 1280x720"
echo "- Higher FPS: 30"
echo "- All notification services enabled"
echo ""
echo "Next steps:"
echo "1. Configure SkyGuard: skyguard-setup"
echo "2. Test the system: skyguard --test-system"
echo "3. Start SkyGuard: sudo systemctl start skyguard.service"
echo "4. Check status: sudo systemctl status skyguard.service"
echo "5. View logs: journalctl -u skyguard.service -f"
