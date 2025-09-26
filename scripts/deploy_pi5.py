#!/usr/bin/env python3
"""
Deploy SkyGuard to Raspberry Pi 5 (8GB)

This script creates a Pi 5 optimized deployment package.
"""

import os
import sys
import shutil
import yaml
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def create_pi5_deployment():
    """Create Raspberry Pi 5 optimized deployment package."""
    print("🍓 Creating Raspberry Pi 5 (8GB) deployment package...")
    
    # Create deployment directory
    deploy_dir = Path("deployment/raspberry_pi5")
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
        "scripts/setup_airbirds_fixed.py",
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
    
    # Create Pi 5 specific requirements
    pi5_requirements = deploy_dir / "requirements-pi5.txt"
    with open(pi5_requirements, 'w') as f:
        f.write("""# SkyGuard - Raspberry Pi 5 (8GB) Requirements
# Core dependencies
opencv-python>=4.8.0
numpy>=1.24.0
pillow>=10.0.0
pyyaml>=6.0
python-dotenv>=1.0.0
requests>=2.31.0
pygame>=2.5.0
pandas>=2.0.0

# AI/ML - Pi 5 can handle full PyTorch
torch>=2.0.0
torchvision>=0.15.0
ultralytics>=8.0.0

# Raspberry Pi 5 specific
RPi.GPIO>=0.7.1
picamera2>=0.3.0
adafruit-circuitpython-neopixel>=6.3.0
pyserial>=3.5
imutils>=0.5.4

# Optional notifications
twilio>=8.5.0
pushbullet.py>=0.11.0
""")
    
    # Create Pi 5 optimized configuration
    pi5_config = {
        'system': {
            'detection_interval': 1.0,  # Faster for Pi 5
            'save_detection_frames': True,
            'max_detection_history': 1000,  # More history for Pi 5
            'debug_mode': False,
        },
        'camera': {
            'source': 0,
            'width': 1280,  # Higher resolution for Pi 5
            'height': 720,
            'fps': 30,  # Higher FPS for Pi 5
            'rotation': 0,
            'flip_horizontal': False,
            'flip_vertical': False,
        },
        'ai': {
            'model_path': 'models/airbirds_raptor_detector.pt',
            'model_type': 'yolo',
            'confidence_threshold': 0.5,  # Higher confidence for Pi 5
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
                'enabled': True,  # Enable for Pi 5
                'api_key': '',
                'device_id': '',
            },
            'sms': {
                'enabled': True,  # Enable for Pi 5
                'account_sid': '',
                'auth_token': '',
                'from_number': '',
                'to_numbers': [],
            },
            'email': {
                'enabled': True,  # Enable for Pi 5
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
            'log_retention_days': 14,  # Longer retention for Pi 5
        },
        'logging': {
            'level': 'INFO',
            'file': 'logs/skyguard.log',
            'max_size_mb': 10,  # Larger log files for Pi 5
            'backup_count': 5,
        },
        'hardware': {
            'platform': 'raspberry_pi5',
            'gpio_enabled': True,
            'led_pin': 18,
            'buzzer_pin': 19,
            'motion_sensor_pin': 20,
        },
    }
    
    # Save Pi 5 config
    config_path = deploy_dir / "config" / "skyguard_pi5.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, 'w') as f:
        yaml.dump(pi5_config, f, default_flow_style=False, indent=2)
    
    print(f"✅ Pi 5 deployment package created at {deploy_dir}")
    return deploy_dir


def create_pi5_install_script(deploy_dir):
    """Create installation script optimized for Raspberry Pi 5."""
    print("📝 Creating Raspberry Pi 5 installation script...")
    
    install_script = deploy_dir / "install_pi5.sh"
    with open(install_script, 'w') as f:
        f.write("""#!/bin/bash
# SkyGuard Raspberry Pi 5 (8GB) Installation Script

set -e

echo "🍓 SkyGuard Raspberry Pi 5 Installation"
echo "======================================="

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install system dependencies optimized for Pi 5
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
    libcanberra-gtk-module \\
    ffmpeg \\
    v4l-utils

# Enable camera interface
echo "📷 Enabling camera interface..."
sudo raspi-config nonint do_camera 0

# Enable I2C and SPI (for sensors)
echo "🔌 Enabling I2C and SPI..."
sudo raspi-config nonint do_i2c 0
sudo raspi-config nonint do_spi 0

# Optimize Pi 5 settings
echo "⚡ Optimizing Pi 5 settings..."
# Increase GPU memory split for Pi 5
echo "gpu_mem=256" | sudo tee -a /boot/config.txt

# Enable hardware acceleration
echo "dtoverlay=vc4-kms-v3d" | sudo tee -a /boot/config.txt
echo "dtoverlay=vc4-kms-v3d-pi5" | sudo tee -a /boot/config.txt

# Create virtual environment
echo "🐍 Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install requirements optimized for Pi 5
echo "📦 Installing Python packages..."
pip install -r requirements-pi5.txt

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
echo "Pi 5 Optimizations Applied:"
echo "- GPU memory split: 256MB"
echo "- Hardware acceleration enabled"
echo "- Higher resolution: 1280x720"
echo "- Higher FPS: 30"
echo "- All notification services enabled"
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
    print(f"✅ Pi 5 installation script created: {install_script}")
    
    return install_script


def create_pi5_guide(deploy_dir):
    """Create deployment guide for Raspberry Pi 5."""
    print("📖 Creating Raspberry Pi 5 deployment guide...")
    
    guide = deploy_dir / "PI5_DEPLOYMENT_GUIDE.md"
    with open(guide, 'w') as f:
        f.write("""# SkyGuard Raspberry Pi 5 (8GB) Deployment Guide

## 🍓 **Raspberry Pi 5 Optimizations**

### **Hardware Specifications**
- **CPU**: ARM Cortex-A76 quad-core 2.4GHz
- **RAM**: 8GB LPDDR4X
- **GPU**: VideoCore VII
- **Storage**: 32GB+ microSD (Class 10 or better)
- **Camera**: USB webcam or Pi Camera Module 3

### **Performance Expectations**
- **Resolution**: 1280x720 (HD)
- **FPS**: 30 (smooth video)
- **Detection Speed**: ~15ms per frame
- **Memory Usage**: ~3GB RAM
- **Storage**: ~2GB for model + data

## 🚀 **Quick Deployment**

### **Method 1: SCP Transfer (Recommended)**
```bash
# From your development machine
scp -r deployment/raspberry_pi5/* pi@<PI_IP_ADDRESS>:~/skyguard/

# SSH into Pi 5
ssh pi@<PI_IP_ADDRESS>

# Install
cd ~/skyguard
chmod +x install_pi5.sh
./install_pi5.sh
```

### **Method 2: USB Transfer**
```bash
# Copy to USB drive
cp -r deployment/raspberry_pi5/* /media/usb/skyguard/

# On Pi 5: cd /media/usb/skyguard && chmod +x install_pi5.sh && ./install_pi5.sh
```

## ⚙️ **Pi 5 Specific Configuration**

### **Camera Setup**
```bash
# Test camera
lsusb | grep -i camera
python -c "import cv2; cap = cv2.VideoCapture(0); print('OK' if cap.isOpened() else 'Failed')"

# For Pi Camera Module 3
sudo raspi-config
# Navigate to Interface Options > Camera > Enable
```

### **Performance Tuning**
```bash
# Enable hardware acceleration
sudo nano /boot/config.txt
# Add:
gpu_mem=256
dtoverlay=vc4-kms-v3d
dtoverlay=vc4-kms-v3d-pi5

# Reboot
sudo reboot
```

### **Memory Optimization**
```bash
# Check memory usage
free -h

# Increase swap if needed
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Set CONF_SWAPSIZE=4096
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

## 🔧 **Pi 5 Optimized Settings**

### **Camera Configuration**
```yaml
camera:
  width: 1280      # HD resolution
  height: 720
  fps: 30          # Smooth video
  rotation: 0
```

### **AI Configuration**
```yaml
ai:
  model_path: 'models/airbirds_raptor_detector.pt'
  confidence_threshold: 0.5  # Higher confidence
  input_size: [640, 640]
  classes: ['bird']
```

### **System Configuration**
```yaml
system:
  detection_interval: 1.0    # Faster detection
  max_detection_history: 1000  # More history
  debug_mode: false
```

## 📊 **Performance Monitoring**

### **System Resources**
```bash
# Check CPU usage
htop

# Check memory usage
free -h

# Check GPU usage
vcgencmd get_mem gpu

# Check temperature
vcgencmd measure_temp
```

### **SkyGuard Performance**
```bash
# Check service status
sudo systemctl status skyguard.service

# View logs
journalctl -u skyguard.service -f

# Check detection rate
tail -f logs/skyguard.log | grep "Detection"
```

## 🔧 **Troubleshooting**

### **Common Pi 5 Issues**

**Camera not detected:**
```bash
# Check USB devices
lsusb

# Check video devices
ls /dev/video*

# Test with OpenCV
python -c "import cv2; cap = cv2.VideoCapture(0); print('OK' if cap.isOpened() else 'Failed')"
```

**Performance issues:**
```bash
# Check GPU memory
vcgencmd get_mem gpu

# Check CPU temperature
vcgencmd measure_temp

# Check memory usage
free -h
```

**Model loading errors:**
```bash
# Check model file
ls -la models/

# Test model loading
python -c "from ultralytics import YOLO; model = YOLO('models/airbirds_raptor_detector.pt'); print('Model loaded successfully')"
```

## 🚀 **Advanced Features**

### **Multi-Camera Support**
```yaml
camera:
  source: 0  # Primary camera
  secondary_source: 1  # Secondary camera
  width: 1280
  height: 720
  fps: 30
```

### **Real-time Streaming**
```bash
# Install streaming dependencies
pip install flask flask-cors

# Run web interface
python scripts/web_interface.py
```

### **Cloud Integration**
```bash
# Install cloud dependencies
pip install boto3 google-cloud-storage

# Configure cloud storage
python scripts/setup_cloud_storage.py
```

## 📱 **Remote Management**

### **SSH Access**
```bash
# Enable SSH
sudo systemctl enable ssh
sudo systemctl start ssh
```

### **Web Interface**
```bash
# Install web interface
pip install flask flask-cors

# Run web interface
python scripts/web_interface.py
```

### **Mobile App**
```bash
# Install mobile app dependencies
pip install fastapi uvicorn

# Run mobile API
python scripts/mobile_api.py
```

## 🔒 **Security**

### **Firewall Setup**
```bash
# Install UFW
sudo apt install ufw

# Configure firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 8080  # Web interface
sudo ufw enable
```

### **User Permissions**
```bash
# Create dedicated user
sudo useradd -m -s /bin/bash skyguard
sudo usermod -a -G video,gpio skyguard

# Update service
sudo nano /etc/systemd/system/skyguard.service
# Change User=pi to User=skyguard
```

## 📞 **Support**

- **Documentation**: Check `docs/` directory
- **Issues**: GitHub Issues
- **Logs**: Check `logs/skyguard.log`
- **System**: Check `journalctl -u skyguard.service`

## 🎯 **Next Steps**

1. **Test the system**: Run `./venv/bin/python -m skyguard.main --test-system`
2. **Configure alerts**: Set up SMS/email notifications
3. **Optimize performance**: Adjust settings for your setup
4. **Monitor operation**: Check logs and system status
5. **Deploy in production**: Set up auto-start service

---

**Congratulations!** Your SkyGuard system is now optimized for Raspberry Pi 5! 🦅
""")
    
    print(f"✅ Pi 5 deployment guide created: {guide}")
    return guide


def main():
    """Main deployment function."""
    print("🍓 SkyGuard Raspberry Pi 5 (8GB) Deployment")
    print("=" * 50)
    
    # Create deployment package
    deploy_dir = create_pi5_deployment()
    
    # Create installation script
    create_pi5_install_script(deploy_dir)
    
    # Create deployment guide
    create_pi5_guide(deploy_dir)
    
    print("\n🎉 Pi 5 deployment package created successfully!")
    print(f"📁 Location: {deploy_dir.absolute()}")
    print("\nPi 5 Optimizations Applied:")
    print("- GPU memory split: 256MB")
    print("- Hardware acceleration enabled")
    print("- Higher resolution: 1280x720")
    print("- Higher FPS: 30")
    print("- All notification services enabled")
    print("\nNext steps:")
    print("1. Copy the deployment folder to your Raspberry Pi 5")
    print("2. Run: chmod +x install_pi5.sh && ./install_pi5.sh")
    print("3. Configure: ./venv/bin/python -m skyguard.setup.configure")
    print("4. Start: sudo systemctl start skyguard.service")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
