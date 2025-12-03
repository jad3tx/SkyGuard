#!/bin/bash
# SkyGuard Installation Common Functions
# Shared functions used by platform-specific install scripts

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

# Run pip command as appropriate user
run_pip_as_user() {
    local current_user=$(whoami)
    local target_user="$PLATFORM_USER"
    
    # If already running as target user, just run the command
    if [ "$current_user" = "$target_user" ]; then
        "$@"
    # If running as root, switch to target user
    elif [ "$current_user" = "root" ]; then
        if id "$target_user" &>/dev/null; then
            runuser -l "$target_user" -c "cd '$PROJECT_ROOT' && $*"
        else
            echo -e "${YELLOW}   ⚠️  User $target_user not found, running as current user${NC}"
            "$@"
        fi
    # Otherwise, run as current user
    else
        "$@"
    fi
}

# Install system dependencies (common to all platforms)
install_system_dependencies() {
    echo -e "${BLUE}📦 Step 1: Updating system packages...${NC}"
    if ! sudo apt update; then
        echo -e "${RED}❌ Failed to update package lists${NC}"
        exit 1
    fi

    if ! sudo apt upgrade -y; then
        echo -e "${YELLOW}⚠️  Some packages failed to upgrade, continuing...${NC}"
    fi

    echo -e "${BLUE}📦 Step 2: Installing system dependencies...${NC}"

    # Check Python version first
    PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1 || echo "unknown")
    PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
    PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)

    echo -e "${CYAN}   Detected Python version: $PYTHON_VERSION${NC}"

    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
        echo -e "${RED}❌ Python 3.8+ is required. Found: $PYTHON_VERSION${NC}"
        echo -e "${YELLOW}   Please upgrade Python and try again${NC}"
        exit 1
    fi

    # Install core dependencies (required)
    echo -e "${CYAN}   Installing core dependencies...${NC}"
    if ! sudo apt install -y \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        git \
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
        libx264-dev; then
        echo -e "${RED}❌ Failed to install core dependencies${NC}"
        exit 1
    fi

    # Try to install GitHub CLI (optional - may not be available in all repos)
    echo -e "${CYAN}   Installing GitHub CLI (optional)...${NC}"
    if sudo apt install -y gh 2>/dev/null; then
        echo -e "${GREEN}✅ GitHub CLI installed${NC}"
    else
        echo -e "${YELLOW}⚠️  GitHub CLI not available in default repos (optional, continuing...)${NC}"
        echo -e "${CYAN}   You can install it later if needed:${NC}"
        echo -e "${CYAN}   curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg${NC}"
        echo -e "${CYAN}   echo \"deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main\" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null${NC}"
        echo -e "${CYAN}   sudo apt update && sudo apt install gh${NC}"
    fi

    # Install BLAS/LAPACK library (try openblas first, fallback to atlas if needed)
    echo -e "${BLUE}Installing BLAS/LAPACK library...${NC}"
    if sudo apt install -y libopenblas-dev 2>/dev/null; then
        echo -e "${GREEN}✅ libopenblas-dev installed${NC}"
    else
        echo -e "${YELLOW}⚠️  libopenblas-dev not available, trying libatlas-base-dev...${NC}"
        sudo apt install -y libatlas-base-dev || echo -e "${YELLOW}⚠️  BLAS/LAPACK library not installed (may affect NumPy performance)${NC}"
    fi
}

# Create virtual environment with proper ownership
create_venv() {
    local use_system_site_packages="$1"
    local venv_path="$2"
    
    if [ ! -d "$venv_path" ]; then
        if [ "$use_system_site_packages" = "true" ]; then
            echo -e "${CYAN}   Creating venv with system site packages (to use CUDA PyTorch)${NC}"
            python3 -m venv --system-site-packages "$venv_path"
        else
            python3 -m venv "$venv_path"
        fi
        echo -e "${GREEN}✅ Virtual environment created${NC}"
        
        # If running as root, ensure venv is owned by the platform user
        if [ "$(id -u)" -eq 0 ] && [ "$PLATFORM_USER" != "root" ]; then
            if id "$PLATFORM_USER" &>/dev/null; then
                echo -e "${CYAN}   Setting venv ownership to $PLATFORM_USER...${NC}"
                chown -R "$PLATFORM_USER:$PLATFORM_USER" "$venv_path" 2>/dev/null || true
            fi
        fi
    else
        echo -e "${YELLOW}⚠️  Virtual environment already exists${NC}"
        if [ "$use_system_site_packages" = "true" ]; then
            # Check if existing venv has system-site-packages
            if [ -f "$venv_path/pyvenv.cfg" ] && ! grep -q "include-system-site-packages = true" "$venv_path/pyvenv.cfg" 2>/dev/null; then
                echo -e "${YELLOW}   ⚠️  Existing venv does NOT have system-site-packages${NC}"
                echo -e "${YELLOW}   Removing old venv to recreate with system site packages...${NC}"
                rm -rf "$venv_path"
                python3 -m venv --system-site-packages "$venv_path"
                echo -e "${GREEN}✅ Virtual environment recreated with system site packages${NC}"
                
                # Set ownership after recreation
                if [ "$(id -u)" -eq 0 ] && [ "$PLATFORM_USER" != "root" ]; then
                    if id "$PLATFORM_USER" &>/dev/null; then
                        echo -e "${CYAN}   Setting venv ownership to $PLATFORM_USER...${NC}"
                        chown -R "$PLATFORM_USER:$PLATFORM_USER" "$venv_path" 2>/dev/null || true
                    fi
                fi
            fi
        fi
        
        # Fix ownership of existing venv if running as root
        if [ "$(id -u)" -eq 0 ] && [ "$PLATFORM_USER" != "root" ]; then
            if id "$PLATFORM_USER" &>/dev/null; then
                echo -e "${CYAN}   Fixing venv ownership to $PLATFORM_USER...${NC}"
                chown -R "$PLATFORM_USER:$PLATFORM_USER" "$venv_path" 2>/dev/null || true
            fi
        fi
    fi
}

# Upgrade pip in virtual environment
upgrade_pip() {
    local venv_path="$1"
    
    # Activate venv
    source "$venv_path/bin/activate"
    
    # Upgrade pip first (as the platform user if running as root)
    if [ "$(id -u)" -eq 0 ] && [ "$PLATFORM_USER" != "root" ] && id "$PLATFORM_USER" &>/dev/null; then
        runuser -l "$PLATFORM_USER" -c "cd '$PROJECT_ROOT' && source $venv_path/bin/activate && pip install --upgrade pip"
        # Fix ownership after pip upgrade (packages may have been installed as root)
        chown -R "$PLATFORM_USER:$PLATFORM_USER" "$venv_path" 2>/dev/null || true
    else
        pip install --upgrade pip
    fi
}

# Create necessary directories
create_directories() {
    echo -e "${BLUE}📦 Creating necessary directories...${NC}"
    mkdir -p logs
    mkdir -p data/detections
    mkdir -p models
}

# Make scripts executable
make_scripts_executable() {
    echo -e "${BLUE}📦 Making scripts executable...${NC}"
    chmod +x scripts/*.sh 2>/dev/null || true
    chmod +x scripts/*.py 2>/dev/null || true
}

# Print installation completion message
print_completion_message() {
    local platform="$1"
    
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
    echo "   Open http://<DEVICE_IP_ADDRESS>:8080 in your browser"
    echo ""
    
    if [ "$platform" = "raspberry_pi" ]; then
        echo -e "${CYAN}💡 Raspberry Pi Tips:${NC}"
        echo "   - If GPIO doesn't work, logout and login again after adding to gpio group"
        echo "   - Monitor temperature: watch -n 1 vcgencmd measure_temp"
        echo "   - Check power supply: vcgencmd measure_volts"
        echo "   - For better performance, use a 5V/5A power supply"
        echo ""
    fi
}

