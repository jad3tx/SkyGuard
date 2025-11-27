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

# Install ultralytics with dependencies (but not torch)
# First try with --no-deps, then install dependencies manually
if pip install --no-deps ultralytics>=8.0.0 2>/dev/null; then
    echo -e "${GREEN}✅ ultralytics installed${NC}"
else
    echo -e "${CYAN}Installing ultralytics with dependencies (will remove torch if installed)...${NC}"
    pip install --no-cache-dir ultralytics>=8.0.0 || {
        echo -e "${RED}❌ Failed to install ultralytics${NC}"
        exit 1
    }
    
    # Remove torch if it was installed
    if [ -d "venv/lib/python3.10/site-packages/torch" ] || [ -d "venv/lib/python3.11/site-packages/torch" ]; then
        echo -e "${YELLOW}⚠️  Removing torch from venv (should use system version)...${NC}"
        pip uninstall -y torch torchvision torchaudio 2>/dev/null || true
        for site_packages in venv/lib/python*/site-packages; do
            rm -rf "$site_packages/torch" 2>/dev/null || true
            rm -rf "$site_packages/torchvision" 2>/dev/null || true
            rm -rf "$site_packages/torchaudio" 2>/dev/null || true
            rm -rf "$site_packages"/torch*.dist-info 2>/dev/null || true
            rm -rf "$site_packages"/torch*.egg-info 2>/dev/null || true
        done
    fi
fi

# Install ultralytics dependencies if needed
echo -e "\n${CYAN}📦 Installing ultralytics dependencies...${NC}"
for dep in pillow pyyaml requests tqdm pandas opencv-python-headless; do
    if ! python3 -c "import $dep" 2>/dev/null; then
        echo -e "${CYAN}  Installing $dep...${NC}"
        pip install --no-cache-dir "$dep" 2>/dev/null || true
    fi
done

echo -e "\n${CYAN}🔍 Checking torchvision compatibility...${NC}"

# Check if torchvision has the nms operator error
if python3 -c "import torchvision" 2>/dev/null; then
    if python3 -c "import torchvision; from torchvision.ops import nms" 2>/dev/null; then
        echo -e "${GREEN}✅ torchvision is working correctly${NC}"
    else
        echo -e "${YELLOW}⚠️  torchvision has compatibility issues${NC}"
        echo -e "${CYAN}  Attempting to fix...${NC}"
        
        # Uninstall current torchvision
        pip3 uninstall -y torchvision 2>/dev/null || true
        
        # Try installing the correct version from Jetson AI Lab
        PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
        PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
        PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
        PYTHON_TAG="cp${PYTHON_MAJOR}${PYTHON_MINOR}"
        
        TORCHVISION_WHEEL="torchvision-0.23.0-${PYTHON_TAG}-${PYTHON_TAG}-linux_aarch64.whl"
        TORCHVISION_URL="https://pypi.jetson-ai-lab.io/jp6/cu126/+f/907/c4c1933789645/${TORCHVISION_WHEEL}"
        
        echo -e "${CYAN}  Downloading torchvision 0.23.0 from Jetson AI Lab...${NC}"
        if wget -q "$TORCHVISION_URL" -O "/tmp/${TORCHVISION_WHEEL}" 2>/dev/null; then
            pip3 install "/tmp/${TORCHVISION_WHEEL}" --no-deps || {
                echo -e "${YELLOW}⚠️  Failed to install torchvision wheel, trying build from source...${NC}"
                echo -e "${CYAN}  Run: ./scripts/build_torchvision_jetson.sh${NC}"
            }
            rm -f "/tmp/${TORCHVISION_WHEEL}"
        else
            echo -e "${YELLOW}⚠️  Could not download torchvision wheel${NC}"
            echo -e "${CYAN}  You may need to build torchvision from source:${NC}"
            echo -e "${CYAN}  ./scripts/build_torchvision_jetson.sh${NC}"
        fi
    fi
else
    echo -e "${YELLOW}⚠️  torchvision not found${NC}"
    echo -e "${CYAN}  Installing torchvision from Jetson AI Lab...${NC}"
    
    PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
    PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
    PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
    PYTHON_TAG="cp${PYTHON_MAJOR}${PYTHON_MINOR}"
    
    TORCHVISION_WHEEL="torchvision-0.23.0-${PYTHON_TAG}-${PYTHON_TAG}-linux_aarch64.whl"
    TORCHVISION_URL="https://pypi.jetson-ai-lab.io/jp6/cu126/+f/907/c4c1933789645/${TORCHVISION_WHEEL}"
    
    if wget -q "$TORCHVISION_URL" -O "/tmp/${TORCHVISION_WHEEL}" 2>/dev/null; then
        pip3 install "/tmp/${TORCHVISION_WHEEL}" --no-deps || {
            echo -e "${YELLOW}⚠️  Failed to install torchvision wheel${NC}"
        }
        rm -f "/tmp/${TORCHVISION_WHEEL}"
    else
        echo -e "${YELLOW}⚠️  Could not download torchvision wheel${NC}"
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

