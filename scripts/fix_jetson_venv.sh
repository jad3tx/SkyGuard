#!/bin/bash
# Fix Jetson Virtual Environment to Use System CUDA PyTorch
# This script helps fix a venv that was created without --system-site-packages

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 Fixing Jetson Virtual Environment for CUDA PyTorch${NC}"
echo "============================================================"
echo ""

# Check if we're on Jetson
if [ ! -f "/etc/nv_tegra_release" ]; then
    echo -e "${YELLOW}⚠️  This script is for Jetson devices only${NC}"
    exit 1
fi

# Check if venv exists
if [ ! -d "venv" ]; then
    echo -e "${RED}❌ Virtual environment not found${NC}"
    echo -e "${YELLOW}   Run the installation script first${NC}"
    exit 1
fi

# Check for system PyTorch
echo -e "${CYAN}Checking for system PyTorch...${NC}"
PYTORCH_STATUS=$(python3 -c "import torch; print('CUDA' if torch.cuda.is_available() else 'CPU')" 2>/dev/null || echo "NOT_FOUND")

if [ "$PYTORCH_STATUS" = "NOT_FOUND" ]; then
    echo -e "${RED}❌ PyTorch not found in system${NC}"
    echo -e "${YELLOW}   Please install PyTorch from NVIDIA's repository first${NC}"
    echo -e "${YELLOW}   See: https://forums.developer.nvidia.com/t/pytorch-for-jetson/${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Found system PyTorch ($PYTORCH_STATUS)${NC}"

# Check if venv has system site packages
echo -e "${CYAN}Checking virtual environment configuration...${NC}"
if grep -q "include-system-site-packages = true" venv/pyvenv.cfg 2>/dev/null; then
    echo -e "${GREEN}✅ Virtual environment already configured with system site packages${NC}"
else
    echo -e "${YELLOW}⚠️  Virtual environment does not have system site packages enabled${NC}"
    echo -e "${CYAN}   Recreating virtual environment...${NC}"
    
    # Backup current venv
    if [ -d "venv_backup" ]; then
        rm -rf venv_backup
    fi
    mv venv venv_backup
    echo -e "${CYAN}   Backed up old venv to venv_backup${NC}"
    
    # Create new venv with system site packages
    python3 -m venv --system-site-packages venv
    echo -e "${GREEN}✅ Created new venv with system site packages${NC}"
    
    # Activate and reinstall dependencies (excluding torch)
    source venv/bin/activate
    pip install --upgrade pip
    
    # Determine requirements file
    if [ -f "requirements-jetson.txt" ]; then
        REQ_FILE="requirements-jetson.txt"
    else
        REQ_FILE="requirements.txt"
    fi
    
    echo -e "${CYAN}   Reinstalling dependencies (excluding torch/torchvision)...${NC}"
    FILTERED_REQ=$(mktemp)
    grep -v -E "^(torch|torchvision|torchaudio)" "$REQ_FILE" > "$FILTERED_REQ" 2>/dev/null || cp "$REQ_FILE" "$FILTERED_REQ"
    pip install -r "$FILTERED_REQ"
    rm -f "$FILTERED_REQ"
    
    echo -e "${GREEN}✅ Dependencies reinstalled${NC}"
fi

# Verify PyTorch CUDA in venv
echo -e "\n${CYAN}Verifying PyTorch CUDA in virtual environment...${NC}"
source venv/bin/activate
VENV_PYTORCH=$(python3 -c "import torch; print('CUDA' if torch.cuda.is_available() else 'CPU')" 2>/dev/null || echo "NOT_FOUND")

if [ "$VENV_PYTORCH" = "CUDA" ]; then
    CUDA_DEVICE=$(python3 -c "import torch; print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A')" 2>/dev/null)
    echo -e "${GREEN}✅ PyTorch CUDA is working in virtual environment!${NC}"
    echo -e "${CYAN}   Device: $CUDA_DEVICE${NC}"
    echo ""
    echo -e "${GREEN}✅ Virtual environment is now properly configured!${NC}"
else
    echo -e "${RED}❌ PyTorch CUDA still not available in virtual environment${NC}"
    echo -e "${YELLOW}   Try:${NC}"
    echo -e "${YELLOW}   1. Ensure PyTorch is installed system-wide with CUDA support${NC}"
    echo -e "${YELLOW}   2. Check that venv/pyvenv.cfg has 'include-system-site-packages = true'${NC}"
    echo -e "${YELLOW}   3. Try recreating the venv manually:${NC}"
    echo -e "${YELLOW}      rm -rf venv${NC}"
    echo -e "${YELLOW}      python3 -m venv --system-site-packages venv${NC}"
    exit 1
fi

