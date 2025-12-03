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
2. **JetPack 6.1** installed (or JetPack 5.x/4.x with appropriate PyTorch version)
3. **Python 3.10+** (usually pre-installed with JetPack 6.1)
4. **Camera** (USB webcam or CSI camera)
5. **Internet connection** for downloading dependencies

## Installation Steps

### Step 1: Install cuSPARSELt 0.7.1

**IMPORTANT**: cuSPARSELt is required for PyTorch on JetPack 6.1.

1. Visit the [NVIDIA cuSPARSELt Downloads](https://developer.nvidia.com/cusparselt/downloads)
2. Download cuSPARSELt 0.7.1 with these settings:
   - **Target OS:** Linux
   - **Target Architecture:** aarch64-jetson
   - **Compilation:** Native
   - **Distribution:** Ubuntu
   - **Target Version:** 22.04
   - **Target Type:** deb (local)
3. Install the downloaded package:
   ```bash
   sudo dpkg -i <downloaded-cusparselt-package>.deb
   sudo apt-get install -f
   ```

### Step 2: Install PyTorch for Jetson

**IMPORTANT**: PyTorch must be installed from NVIDIA's repository, not from PyPI.

#### For JetPack 6.1 (Python 3.10+)

1. Check your JetPack version:
   ```bash
   cat /etc/nv_tegra_release
   ```

2. Download PyTorch wheel from NVIDIA Embedded Downloads:
   - Visit: https://developer.nvidia.com/embedded/downloads
   - Search for "PyTorch"
   - Download the wheel file specifically for JetPack 6.1
   - Ensure it matches your Python version (typically Python 3.10)
   - The wheel file will have a name similar to `torch-2.x.x+nv24.xx-cp310-cp310-linux_aarch64.whl`

3. Install the downloaded PyTorch wheel:
   ```bash
   pip3 install <downloaded-pytorch-wheel-file>.whl
   ```

4. Verify PyTorch installation with CUDA:
   ```bash
   python3 -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}'); print(f'CUDA device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')"
   ```

   You should see:
   ```
   PyTorch: 2.5.0a0+872d972e41.nv24.08.17622132
   CUDA available: True
   CUDA device: NVIDIA Tegra
   ```

### Step 3: Build and Install TorchVision

TorchVision must be built from source to match your PyTorch version.

1. Install TorchVision build dependencies:
   ```bash
   sudo apt-get install -y \
       libjpeg-dev \
       zlib1g-dev \
       libpython3-dev \
       libopenblas-dev \
       libavcodec-dev \
       libavformat-dev \
       libswscale-dev
   ```

2. Build TorchVision 0.20.0 from source:
   ```bash
   # Clone TorchVision repository
   git clone --branch v0.20.0 https://github.com/pytorch/vision torchvision
   cd torchvision
   
   # Set the build version
   export BUILD_VERSION=0.20.0
   
   # Build and install TorchVision
   python3 setup.py install --user
   
   # Return to parent directory (important!)
   cd ../
   
   # Install Pillow compatibility (if needed)
   pip3 install 'pillow<7' --user
   ```

   **Note**: The build process will take 10-30 minutes. Alternatively, you can use the provided build script:
   ```bash
   cd ~/SkyGuard
   ./scripts/build_torchvision_jetson.sh
   ```

3. Verify TorchVision installation:
   ```bash
   python3 -c "import torchvision; print(f'TorchVision {torchvision.__version__} installed successfully')"
   ```

#### For JetPack 4.x

Follow similar steps but use the appropriate PyTorch version for JetPack 4.x from NVIDIA's repository.

### Step 4: Install System Dependencies

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

### Step 5: Clone SkyGuard Repository

```bash
cd ~
git clone https://github.com/jad3tx/SkyGuard.git
cd SkyGuard
```

### Step 6: Create Virtual Environment

**IMPORTANT**: For Jetson, you must create the virtual environment with `--system-site-packages` to access system-installed CUDA PyTorch:

```bash
python3 -m venv --system-site-packages venv
source venv/bin/activate
pip install --upgrade pip
```

**Note**: The installation script (`./scripts/install.sh`) will automatically create the venv with this flag if it detects Jetson and system PyTorch.

### Step 7: Install SkyGuard Dependencies

The installation script will automatically detect Jetson and install everything:

```bash
./scripts/install.sh
```

Or use the Jetson-specific script directly:

```bash
./scripts/install-jetson.sh
```

The script will:
- Install cuSPARSELt (if not already installed)
- Install PyTorch from NVIDIA wheel (if not already installed)
- Build and install TorchVision from source (if not already installed)
- Create a virtual environment with `--system-site-packages` to access system PyTorch
- Filter out torch/torchvision from requirements (to avoid installing non-CUDA versions)
- Install all other dependencies

**Note**: The installation script will prompt you for the PyTorch wheel file path if PyTorch is not already installed.

Or manually:

```bash
# Create venv with system site packages (IMPORTANT for CUDA PyTorch!)
python3 -m venv --system-site-packages venv
source venv/bin/activate

# Install Jetson-specific requirements (PyTorch excluded - uses system version)
pip install -r requirements-jetson.txt
```

**Important Notes**:
- The virtual environment **must** be created with `--system-site-packages` to access system-installed CUDA PyTorch
- If you see warnings about PyTorch, that's normal - PyTorch should already be installed from Step 1
- If your venv was created without `--system-site-packages`, see "Fixing Virtual Environment" below

### Step 8: Configure SkyGuard

```bash
source venv/bin/activate
python -m skyguard.setup.configure
```

The configuration wizard will:
- Detect your camera
- Set up detection parameters
- Configure notifications (optional)
- Set up storage paths

### Step 9: Test Installation

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

### Virtual Environment Not Using CUDA PyTorch

If your virtual environment was created without `--system-site-packages`, it won't be able to access the system-installed CUDA PyTorch. You'll see errors like:
- `torch.cuda.is_available()` returns `False`
- Model runs on CPU instead of GPU

**Fix Option 1: Re-run Installation Script (Recommended)**
```bash
cd ~/SkyGuard
./scripts/install-jetson.sh
```

The installation script will automatically detect and fix the virtual environment configuration.

**Fix Option 2: Manual Fix**
```bash
cd ~/SkyGuard

# Backup current venv
mv venv venv_backup

# Create new venv with system site packages
python3 -m venv --system-site-packages venv
source venv/bin/activate

# Reinstall dependencies (excluding torch)
pip install --upgrade pip
grep -v -E "^(torch|torchvision|torchaudio)" requirements-jetson.txt > /tmp/req_filtered.txt
pip install -r /tmp/req_filtered.txt
rm /tmp/req_filtered.txt

# Verify CUDA is working
python3 -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

**Verify Fix:**
```bash
source venv/bin/activate
python3 -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}'); print(f'Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')"
```

You should see:
```
CUDA available: True
Device: NVIDIA Tegra
```

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

## Starting Services as the Correct User

**Important**: SkyGuard services must run as the user who installed PyTorch (typically `jad3` on Jetson, `pi` on Raspberry Pi), not as root. This is because PyTorch is installed in user site-packages (`~/.local/lib/python3.10/site-packages/`), which root cannot access.

### Using the Start Scripts (Recommended)

The start scripts automatically detect if they're running as root and switch to the correct user:

```bash
# The script will automatically use the correct user
sudo ./scripts/start_skyguard.sh --background

# Or run as the user directly (no sudo needed)
./scripts/start_skyguard.sh --background
```

### Manual Startup (Without Scripts)

If you need to start services manually, use one of these methods:

#### Method 1: Switch to the User First

```bash
# Switch to the platform user (jad3 on Jetson, pi on RPi)
su - jad3  # or 'su - pi' on Raspberry Pi

# Navigate to SkyGuard directory
cd ~/SkyGuard

# Activate virtual environment
source venv/bin/activate

# Start main system in background
nohup python3 -m skyguard.main --config config/skyguard.yaml > logs/main.log 2>&1 &

# Start web portal in background
nohup python3 skyguard/web/app.py > logs/web.log 2>&1 &
```

#### Method 2: Use `runuser` (When Running as Root)

```bash
# Start main system as user jad3
runuser -l jad3 -c "cd ~/SkyGuard && source venv/bin/activate && nohup python3 -m skyguard.main --config config/skyguard.yaml > logs/main.log 2>&1 &"

# Start web portal as user jad3
runuser -l jad3 -c "cd ~/SkyGuard && source venv/bin/activate && nohup python3 skyguard/web/app.py > logs/web.log 2>&1 &"
```

#### Method 3: Use `sudo -u` (Alternative)

```bash
# Start main system
sudo -u jad3 bash -c "cd ~/SkyGuard && source venv/bin/activate && nohup python3 -m skyguard.main --config config/skyguard.yaml > logs/main.log 2>&1 &"

# Start web portal
sudo -u jad3 bash -c "cd ~/SkyGuard && source venv/bin/activate && nohup python3 skyguard/web/app.py > logs/web.log 2>&1 &"
```

### Verifying Services Are Running as the Correct User

```bash
# Check which user the processes are running as
ps aux | grep skyguard

# Should show processes owned by 'jad3' (or 'pi' on RPi), not 'root'
```

### Troubleshooting

**Problem**: Services start but can't load PyTorch models
- **Solution**: Check that services are running as the correct user (not root)
- **Fix**: Stop services and restart using one of the methods above

**Problem**: "ModuleNotFoundError: No module named 'torch'"
- **Solution**: Ensure you're running as the user who installed PyTorch
- **Fix**: Use `runuser` or `su` to switch to the correct user before starting

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
5. Ensure services are running as the correct user (not root)

---

**Note**: This installation guide is optimized for JetPack 6.1. The installation process follows the guide at: https://github.com/hamzashafiq28/pytorch-jetson-jp6.1

For other JetPack versions:
- **JetPack 6.x**: Use Python 3.10+ wheels from NVIDIA Embedded Downloads
- **JetPack 5.x**: Use Python 3.8+ wheels from NVIDIA Embedded Downloads
- **JetPack 4.x**: Use the appropriate PyTorch version from NVIDIA's repository

Always check the [NVIDIA Developer Forums](https://forums.developer.nvidia.com/t/pytorch-for-jetson/) for the latest PyTorch installation instructions.

