#!/usr/bin/env python3
"""
Deploy SkyGuard to Raspberry Pi

This script helps prepare and deploy SkyGuard to a Raspberry Pi.
It creates a deployment package and provides instructions.
"""

import os
import sys
import shutil
import zipfile
from pathlib import Path
import yaml

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def create_deployment_package():
    """Create a deployment package for Raspberry Pi."""
    print("🍓 Creating Raspberry Pi deployment package...")
    
    # Create deployment directory
    deploy_dir = Path("deployment/raspberry_pi")
    deploy_dir.mkdir(parents=True, exist_ok=True)
    
    # Files to include in deployment
    files_to_copy = [
        "skyguard/",
        "config/",
        "models/",
        "requirements-minimal.txt",
        "requirements-hardware.txt",
        "setup.py",
        "README.md",
        "scripts/install.sh",
        "scripts/setup_yolov8n.py",
    ]
    
    print("📦 Copying files to deployment package...")
    for item in files_to_copy:
        src = Path(item)
        dst = deploy_dir / item
        
        if src.is_file():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            print(f"   ✅ {item}")
        elif src.is_dir():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            print(f"   ✅ {item}/")
    
    # Create Pi-specific requirements
    pi_requirements = deploy_dir / "requirements-pi.txt"
    with open(pi_requirements, 'w') as f:
        f.write("""# SkyGuard - Raspberry Pi Requirements
# Core dependencies
opencv-python>=4.8.0
numpy>=1.24.0
pillow>=10.0.0
pyyaml>=6.0
python-dotenv>=1.0.0
requests>=2.31.0
pygame>=2.5.0
pandas>=2.0.0

# AI/ML (choose one)
# Option 1: PyTorch + YOLO (recommended)
torch>=2.0.0
torchvision>=0.15.0
ultralytics>=8.0.0

# Option 2: TensorFlow (alternative)
# tensorflow>=2.13.0

# Raspberry Pi specific
RPi.GPIO>=0.7.1
picamera2>=0.3.0
adafruit-circuitpython-neopixel>=6.3.0
pyserial>=3.5
imutils>=0.5.4

# Optional notifications
# twilio>=8.5.0
# pushbullet.py>=0.11.0
""")
    
    print(f"✅ Deployment package created at {deploy_dir}")
    return deploy_dir


def create_pi_install_script(deploy_dir):
    """Create installation script for Raspberry Pi."""
    print("📝 Creating Raspberry Pi installation script...")
    
    install_script = deploy_dir / "install_on_pi.sh"
    with open(install_script, 'w', encoding='utf-8') as f:
        f.write("""#!/bin/bash
# SkyGuard Raspberry Pi Installation Script

set -e

echo "🍓 SkyGuard Raspberry Pi Installation"
echo "====================================="

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install system dependencies
echo "🔧 Installing system dependencies..."
sudo apt install -y \\
    python3 \\
    python3-pip \\
    python3-venv \\
    python3-dev \\
    python3-opencv \\
    libopencv-dev \\
    libatlas-base-dev \\
    git \\
    wget \\
    curl \\
    build-essential \\
    cmake \\
    pkg-config \\
    libjpeg-dev \\
    libtiff5-dev \\
    libpng-dev \\
    libavcodec-dev \\
    libavformat-dev \\
    libswscale-dev \\
    libv4l-dev \\
    libxvidcore-dev \\
    libx264-dev \\
    libgtk-3-dev \\
    libcanberra-gtk3-dev \\
    libcanberra-gtk3-module \\
    libcanberra-gtk-dev \\
    libcanberra-gtk-module

# Enable camera interface
echo "📷 Enabling camera interface..."
sudo raspi-config nonint do_camera 0

# Enable I2C and SPI (for sensors)
echo "🔌 Enabling I2C and SPI..."
sudo raspi-config nonint do_i2c 0
sudo raspi-config nonint do_spi 0

# Create virtual environment
echo "🐍 Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install requirements
echo "📦 Installing Python packages..."
pip install -r requirements-pi.txt

# Install SkyGuard
echo "🦅 Installing SkyGuard..."
pip install -e .

# Create systemd service
echo "⚙️  Creating systemd service..."
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

echo "✅ Installation complete!"
echo ""
echo "Next steps:"
echo "1. Configure SkyGuard: ./venv/bin/python -m skyguard.setup.configure"
echo "2. Test the system: ./venv/bin/python -m skyguard.main --test-system"
echo "3. Start SkyGuard: sudo systemctl start skyguard.service"
echo "4. Check status: sudo systemctl status skyguard.service"
echo "5. View logs: journalctl -u skyguard.service -f"
""")
    
    # Make script executable
    os.chmod(install_script, 0o755)
    print(f"✅ Installation script created: {install_script}")
    
    return install_script


def create_pi_config():
    """Create Raspberry Pi optimized configuration."""
    print("⚙️  Creating Raspberry Pi configuration...")
    
    pi_config = {
        'system': {
            'detection_interval': 2.0,  # Slower for Pi
            'save_detection_frames': True,
            'max_detection_history': 500,
            'debug_mode': False,
        },
        'camera': {
            'source': 0,  # Default camera
            'width': 640,  # Lower resolution for Pi
            'height': 480,
            'fps': 15,  # Lower FPS for Pi
            'rotation': 0,
            'flip_horizontal': False,
            'flip_vertical': False,
        },
        'ai': {
            'model_path': 'models/yolo11n-seg.pt',
            'model_type': 'yolo',
            'confidence_threshold': 0.3,
            'nms_threshold': 0.4,
            'input_size': [640, 640],
            'classes': ['bird'],
        },
        'notifications': {
            'audio': {
                'enabled': True,
                'sound_file': 'sounds/raptor_alert.wav',
                'volume': 0.8,
            },
            'push': {
                'enabled': False,
                'api_key': '',
                'device_id': '',
            },
            'sms': {
                'enabled': False,
                'account_sid': '',
                'auth_token': '',
                'from_number': '',
                'to_numbers': [],
            },
            'email': {
                'enabled': False,
                'smtp_server': '',
                'smtp_port': 587,
                'username': '',
                'password': '',
                'from_email': '',
                'to_emails': [],
            },
        },
        'storage': {
            'database_path': 'data/skyguard.db',
            'detection_images_path': 'data/detections',
            'log_retention_days': 7,  # Shorter retention for Pi
        },
        'logging': {
            'level': 'INFO',
            'file': 'logs/skyguard.log',
            'max_size_mb': 5,  # Smaller log files for Pi
            'backup_count': 3,
        },
        'hardware': {
            'platform': 'raspberry_pi',
            'gpio_enabled': True,
            'led_pin': 18,
            'buzzer_pin': 19,
            'motion_sensor_pin': 20,
        },
    }
    
    return pi_config


def create_deployment_instructions(deploy_dir):
    """Create deployment instructions."""
    print("📖 Creating deployment instructions...")
    
    instructions = deploy_dir / "DEPLOYMENT_INSTRUCTIONS.md"
    with open(instructions, 'w', encoding='utf-8') as f:
        f.write("""# SkyGuard Raspberry Pi Deployment Instructions

## 🍓 Prerequisites

- Raspberry Pi 5 (4GB RAM minimum, 8GB recommended)
- 32GB+ microSD card (Class 10 or better)
- USB webcam or Raspberry Pi camera module
- Internet connection
- Power supply (5V/3A)

## 📦 Deployment Methods

### Method 1: Direct Transfer (Recommended)

1. **Copy files to Raspberry Pi:**
   ```bash
   # From your development machine
   scp -r deployment/raspberry_pi/* pi@<PI_IP_ADDRESS>:~/skyguard/
   ```

2. **SSH into Raspberry Pi:**
   ```bash
   ssh pi@<PI_IP_ADDRESS>
   ```

3. **Run installation:**
   ```bash
   cd ~/skyguard
   chmod +x install_on_pi.sh
   ./install_on_pi.sh
   ```

### Method 2: Git Clone

1. **Clone repository on Pi:**
   ```bash
   git clone https://github.com/jad3tx/SkyGuard.git
   cd skyguard
   ```

2. **Run installation:**
   ```bash
   chmod +x scripts/install.sh
   ./scripts/install.sh
   ```

### Method 3: USB Transfer

1. **Create deployment package:**
   ```bash
   # On development machine
   python scripts/deploy_to_pi.py
   ```

2. **Copy to USB drive:**
   ```bash
   cp -r deployment/raspberry_pi/* /media/usb/skyguard/
   ```

3. **Transfer to Pi and install:**
   ```bash
   # On Raspberry Pi
   cd /media/usb/skyguard
   chmod +x install_on_pi.sh
   ./install_on_pi.sh
   ```

## ⚙️ Configuration

### 1. Camera Setup

**For USB Webcam:**
```bash
# Test camera
lsusb | grep -i camera
python -c "import cv2; cap = cv2.VideoCapture(0); print('OK' if cap.isOpened() else 'Failed')"
```

**For Raspberry Pi Camera:**
```bash
# Enable camera interface
sudo raspi-config
# Navigate to Interface Options > Camera > Enable

# Test camera
libcamera-hello --list-cameras
```

### 2. Configure SkyGuard

```bash
# Run configuration wizard
./venv/bin/python -m skyguard.setup.configure

# Or edit config manually
nano config/skyguard.yaml
```

### 3. Test the System

```bash
# Test camera
./venv/bin/python -m skyguard.main --test-camera

# Test AI model
./venv/bin/python -m skyguard.main --test-model

# Test alerts
./venv/bin/python -m skyguard.main --test-alerts
```

## 🚀 Running SkyGuard

### Manual Start
```bash
# Activate virtual environment
source venv/bin/activate

# Run SkyGuard
python -m skyguard.main
```

### Auto-start Service
```bash
# Start service
sudo systemctl start skyguard.service

# Enable auto-start on boot
sudo systemctl enable skyguard.service

# Check status
sudo systemctl status skyguard.service

# View logs
journalctl -u skyguard.service -f
```

## 🔧 Troubleshooting

### Common Issues

**Camera not detected:**
```bash
# Check USB devices
lsusb

# Check video devices
ls /dev/video*

# Test with OpenCV
python -c "import cv2; cap = cv2.VideoCapture(0); print('OK' if cap.isOpened() else 'Failed')"
```

**Permission errors:**
```bash
# Add user to video group
sudo usermod -a -G video pi

# Reboot
sudo reboot
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
# Check model file
ls -la models/

# Test model loading
python -c "from ultralytics import YOLO; model = YOLO('models/yolo11n-seg.pt'); print('Model loaded successfully')"
```

### Performance Optimization

**For Raspberry Pi 5 (4GB):**
- Use lower resolution: 640x480
- Reduce FPS: 15
- Lower confidence threshold: 0.3
- Enable GPU memory split: 128MB

**For Raspberry Pi 5 (8GB):**
- Use medium resolution: 1280x720
- Higher FPS: 30
- Standard confidence threshold: 0.5
- Enable GPU memory split: 256MB

## 📊 Monitoring

### Check System Status
```bash
# Service status
sudo systemctl status skyguard.service

# System resources
htop
df -h
free -h

# Camera status
ls /dev/video*
```

### View Logs
```bash
# Real-time logs
journalctl -u skyguard.service -f

# Log files
tail -f logs/skyguard.log
```

## 🔄 Updates

### Update SkyGuard
```bash
# Stop service
sudo systemctl stop skyguard.service

# Update code
git pull origin main

# Update dependencies
source venv/bin/activate
pip install -r requirements-pi.txt

# Restart service
sudo systemctl start skyguard.service
```

### Update Model
```bash
# Replace model file
cp new_model.pt models/yolo11n-seg.pt

# Restart service
sudo systemctl restart skyguard.service
```

## 📱 Remote Access

### SSH Access
```bash
# Enable SSH
sudo systemctl enable ssh
sudo systemctl start ssh
```

### Web Interface (Optional)
```bash
# Install web interface
pip install flask flask-cors

# Run web interface
python scripts/web_interface.py
```

## 🔒 Security

### Firewall Setup
```bash
# Install UFW
sudo apt install ufw

# Configure firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw enable
```

### User Permissions
```bash
# Create dedicated user
sudo useradd -m -s /bin/bash skyguard
sudo usermod -a -G video,gpio skyguard

# Update service to use skyguard user
sudo nano /etc/systemd/system/skyguard.service
# Change User=pi to User=skyguard
```

## 📞 Support

- **Documentation**: Check docs/ directory
- **Issues**: GitHub Issues
- **Logs**: Check logs/skyguard.log
- **System**: Check journalctl -u skyguard.service
""")
    
    print(f"✅ Deployment instructions created: {instructions}")
    return instructions


def main():
    """Main deployment function."""
    print("🍓 SkyGuard Raspberry Pi Deployment")
    print("=" * 50)
    
    # Create deployment package
    deploy_dir = create_deployment_package()
    
    # Create installation script
    create_pi_install_script(deploy_dir)
    
    # Create Pi-specific config
    pi_config = create_pi_config()
    config_path = deploy_dir / "config" / "skyguard_pi.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, 'w') as f:
        yaml.dump(pi_config, f, default_flow_style=False, indent=2)
    
    # Create deployment instructions
    create_deployment_instructions(deploy_dir)
    
    print("\n🎉 Deployment package created successfully!")
    print(f"📁 Location: {deploy_dir.absolute()}")
    print("\nNext steps:")
    print("1. Copy the deployment folder to your Raspberry Pi")
    print("2. Run: chmod +x install_on_pi.sh && ./install_on_pi.sh")
    print("3. Configure: ./venv/bin/python -m skyguard.setup.configure")
    print("4. Start: sudo systemctl start skyguard.service")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
