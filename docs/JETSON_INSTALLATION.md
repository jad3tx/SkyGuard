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

### Step 1: Install PyTorch for Jetson

**IMPORTANT**: PyTorch must be installed from NVIDIA's repository, not from PyPI.

#### For JetPack 6.1 (Python 3.10+)

1. Check your JetPack version:
   ```bash
   cat /etc/nv_tegra_release
   # Or run:
   sudo apt show nvidia-jetpack
   ```

2. Install PyTorch from NVIDIA's repository:
   ```bash
   # For JetPack 6.1, use the CUDA-enabled PyTorch wheel:
   wget https://developer.download.nvidia.com/compute/redist/jp/v61/pytorch/torch-2.5.0a0+872d972e41.nv24.08.17622132-cp310-cp310-linux_aarch64.whl
   pip3 install torch-2.5.0a0+872d972e41.nv24.08.17622132-cp310-cp310-linux_aarch64.whl
   
   # Install torchvision from NVIDIA Jetson AI Lab (compatible with PyTorch 2.5.0)
   wget https://pypi.jetson-ai-lab.io/jp6/cu126/+f/907/c4c1933789645/torchvision-0.23.0-cp310-cp310-linux_aarch64.whl
   pip3 install torchvision-0.23.0-cp310-cp310-linux_aarch64.whl --no-deps
   rm -f torchvision-0.23.0-cp310-cp310-linux_aarch64.whl
   
   # Note: If the wheel URL doesn't work, you can build from source:
   #   cd ~/SkyGuard
   #   ./scripts/build_torchvision_jetson.sh

   # Note: numpy 1.26.0 will be installed in the venv (see requirements-jetson.txt)
   # If you encounter numpy versioning issues, ensure numpy < 2.0:
   python3 -m pip install --user --force-reinstall "numpy==1.26.0"
   ```
   
   **Note**: For JetPack 6.1, Python 3.10+ is typically used. Check the exact Python version:
   ```bash
   python3 --version
   ```
   
   Then download the matching PyTorch wheel (cp310 for Python 3.10, cp311 for Python 3.11, etc.)
 

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

**IMPORTANT**: For Jetson, you must create the virtual environment with `--system-site-packages` to access system-installed CUDA PyTorch:

```bash
python3 -m venv --system-site-packages venv
source venv/bin/activate
pip install --upgrade pip
```

**Note**: The installation script (`./scripts/install.sh`) will automatically create the venv with this flag if it detects Jetson and system PyTorch.

### Step 5: Install SkyGuard Dependencies

The installation script will automatically detect Jetson and use the appropriate requirements file:

```bash
./scripts/install.sh
```

The script will:
- Detect that you're on a Jetson device
- Check for system-installed CUDA PyTorch
- Create a virtual environment with `--system-site-packages` to access system PyTorch
- Filter out torch/torchvision from requirements (to avoid installing non-CUDA versions)
- Install all other dependencies

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

### Virtual Environment Not Using CUDA PyTorch

If your virtual environment was created without `--system-site-packages`, it won't be able to access the system-installed CUDA PyTorch. You'll see errors like:
- `torch.cuda.is_available()` returns `False`
- Model runs on CPU instead of GPU

**Fix Option 1: Use the Fix Script (Recommended)**
```bash
cd ~/SkyGuard
./scripts/fix_jetson_venv.sh
```

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

**Note**: This installation guide is optimized for JetPack 6.1. For other JetPack versions:
- **JetPack 6.x**: Use Python 3.10+ wheels from https://pypi.jetson-ai-lab.io/jp6/
- **JetPack 5.x**: Use Python 3.8+ wheels from https://pypi.jetson-ai-lab.io/jp5/
- **JetPack 4.x**: Use the appropriate PyTorch version from NVIDIA's repository

Always check the [NVIDIA Developer Forums](https://forums.developer.nvidia.com/t/pytorch-for-jetson/) for the latest PyTorch installation instructions.

