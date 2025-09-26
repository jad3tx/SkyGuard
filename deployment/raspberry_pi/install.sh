#!/bin/bash
# SkyGuard Raspberry Pi Installation

set -e

echo "SkyGuard Raspberry Pi Installation"
echo "=================================="

# Update system
echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install system dependencies
echo "Installing system dependencies..."
sudo apt install -y python3 python3-pip python3-venv python3-dev python3-opencv libopencv-dev git

# Enable camera interface
echo "Enabling camera interface..."
sudo raspi-config nonint do_camera 0

# Create virtual environment
echo "Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install requirements
echo "Installing Python packages..."
pip install -r requirements-minimal.txt
pip install -r requirements-hardware.txt

# Install SkyGuard
echo "Installing SkyGuard..."
pip install -e .

echo "Installation complete!"
echo ""
echo "Next steps:"
echo "1. Configure: ./venv/bin/python -m skyguard.setup.configure"
echo "2. Test: ./venv/bin/python -m skyguard.main --test-system"
echo "3. Run: ./venv/bin/python -m skyguard.main"
