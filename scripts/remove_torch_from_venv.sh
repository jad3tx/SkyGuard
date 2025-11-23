#!/bin/bash
# Remove PyTorch from Virtual Environment (Jetson)
# This script aggressively removes torch packages from the venv
# so that the system-installed CUDA version can be used

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 Removing PyTorch from Virtual Environment${NC}"
echo "=============================================="
echo ""

# Auto-detect SkyGuard directory
if [ -d "$(pwd)/SkyGuard" ]; then
    SKYGUARD_DIR="$(pwd)/SkyGuard"
elif [ -d "$HOME/SkyGuard" ]; then
    SKYGUARD_DIR="$HOME/SkyGuard"
elif [ -d "/home/jad3/SkyGuard" ]; then
    SKYGUARD_DIR="/home/jad3/SkyGuard"
elif [ -d "/home/pi/SkyGuard" ]; then
    SKYGUARD_DIR="/home/pi/SkyGuard"
else
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    SKYGUARD_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
fi

VENV_DIR="$SKYGUARD_DIR/venv"

echo -e "${CYAN}SkyGuard directory: $SKYGUARD_DIR${NC}"
echo -e "${CYAN}Virtual environment: $VENV_DIR${NC}"
echo ""

# Check if venv exists
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${RED}❌ Virtual environment not found: $VENV_DIR${NC}"
    exit 1
fi

# Check if venv has system site packages enabled
if [ -f "$VENV_DIR/pyvenv.cfg" ]; then
    if grep -q "include-system-site-packages = true" "$VENV_DIR/pyvenv.cfg" 2>/dev/null; then
        echo -e "${GREEN}✅ Virtual environment has system site packages enabled${NC}"
    else
        echo -e "${YELLOW}⚠️  Virtual environment does NOT have system site packages enabled${NC}"
        echo -e "${CYAN}   This is required for accessing system PyTorch${NC}"
        read -p "Enable system site packages? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            # Enable system site packages
            if grep -q "include-system-site-packages" "$VENV_DIR/pyvenv.cfg" 2>/dev/null; then
                sed -i 's/include-system-site-packages = false/include-system-site-packages = true/' "$VENV_DIR/pyvenv.cfg"
            else
                echo "include-system-site-packages = true" >> "$VENV_DIR/pyvenv.cfg"
            fi
            echo -e "${GREEN}✅ Enabled system site packages${NC}"
        fi
    fi
fi

# Activate venv
echo -e "${CYAN}Activating virtual environment...${NC}"
source "$VENV_DIR/bin/activate"

# Check current torch status
echo -e "${CYAN}Checking current PyTorch installation...${NC}"
TORCH_INFO=$(python3 -c "
import sys
import os
try:
    import torch
    torch_path = os.path.abspath(torch.__file__)
    venv_path = os.path.abspath('$VENV_DIR')
    if venv_path in torch_path:
        print(f'venv|{torch.__version__}|{torch.cuda.is_available()}')
    else:
        print(f'system|{torch.__version__}|{torch.cuda.is_available()}')
except Exception as e:
    print(f'error|{str(e)}')
" 2>/dev/null || echo "error|unknown")

IFS='|' read -r TORCH_SOURCE TORCH_VERSION TORCH_CUDA <<< "$TORCH_INFO"

if [ "$TORCH_SOURCE" = "venv" ]; then
    echo -e "${YELLOW}⚠️  PyTorch is installed in venv: $TORCH_VERSION (CUDA: $TORCH_CUDA)${NC}"
    echo -e "${CYAN}   This will be removed to use system version${NC}"
elif [ "$TORCH_SOURCE" = "system" ]; then
    echo -e "${GREEN}✅ PyTorch is already using system version: $TORCH_VERSION (CUDA: $TORCH_CUDA)${NC}"
    echo -e "${CYAN}   No action needed${NC}"
    deactivate 2>/dev/null || true
    exit 0
else
    echo -e "${YELLOW}⚠️  Could not determine torch source${NC}"
fi

echo ""
echo -e "${CYAN}Removing PyTorch packages from virtual environment...${NC}"

# Step 1: Uninstall via pip
echo -e "${CYAN}   Step 1: Uninstalling via pip...${NC}"
pip uninstall -y torch torchvision torchaudio 2>/dev/null || true

# Step 2: Physically remove from site-packages
echo -e "${CYAN}   Step 2: Removing from filesystem...${NC}"
for site_packages in "$VENV_DIR"/lib/python*/site-packages; do
    if [ -d "$site_packages" ]; then
        # Remove torch directories
        rm -rf "$site_packages/torch" 2>/dev/null || true
        rm -rf "$site_packages/torchvision" 2>/dev/null || true
        rm -rf "$site_packages/torchaudio" 2>/dev/null || true
        
        # Remove torch dist-info and egg-info
        rm -rf "$site_packages"/torch*.dist-info 2>/dev/null || true
        rm -rf "$site_packages"/torch*.egg-info 2>/dev/null || true
        rm -rf "$site_packages"/torchvision*.dist-info 2>/dev/null || true
        rm -rf "$site_packages"/torchvision*.egg-info 2>/dev/null || true
        rm -rf "$site_packages"/torchaudio*.dist-info 2>/dev/null || true
        rm -rf "$site_packages"/torchaudio*.egg-info 2>/dev/null || true
        
        # Remove any torch-* directories (for packages like torch-2.9.1+cpu.dist-info)
        find "$site_packages" -maxdepth 1 -type d -name "torch-*" -exec rm -rf {} + 2>/dev/null || true
        find "$site_packages" -maxdepth 1 -type d -name "torchvision-*" -exec rm -rf {} + 2>/dev/null || true
        find "$site_packages" -maxdepth 1 -type d -name "torchaudio-*" -exec rm -rf {} + 2>/dev/null || true
    fi
done

echo -e "${GREEN}   ✅ PyTorch packages removed${NC}"

# Step 3: Verify system PyTorch is accessible
echo ""
echo -e "${CYAN}Verifying system PyTorch is accessible...${NC}"

# Deactivate and reactivate to ensure clean state
deactivate 2>/dev/null || true
source "$VENV_DIR/bin/activate"

TORCH_VERIFY=$(python3 -c "
import sys
import os
try:
    import torch
    torch_path = os.path.abspath(torch.__file__)
    venv_path = os.path.abspath('$VENV_DIR')
    if venv_path in torch_path:
        print('venv')
    else:
        version = torch.__version__
        cuda_available = torch.cuda.is_available()
        device = torch.cuda.get_device_name(0) if cuda_available else 'N/A'
        print(f'system|{version}|{cuda_available}|{device}')
except Exception as e:
    print(f'error|{str(e)}')
" 2>/dev/null || echo "error|unknown")

IFS='|' read -r VERIFY_SOURCE VERIFY_VERSION VERIFY_CUDA VERIFY_DEVICE <<< "$TORCH_VERIFY"

if [ "$VERIFY_SOURCE" = "system" ]; then
    echo -e "${GREEN}✅ SUCCESS! Now using system PyTorch${NC}"
    echo -e "${CYAN}   Version: $VERIFY_VERSION${NC}"
    echo -e "${CYAN}   CUDA available: $VERIFY_CUDA${NC}"
    if [ "$VERIFY_CUDA" = "True" ]; then
        echo -e "${CYAN}   CUDA device: $VERIFY_DEVICE${NC}"
        echo ""
        echo -e "${GREEN}✅ Virtual environment is now correctly configured!${NC}"
    else
        echo -e "${YELLOW}⚠️  CUDA not available - check system PyTorch installation${NC}"
    fi
elif [ "$VERIFY_SOURCE" = "venv" ]; then
    echo -e "${RED}❌ ERROR: PyTorch is still loading from venv${NC}"
    echo -e "${YELLOW}   This should not happen. Try recreating the venv:${NC}"
    echo -e "${CYAN}   rm -rf $VENV_DIR${NC}"
    echo -e "${CYAN}   python3 -m venv --system-site-packages $VENV_DIR${NC}"
    exit 1
else
    echo -e "${RED}❌ ERROR: Could not import PyTorch${NC}"
    echo -e "${YELLOW}   Check that PyTorch is installed system-wide${NC}"
    exit 1
fi

deactivate 2>/dev/null || true

echo ""
echo -e "${GREEN}✅ Done!${NC}"

