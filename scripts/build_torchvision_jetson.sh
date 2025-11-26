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
PYTHON_MAJOR_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f1,2)
echo "Python version: $PYTHON_VERSION"

# Check if torch is installed
if ! python3 -c "import torch" 2>/dev/null; then
    echo "❌ PyTorch is not installed. Please install it first."
    exit 1
fi

TORCH_VERSION=$(python3 -c "import torch; print(torch.__version__)" 2>/dev/null)
echo "PyTorch version: $TORCH_VERSION"

# Detect Jetson model and set CUDA architecture
# This suppresses the warning and optimizes the build
if [ -f "/proc/device-tree/model" ]; then
    JETSON_MODEL=$(cat /proc/device-tree/model | tr -d '\0')
    echo "Jetson model: $JETSON_MODEL"
    
    # Set CUDA architecture based on Jetson model
    # Orin series (Orin Nano, Orin NX, AGX Orin): sm_87
    # Xavier series: sm_72
    # Nano (older): sm_53
    if echo "$JETSON_MODEL" | grep -qi "orin"; then
        CUDA_ARCH="7.2;8.7"  # Support both Xavier and Orin for compatibility
        echo "Setting CUDA architecture: $CUDA_ARCH (Orin series)"
    elif echo "$JETSON_MODEL" | grep -qi "xavier"; then
        CUDA_ARCH="7.2"
        echo "Setting CUDA architecture: $CUDA_ARCH (Xavier series)"
    else
        # Default to Orin (most common for new installations)
        CUDA_ARCH="7.2;8.7"
        echo "Setting CUDA architecture: $CUDA_ARCH (default - supports Orin and Xavier)"
    fi
    
    export TORCH_CUDA_ARCH_LIST="$CUDA_ARCH"
    echo "✅ TORCH_CUDA_ARCH_LIST set to: $TORCH_CUDA_ARCH_LIST"
else
    # Not a Jetson, but set a reasonable default
    export TORCH_CUDA_ARCH_LIST="7.0;7.5;8.0;8.6;8.9"
    echo "⚠️  Not a Jetson device, using default CUDA architectures"
fi

# Check if we're in a venv
if [ -n "$VIRTUAL_ENV" ]; then
    echo "📦 Virtual environment detected: $VIRTUAL_ENV"
    INSTALL_MODE="venv"
else
    INSTALL_MODE="user"
fi

# Uninstall existing torchvision (if any)
echo ""
echo "🧹 Removing existing torchvision installation..."
echo "   Removing from venv (if in venv)..."
pip3 uninstall -y torchvision 2>/dev/null || true
python3 -m pip uninstall -y torchvision 2>/dev/null || true

# CRITICAL: Also remove from user site-packages (takes precedence!)
echo "   Removing from user site-packages..."
python3 -m pip uninstall -y torchvision --user 2>/dev/null || true
# Manually remove if pip doesn't work
USER_SITE=$(python3 -m site --user-site 2>/dev/null || echo "$HOME/.local/lib/python3.10/site-packages")
if [ -d "$USER_SITE/torchvision" ]; then
    echo "   Removing $USER_SITE/torchvision..."
    rm -rf "$USER_SITE/torchvision" "$USER_SITE/torchvision-*.dist-info" 2>/dev/null || true
fi

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

# Determine installation mode and check permissions
FALLBACK_TO_USER=false
if [ "$INSTALL_MODE" = "venv" ]; then
    echo "   Installing into virtual environment..."
    
    # Use detected Python version for path construction (fixes Bug 2)
    VENV_SITE_PACKAGES="$VIRTUAL_ENV/lib/python$PYTHON_MAJOR_MINOR/site-packages"
    
    # Fix venv permissions if needed
    if [ ! -w "$VENV_SITE_PACKAGES" ]; then
        echo "   ⚠️  Venv not writable, fixing permissions..."
        sudo chown -R "$(whoami):$(whoami)" "$VIRTUAL_ENV" 2>/dev/null || {
            echo "   ⚠️  Could not fix permissions, will fall back to user installation"
            FALLBACK_TO_USER=true
        }
    fi
fi

# Build wheel first (creates proper metadata)
echo "   Building wheel (this creates proper package metadata)..."
python3 setup.py bdist_wheel

# Find the wheel file (must be .whl, not .egg)
WHEEL_FILE=$(ls -t dist/torchvision-*.whl 2>/dev/null | head -1)

# Determine final installation mode (fixes Bug 1: handle fallback properly)
if [ "$INSTALL_MODE" = "venv" ] && [ "$FALLBACK_TO_USER" = false ]; then
    # Install into venv
    if [ -n "$WHEEL_FILE" ] && [ -f "$WHEEL_FILE" ]; then
        echo "   Installing wheel with pip (ensures proper metadata)..."
        pip install "$WHEEL_FILE" --force-reinstall --no-deps
        echo "   ✅ Installed from wheel: $WHEEL_FILE"
    else
        echo "   ⚠️  Wheel not found, using pip install (creates metadata)..."
        pip install . --force-reinstall --no-deps
    fi
else
    # Install to user site-packages (either originally user mode, or fallback from venv)
    echo "   Installing to user site-packages..."
    if [ -n "$WHEEL_FILE" ] && [ -f "$WHEEL_FILE" ]; then
        pip install "$WHEEL_FILE" --user --force-reinstall --no-deps
        echo "   ✅ Installed from wheel: $WHEEL_FILE"
    else
        pip install . --user --force-reinstall --no-deps
    fi
fi

# Verify installation
echo ""
echo "✅ Verifying installation..."
if python3 -c "import torchvision; print(f'torchvision {torchvision.__version__} installed successfully')" 2>/dev/null; then
    echo "✅ torchvision installed successfully!"
    
    # Test that it actually works (not just imports)
    echo ""
    echo "🧪 Testing torchvision functionality..."
    if python3 -c "
import torch
import torchvision
print(f'PyTorch: {torch.__version__}')
print(f'torchvision: {torchvision.__version__}')
# Try to use a basic torchvision function
try:
    from torchvision import transforms
    t = transforms.Compose([transforms.ToTensor()])
    print('✅ torchvision transforms work')
except Exception as e:
    print(f'⚠️  torchvision transforms error: {e}')
    raise
" 2>/dev/null; then
        echo "✅ torchvision is fully functional!"
    else
        echo "⚠️  torchvision imported but may have runtime issues"
    fi
    
    echo ""
    echo "Test it manually:"
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

