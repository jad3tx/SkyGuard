# SkyGuard Hardware Guide

![SkyGuard Logo](../skyGuardShield.png)

This guide covers the hardware requirements, recommendations, and setup for the SkyGuard raptor alert system.

## Hardware Requirements

### Minimum Requirements

**Controller:**
- Raspberry Pi 5 (8GB RAM) or equivalent single-board computer
- 32GB+ microSD card (Class 10 or better)
- 5V/3A power supply with USB-C connector

**Camera:**
- USB webcam (720p, 30fps minimum)
- Or Raspberry Pi camera module v2

**Connectivity:**
- Ethernet cable or WiFi adapter
- Internet connection for initial setup and updates

**Enclosure:**
- Weatherproof case (IP65 or better)
- Mounting hardware for camera and controller

### Recommended Setup

**Controller:**
- Raspberry Pi 5 (8GB RAM) for better performance
- 64GB+ microSD card (Class 10, A2 rating)
- 5V/2A Power supply with USB-C connector

**Camera:**
- High-quality USB webcam (1080p, 30fps)
- Or Raspberry Pi HQ camera module
- Wide-angle lens for better coverage



## Hardware Components

### 1. Single Board Computer

#### Raspberry Pi 5 (Recommended)
- **CPU:** Quad-core ARM Cortex-A72 @ 1.5GHz
- **RAM:** 4GB or 8GB LPDDR4
- **Storage:** microSD card slot
- **Connectivity:** WiFi 802.11ac, Bluetooth 5.0, Gigabit Ethernet
- **GPIO:** 40-pin header with I2C, SPI, UART
- **Price:** $80-90

#### Alternative Options
- **Orange Pi 5:** More powerful, similar price
- **Intel NUC:** Desktop-class performance, higher power consumption

### 2. Camera Options

#### USB Webcams
**Recommended Models:**
- Logitech C920/C922: 1080p, good low-light performance
- Logitech C270: 720p, budget option


**Specifications:**
- Resolution: 720p minimum, 1080p recommended
- Frame rate: 30fps
- Interface: USB 2.0 or 3.0
- Mounting: Standard tripod thread

#### Raspberry Pi Camera Modules
**Camera Module v2:**
- 8MP sensor, 1080p video
- Fixed focus lens
- CSI interface (better performance than USB)
- Price: $25

**HQ Camera Module:**
- 12.3MP sensor, 4K video
- Interchangeable lenses
- Better image quality
- Price: $50

### 3. Storage

#### microSD Cards
**Recommended Specifications:**
- Capacity: 32GB minimum, 64GB recommended
- Speed: Class 10, A2 rating
- Brand: SanDisk, Samsung, or Kingston
- Price: $10-20

**Why A2 rating?**
- Better random read/write performance
- Faster application loading
- Improved system responsiveness

### 4. Power Supply

#### Requirements
- **Voltage:** 5V DC
- **Current:** 2A minimum
- **Connector:** USB-C (Raspberry Pi 5)
- **Protection:** Overcurrent, overvoltage protection

#### Recommended Options
- Official Raspberry Pi 5 power supply
- Anker PowerPort III with USB-C
- CanaKit 5V 3A power supply

### 5. Enclosure and Mounting

#### Weatherproof Enclosure
**Requirements:**
- IP65 or better weatherproof rating
- Ventilation for heat dissipation
- Access to ports and connectors
- Mounting points for camera

**Recommended Options:**
- Pelican cases with custom cutouts
- 3D printed enclosures (PLA+ or PETG)
- Commercial IP65 electrical boxes

#### Camera Mounting
- Standard 1/4"-20 tripod thread
- Adjustable angle mounting
- Vibration dampening
- Easy access for maintenance

### 6. Optional Components

#### LED Status Indicators
- **Green LED:** System running normally
- **Red LED:** Alert/error condition
- **Blue LED:** Detection in progress
- **GPIO pins:** 18, 19, 20 (configurable)

#### Audio Alerts
- **Piezo buzzer:** Simple audio alerts
- **Speaker:** More complex audio notifications
- **GPIO pin:** 19 (configurable)

#### Motion Sensor
- **PIR sensor:** Detect movement for activation
- **GPIO pin:** 20 (configurable)
- **Power saving:** Wake system from sleep

#### Solar Power (Optional)
- **Solar panel:** 20W minimum
- **Charge controller:** MPPT type
- **Battery:** 12V 7Ah lead-acid or LiFePO4
- **Inverter:** 12V to 5V DC-DC converter

## Assembly Instructions

### Step 1: Prepare the Controller

1. **Flash the operating system**
   ```bash
   # Download Raspberry Pi Imager
   # Select Raspberry Pi OS Lite (64-bit)
   # Flash to microSD card
   ```

2. **Enable required interfaces**
   ```bash
   sudo raspi-config
   # Enable SSH
   # Enable Camera (if using Pi camera)
   # Enable I2C (if using sensors)
   # Enable SPI (if using sensors)
   ```

3. **Update system**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

### Step 2: Install Camera

#### USB Webcam
1. Connect webcam to USB port
2. Test with: `lsusb | grep -i camera`
3. Verify with: `python -c "import cv2; cap = cv2.VideoCapture(0); print('OK' if cap.isOpened() else 'Failed')"`

#### Raspberry Pi Camera
1. Connect camera ribbon cable to CSI port
2. Enable camera interface in raspi-config
3. Test with: `libcamera-hello --list-cameras`



### Step 3: Enclosure Assembly

1. **Prepare enclosure**
   - Drill holes for camera lens
   - Cut openings for connectors
   - Install ventilation fans if needed

2. **Mount components**
   - Secure Raspberry Pi with standoffs
   - Mount camera with adjustable bracket
   - Install LEDs and buzzer in visible locations

3. **Cable management**
   - Route cables neatly
   - Use cable ties and clips
   - Leave slack for maintenance

4. **Weatherproofing**
   - Seal all openings with gaskets
   - Use waterproof connectors
   - Install desiccant packets

## Power Consumption

### Typical Power Usage
- **Raspberry Pi 5 (idle):** 2-3W
- **Raspberry Pi 5 (active):** 4-6W
- **USB webcam:** 1-2W
- **LED indicators:** 0.1W each
- **Piezo buzzer:** 0.5W
- **Total system:** 6-10W

### Battery Backup Calculations
For 24-hour operation:
- **Daily consumption:** 144-240Wh
- **12V 7Ah battery:** 84Wh (6-12 hours)
- **12V 20Ah battery:** 240Wh (24+ hours)

## Troubleshooting

### Common Issues

**Camera not detected:**
```bash
# Check USB devices
lsusb

# Check video devices
ls /dev/video*

# Test camera
python -c "import cv2; cap = cv2.VideoCapture(0); print('OK' if cap.isOpened() else 'Failed')"
```

**GPIO not working:**
```bash
# Check GPIO permissions
groups $USER

# Add user to gpio group
sudo usermod -a -G gpio $USER

# Reboot or logout/login
```

**Power issues:**
```bash
# Check power supply voltage
vcgencmd measure_volts

# Check for undervoltage warnings
dmesg | grep -i voltage
```

**Overheating:**
```bash
# Check temperature
vcgencmd measure_temp

# Install heatsinks and fan
# Monitor with: watch -n 1 vcgencmd measure_temp
```

### Performance Optimization

**Increase GPU memory:**
```bash
# Edit /boot/config.txt
echo "gpu_mem=128" | sudo tee -a /boot/config.txt
```

**Disable unnecessary services:**
```bash
sudo systemctl disable bluetooth
sudo systemctl disable hciuart
sudo systemctl disable ModemManager
```

**Optimize camera settings:**
```yaml
# In config/skyguard.yaml
camera:
  width: 640
  height: 480
  fps: 15  # Reduce FPS to save CPU
```

## Cost Breakdown

### Basic Setup (~$150)
- Raspberry Pi 5 (4GB): $55
- 32GB microSD card: $10
- Power supply: $10
- USB webcam: $30
- Enclosure: $20 or 'free' if you 3d print
- Cables and connectors: $10
- Mounting hardware: $15

### Recommended Setup (~$200)
- Raspberry Pi 5 (8GB): $80
- 64GB microSD card: $15
- Power supply with fan: $15
- High-quality webcam: $50
- Weatherproof enclosure: $30
- LED indicators and buzzer: $10
- Cables and connectors: $15

### Premium Setup (~$400)
- Raspberry Pi 5 (8GB): $80
- 128GB microSD card: $25
- HQ camera module: $50
- Professional enclosure: $50
- Professional mounting: $25
- Additional accessories: $170


