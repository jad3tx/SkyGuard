#!/bin/bash
# SkyGuard Installation Script for NVIDIA Jetson
# Installs PyTorch and TorchVision from NVIDIA wheels for JetPack 6.1
# Based on: https://github.com/hamzashafiq28/pytorch-jetson-jp6.1
#
# Hardcoded versions (known working combination for JetPack 6.1):
#   - JetPack: 6.1
#   - cuSPARSELt: 0.7.1
#   - PyTorch: 2.5.0a0+872d972e41.nv24.08.17622132
#   - TorchVision: 0.20.0
#   - Python: 3.10+ (recommended)

# Don't use set -e - we want to handle errors gracefully
set -o pipefail  # Only fail on pipe errors, not individual commands

# Source common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/install-common.sh"

echo -e "${BLUE}🛡️  SkyGuard Installation for NVIDIA Jetson${NC}"
echo "=============================================="
echo ""

cd "$PROJECT_ROOT"

# Platform-specific variables
PLATFORM_USER="jad3"
REQUIREMENTS_FILE="requirements-jetson.txt"

# Hardcoded versions for JetPack 6.1 (known working combination)
JETPACK_VERSION="6.1"
CUSPARSELT_VERSION="0.7.1"
PYTORCH_VERSION="2.5.0a0+872d972e41.nv24.08.17622132"
TORCHVISION_VERSION="0.20.0"
PYTHON_VERSION_REQUIRED="3.10"

# PyTorch wheel URL pattern (will be constructed based on Python version)
# Base URL: https://developer.download.nvidia.com/compute/redist/jp/v61/pytorch/
PYTORCH_BASE_URL="https://developer.download.nvidia.com/compute/redist/jp/v61/pytorch"

# Detect platform username (fallback if jad3 doesn't exist)
if ! id "$PLATFORM_USER" &>/dev/null; then
    PLATFORM_USER=$(whoami)
    echo -e "${YELLOW}⚠️  User 'jad3' not found, using current user: $PLATFORM_USER${NC}"
fi
echo -e "${CYAN}   Platform user: $PLATFORM_USER${NC}"

# Check if we're on Jetson
if [ ! -f "/etc/nv_tegra_release" ]; then
    echo -e "${RED}❌ This script is for NVIDIA Jetson devices only${NC}"
    exit 1
fi

# Detect JetPack version
DETECTED_JETPACK=$(cat /etc/nv_tegra_release 2>/dev/null | head -1 | cut -d' ' -f8 || echo "unknown")
echo -e "${CYAN}   Detected JetPack version: $DETECTED_JETPACK${NC}"
echo -e "${CYAN}   Target JetPack version: $JETPACK_VERSION${NC}"

# Detect Python version
PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1 || echo "unknown")
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
PYTHON_TAG="cp${PYTHON_MAJOR}${PYTHON_MINOR}"

echo -e "${CYAN}   Python version: $PYTHON_VERSION ($PYTHON_TAG)${NC}"

# Verify Python version compatibility
if [ "$PYTHON_MAJOR" != "3" ] || [ "$PYTHON_MINOR" -lt 10 ]; then
    echo -e "${YELLOW}⚠️  Python $PYTHON_VERSION_REQUIRED+ recommended for JetPack 6.1${NC}"
    echo -e "${YELLOW}   Continuing with Python $PYTHON_VERSION...${NC}"
fi

# Construct PyTorch wheel filename
PYTORCH_WHEEL_NAME="torch-${PYTORCH_VERSION}-${PYTHON_TAG}-${PYTHON_TAG}-linux_aarch64.whl"
PYTORCH_WHEEL_URL="${PYTORCH_BASE_URL}/${PYTORCH_WHEEL_NAME}"

# Filter torch packages from requirements file for Jetson
filter_jetson_requirements() {
    local req_file="$1"
    local filtered_file="${req_file}.filtered"
    
    # Create filtered requirements file excluding torch/torchvision/torchaudio
    grep -v -E "^[[:space:]#]*(torch|torchvision|torchaudio)(\[[^\]]+\])?[[:space:]]*[>=<~!#]" "$req_file" > "$filtered_file" 2>/dev/null || cp "$req_file" "$filtered_file"
    echo "$filtered_file"
}

# Install system dependencies
install_system_dependencies

# Step 1: Install cuSPARSELt 0.7.1
echo -e "${BLUE}📦 Step 1: Installing cuSPARSELt $CUSPARSELT_VERSION...${NC}"
echo -e "${CYAN}   cuSPARSELt is required for PyTorch on JetPack $JETPACK_VERSION${NC}"

# Check if cuSPARSELt is already installed
if dpkg -l | grep -q cusparselt; then
    INSTALLED_VERSION=$(dpkg -l | grep cusparselt | awk '{print $3}' | head -1)
    echo -e "${GREEN}   ✅ cuSPARSELt already installed: $INSTALLED_VERSION${NC}"
else
    echo -e "${YELLOW}   cuSPARSELt $CUSPARSELT_VERSION is required but not installed${NC}"
    echo -e "${CYAN}   Download from: https://developer.nvidia.com/cusparselt/downloads${NC}"
    echo -e "${CYAN}   Settings: Linux, aarch64-jetson, Native, Ubuntu 22.04, deb (local)${NC}"
    echo ""
    read -p "Press Enter after installing cuSPARSELt, or Ctrl+C to cancel..."
    
    # Verify cuSPARSELt installation
    if ! dpkg -l | grep -q cusparselt; then
        echo -e "${YELLOW}⚠️  cuSPARSELt not detected. Installation may fail.${NC}"
    else
        INSTALLED_VERSION=$(dpkg -l | grep cusparselt | awk '{print $3}' | head -1)
        echo -e "${GREEN}✅ cuSPARSELt installed: $INSTALLED_VERSION${NC}"
    fi
fi

# Step 2: Install PyTorch from NVIDIA wheel
echo -e "${BLUE}📦 Step 2: Installing PyTorch $PYTORCH_VERSION from NVIDIA wheel...${NC}"

# Check if PyTorch is already installed
PYTORCH_INSTALLED=false
if python3 -c "import torch" 2>/dev/null; then
    TORCH_VERSION=$(python3 -c "import torch; print(torch.__version__)" 2>/dev/null || echo "")
    if echo "$TORCH_VERSION" | grep -q "nv24\|nv23"; then
        echo -e "${GREEN}   ✅ NVIDIA PyTorch already installed: $TORCH_VERSION${NC}"
        if python3 -c "import torch; print('CUDA' if torch.cuda.is_available() else 'CPU')" 2>/dev/null | grep -q "CUDA"; then
            echo -e "${GREEN}   ✅ CUDA is available${NC}"
            # Check if it's the correct version
            if echo "$TORCH_VERSION" | grep -q "$PYTORCH_VERSION"; then
                echo -e "${GREEN}   ✅ Correct version for JetPack $JETPACK_VERSION${NC}"
                PYTORCH_INSTALLED=true
            else
                echo -e "${YELLOW}   ⚠️  Version mismatch. Expected: $PYTORCH_VERSION, Found: $TORCH_VERSION${NC}"
                echo -e "${CYAN}   Will install correct version...${NC}"
            fi
        else
            echo -e "${YELLOW}   ⚠️  PyTorch installed but CUDA not available${NC}"
        fi
    else
        echo -e "${YELLOW}   ⚠️  Non-NVIDIA PyTorch detected: $TORCH_VERSION${NC}"
        echo -e "${CYAN}   Will install NVIDIA version...${NC}"
    fi
fi

if [ "$PYTORCH_INSTALLED" = false ]; then
    DOWNLOAD_DIR="/tmp"
    PYTORCH_WHEEL_PATH="$DOWNLOAD_DIR/$PYTORCH_WHEEL_NAME"
    
    echo -e "${CYAN}   Target wheel: $PYTORCH_WHEEL_NAME${NC}"
    echo -e "${CYAN}   Attempting to download from NVIDIA...${NC}"
    
    # Try to download the wheel
    if wget -q --spider "$PYTORCH_WHEEL_URL" 2>/dev/null; then
        echo -e "${CYAN}   Downloading PyTorch wheel...${NC}"
        if wget "$PYTORCH_WHEEL_URL" -O "$PYTORCH_WHEEL_PATH" 2>/dev/null; then
            echo -e "${GREEN}   ✅ Downloaded successfully${NC}"
            PYTORCH_WHEEL="$PYTORCH_WHEEL_PATH"
        else
            echo -e "${YELLOW}   ⚠️  Download failed, will prompt for manual path${NC}"
            PYTORCH_WHEEL=""
        fi
    else
        echo -e "${YELLOW}   ⚠️  Direct download not available${NC}"
        echo -e "${CYAN}   Please download manually from:${NC}"
        echo -e "${CYAN}   https://developer.nvidia.com/embedded/downloads${NC}"
        echo -e "${CYAN}   Search for 'PyTorch' and download wheel for JetPack $JETPACK_VERSION${NC}"
        echo -e "${CYAN}   Expected filename: $PYTORCH_WHEEL_NAME${NC}"
        echo ""
        read -p "Enter path to downloaded PyTorch wheel file: " PYTORCH_WHEEL
    fi
    
    if [ -n "$PYTORCH_WHEEL" ] && [ -f "$PYTORCH_WHEEL" ]; then
        echo -e "${CYAN}   Installing PyTorch from: $PYTORCH_WHEEL${NC}"
        pip3 install "$PYTORCH_WHEEL" || {
            echo -e "${RED}❌ Failed to install PyTorch wheel${NC}"
            exit 1
        }
        echo -e "${GREEN}✅ PyTorch $PYTORCH_VERSION installed${NC}"
        # Clean up downloaded file
        if [ "$PYTORCH_WHEEL" = "$PYTORCH_WHEEL_PATH" ]; then
            rm -f "$PYTORCH_WHEEL_PATH"
        fi
    else
        echo -e "${RED}❌ PyTorch wheel not found: $PYTORCH_WHEEL${NC}"
        echo -e "${YELLOW}   You must install PyTorch manually before continuing.${NC}"
        exit 1
    fi
fi

# Verify PyTorch installation
echo -e "${CYAN}   Verifying PyTorch installation...${NC}"
TORCH_VERSION=$(python3 -c "import torch; print(torch.__version__)" 2>/dev/null || echo "NOT_FOUND")
CUDA_AVAILABLE=$(python3 -c "import torch; print('CUDA' if torch.cuda.is_available() else 'CPU')" 2>/dev/null || echo "NOT_FOUND")

if [ "$CUDA_AVAILABLE" = "CUDA" ]; then
    CUDA_DEVICE=$(python3 -c "import torch; print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A')" 2>/dev/null)
    echo -e "${GREEN}   ✅ PyTorch $TORCH_VERSION with CUDA support${NC}"
    echo -e "${CYAN}   Device: $CUDA_DEVICE${NC}"
else
    echo -e "${RED}❌ PyTorch CUDA not available${NC}"
    echo -e "${YELLOW}   Please verify PyTorch installation${NC}"
    exit 1
fi

# Step 3: Install TorchVision dependencies
echo -e "${BLUE}📦 Step 3: Installing TorchVision build dependencies...${NC}"
sudo apt-get install -y \
    libjpeg-dev \
    zlib1g-dev \
    libpython3-dev \
    libopenblas-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev || {
    echo -e "${YELLOW}⚠️  Some dependencies may have failed to install${NC}"
}

# Step 4: Build and install TorchVision from source
echo -e "${BLUE}📦 Step 4: Building TorchVision from source...${NC}"

# Check if torchvision is already installed and compatible
TORCHVISION_INSTALLED=false
if python3 -c "import torchvision" 2>/dev/null; then
    if python3 -c "import torchvision; from torchvision.ops import nms" 2>/dev/null; then
        TV_VERSION=$(python3 -c "import torchvision; print(torchvision.__version__)" 2>/dev/null || echo "")
        echo -e "${GREEN}   ✅ TorchVision already installed: $TV_VERSION${NC}"
        TORCHVISION_INSTALLED=true
    else
        echo -e "${YELLOW}   ⚠️  TorchVision installed but has compatibility issues${NC}"
        echo -e "${CYAN}   Will rebuild...${NC}"
    fi
fi

if [ "$TORCHVISION_INSTALLED" = false ]; then
    echo -e "${CYAN}   Building TorchVision $TORCHVISION_VERSION (compatible with PyTorch $PYTORCH_VERSION)${NC}"
    echo -e "${CYAN}   This will take 10-30 minutes...${NC}"
    
    # Use the build script if available
    if [ -f "$SCRIPT_DIR/build_torchvision_jetson.sh" ]; then
        chmod +x "$SCRIPT_DIR/build_torchvision_jetson.sh"
        "$SCRIPT_DIR/build_torchvision_jetson.sh" || {
            echo -e "${RED}❌ Failed to build TorchVision${NC}"
            exit 1
        }
    else
        # Manual build process
        BUILD_DIR="/tmp/torchvision_build"
        rm -rf "$BUILD_DIR"
        
        echo -e "${CYAN}   Cloning TorchVision repository (v$TORCHVISION_VERSION)...${NC}"
        git clone --branch v$TORCHVISION_VERSION https://github.com/pytorch/vision.git "$BUILD_DIR"
        cd "$BUILD_DIR"
        
        export BUILD_VERSION=$TORCHVISION_VERSION
        echo -e "${CYAN}   Building TorchVision $TORCHVISION_VERSION...${NC}"
        python3 setup.py install --user || {
            echo -e "${RED}❌ Failed to build TorchVision${NC}"
            cd "$PROJECT_ROOT"
            rm -rf "$BUILD_DIR"
            exit 1
        }
        
        cd "$PROJECT_ROOT"
        rm -rf "$BUILD_DIR"
        
        # Install Pillow compatibility if needed
        pip3 install 'pillow<7' --user 2>/dev/null || true
    fi
    
    echo -e "${GREEN}✅ TorchVision $TORCHVISION_VERSION built and installed${NC}"
fi

# Verify TorchVision installation
echo -e "${CYAN}   Verifying TorchVision installation...${NC}"
if python3 -c "import torchvision; from torchvision.ops import nms" 2>/dev/null; then
    TV_VERSION=$(python3 -c "import torchvision; print(torchvision.__version__)" 2>/dev/null || echo "")
    echo -e "${GREEN}   ✅ TorchVision $TV_VERSION is working${NC}"
    if echo "$TV_VERSION" | grep -q "$TORCHVISION_VERSION"; then
        echo -e "${GREEN}   ✅ Correct version for PyTorch $PYTORCH_VERSION${NC}"
    else
        echo -e "${YELLOW}   ⚠️  Version mismatch. Expected: $TORCHVISION_VERSION, Found: $TV_VERSION${NC}"
    fi
else
    echo -e "${RED}❌ TorchVision verification failed${NC}"
    exit 1
fi

# Step 5: Create virtual environment with system site packages
echo -e "${BLUE}📦 Step 5: Creating Python virtual environment...${NC}"
echo -e "${CYAN}   Creating venv with system site packages to access system PyTorch${NC}"
create_venv "true" "$PROJECT_ROOT/venv"

# Step 6: Install Python dependencies
echo -e "${BLUE}📦 Step 6: Installing Python dependencies...${NC}"

# Activate venv
source venv/bin/activate

# Upgrade pip
upgrade_pip "$PROJECT_ROOT/venv"

# Install dependencies (excluding torch/torchvision which are system-installed)
if [ -f "$REQUIREMENTS_FILE" ]; then
    echo -e "${BLUE}Installing from $REQUIREMENTS_FILE...${NC}"
    
    FILTERED_REQ=$(filter_jetson_requirements "$REQUIREMENTS_FILE")
    echo -e "${CYAN}   Filtered out torch/torchvision/torchaudio (using system CUDA versions)${NC}"
    
    # Install filtered requirements
    INSTALL_SUCCESS=false
    if [ "$(id -u)" -eq 0 ] && [ "$PLATFORM_USER" != "root" ] && id "$PLATFORM_USER" &>/dev/null; then
        if runuser -l "$PLATFORM_USER" -c "cd '$PROJECT_ROOT' && source venv/bin/activate && pip install --no-cache-dir -r '$FILTERED_REQ'"; then
            INSTALL_SUCCESS=true
        fi
        chown -R "$PLATFORM_USER:$PLATFORM_USER" venv 2>/dev/null || true
    else
        if pip install --no-cache-dir -r "$FILTERED_REQ"; then
            INSTALL_SUCCESS=true
        fi
    fi
    
    if [ "$INSTALL_SUCCESS" = false ]; then
        echo -e "${RED}❌ Failed to install some packages${NC}"
        echo -e "${YELLOW}   Continuing anyway...${NC}"
    fi
    
    rm -f "$FILTERED_REQ"
else
    echo -e "${YELLOW}⚠️  $REQUIREMENTS_FILE not found, using requirements.txt...${NC}"
    FILTERED_REQ=$(filter_jetson_requirements "requirements.txt")
    pip install --no-cache-dir -r "$FILTERED_REQ" || {
        echo -e "${RED}❌ Failed to install packages${NC}"
        exit 1
    }
    rm -f "$FILTERED_REQ"
fi

make_scripts_executable
create_directories

# Final verification
echo -e "\n${BLUE}🔍 Final Verification...${NC}"

# Verify PyTorch in venv (should use system version)
TORCH_SOURCE=$(python3 -c "
import sys
import os
try:
    import torch
    torch_path = os.path.abspath(torch.__file__)
    venv_path = os.path.abspath('$PROJECT_ROOT/venv')
    if venv_path in torch_path:
        print('venv')
    else:
        print('system')
    print(torch.__version__)
    print('CUDA' if torch.cuda.is_available() else 'CPU')
except Exception:
    print('error')
" 2>/dev/null || echo "error")

IFS=$'\n' read -r TORCH_LOCATION TORCH_VER CUDA_STATUS <<< "$TORCH_SOURCE"

if [ "$TORCH_LOCATION" = "system" ]; then
    echo -e "${GREEN}✅ PyTorch $TORCH_VER using system installation (correct)${NC}"
    if [ "$CUDA_STATUS" = "CUDA" ]; then
        CUDA_DEVICE=$(python3 -c "import torch; print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A')" 2>/dev/null)
        echo -e "${GREEN}✅ CUDA available: $CUDA_DEVICE${NC}"
    else
        echo -e "${YELLOW}⚠️  CUDA not available${NC}"
    fi
elif [ "$TORCH_LOCATION" = "venv" ]; then
    echo -e "${RED}❌ ERROR: PyTorch is in venv instead of system!${NC}"
    echo -e "${YELLOW}   This should not happen. Please check venv configuration.${NC}"
else
    echo -e "${RED}❌ ERROR: Could not verify PyTorch installation${NC}"
fi

# Verify TorchVision
if python3 -c "import torchvision; from torchvision.ops import nms" 2>/dev/null; then
    TV_VERSION=$(python3 -c "import torchvision; print(torchvision.__version__)" 2>/dev/null || echo "")
    echo -e "${GREEN}✅ TorchVision $TV_VERSION is working${NC}"
else
    echo -e "${RED}❌ TorchVision verification failed${NC}"
fi

# Check critical packages
echo -e "${CYAN}   Checking critical packages...${NC}"
for package in ultralytics opencv-python flask; do
    if python3 -c "import $package" 2>/dev/null; then
        VERSION=$(python3 -c "import $package; print($package.__version__)" 2>/dev/null || echo "installed")
        echo -e "${GREEN}   ✅ $package ($VERSION)${NC}"
    else
        echo -e "${RED}   ❌ $package not found${NC}"
    fi
done

deactivate 2>/dev/null || true

echo ""
echo -e "${GREEN}✅ Installation complete!${NC}"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANT: Reboot your system to ensure all changes take effect:${NC}"
echo -e "${CYAN}   sudo reboot${NC}"
echo ""

print_completion_message "jetson"
