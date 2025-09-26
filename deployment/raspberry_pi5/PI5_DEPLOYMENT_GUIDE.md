# SkyGuard Raspberry Pi 5 (8GB) Deployment Guide

## Raspberry Pi 5 Optimizations

### Hardware Specifications
- **CPU**: ARM Cortex-A76 quad-core 2.4GHz
- **RAM**: 8GB LPDDR4X
- **GPU**: VideoCore VII
- **Storage**: 32GB+ microSD (Class 10 or better)
- **Camera**: USB webcam or Pi Camera Module 3

### Performance Expectations
- **Resolution**: 1280x720 (HD)
- **FPS**: 30 (smooth video)
- **Detection Speed**: ~15ms per frame
- **Memory Usage**: ~3GB RAM
- **Storage**: ~2GB for model + data

## Quick Deployment

### Method 1: SCP Transfer (Recommended)
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

### Method 2: USB Transfer
```bash
# Copy to USB drive
cp -r deployment/raspberry_pi5/* /media/usb/skyguard/

# On Pi 5: cd /media/usb/skyguard && chmod +x install_pi5.sh && ./install_pi5.sh
```

## Pi 5 Specific Configuration

### Camera Setup
```bash
# Test camera
lsusb | grep -i camera
python -c "import cv2; cap = cv2.VideoCapture(0); print('OK' if cap.isOpened() else 'Failed')"

# For Pi Camera Module 3
sudo raspi-config
# Navigate to Interface Options > Camera > Enable
```

### Performance Tuning
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

### Memory Optimization
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

## Pi 5 Optimized Settings

### Camera Configuration
```yaml
camera:
  width: 1280      # HD resolution
  height: 720
  fps: 30          # Smooth video
  rotation: 0
```

### AI Configuration
```yaml
ai:
  model_path: 'models/airbirds_raptor_detector.pt'
  confidence_threshold: 0.5  # Higher confidence
  input_size: [640, 640]
  classes: ['bird']
```

### System Configuration
```yaml
system:
  detection_interval: 1.0    # Faster detection
  max_detection_history: 1000  # More history
  debug_mode: false
```

## Performance Monitoring

### System Resources
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

### SkyGuard Performance
```bash
# Check service status
sudo systemctl status skyguard.service

# View logs
journalctl -u skyguard.service -f

# Check detection rate
tail -f logs/skyguard.log | grep "Detection"
```

## Troubleshooting

### Common Pi 5 Issues

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

## Advanced Features

### Multi-Camera Support
```yaml
camera:
  source: 0  # Primary camera
  secondary_source: 1  # Secondary camera
  width: 1280
  height: 720
  fps: 30
```

### Real-time Streaming
```bash
# Install streaming dependencies
pip install flask flask-cors

# Run web interface
python scripts/web_interface.py
```

### Cloud Integration
```bash
# Install cloud dependencies
pip install boto3 google-cloud-storage

# Configure cloud storage
python scripts/setup_cloud_storage.py
```

## Remote Management

### SSH Access
```bash
# Enable SSH
sudo systemctl enable ssh
sudo systemctl start ssh
```

### Web Interface
```bash
# Install web interface
pip install flask flask-cors

# Run web interface
python scripts/web_interface.py
```

### Mobile App
```bash
# Install mobile app dependencies
pip install fastapi uvicorn

# Run mobile API
python scripts/mobile_api.py
```

## Security

### Firewall Setup
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

### User Permissions
```bash
# Create dedicated user
sudo useradd -m -s /bin/bash skyguard
sudo usermod -a -G video,gpio skyguard

# Update service
sudo nano /etc/systemd/system/skyguard.service
# Change User=pi to User=skyguard
```

## Support

- **Documentation**: Check `docs/` directory
- **Issues**: GitHub Issues
- **Logs**: Check `logs/skyguard.log`
- **System**: Check `journalctl -u skyguard.service`

## Next Steps

1. **Test the system**: Run `./venv/bin/python -m skyguard.main --test-system`
2. **Configure alerts**: Set up SMS/email notifications
3. **Optimize performance**: Adjust settings for your setup
4. **Monitor operation**: Check logs and system status
5. **Deploy in production**: Set up auto-start service

---

**Congratulations!** Your SkyGuard system is now optimized for Raspberry Pi 5!
