# SkyGuard Management Scripts

This directory contains management scripts for the SkyGuard system.

## 📦 Installation Scripts

### `install.sh`
Main installation script that automatically detects the platform (Jetson or Raspberry Pi) and calls the appropriate platform-specific install script.

**Usage:**
```bash
./scripts/install.sh
```

The script will automatically:
- Detect if you're on a Jetson or Raspberry Pi
- Call `install-jetson.sh` for Jetson devices
- Call `install-rpi.sh` for Raspberry Pi devices

### `install-jetson.sh`
Jetson-specific installation script. Handles:
- System PyTorch detection and verification
- Virtual environment with `--system-site-packages` for CUDA PyTorch access
- Filtering torch packages from requirements (uses system CUDA versions)
- CUDA verification and testing

**Usage:**
```bash
./scripts/install-jetson.sh
```

### `install-rpi.sh`
Raspberry Pi-specific installation script. Handles:
- Standard virtual environment creation
- Full PyTorch installation (CPU version)
- GPIO group setup
- Disk space and camera checks
- Retry logic for package installation

**Usage:**
```bash
./scripts/install-rpi.sh
```

### `install-common.sh`
Shared functions used by both platform-specific install scripts. Contains:
- System dependency installation
- Virtual environment creation utilities
- Common verification functions
- Shared helper functions

**Note:** This file is sourced by the platform-specific scripts and should not be run directly.

## 🚀 Startup Scripts

### `start_skyguard.sh`
Starts the SkyGuard system (both detection and web portal).

**Usage:**
```bash
# Start both services
./scripts/start_skyguard.sh

# Start only detection system
./scripts/start_skyguard.sh --main-only

# Start only web portal
./scripts/start_skyguard.sh --web-only

# Start in background
./scripts/start_skyguard.sh --background

# Start without waiting for stabilization
./scripts/start_skyguard.sh --no-wait
```

**Options:**
- `--main-only`: Start only the main detection system
- `--web-only`: Start only the web portal
- `--background`: Run services in background
- `--no-wait`: Don't wait for services to stabilize
- `--verbose`: Enable verbose output
- `--help`: Show help message

### `stop_skyguard.sh`
Stops the SkyGuard system.

**Usage:**
```bash
# Stop both services
./scripts/stop_skyguard.sh

# Stop only detection system
./scripts/stop_skyguard.sh --main-only

# Stop only web portal
./scripts/stop_skyguard.sh --web-only

# Force stop (kill processes)
./scripts/stop_skyguard.sh --force
```

**Options:**
- `--main-only`: Stop only the main detection system
- `--web-only`: Stop only the web portal
- `--force`: Force stop (kill processes)
- `--verbose`: Enable verbose output
- `--help`: Show help message

## 📋 Service Management

### Using systemd (Recommended)
```bash
# Start services
sudo systemctl start skyguard.service
sudo systemctl start skyguard-web.service

# Stop services
sudo systemctl stop skyguard.service
sudo systemctl stop skyguard-web.service

# Check status
sudo systemctl status skyguard.service skyguard-web.service

# Enable auto-start
sudo systemctl enable skyguard.service skyguard-web.service

# Disable auto-start
sudo systemctl disable skyguard.service skyguard-web.service
```

## 🔍 Monitoring and Troubleshooting

### Check Service Status
```bash
# Check if services are running
ps aux | grep skyguard

# Check systemd services
sudo systemctl status skyguard.service skyguard-web.service

# Check logs
tail -f $SKYGUARD_DIR/logs/skyguard.log
tail -f $SKYGUARD_DIR/logs/web.log
```

### Web Portal Access
- **URL**: `http://<DEVICE_IP_ADDRESS>:8080`
- **Local**: `http://localhost:8080`

### Common Issues

1. **Services won't start:**
   - Check logs: `tail -f logs/skyguard.log` (from SkyGuard directory)
   - Check systemd: `sudo systemctl status skyguard.service`
   - Check dependencies: `pip list | grep -E "(ultralytics|opencv|flask)"`

2. **Web portal not accessible:**
   - Check if web service is running: `sudo systemctl status skyguard-web.service`
   - Check port 8080: `netstat -tlnp | grep 8080`
   - Check firewall: `sudo ufw status`

3. **Camera not working:**
   - Test camera: `python -c "import cv2; cap = cv2.VideoCapture(0); print('OK' if cap.isOpened() else 'Failed')"`
   - Check camera permissions: `ls -la /dev/video*`

## 📁 File Locations

- **Main Directory**: `$SKYGUARD_DIR` (auto-detected, typically `/home/pi/SkyGuard` or `/home/jad3/SkyGuard`)
- **Logs**: `$SKYGUARD_DIR/logs/`
- **Configuration**: `$SKYGUARD_DIR/config/skyguard.yaml`
- **Data**: `$SKYGUARD_DIR/data/`
- **Models**: `$SKYGUARD_DIR/models/`

**Note**: The scripts automatically detect the platform (Jetson uses `jad3`, Raspberry Pi uses `pi`) and set the appropriate paths.

## 🆘 Getting Help

If you encounter issues:

1. **Check the logs** in `logs/`
2. **Check systemd status**: `sudo systemctl status skyguard.service skyguard-web.service`
3. **View recent logs**: `tail -f logs/skyguard.log`
4. **Check service processes**: `ps aux | grep skyguard`

For more detailed troubleshooting, see the main documentation in the `docs/` directory.
