#!/bin/bash
# SkyGuard Installation Script for Raspberry Pi
# Handles Raspberry Pi-specific installation requirements

# Don't use set -e - we want to handle errors gracefully
set -o pipefail  # Only fail on pipe errors, not individual commands

# Source common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/install-common.sh"

echo -e "${BLUE}🛡️  SkyGuard Installation for Raspberry Pi${NC}"
echo "=========================================="
echo ""

cd "$PROJECT_ROOT"

# Platform-specific variables
PLATFORM_USER="pi"
REQUIREMENTS_FILE="requirements-pi.txt"

# Detect platform username (fallback if pi doesn't exist)
if ! id "$PLATFORM_USER" &>/dev/null; then
    PLATFORM_USER=$(whoami)
    echo -e "${YELLOW}⚠️  User 'pi' not found, using current user: $PLATFORM_USER${NC}"
fi
echo -e "${CYAN}   Platform user: $PLATFORM_USER${NC}"

# Check if Desktop version is installed (required for OpenCV)
echo -e "${BLUE}📦 Step 1: Verifying Raspberry Pi OS Desktop installation...${NC}"
if [ -d "/usr/share/desktop-base" ] || [ -d "/usr/share/xsessions" ] || command -v startx &>/dev/null; then
    echo -e "${GREEN}✅ Raspberry Pi OS Desktop detected${NC}"
else
    echo -e "${YELLOW}⚠️  Desktop environment not detected${NC}"
    echo -e "${YELLOW}   SkyGuard requires Raspberry Pi OS with Desktop (not Lite) for OpenCV support${NC}"
    echo -e "${CYAN}   Please install the Desktop version:${NC}"
    echo -e "${CYAN}   sudo apt update && sudo apt install -y raspberrypi-ui-mods${NC}"
    echo -e "${CYAN}   Or reinstall with Raspberry Pi OS Desktop from Raspberry Pi Imager${NC}"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Install system dependencies
install_system_dependencies

echo -e "${BLUE}📦 Step 3: Creating Python virtual environment...${NC}"
create_venv "false" "$PROJECT_ROOT/venv"

echo -e "${BLUE}📦 Step 4: Activating virtual environment and installing Python packages...${NC}"

# Activate venv
source venv/bin/activate

# Upgrade pip
upgrade_pip "$PROJECT_ROOT/venv"

# Install dependencies
if [ -f "$REQUIREMENTS_FILE" ]; then
    echo -e "${BLUE}Installing from $REQUIREMENTS_FILE...${NC}"
    echo -e "${YELLOW}Note: You may be prompted to install:${NC}"
    echo -e "${YELLOW}  - Raspberry Pi hardware dependencies (RPi.GPIO) - Answer 'yes' to enable GPIO features${NC}"
    echo -e "${YELLOW}  - Notification dependencies (Twilio, Pushbullet) - Answer 'yes' to enable notifications${NC}"
    echo -e "${CYAN}   PyTorch installation on Raspberry Pi can take 15-30 minutes...${NC}"
    echo -e "${CYAN}   Please be patient and ensure you have a stable internet connection${NC}"
    
    # For Raspberry Pi, install packages with retries and better error handling
    INSTALL_SUCCESS=false
    MAX_RETRIES=2
    
    for attempt in $(seq 1 $MAX_RETRIES); do
        if [ "$attempt" -gt 1 ]; then
            echo -e "${YELLOW}   Retry attempt $attempt of $MAX_RETRIES...${NC}"
        fi
        
        if [ "$(id -u)" -eq 0 ] && [ "$PLATFORM_USER" != "root" ] && id "$PLATFORM_USER" &>/dev/null; then
            if runuser -l "$PLATFORM_USER" -c "cd '$PROJECT_ROOT' && source venv/bin/activate && pip install --no-cache-dir --timeout=300 -r '$REQUIREMENTS_FILE'"; then
                INSTALL_SUCCESS=true
                break
            fi
            # Fix ownership after installation
            chown -R "$PLATFORM_USER:$PLATFORM_USER" venv 2>/dev/null || true
        else
            if pip install --no-cache-dir --timeout=300 -r "$REQUIREMENTS_FILE"; then
                INSTALL_SUCCESS=true
                break
            fi
        fi
        
        if [ "$attempt" -lt $MAX_RETRIES ]; then
            echo -e "${YELLOW}   Installation failed, waiting 5 seconds before retry...${NC}"
            sleep 5
        fi
    done
    
    if [ "$INSTALL_SUCCESS" = false ]; then
        echo -e "${RED}❌ Failed to install packages after $MAX_RETRIES attempts${NC}"
        echo -e "${YELLOW}   Some packages may have failed. Common issues:${NC}"
        echo -e "${YELLOW}   - PyTorch: Very large package, may need more time or disk space${NC}"
        echo -e "${YELLOW}   - Network timeout: Check your internet connection${NC}"
        echo -e "${YELLOW}   - Disk space: Ensure you have at least 5GB free${NC}"
        echo ""
        echo -e "${CYAN}   You can try installing packages manually:${NC}"
        echo -e "${CYAN}   source venv/bin/activate${NC}"
        echo -e "${CYAN}   pip install --no-cache-dir -r $REQUIREMENTS_FILE${NC}"
        echo ""
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
else
    echo -e "${YELLOW}⚠️  $REQUIREMENTS_FILE not found, using requirements.txt...${NC}"
    INSTALL_SUCCESS=false
    if [ "$(id -u)" -eq 0 ] && [ "$PLATFORM_USER" != "root" ] && id "$PLATFORM_USER" &>/dev/null; then
        if runuser -l "$PLATFORM_USER" -c "cd '$PROJECT_ROOT' && source venv/bin/activate && pip install --no-cache-dir --timeout=300 -r requirements.txt"; then
            INSTALL_SUCCESS=true
        fi
        # Fix ownership after installation
        chown -R "$PLATFORM_USER:$PLATFORM_USER" venv 2>/dev/null || true
    else
        if pip install --no-cache-dir --timeout=300 -r requirements.txt; then
            INSTALL_SUCCESS=true
        fi
    fi
    
    if [ "$INSTALL_SUCCESS" = false ]; then
        echo -e "${RED}❌ Failed to install packages from requirements.txt${NC}"
        exit 1
    fi
fi

make_scripts_executable
create_directories

# Raspberry Pi specific setup
echo -e "${BLUE}📦 Step 5: Raspberry Pi specific setup...${NC}"

# Check if user is in gpio group (for GPIO access)
if groups | grep -q gpio; then
    echo -e "${GREEN}✅ User is in gpio group${NC}"
else
    echo -e "${YELLOW}⚠️  User is not in gpio group${NC}"
    echo -e "${CYAN}   Adding user to gpio group for hardware access...${NC}"
    if [ "$(id -u)" -eq 0 ]; then
        usermod -a -G gpio "$PLATFORM_USER" 2>/dev/null || echo -e "${YELLOW}   ⚠️  Could not add user to gpio group (may need manual setup)${NC}"
    else
        echo -e "${YELLOW}   Run this command as root to enable GPIO:${NC}"
        echo -e "${CYAN}   sudo usermod -a -G gpio $PLATFORM_USER${NC}"
        echo -e "${YELLOW}   Then logout and login again for changes to take effect${NC}"
    fi
fi

# Check available disk space
AVAILABLE_SPACE=$(df -BG "$PROJECT_ROOT" | tail -1 | awk '{print $4}' | sed 's/G//')
if [ "$AVAILABLE_SPACE" -lt 5 ]; then
    echo -e "${YELLOW}⚠️  Low disk space: ${AVAILABLE_SPACE}GB available${NC}"
    echo -e "${YELLOW}   PyTorch installation requires at least 5GB free space${NC}"
else
    echo -e "${GREEN}✅ Sufficient disk space: ${AVAILABLE_SPACE}GB available${NC}"
fi

# Check if camera is available (optional)
if [ -c /dev/video0 ] || [ -c /dev/video1 ]; then
    echo -e "${GREEN}✅ Camera device detected${NC}"
else
    echo -e "${YELLOW}⚠️  No camera device detected (optional)${NC}"
    echo -e "${CYAN}   Connect a USB webcam or enable the Pi camera module${NC}"
fi

deactivate 2>/dev/null || true

# Final verification
echo -e "\n${BLUE}🔍 Verifying installation...${NC}"
VERIFICATION_FAILED=false

# Check if venv is working
if [ ! -f "venv/bin/python3" ]; then
    echo -e "${RED}❌ Virtual environment Python not found${NC}"
    VERIFICATION_FAILED=true
else
    echo -e "${GREEN}✅ Virtual environment is working${NC}"
fi

# Check critical packages
echo -e "${CYAN}   Checking critical packages...${NC}"
source venv/bin/activate

# Function to get Python import name from pip package name
get_import_name() {
    local pkg_name="$1"
    case "$pkg_name" in
        opencv-python|opencv-python-headless)
            echo "cv2"
            ;;
        *)
            echo "$pkg_name"
            ;;
    esac
}

for package in torch ultralytics opencv-python flask; do
    IMPORT_NAME=$(get_import_name "$package")
    if python3 -c "import $IMPORT_NAME" 2>/dev/null; then
        VERSION=$(python3 -c "import $IMPORT_NAME; print($IMPORT_NAME.__version__)" 2>/dev/null || echo "installed")
        echo -e "${GREEN}   ✅ $package ($VERSION)${NC}"
    else
        echo -e "${RED}   ❌ $package not found${NC}"
        VERIFICATION_FAILED=true
    fi
done

deactivate

if [ "$VERIFICATION_FAILED" = true ]; then
    echo ""
    echo -e "${YELLOW}⚠️  Some packages failed verification${NC}"
    echo -e "${CYAN}   You may need to install them manually:${NC}"
    echo -e "${CYAN}   source venv/bin/activate${NC}"
    echo -e "${CYAN}   pip install --no-cache-dir -r $REQUIREMENTS_FILE${NC}"
    echo ""
fi

print_completion_message "raspberry_pi"

