#!/bin/bash
# SkyGuard Installation Script
# Supports Raspberry Pi, NVIDIA Jetson, and other Linux platforms

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🛡️  SkyGuard Installation${NC}"
echo "================================"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Platform detection function
detect_platform() {
    local platform="unknown"
    local requirements_file="requirements.txt"
    
    # Check for Jetson
    if [ -f "/etc/nv_tegra_release" ] || [ -n "$JETSON_VERSION" ]; then
        platform="jetson"
        requirements_file="requirements-jetson.txt"
        echo -e "${GREEN}✅ NVIDIA Jetson detected${NC}"
    elif [ -f "/proc/device-tree/model" ]; then
        model=$(cat /proc/device-tree/model 2>/dev/null || echo "")
        if echo "$model" | grep -qi "jetson\|tegra"; then
            platform="jetson"
            requirements_file="requirements-jetson.txt"
            echo -e "${GREEN}✅ NVIDIA Jetson detected: $model${NC}"
        elif echo "$model" | grep -qi "raspberry pi"; then
            platform="raspberry_pi"
            requirements_file="requirements-pi.txt"
            echo -e "${GREEN}✅ Raspberry Pi detected: $model${NC}"
        fi
    elif [ -f "/etc/os-release" ]; then
        if grep -qi "raspbian\|raspberry" /etc/os-release 2>/dev/null; then
            platform="raspberry_pi"
            requirements_file="requirements-pi.txt"
            echo -e "${GREEN}✅ Raspberry Pi detected${NC}"
        fi
    fi
    
    echo "$requirements_file"
}

echo -e "${BLUE}📦 Step 1: Updating system packages...${NC}"
sudo apt update
sudo apt upgrade -y

echo -e "${BLUE}📦 Step 2: Installing system dependencies...${NC}"
# Install core dependencies (required)
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    git \
    gh \
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

# Install BLAS/LAPACK library (try openblas first, fallback to atlas if needed)
echo -e "${BLUE}Installing BLAS/LAPACK library...${NC}"
if sudo apt install -y libopenblas-dev 2>/dev/null; then
    echo -e "${GREEN}✅ libopenblas-dev installed${NC}"
else
    echo -e "${YELLOW}⚠️  libopenblas-dev not available, trying libatlas-base-dev...${NC}"
    sudo apt install -y libatlas-base-dev || echo -e "${YELLOW}⚠️  BLAS/LAPACK library not installed (may affect NumPy performance)${NC}"
fi

# Detect platform and select appropriate requirements file
REQUIREMENTS_FILE=$(detect_platform)

# Check for system PyTorch on Jetson
USE_SYSTEM_SITE_PACKAGES=false
if [ "$REQUIREMENTS_FILE" = "requirements-jetson.txt" ]; then
    echo -e "${BLUE}📦 Step 3a: Checking PyTorch installation for Jetson...${NC}"
    
    # Check if PyTorch is installed system-wide
    if python3 -c "import torch; print('CUDA' if torch.cuda.is_available() else 'CPU')" 2>/dev/null | grep -q "CUDA"; then
        echo -e "${GREEN}✅ Found CUDA-enabled PyTorch in system${NC}"
        USE_SYSTEM_SITE_PACKAGES=true
    elif python3 -c "import torch" 2>/dev/null; then
        echo -e "${YELLOW}⚠️  Found PyTorch but CUDA not available - will use system packages anyway${NC}"
        USE_SYSTEM_SITE_PACKAGES=true
    else
        echo -e "${YELLOW}⚠️  No system PyTorch found${NC}"
        echo -e "${YELLOW}   IMPORTANT: PyTorch for Jetson should be installed from NVIDIA's repository!${NC}"
        echo -e "${YELLOW}   See: https://forums.developer.nvidia.com/t/pytorch-for-jetson/${NC}"
        echo ""
        echo -e "${YELLOW}   Quick install (example for JetPack 5.x):${NC}"
        echo -e "${YELLOW}   wget https://nvidia.box.com/shared/static/.../torch-2.x.x-cp3x-cp3x-linux_aarch64.whl${NC}"
        echo -e "${YELLOW}   pip install torch-2.x.x-cp3x-cp3x-linux_aarch64.whl${NC}"
        echo ""
        read -p "Press Enter to continue (will create venv without system packages), or Ctrl+C to cancel..."
    fi
fi

echo -e "${BLUE}📦 Step 3: Creating Python virtual environment...${NC}"
if [ ! -d "venv" ]; then
    if [ "$USE_SYSTEM_SITE_PACKAGES" = "true" ]; then
        echo -e "${CYAN}   Creating venv with system site packages (to use CUDA PyTorch)${NC}"
        python3 -m venv --system-site-packages venv
    else
        python3 -m venv venv
    fi
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${YELLOW}⚠️  Virtual environment already exists${NC}"
    if [ "$USE_SYSTEM_SITE_PACKAGES" = "true" ]; then
        echo -e "${YELLOW}   Note: If venv was created without --system-site-packages, you may need to recreate it${NC}"
    fi
fi

echo -e "${BLUE}📦 Step 4: Activating virtual environment and installing Python packages...${NC}"
source venv/bin/activate

# Upgrade pip first
pip install --upgrade pip

# Install dependencies
if [ -f "$REQUIREMENTS_FILE" ]; then
    echo -e "${BLUE}Installing from $REQUIREMENTS_FILE...${NC}"
    if [ "$REQUIREMENTS_FILE" = "requirements-pi.txt" ]; then
        echo -e "${YELLOW}Note: You may be prompted to install:${NC}"
        echo -e "${YELLOW}  - Raspberry Pi hardware dependencies (RPi.GPIO) - Answer 'yes' to enable GPIO features${NC}"
        echo -e "${YELLOW}  - Notification dependencies (Twilio, Pushbullet) - Answer 'yes' to enable notifications${NC}"
    fi
    
    # For Jetson with system PyTorch, filter out torch packages
    if [ "$USE_SYSTEM_SITE_PACKAGES" = "true" ] && [ "$REQUIREMENTS_FILE" = "requirements-jetson.txt" ]; then
        echo -e "${CYAN}   Filtering out torch/torchvision (using system CUDA versions)${NC}"
        FILTERED_REQ=$(mktemp)
        grep -v -E "^(torch|torchvision|torchaudio)" "$REQUIREMENTS_FILE" > "$FILTERED_REQ" 2>/dev/null || cp "$REQUIREMENTS_FILE" "$FILTERED_REQ"
        pip install -r "$FILTERED_REQ"
        rm -f "$FILTERED_REQ"
    else
        pip install -r "$REQUIREMENTS_FILE"
    fi
else
    echo -e "${YELLOW}⚠️  $REQUIREMENTS_FILE not found, using requirements.txt...${NC}"
    if [ "$USE_SYSTEM_SITE_PACKAGES" = "true" ] && [ "$REQUIREMENTS_FILE" = "requirements-jetson.txt" ]; then
        FILTERED_REQ=$(mktemp)
        grep -v -E "^(torch|torchvision|torchaudio)" requirements.txt > "$FILTERED_REQ" 2>/dev/null || cp requirements.txt "$FILTERED_REQ"
        pip install -r "$FILTERED_REQ"
        rm -f "$FILTERED_REQ"
    else
        pip install -r requirements.txt
    fi
fi

echo -e "${BLUE}📦 Step 5: Making scripts executable...${NC}"
chmod +x scripts/*.sh 2>/dev/null || true
chmod +x scripts/*.py 2>/dev/null || true

echo -e "${BLUE}📦 Step 6: Creating necessary directories...${NC}"
mkdir -p logs
mkdir -p data/detections
mkdir -p models

echo ""
echo -e "${GREEN}✅ Installation complete!${NC}"
echo ""
echo -e "${BLUE}📋 Next steps:${NC}"
echo "1. Configure the system:"
echo "   source venv/bin/activate"
echo "   python -m skyguard.setup.configure"
echo ""
echo "2. Start SkyGuard:"
echo "   ./scripts/start_skyguard.sh"
echo ""
echo "3. Access the web portal:"
echo "   Open http://<PI_IP_ADDRESS>:8080 in your browser"
echo ""

