# SkyGuard Installation Options

This guide explains the different installation options for SkyGuard, allowing you to choose the dependencies that match your needs and hardware.

## Quick Start Options

### Option 1: Minimal Installation (Recommended for Testing)
```bash
pip install -r requirements-minimal.txt
```
This installs only the core dependencies needed to run SkyGuard in dummy mode for testing.

### Option 2: Full Installation (All Features)
```bash
pip install -r requirements.txt
```
This installs all dependencies including AI frameworks, hardware support, and notifications.

### Option 3: Custom Installation
Choose specific components based on your needs:

```bash
# Core dependencies (always needed)
pip install -r requirements-minimal.txt

# AI framework (choose one)
pip install -r requirements-ai.txt  # PyTorch + YOLO (recommended)
# OR
pip install tensorflow>=2.13.0  # TensorFlow alternative

# Hardware support (if using Raspberry Pi)
pip install -r requirements-hardware.txt

# Notifications (if you want SMS/push alerts)
pip install -r requirements-notifications.txt
```

## AI Framework Options

### PyTorch + YOLO (Recommended)
- **Pros**: Best performance, active development, easy to use
- **Cons**: Larger download size
- **Install**: `pip install torch torchvision ultralytics`

### TensorFlow
- **Pros**: Mature ecosystem, good documentation
- **Cons**: More complex setup, larger memory footprint
- **Install**: `pip install tensorflow>=2.13.0`

### Dummy Mode (No AI)
- **Pros**: Minimal dependencies, fast installation
- **Cons**: No real detection, testing only
- **Use case**: Development, testing, or when you don't have a trained model

## Hardware Support

### Raspberry Pi
Install these if you're using a Raspberry Pi:
```bash
pip install RPi.GPIO picamera2 adafruit-circuitpython-neopixel
```

### Desktop/Laptop
No additional hardware dependencies needed.

### Custom Hardware
You may need additional packages for specific sensors or devices.

## Notification Options

### Audio Alerts (Always Available)
- Uses pygame for system audio
- No additional setup required

### SMS Notifications
```bash
pip install twilio
```
Requires Twilio account and API credentials.

### Push Notifications
```bash
pip install pushbullet.py
```
Requires Pushbullet account and API key.

### Email Notifications
Uses built-in Python libraries, no additional packages needed.

## Platform-Specific Notes

### Windows
- Use the batch installer: `scripts/install.bat`
- Some hardware packages may not be available
- Consider using WSL for better compatibility

### macOS
- Use the shell installer: `scripts/install.sh`
- May need to install Xcode command line tools
- Some packages may require Homebrew

### Linux/Raspberry Pi
- Use the shell installer: `scripts/install.sh`
- May need to install system dependencies first
- Full hardware support available

## Troubleshooting

### TensorFlow Version Issues
If you get TensorFlow version errors:
```bash
# Check available versions
pip index versions tensorflow

# Install specific version
pip install tensorflow==2.13.1
```

### PyTorch Installation Issues
If PyTorch installation fails:
```bash
# Install CPU-only version (smaller)
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Or install with specific CUDA version
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### Hardware Package Issues
If hardware packages fail to install:
```bash
# Skip hardware dependencies and use dummy mode
# Edit config/skyguard.yaml to disable hardware features
```

### Memory Issues
If you run out of memory during installation:
```bash
# Install packages one at a time
pip install opencv-python
pip install numpy
pip install torch
# etc.
```

## Development Setup

For development, install the full requirements plus development tools:
```bash
pip install -r requirements.txt
pip install -e .[dev]  # Development dependencies
```

## Production Deployment

For production deployment, consider:
1. Using Docker containers
2. Installing only necessary dependencies
3. Using pre-compiled wheels for faster installation
4. Setting up proper logging and monitoring

## Verification

After installation, verify everything works:
```bash
python scripts/test_installation.py
```

This will test all installed components and report any issues.
