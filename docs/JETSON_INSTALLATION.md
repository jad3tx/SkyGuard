# SkyGuard Installation on NVIDIA Jetson

This guide covers installing and running SkyGuard on NVIDIA Jetson devices (Jetson Orin Nano, Jetson Orin NX, Jetson AGX Orin, etc.).

## Overview

NVIDIA Jetson devices provide significant advantages over Raspberry Pi for AI workloads:
- **GPU Acceleration**: Built-in NVIDIA GPU with CUDA support
- **Better Performance**: Faster inference times, higher frame rates
- **No Overheating**: Better thermal management than Raspberry Pi 5
- **More Memory**: Typically more RAM available

## Prerequisites

1. **NVIDIA Jetson device** (Jetson Orin Nano recommended)
2. **JetPack 5.x** installed (or JetPack 4.x with appropriate PyTorch version)
3. **Python 3.8+** (usually pre-installed with JetPack)
4. **Camera** (USB webcam or CSI camera)
5. **Internet connection** for downloading dependencies

## Installation Steps

### Step 1: Install PyTorch for Jetson

**IMPORTANT**: PyTorch must be installed from NVIDIA's repository, not from PyPI.

#### For JetPack 5.x (Python 3.8+)

1. Check your JetPack version:
   ```bash
   cat /etc/nv_tegra_release
   ```  Note: google the release version or run 'sudo apt show nvidia-jetpack' to see your jetpack version

2. Install PyTorch from NVIDIA's repository:
   ```bash
   # For JetPack 5.1.2 (example - check for latest version) 
   wget https://nvidia.box.com/shared/static/[LATEST_VERSION]/torch-2.1.0-cp38-cp38-linux_aarch64.whl
   pip3 install torch-2.1.0-cp38-cp38-linux_aarch64.whl
   
   # Install torchvision
   pip3 install torchvision
   ```
    Check the latest version at - https://pypi.jetson-ai-lab.io/jp6/cu126 or
   you can start with https://developer.download.nvidia.com/compute/redist/jp/ and click through your jetpack version
 

4. Verify PyTorch installation with CUDA:
   ```bash
   python3 -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}'); print(f'CUDA device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')"
   ```

   You should see:
   ```
   PyTorch: 2.1.0
   CUDA available: True
   CUDA device: NVIDIA Tegra
   ```

#### For JetPack 4.x

Follow similar steps but use the appropriate PyTorch version for JetPack 4.x from NVIDIA's repository.

### Step 2: Install System Dependencies

```bash
sudo apt update
sudo apt upgrade -y

# Install build tools and dependencies
sudo apt install -y \
    python3-pip \
    python3-dev \
    git \
    wget \
    curl \
    build-essential \
    cmake \
    pkg-config \
    libjpeg-dev \
    libtiff5-dev \
    libpng-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev
```

### Step 3: Clone SkyGuard Repository

```bash
cd ~
git clone https://github.com/jad3tx/SkyGuard.git
cd SkyGuard
```

### Step 4: Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
```

### Step 5: Install SkyGuard Dependencies

The installation script will automatically detect Jetson and use the appropriate requirements file:

```bash
./scripts/install.sh
```

Or manually:

```bash
# Install Jetson-specific requirements (PyTorch should already be installed)
pip install -r requirements-jetson.txt
```

**Note**: If you see warnings about PyTorch, that's normal - PyTorch should already be installed from Step 1.

### Step 6: Configure SkyGuard

```bash
source venv/bin/activate
python -m skyguard.setup.configure
```

The configuration wizard will:
- Detect your camera
- Set up detection parameters
- Configure notifications (optional)
- Set up storage paths

### Step 7: Test Installation

Test that GPU acceleration is working:

```bash
source venv/bin/activate
python3 -c "
from skyguard.utils.platform import get_platform_detector
detector = get_platform_detector()
info = detector.get_platform_info()
print(f'Platform: {info[\"name\"]}')
print(f'GPU Available: {info[\"is_gpu_available\"]}')
print(f'Recommended Device: {detector.get_recommended_device()}')
"
```

You should see:
```
Platform: NVIDIA Jetson Orin Nano
GPU Available: True
Recommended Device: cuda:0
```

## Running SkyGuard on Jetson

### Start the System

```bash
cd ~/SkyGuard
source venv/bin/activate
./scripts/start_skyguard.sh
```

Or run manually:

```bash
# Start main detection system
python -m skyguard.main --config config/skyguard.yaml

# In another terminal, start web portal
python scripts/start_web_portal.py --host 0.0.0.0 --port 8080
```

### Access Web Portal

Open your browser and navigate to:
```
http://<JETSON_IP_ADDRESS>:8080
```

## Performance Optimization

### 1. Enable Maximum Performance Mode

```bash
sudo nvpmodel -m 0  # Maximum performance mode
sudo jetson_clocks  # Set clocks to maximum
```

### 2. Monitor GPU Usage

```bash
# Monitor GPU usage in real-time
watch -n 1 sudo tegrastats
```

### 3. Adjust Detection Settings

Edit `config/skyguard.yaml` to optimize for Jetson:

```yaml
ai:
  input_size: 1080  # Can use higher resolution on Jetson
  confidence_threshold: 0.6
  
system:
  detection_interval: 1  # Can run faster on Jetson (was 2 for Pi)
  
camera:
  fps: 30  # Can handle higher FPS on Jetson
```

### 4. Use TensorRT (Optional)

For even better performance, you can convert YOLO models to TensorRT:

```bash
# This is advanced - see Ultralytics documentation for TensorRT export
# The system will automatically use GPU acceleration with PyTorch
```

## Troubleshooting

### PyTorch CUDA Not Available

If `torch.cuda.is_available()` returns `False`:

1. Verify PyTorch was installed from NVIDIA's repository (not PyPI)
2. Check JetPack version compatibility
3. Reinstall PyTorch following Step 1

### Camera Not Detected

1. Check camera connection:
   ```bash
   ls -la /dev/video*
   ```

2. Test camera with OpenCV:
   ```bash
   python3 scripts/diagnose_camera.py
   ```

3. Ensure user is in `video` group:
   ```bash
   sudo usermod -a -G video $USER
   # Log out and back in for changes to take effect
   ```

### Overheating (Rare on Jetson)

Jetson devices have better thermal management than Raspberry Pi, but if overheating occurs:

1. Check thermal status:
   ```bash
   cat /sys/class/thermal/thermal_zone*/temp
   ```

2. Reduce detection frequency in `config/skyguard.yaml`:
   ```yaml
   system:
     detection_interval: 2  # Increase interval
   ```

3. Lower camera FPS:
   ```yaml
   camera:
     fps: 15  # Reduce FPS
   ```

### Low Inference Performance

1. Verify GPU is being used:
   ```bash
   # Check GPU utilization
   sudo tegrastats
   ```

2. Ensure model is using CUDA:
   - Check logs for "Jetson platform detected - using GPU acceleration"
   - Verify `device: cuda:0` in logs

3. Use smaller model if needed:
   ```yaml
   ai:
     model_path: models/yolo11n-seg.pt  # Nano model (fastest)
   ```

## Comparison: Jetson vs Raspberry Pi

| Feature | Raspberry Pi 5 | Jetson Orin Nano |
|---------|----------------|------------------|
| Inference Speed | ~100-200ms | ~20-50ms |
| Max FPS | ~10-15 | ~30+ |
| GPU Acceleration | No | Yes (CUDA) |
| Thermal Issues | Common | Rare |
| Power Consumption | Lower | Higher |
| Cost | Lower | Higher |

## Additional Resources

- [NVIDIA Jetson Developer Forums](https://forums.developer.nvidia.com/)
- [PyTorch for Jetson](https://forums.developer.nvidia.com/t/pytorch-for-jetson/)
- [Ultralytics YOLO Documentation](https://docs.ultralytics.com/)
- [SkyGuard GitHub Repository](https://github.com/jad3tx/SkyGuard)

## Support

If you encounter issues specific to Jetson:

1. Check the [SkyGuard Issues](https://github.com/jad3tx/SkyGuard/issues) on GitHub
2. Verify your PyTorch installation with CUDA support
3. Check Jetson system logs: `dmesg | tail -50`
4. Verify camera permissions and device access

---

**Note**: This installation guide assumes JetPack 5.x. For JetPack 4.x, use the appropriate PyTorch version from NVIDIA's repository. Always check the [NVIDIA Developer Forums](https://forums.developer.nvidia.com/t/pytorch-for-jetson/) for the latest PyTorch installation instructions.

