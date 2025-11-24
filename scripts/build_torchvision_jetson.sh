#!/bin/bash
# Build torchvision from source for NVIDIA Jetson
# Compatible with torch 2.5.0a0 from NVIDIA

set -e

echo "=========================================="
echo "Building torchvision for NVIDIA Jetson"
echo "=========================================="

# Check if running on Jetson
if [ ! -f "/etc/nv_tegra_release" ]; then
    echo "⚠️  This script is intended for NVIDIA Jetson devices"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
echo "Python version: $PYTHON_VERSION"

# Check if torch is installed
if ! python3 -c "import torch" 2>/dev/null; then
    echo "❌ PyTorch is not installed. Please install it first."
    exit 1
fi

TORCH_VERSION=$(python3 -c "import torch; print(torch.__version__)" 2>/dev/null)
echo "PyTorch version: $TORCH_VERSION"

# Determine compatible torchvision version
# For torch 2.5.0, use torchvision 0.20.0
TV_VERSION="0.20.0"
echo "Building torchvision version: $TV_VERSION"

# Install build dependencies
echo ""
echo "📦 Installing build dependencies..."
sudo apt-get update
sudo apt-get install -y \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    python3-dev \
    python3-pip \
    git \
    build-essential

# Clone torchvision repository
BUILD_DIR="/tmp/torchvision_build"
if [ -d "$BUILD_DIR" ]; then
    echo "🧹 Cleaning previous build directory..."
    rm -rf "$BUILD_DIR"
fi

echo ""
echo "📥 Cloning torchvision repository..."
git clone https://github.com/pytorch/vision.git "$BUILD_DIR"
cd "$BUILD_DIR"

# Checkout compatible version
echo "📌 Checking out torchvision $TV_VERSION..."
git checkout "v$TV_VERSION"

# Build and install
echo ""
echo "🔨 Building torchvision (this may take 10-30 minutes)..."
export BUILD_VERSION="$TV_VERSION"
python3 setup.py install --user

# Verify installation
echo ""
echo "✅ Verifying installation..."
if python3 -c "import torchvision; print(f'torchvision {torchvision.__version__} installed successfully')" 2>/dev/null; then
    echo "✅ torchvision installed successfully!"
    echo ""
    echo "Test it:"
    echo "  python3 -c \"import torch; import torchvision; print(f'PyTorch: {torch.__version__}'); print(f'torchvision: {torchvision.__version__}')\""
else
    echo "❌ Installation verification failed"
    exit 1
fi

# Cleanup
echo ""
echo "🧹 Cleaning up build directory..."
rm -rf "$BUILD_DIR"

echo ""
echo "✅ Done!"

