#!/bin/bash
# SkyGuard Installation Script
# Simple installation script for Raspberry Pi

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

echo -e "${BLUE}📦 Step 1: Updating system packages...${NC}"
sudo apt update
sudo apt upgrade -y

echo -e "${BLUE}📦 Step 2: Installing system dependencies...${NC}"
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
    libx264-dev \
    libatlas-base-dev \
    libopenblas-dev

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

# Install dependencies
if [ -f "requirements-pi.txt" ]; then
    echo -e "${BLUE}Installing from requirements-pi.txt...${NC}"
    echo -e "${YELLOW}Note: You may be prompted to install:${NC}"
    echo -e "${YELLOW}  - Raspberry Pi hardware dependencies (RPi.GPIO) - Answer 'yes' to enable GPIO features${NC}"
    echo -e "${YELLOW}  - Notification dependencies (Twilio, Pushbullet) - Answer 'yes' to enable notifications${NC}"
    pip install -r requirements-pi.txt
else
    echo -e "${YELLOW}⚠️  requirements-pi.txt not found, using requirements.txt...${NC}"
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

