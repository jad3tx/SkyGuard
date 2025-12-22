#!/bin/bash
# Fix OpenCV installation on Raspberry Pi
# Ensures opencv-python (full version) is installed with required system libraries
# NOTE: Requires Raspbian with Desktop/UI

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}OpenCV Installation Fix for Raspberry Pi${NC}"
echo -e "${CYAN}Requires Raspbian with Desktop/UI${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# Check if we're in a virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}⚠️  No virtual environment detected.${NC}"
    echo -e "${CYAN}   Please activate your virtual environment first:${NC}"
    echo -e "${CYAN}   source venv/bin/activate${NC}"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✅ Virtual environment detected: $VIRTUAL_ENV${NC}"
fi

echo ""
echo -e "${CYAN}Checking current OpenCV installation...${NC}"

# Check which OpenCV package is installed
OPENCV_PACKAGE=$(pip list | grep -i opencv | head -n 1 | awk '{print $1}' || echo "")

if [ -z "$OPENCV_PACKAGE" ]; then
    echo -e "${YELLOW}⚠️  No OpenCV package found.${NC}"
    echo -e "${CYAN}   Installing required system libraries first...${NC}"
    sudo apt-get update
    sudo apt-get install -y libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1
    echo -e "${CYAN}   Installing opencv-python (full version)...${NC}"
    pip install --no-cache-dir opencv-python
    echo -e "${GREEN}✅ opencv-python installed${NC}"
    exit 0
fi

echo -e "${CYAN}   Found: $OPENCV_PACKAGE${NC}"

if [ "$OPENCV_PACKAGE" = "opencv-python" ]; then
    echo -e "${GREEN}✅ Correct package (opencv-python) is installed${NC}"
    echo ""
    echo -e "${CYAN}Testing OpenCV import...${NC}"
    if python3 -c "import cv2; print(f'OpenCV version: {cv2.__version__}')" 2>/dev/null; then
        echo -e "${GREEN}✅ OpenCV imports successfully${NC}"
        exit 0
    else
        echo -e "${YELLOW}⚠️  OpenCV import failed. Installing required system libraries...${NC}"
        sudo apt-get update
        sudo apt-get install -y libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1
        echo -e "${GREEN}✅ System libraries installed${NC}"
        echo -e "${CYAN}   Testing OpenCV import again...${NC}"
        if python3 -c "import cv2; print(f'OpenCV version: {cv2.__version__}')" 2>/dev/null; then
            echo -e "${GREEN}✅ OpenCV imports successfully after installing libraries${NC}"
        else
            echo -e "${RED}❌ OpenCV still fails to import${NC}"
            echo -e "${YELLOW}   Please ensure you are running Raspbian with Desktop/UI${NC}"
            echo -e "${YELLOW}   Check logs/main.log for detailed error messages${NC}"
        fi
        exit 0
    fi
fi

if [ "$OPENCV_PACKAGE" = "opencv-python-headless" ]; then
    echo -e "${YELLOW}⚠️  Found opencv-python-headless (headless version)${NC}"
    echo -e "${CYAN}   Replacing with opencv-python (full version) for Raspbian with UI...${NC}"
    echo ""
    
    # Uninstall opencv-python-headless
    echo -e "${CYAN}   Step 1: Uninstalling opencv-python-headless...${NC}"
    pip uninstall -y opencv-python-headless 2>/dev/null || true
    
    # Install required system libraries
    echo -e "${CYAN}   Step 2: Installing required system libraries...${NC}"
    sudo apt-get update
    sudo apt-get install -y libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1
    
    # Install opencv-python
    echo -e "${CYAN}   Step 3: Installing opencv-python (full version)...${NC}"
    pip install --no-cache-dir opencv-python
    
    echo ""
    echo -e "${GREEN}✅ Successfully replaced opencv-python-headless with opencv-python${NC}"
    
    # Test the installation
    echo ""
    echo -e "${CYAN}Testing OpenCV import...${NC}"
    if python3 -c "import cv2; print(f'OpenCV version: {cv2.__version__}')" 2>/dev/null; then
        echo -e "${GREEN}✅ OpenCV imports successfully!${NC}"
        echo -e "${GREEN}✅ Fix completed successfully${NC}"
    else
        echo -e "${RED}❌ OpenCV still fails to import${NC}"
        echo -e "${YELLOW}   Please ensure you are running Raspbian with Desktop/UI${NC}"
        echo -e "${YELLOW}   Check logs/main.log for detailed error messages${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Unknown OpenCV package: $OPENCV_PACKAGE${NC}"
    echo -e "${CYAN}   Installing opencv-python (full version) and system libraries...${NC}"
    sudo apt-get update
    sudo apt-get install -y libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1
    pip install --no-cache-dir opencv-python
    echo -e "${GREEN}✅ opencv-python installed${NC}"
fi

echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${GREEN}Fix script completed${NC}"
echo -e "${CYAN}========================================${NC}"
