#!/bin/bash
# SkyGuard Installation Script
# Platform detection wrapper that calls platform-specific install scripts

# Don't use set -e - we want to handle errors gracefully
set -o pipefail  # Only fail on pipe errors, not individual commands

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Platform detection function
detect_platform() {
    local platform="unknown"
    
    # Check for Jetson
    if [ -f "/etc/nv_tegra_release" ] || [ -n "$JETSON_VERSION" ]; then
        platform="jetson"
        echo -e "${GREEN}✅ NVIDIA Jetson detected${NC}" >&2
    elif [ -f "/proc/device-tree/model" ]; then
        model=$(cat /proc/device-tree/model 2>/dev/null || echo "")
        if echo "$model" | grep -qi "jetson\|tegra"; then
            platform="jetson"
            echo -e "${GREEN}✅ NVIDIA Jetson detected: $model${NC}" >&2
        elif echo "$model" | grep -qi "raspberry pi"; then
            platform="raspberry_pi"
            echo -e "${GREEN}✅ Raspberry Pi detected: $model${NC}" >&2
        fi
    elif [ -f "/etc/os-release" ]; then
        if grep -qi "raspbian\|raspberry" /etc/os-release 2>/dev/null; then
            platform="raspberry_pi"
            echo -e "${GREEN}✅ Raspberry Pi detected${NC}" >&2
        fi
    fi
    
    echo "$platform"
}

echo -e "${BLUE}🛡️  SkyGuard Installation${NC}"
echo "================================"
echo ""

# Detect platform
DETECTED_PLATFORM=$(detect_platform)

# Determine which install script to use
if [ "$DETECTED_PLATFORM" = "jetson" ]; then
    INSTALL_SCRIPT="$SCRIPT_DIR/install-jetson.sh"
    echo -e "${CYAN}Using Jetson-specific installation script...${NC}"
    echo ""
elif [ "$DETECTED_PLATFORM" = "raspberry_pi" ]; then
    INSTALL_SCRIPT="$SCRIPT_DIR/install-rpi.sh"
    echo -e "${CYAN}Using Raspberry Pi-specific installation script...${NC}"
    echo ""
else
    echo -e "${YELLOW}⚠️  Platform not detected or unsupported${NC}"
    echo -e "${CYAN}Attempting generic installation...${NC}"
    echo ""
    # For unknown platforms, try to use RPi script as fallback (most compatible)
    INSTALL_SCRIPT="$SCRIPT_DIR/install-rpi.sh"
fi

# Check if the install script exists
if [ ! -f "$INSTALL_SCRIPT" ]; then
    echo -e "${RED}❌ Installation script not found: $INSTALL_SCRIPT${NC}"
    echo -e "${YELLOW}Please ensure the platform-specific install script exists${NC}"
    exit 1
fi

# Make sure the script is executable
chmod +x "$INSTALL_SCRIPT" 2>/dev/null || true

# Check if common functions file exists (required by platform scripts)
if [ ! -f "$SCRIPT_DIR/install-common.sh" ]; then
    echo -e "${RED}❌ Common installation functions not found: $SCRIPT_DIR/install-common.sh${NC}"
    echo -e "${YELLOW}Please ensure install-common.sh exists in the scripts directory${NC}"
    exit 1
fi

# Execute the platform-specific install script
# Use bash explicitly to ensure proper execution
bash "$INSTALL_SCRIPT"
exit_code=$?

if [ $exit_code -ne 0 ]; then
    echo -e "${RED}❌ Installation failed with exit code: $exit_code${NC}"
    exit $exit_code
fi
