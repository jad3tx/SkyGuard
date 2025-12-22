#!/bin/bash
# Install system libraries required for opencv-python on Raspbian with Desktop/UI
# This script installs all necessary system dependencies for the full OpenCV package

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}Installing OpenCV System Libraries${NC}"
echo -e "${CYAN}For Raspbian with Desktop/UI${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}⚠️  This script requires sudo privileges${NC}"
    echo -e "${CYAN}   Please run with: sudo ./scripts/install_opencv_libs.sh${NC}"
    exit 1
fi

echo -e "${CYAN}Updating package lists...${NC}"
apt-get update

echo ""
echo -e "${CYAN}Installing OpenCV system dependencies...${NC}"
echo -e "${CYAN}This includes:${NC}"
echo -e "${CYAN}  - libgl1-mesa-glx (OpenGL library)${NC}"
echo -e "${CYAN}  - libglib2.0-0 (GLib library)${NC}"
echo -e "${CYAN}  - libsm6 (X11 Session Management)${NC}"
echo -e "${CYAN}  - libxext6 (X11 extensions)${NC}"
echo -e "${CYAN}  - libxrender-dev (X11 Render extension)${NC}"
echo -e "${CYAN}  - libgomp1 (GNU OpenMP library)${NC}"
echo ""

apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1

echo ""
echo -e "${GREEN}✅ All OpenCV system libraries installed successfully${NC}"
echo ""
echo -e "${CYAN}You can now install opencv-python:${NC}"
echo -e "${CYAN}  source venv/bin/activate${NC}"
echo -e "${CYAN}  pip install opencv-python${NC}"
echo ""
echo -e "${CYAN}Or test the installation:${NC}"
echo -e "${CYAN}  python3 -c \"import cv2; print(f'OpenCV version: {cv2.__version__}')\"${NC}"
echo ""

