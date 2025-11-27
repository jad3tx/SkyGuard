#!/bin/bash
# Fix missing packages in Jetson venv
# Installs ultralytics and fixes torchvision compatibility

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Fixing Jetson venv packages"
echo "=========================================="

# Detect SkyGuard directory
if [ -d "$(pwd)/SkyGuard" ]; then
    SKYGUARD_DIR="$(pwd)/SkyGuard"
elif [ -d "$HOME/SkyGuard" ]; then
    SKYGUARD_DIR="$HOME/SkyGuard"
else
    echo -e "${RED}❌ SkyGuard directory not found${NC}"
    exit 1
fi

cd "$SKYGUARD_DIR"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment not found${NC}"
    exit 1
fi

# Activate venv
source venv/bin/activate

echo -e "\n${CYAN}📦 Installing ultralytics...${NC}"

# Install ultralytics - try with dependencies first (it should use system torch via --system-site-packages)
echo -e "${CYAN}  Installing ultralytics (will use system PyTorch via --system-site-packages)...${NC}"
pip install --no-cache-dir ultralytics>=8.0.0 || {
    echo -e "${RED}❌ Failed to install ultralytics${NC}"
    exit 1
}
    
# Check if torch was installed in venv (should NOT be)
for site_packages in venv/lib/python*/site-packages; do
    if [ -d "$site_packages/torch" ] 2>/dev/null; then
        echo -e "${YELLOW}⚠️  Removing torch from venv (should use system version)...${NC}"
        pip uninstall -y torch torchvision torchaudio 2>/dev/null || true
        rm -rf "$site_packages/torch" 2>/dev/null || true
        rm -rf "$site_packages/torchvision" 2>/dev/null || true
        rm -rf "$site_packages/torchaudio" 2>/dev/null || true
        rm -rf "$site_packages"/torch*.dist-info 2>/dev/null || true
        rm -rf "$site_packages"/torch*.egg-info 2>/dev/null || true
        break
    fi
done

# Install ultralytics dependencies if needed
echo -e "\n${CYAN}📦 Installing ultralytics dependencies...${NC}"
for dep in pillow pyyaml requests tqdm pandas opencv-python-headless; do
    if ! python3 -c "import $dep" 2>/dev/null; then
        echo -e "${CYAN}  Installing $dep...${NC}"
        pip install --no-cache-dir "$dep" 2>/dev/null || true
    fi
done

echo -e "\n${CYAN}🔍 Checking PyTorch version and torchvision compatibility...${NC}"

# Check installed PyTorch version
TORCH_VERSION=$(python3 -c "import torch; print(torch.__version__)" 2>/dev/null || echo "unknown")
echo -e "${CYAN}  Installed PyTorch: $TORCH_VERSION${NC}"

# Verify it's NVIDIA version
if echo "$TORCH_VERSION" | grep -q "nv24\|nv23\|nv22"; then
    echo -e "${GREEN}  ✅ NVIDIA PyTorch detected${NC}"
else
    echo -e "${YELLOW}  ⚠️  Non-NVIDIA PyTorch detected - may have compatibility issues${NC}"
fi

# Check if torchvision is installed and compatible
TORCHVISION_OK=false
if python3 -c "import torchvision" 2>/dev/null; then
    if python3 -c "import torchvision; from torchvision.ops import nms" 2>/dev/null; then
        TV_VERSION=$(python3 -c "import torchvision; print(torchvision.__version__)" 2>/dev/null || echo "unknown")
        echo -e "${GREEN}✅ torchvision $TV_VERSION is working correctly${NC}"
        TORCHVISION_OK=true
    else
        echo -e "${YELLOW}⚠️  torchvision has compatibility issues (nms operator error)${NC}"
        echo -e "${CYAN}  Uninstalling incompatible torchvision...${NC}"
        pip3 uninstall -y torchvision 2>/dev/null || true
    fi
else
    echo -e "${YELLOW}⚠️  torchvision not found${NC}"
fi

# Install compatible torchvision if needed
if [ "$TORCHVISION_OK" = false ]; then
    echo -e "${CYAN}  Installing compatible torchvision for PyTorch $TORCH_VERSION...${NC}"
    
    PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
    PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
    PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
    PYTHON_TAG="cp${PYTHON_MAJOR}${PYTHON_MINOR}"
    
    # Try torchvision 0.23.0 wheel first
    TORCHVISION_WHEEL="torchvision-0.23.0-${PYTHON_TAG}-${PYTHON_TAG}-linux_aarch64.whl"
    TORCHVISION_URL="https://pypi.jetson-ai-lab.io/jp6/cu126/+f/907/c4c1933789645/${TORCHVISION_WHEEL}"
    
    echo -e "${CYAN}  Attempting to download torchvision 0.23.0 from Jetson AI Lab...${NC}"
    
    if wget -q "$TORCHVISION_URL" -O "/tmp/${TORCHVISION_WHEEL}" 2>/dev/null && [ -f "/tmp/${TORCHVISION_WHEEL}" ]; then
        if pip3 install "/tmp/${TORCHVISION_WHEEL}" --no-deps 2>/dev/null; then
            # Verify it works
            if python3 -c "import torchvision; from torchvision.ops import nms" 2>/dev/null; then
                echo -e "${GREEN}✅ torchvision 0.23.0 installed and verified${NC}"
                TORCHVISION_OK=true
            else
                echo -e "${YELLOW}⚠️  torchvision 0.23.0 installed but still has compatibility issues${NC}"
                pip3 uninstall -y torchvision 2>/dev/null || true
            fi
        fi
        rm -f "/tmp/${TORCHVISION_WHEEL}"
    fi
    
    # If wheel didn't work, build from source
    if [ "$TORCHVISION_OK" = false ]; then
        echo -e "${YELLOW}⚠️  Pre-built wheel not available or incompatible${NC}"
        echo -e "${CYAN}  Building torchvision from source to match PyTorch version...${NC}"
        echo -e "${CYAN}  This will take 10-30 minutes...${NC}"
        
        if [ -f "$SKYGUARD_DIR/scripts/build_torchvision_jetson.sh" ]; then
            chmod +x "$SKYGUARD_DIR/scripts/build_torchvision_jetson.sh"
            if "$SKYGUARD_DIR/scripts/build_torchvision_jetson.sh"; then
                if python3 -c "import torchvision; from torchvision.ops import nms" 2>/dev/null; then
                    echo -e "${GREEN}✅ torchvision built and verified${NC}"
                    TORCHVISION_OK=true
                fi
            fi
        fi
    fi
fi

echo -e "\n${CYAN}✅ Verification...${NC}"

# Verify ultralytics
if python3 -c "import ultralytics" 2>/dev/null; then
    echo -e "${GREEN}✅ ultralytics is installed${NC}"
else
    echo -e "${RED}❌ ultralytics is not installed${NC}"
fi

# Verify torchvision
if python3 -c "import torchvision" 2>/dev/null; then
    if python3 -c "import torchvision; from torchvision.ops import nms" 2>/dev/null; then
        echo -e "${GREEN}✅ torchvision is working${NC}"
    else
        echo -e "${YELLOW}⚠️  torchvision has compatibility issues${NC}"
        echo -e "${CYAN}  You may need to build from source: ./scripts/build_torchvision_jetson.sh${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  torchvision is not installed${NC}"
fi

echo -e "\n${GREEN}✅ Done!${NC}"
echo -e "${CYAN}Run the diagnostic again: ./scripts/diagnose_model_loading.py${NC}"

