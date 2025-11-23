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

echo -e "${BLUE}📦 Step 3: Creating Python virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${YELLOW}⚠️  Virtual environment already exists${NC}"
fi

echo -e "${BLUE}📦 Step 4: Activating virtual environment and installing Python packages...${NC}"
source venv/bin/activate

# Upgrade pip first
pip install --upgrade pip

# Detect platform and select appropriate requirements file
REQUIREMENTS_FILE=$(detect_platform)

# Special handling for Jetson
if [ "$REQUIREMENTS_FILE" = "requirements-jetson.txt" ]; then
    echo -e "${BLUE}📦 Step 4a: Checking PyTorch installation for Jetson...${NC}"
    echo -e "${YELLOW}⚠️  IMPORTANT: PyTorch for Jetson must be installed separately!${NC}"
    echo -e "${YELLOW}   Please install PyTorch from NVIDIA's repository first:${NC}"
    echo ""
    echo -e "${CYAN}   For JetPack 6.1, install the CUDA-enabled PyTorch wheel:${NC}"
    echo -e "${CYAN}   wget https://developer.download.nvidia.com/compute/redist/jp/v61/pytorch/torch-2.5.0a0+872d972e41.nv24.08.17622132-cp310-cp310-linux_aarch64.whl${NC}"
    echo -e "${CYAN}   pip3 install torch-2.5.0a0+872d972e41.nv24.08.17622132-cp310-cp310-linux_aarch64.whl${NC}"
    echo -e "${CYAN}   pip3 install torchvision${NC}"
    echo ""
    echo -e "${YELLOW}   See: https://forums.developer.nvidia.com/t/pytorch-for-jetson/ for other versions${NC}"
    echo ""
    read -p "Press Enter to continue after installing PyTorch, or Ctrl+C to cancel..."
fi

# Install dependencies
if [ -f "$REQUIREMENTS_FILE" ]; then
    echo -e "${BLUE}Installing from $REQUIREMENTS_FILE...${NC}"
    if [ "$REQUIREMENTS_FILE" = "requirements-pi.txt" ]; then
        echo -e "${YELLOW}Note: You may be prompted to install:${NC}"
        echo -e "${YELLOW}  - Raspberry Pi hardware dependencies (RPi.GPIO) - Answer 'yes' to enable GPIO features${NC}"
        echo -e "${YELLOW}  - Notification dependencies (Twilio, Pushbullet) - Answer 'yes' to enable notifications${NC}"
    fi
    pip install -r "$REQUIREMENTS_FILE"
else
    echo -e "${YELLOW}⚠️  $REQUIREMENTS_FILE not found, using requirements.txt...${NC}"
    pip install -r requirements.txt
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
