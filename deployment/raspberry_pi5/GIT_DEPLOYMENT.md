# SkyGuard Raspberry Pi 5 - Git Deployment Guide

## 🚀 **Quick Git Deployment**

### **Step 1: Clone Repository on Pi 5**

```bash
# SSH into your Raspberry Pi 5
ssh pi@<PI_IP_ADDRESS>

# Clone the repository
git clone https://github.com/johndaughtridge/skyguard.git
cd skyguard
```

### **Step 2: Install Dependencies**

```bash
# Make installation script executable
chmod +x install_pi5.sh

# Run Pi 5 optimized installation
./install_pi5.sh
```

### **Step 3: Configure SkyGuard**

```bash
# Run configuration wizard
skyguard-setup

# Or edit config manually
nano config/skyguard.yaml
```

### **Step 4: Test the System**

```bash
# Test camera
skyguard --test-camera

# Test AI model
skyguard --test-model

# Test alerts
skyguard --test-alerts
```

### **Step 5: Run SkyGuard**

```bash
# Manual start
skyguard

# Or create systemd service for auto-start (already created by install script)
sudo systemctl start skyguard.service
```

## ⚙️ **Pi 5 Optimizations**

### **Enable Hardware Acceleration**

```bash
# Edit boot config
sudo nano /boot/config.txt

# Add these lines:
gpu_mem=256
dtoverlay=vc4-kms-v3d
dtoverlay=vc4-kms-v3d-pi5

# Reboot
sudo reboot
```

### **Optimize Performance**

```bash
# Set CPU governor to performance
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# Check GPU memory
vcgencmd get_mem gpu

# Check temperature
vcgencmd measure_temp
```

## 🔧 **Configuration**

### **Camera Setup**

**USB Webcam:**
```bash
# Test camera
lsusb | grep -i camera
./venv/bin/python -c "import cv2; cap = cv2.VideoCapture(0); print('OK' if cap.isOpened() else 'Failed')"
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
- **Confidence**: `0.5` (Pi 5 optimized)

### **Performance Settings**

**For Raspberry Pi 5 (8GB):**
```yaml
camera:
  width: 1280      # HD resolution
  height: 720
  fps: 30          # Smooth video

ai:
  confidence_threshold: 0.5  # Higher confidence
  input_size: [640, 640]
  classes: ['bird']

system:
  detection_interval: 1.0    # Faster detection
  max_detection_history: 1000  # More history
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

# GPU status
vcgencmd get_mem gpu
vcgencmd measure_temp
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

## 🔧 **Troubleshooting**

### **Common Issues**

**Camera not detected:**
```bash
# Check USB devices
lsusb

# Check video devices
ls /dev/video*

# Test with OpenCV
./venv/bin/python -c "import cv2; cap = cv2.VideoCapture(0); print('OK' if cap.isOpened() else 'Failed')"
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
# Set CONF_SWAPSIZE=4096
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

**Model loading errors:**
```bash
# Check model file
ls -la models/

# Test model loading
./venv/bin/python -c "from ultralytics import YOLO; model = YOLO('models/airbirds_raptor_detector.pt'); print('Model loaded successfully')"
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
./venv/bin/python scripts/web_interface.py
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

1. **Clone repository**: `git clone https://github.com/johndaughtridge/skyguard.git`
2. **Install dependencies**: `./install_pi5.sh`
3. **Configure system**: `skyguard-setup`
4. **Test system**: `skyguard --test-system`
5. **Deploy**: `skyguard`

---

**Congratulations!** Your SkyGuard system is now ready for Raspberry Pi 5! 🦅
