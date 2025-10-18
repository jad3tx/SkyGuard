# SkyGuard Raspberry Pi Deployment Guide

## 🍓 **Quick Start**

### **Method 1: Direct Transfer (Recommended)**

1. **Copy files to Raspberry Pi:**
   ```bash
   # From your development machine
   scp -r deployment/raspberry_pi/* pi@<PI_IP_ADDRESS>:~/skyguard/
   ```

2. **SSH into Raspberry Pi:**
   ```bash
   ssh pi@<PI_IP_ADDRESS>
   ```

3. **Install and run:**
   ```bash
   cd ~/skyguard
   chmod +x install.sh
   ./install.sh
   ```

### **Method 2: USB Transfer**

1. **Copy to USB drive:**
   ```bash
   cp -r deployment/raspberry_pi/* /media/usb/skyguard/
   ```

2. **On Raspberry Pi:**
   ```bash
   cd /media/usb/skyguard
   chmod +x install.sh
   ./install.sh
   ```

## 🔧 **Prerequisites**

- **Raspberry Pi 4** (4GB RAM minimum, 8GB recommended)
- **32GB+ microSD card** (Class 10 or better)
- **USB webcam** or **Raspberry Pi camera module**
- **Internet connection**
- **Power supply** (5V/3A)

## 📦 **What's Included**

The deployment package contains:
- ✅ **SkyGuard source code** (`skyguard/`)
- ✅ **Trained AirBirds model** (`models/airbirds_raptor_detector.pt`)
- ✅ **Configuration files** (`config/`)
- ✅ **Installation script** (`install.sh`)
- ✅ **Requirements** (`requirements-*.txt`)

## 🚀 **Installation Steps**

### **Step 1: Transfer Files**

**Option A: SCP (Secure Copy)**
```bash
# From your development machine
scp -r deployment/raspberry_pi/* pi@192.168.1.100:~/skyguard/
```

**Option B: USB Drive**
```bash
# Copy to USB drive
cp -r deployment/raspberry_pi/* /media/usb/skyguard/
```

**Option C: Git Clone**
```bash
# On Raspberry Pi
git clone https://github.com/jad3tx/SkyGuard.git
cd skyguard
```

### **Step 2: Install Dependencies**

```bash
# SSH into Raspberry Pi
ssh pi@<PI_IP_ADDRESS>

# Navigate to SkyGuard directory
cd ~/skyguard

# Make installation script executable
chmod +x install.sh

# Run installation
./install.sh
```

### **Step 3: Configure SkyGuard**

```bash
# Run configuration wizard
./venv/bin/python -m skyguard.setup.configure

# Or edit config manually
nano config/skyguard.yaml
```

### **Step 4: Test the System**

```bash
# Test camera
./venv/bin/python -m skyguard.main --test-camera

# Test AI model
./venv/bin/python -m skyguard.main --test-model

# Test alerts
./venv/bin/python -m skyguard.main --test-alerts
```

### **Step 5: Run SkyGuard**

```bash
# Manual start
./venv/bin/python -m skyguard.main

# Or create systemd service for auto-start
sudo nano /etc/systemd/system/skyguard.service
```

## ⚙️ **Configuration**

### **Camera Setup**

**USB Webcam:**
```bash
# Test camera
lsusb | grep -i camera
python -c "import cv2; cap = cv2.VideoCapture(0); print('OK' if cap.isOpened() else 'Failed')"
```

**Raspberry Pi Camera:**
```bash
# Enable camera interface
sudo raspi-config
# Navigate to Interface Options > Camera > Enable

# Test camera
libcamera-hello --list-cameras
```

### **Model Configuration**

The trained AirBirds model is already included:
- **Model**: `models/airbirds_raptor_detector.pt`
- **Classes**: `['bird']`
- **Confidence**: `0.3` (adjustable in config)

### **Performance Settings**

**For Raspberry Pi 4 (4GB):**
```yaml
camera:
  width: 640
  height: 480
  fps: 15

ai:
  confidence_threshold: 0.3
  input_size: [640, 640]
```

**For Raspberry Pi 4 (8GB):**
```yaml
camera:
  width: 1280
  height: 720
  fps: 30

ai:
  confidence_threshold: 0.5
  input_size: [640, 640]
```

## 🔧 **Troubleshooting**

### **Common Issues**

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
python -c "from ultralytics import YOLO; model = YOLO('models/airbirds_raptor_detector.pt'); print('Model loaded successfully')"
```

### **Performance Optimization**

**GPU Memory Split:**
```bash
# Edit boot config
sudo nano /boot/config.txt

# Add or modify:
gpu_mem=128  # For 4GB Pi
gpu_mem=256  # For 8GB Pi

# Reboot
sudo reboot
```

**CPU Governor:**
```bash
# Set performance mode
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

## 📊 **Monitoring**

### **Check System Status**
```bash
# System resources
htop
df -h
free -h

# Camera status
ls /dev/video*
```

### **View Logs**
```bash
# SkyGuard logs
tail -f logs/skyguard.log

# System logs
journalctl -u skyguard.service -f
```

## 🔄 **Updates**

### **Update SkyGuard**
```bash
# Stop service
sudo systemctl stop skyguard.service

# Update code
git pull origin main

# Update dependencies
source venv/bin/activate
pip install -r requirements-minimal.txt
pip install -r requirements-hardware.txt

# Restart service
sudo systemctl start skyguard.service
```

### **Update Model**
```bash
# Replace model file
cp new_model.pt models/airbirds_raptor_detector.pt

# Restart service
sudo systemctl restart skyguard.service
```

## 🚀 **Auto-Start Service**

### **Create Systemd Service**
```bash
sudo nano /etc/systemd/system/skyguard.service
```

Add this content:
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

### **Enable Service**
```bash
# Enable service
sudo systemctl daemon-reload
sudo systemctl enable skyguard.service

# Start service
sudo systemctl start skyguard.service

# Check status
sudo systemctl status skyguard.service
```

## 📱 **Remote Access**

### **SSH Access**
```bash
# Enable SSH
sudo systemctl enable ssh
sudo systemctl start ssh
```

### **Web Interface (Optional)**
```bash
# Install web interface
pip install flask flask-cors

# Run web interface
python scripts/web_interface.py
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
sudo ufw enable
```

### **User Permissions**
```bash
# Create dedicated user
sudo useradd -m -s /bin/bash skyguard
sudo usermod -a -G video,gpio skyguard

# Update service to use skyguard user
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
3. **Optimize performance**: Adjust settings for your Pi model
4. **Monitor operation**: Check logs and system status
5. **Deploy in production**: Set up auto-start service

---

**Congratulations!** Your SkyGuard system is now ready to protect your flock! 🦅
