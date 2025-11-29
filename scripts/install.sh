#!/bin/bash
# SkyGuard Installation Script
# Supports Raspberry Pi, NVIDIA Jetson, and other Linux platforms

# Don't use set -e - we want to handle errors gracefully
set -o pipefail  # Only fail on pipe errors, not individual commands

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}🛡️  SkyGuard Installation${NC}"
echo "================================"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

# Platform detection function
detect_platform() {
    local platform="unknown"
    local requirements_file="requirements.txt"
    
    # Check for Jetson
    if [ -f "/etc/nv_tegra_release" ] || [ -n "$JETSON_VERSION" ]; then
        platform="jetson"
        requirements_file="requirements-jetson.txt"
        echo -e "${GREEN}✅ NVIDIA Jetson detected${NC}" >&2
    elif [ -f "/proc/device-tree/model" ]; then
        model=$(cat /proc/device-tree/model 2>/dev/null || echo "")
        if echo "$model" | grep -qi "jetson\|tegra"; then
            platform="jetson"
            requirements_file="requirements-jetson.txt"
            echo -e "${GREEN}✅ NVIDIA Jetson detected: $model${NC}" >&2
        elif echo "$model" | grep -qi "raspberry pi"; then
            platform="raspberry_pi"
            requirements_file="requirements-pi.txt"
            echo -e "${GREEN}✅ Raspberry Pi detected: $model${NC}" >&2
        fi
    elif [ -f "/etc/os-release" ]; then
        if grep -qi "raspbian\|raspberry" /etc/os-release 2>/dev/null; then
            platform="raspberry_pi"
            requirements_file="requirements-pi.txt"
            echo -e "${GREEN}✅ Raspberry Pi detected${NC}" >&2
        fi
    fi
    
    # Output only the requirements filename to stdout (for capture)
    echo "$requirements_file"
}

# Detect platform username
detect_platform_username() {
    local username=""
    
    # Check for Jetson
    if [ -f "/etc/nv_tegra_release" ]; then
        username="jad3"
    elif [ -f "/proc/device-tree/model" ]; then
        model=$(cat /proc/device-tree/model 2>/dev/null || echo "")
        if echo "$model" | grep -qi "jetson\|tegra"; then
            username="jad3"
        elif echo "$model" | grep -qi "raspberry pi"; then
            username="pi"
        fi
    elif [ -f "/etc/os-release" ]; then
        if grep -qi "raspbian\|raspberry" /etc/os-release 2>/dev/null; then
            username="pi"
        fi
    fi
    
    # Fallback: use current user if platform not detected
    if [ -z "$username" ]; then
        username=$(whoami)
    fi
    
    echo "$username"
}

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

# Check for system PyTorch on Jetson
check_system_pytorch() {
    python3 -c "
import sys
try:
    import torch
    if torch.cuda.is_available():
        print('CUDA')
    else:
        print('CPU')
except ImportError:
    print('NOT_FOUND')
" 2>/dev/null || echo "NOT_FOUND"
}

# Filter torch packages from requirements file for Jetson
filter_jetson_requirements() {
    local req_file="$1"
    local filtered_file="${req_file}.filtered"
    
    # Create filtered requirements file excluding torch/torchvision/torchaudio
    # Remove lines that start with torch, torchvision, or torchaudio (with optional whitespace/comments)
    # This handles:
    #   - "torch>=2.0", "torch!=2.0", "torch~=2.0" (all version operators)
    #   - "torch[cuda]>=2.0", "torch[cpu]!=2.0" (extras syntax)
    #   - " torch>=2.0", "# torch>=2.0" (with leading whitespace/comments)
    # Character class [>=<~!#] covers: >=, <=, ==, !=, ~=, and # (comment)
    grep -v -E "^[[:space:]#]*(torch|torchvision|torchaudio)(\[[^\]]+\])?[[:space:]]*[>=<~!#]" "$req_file" > "$filtered_file" 2>/dev/null || cp "$req_file" "$filtered_file"
    echo "$filtered_file"
}

# Aggressively remove torch packages from venv (both via pip and filesystem)
remove_torch_from_venv() {
    local venv_path="$1"
    
    if [ ! -d "$venv_path" ]; then
        return 0
    fi
    
    echo -e "${CYAN}   Aggressively removing torch packages from venv...${NC}"
    
    # Fix ownership first (in case packages were installed as root)
    if [ "$(id -u)" -eq 0 ] && [ "$PLATFORM_USER" != "root" ] && id "$PLATFORM_USER" &>/dev/null; then
        echo -e "${CYAN}   Fixing venv ownership to $PLATFORM_USER before removal...${NC}"
        chown -R "$PLATFORM_USER:$PLATFORM_USER" "$venv_path" 2>/dev/null || true
    fi
    
    # First, try pip uninstall if venv is activated
    if [ -f "$venv_path/bin/activate" ]; then
        if [ "$(id -u)" -eq 0 ] && [ "$PLATFORM_USER" != "root" ] && id "$PLATFORM_USER" &>/dev/null; then
            runuser -l "$PLATFORM_USER" -c "cd '$PROJECT_ROOT' && source venv/bin/activate && pip uninstall -y torch torchvision torchaudio" 2>/dev/null || true
        else
            source "$venv_path/bin/activate"
            pip uninstall -y torch torchvision torchaudio 2>/dev/null || true
            deactivate 2>/dev/null || true
        fi
    fi
    
    # Then physically remove from site-packages directories
    for site_packages in "$venv_path"/lib/python*/site-packages; do
        if [ -d "$site_packages" ]; then
            # Remove torch directories
            rm -rf "$site_packages/torch" 2>/dev/null || true
            rm -rf "$site_packages/torchvision" 2>/dev/null || true
            rm -rf "$site_packages/torchaudio" 2>/dev/null || true
            rm -rf "$site_packages/torch-"* 2>/dev/null || true
            rm -rf "$site_packages/torchvision-"* 2>/dev/null || true
            rm -rf "$site_packages/torchaudio-"* 2>/dev/null || true
            
            # Remove torch egg-info and dist-info
            rm -rf "$site_packages"/torch*.egg-info 2>/dev/null || true
            rm -rf "$site_packages"/torch*.dist-info 2>/dev/null || true
            rm -rf "$site_packages"/torchvision*.egg-info 2>/dev/null || true
            rm -rf "$site_packages"/torchvision*.dist-info 2>/dev/null || true
            rm -rf "$site_packages"/torchaudio*.egg-info 2>/dev/null || true
            rm -rf "$site_packages"/torchaudio*.dist-info 2>/dev/null || true
        fi
    done
    
    echo -e "${GREEN}   ✅ Torch packages removed from venv${NC}"
}

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

# Detect platform and select appropriate requirements file (before venv creation)
REQUIREMENTS_FILE=$(detect_platform)
PLATFORM_USER=$(detect_platform_username)
echo -e "${CYAN}   Platform user: $PLATFORM_USER${NC}"

# Check for system PyTorch on Jetson (before venv creation)
USE_SYSTEM_SITE_PACKAGES=false
if [ "$REQUIREMENTS_FILE" = "requirements-jetson.txt" ]; then
    echo -e "${BLUE}📦 Step 3a: Checking PyTorch installation for Jetson...${NC}"
    PYTORCH_STATUS=$(check_system_pytorch)
    if [ "$PYTORCH_STATUS" = "CUDA" ]; then
        echo -e "${GREEN}   ✅ Found CUDA-enabled PyTorch in system${NC}"
        USE_SYSTEM_SITE_PACKAGES=true
    elif [ "$PYTORCH_STATUS" = "CPU" ]; then
        echo -e "${YELLOW}   ⚠️  Found PyTorch but CUDA not available - will use system packages anyway${NC}"
        USE_SYSTEM_SITE_PACKAGES=true
    else
        echo -e "${YELLOW}⚠️  IMPORTANT: PyTorch for Jetson must be installed separately!${NC}"
        echo -e "${YELLOW}   Please install PyTorch from NVIDIA's repository first:${NC}"
        echo ""
        echo -e "${CYAN}   For JetPack 6.1, install the CUDA-enabled PyTorch wheel:${NC}"
        echo -e "${CYAN}   wget https://developer.download.nvidia.com/compute/redist/jp/v61/pytorch/torch-2.5.0a0+872d972e41.nv24.08.17622132-cp310-cp310-linux_aarch64.whl${NC}"
        echo -e "${CYAN}   pip3 install torch-2.5.0a0+872d972e41.nv24.08.17622132-cp310-cp310-linux_aarch64.whl${NC}"
        echo -e "${CYAN}   pip3 install torchvision${NC}"
        echo ""
        echo -e "${YELLOW}   See: https://forums.developer.nvidia.com/t/pytorch-for-jetson/ for other versions${NC}"
        echo ""
        read -p "Press Enter to continue after installing PyTorch, or Ctrl+C to cancel..."
        # Re-check after user installs
        PYTORCH_STATUS=$(check_system_pytorch)
        if [ "$PYTORCH_STATUS" != "NOT_FOUND" ]; then
            USE_SYSTEM_SITE_PACKAGES=true
        fi
    fi
fi

echo -e "${BLUE}📦 Step 3: Creating Python virtual environment...${NC}"
if [ ! -d "venv" ]; then
    if [ "$USE_SYSTEM_SITE_PACKAGES" = "true" ]; then
        echo -e "${CYAN}   Creating venv with system site packages (to use CUDA PyTorch)${NC}"
        python3 -m venv --system-site-packages venv
    else
        python3 -m venv venv
    fi
    echo -e "${GREEN}✅ Virtual environment created${NC}"
    
    # If running as root, ensure venv is owned by the platform user
    if [ "$(id -u)" -eq 0 ] && [ "$PLATFORM_USER" != "root" ]; then
        if id "$PLATFORM_USER" &>/dev/null; then
            echo -e "${CYAN}   Setting venv ownership to $PLATFORM_USER...${NC}"
            chown -R "$PLATFORM_USER:$PLATFORM_USER" venv 2>/dev/null || true
        fi
    fi
else
    echo -e "${YELLOW}⚠️  Virtual environment already exists${NC}"
    if [ "$USE_SYSTEM_SITE_PACKAGES" = "true" ]; then
        # Check if existing venv has system-site-packages
        if [ -f "venv/pyvenv.cfg" ] && ! grep -q "include-system-site-packages = true" "venv/pyvenv.cfg" 2>/dev/null; then
            echo -e "${YELLOW}   ⚠️  Existing venv does NOT have system-site-packages${NC}"
            echo -e "${YELLOW}   Removing old venv to recreate with system site packages...${NC}"
            rm -rf venv
            python3 -m venv --system-site-packages venv
            echo -e "${GREEN}✅ Virtual environment recreated with system site packages${NC}"
            
            # Set ownership after recreation
            if [ "$(id -u)" -eq 0 ] && [ "$PLATFORM_USER" != "root" ]; then
                if id "$PLATFORM_USER" &>/dev/null; then
                    echo -e "${CYAN}   Setting venv ownership to $PLATFORM_USER...${NC}"
                    chown -R "$PLATFORM_USER:$PLATFORM_USER" venv 2>/dev/null || true
                fi
            fi
        fi
    fi
    
    # Fix ownership of existing venv if running as root
    if [ "$(id -u)" -eq 0 ] && [ "$PLATFORM_USER" != "root" ]; then
        if id "$PLATFORM_USER" &>/dev/null; then
            echo -e "${CYAN}   Fixing venv ownership to $PLATFORM_USER...${NC}"
            chown -R "$PLATFORM_USER:$PLATFORM_USER" venv 2>/dev/null || true
        fi
    fi
fi

echo -e "${BLUE}📦 Step 4: Activating virtual environment and installing Python packages...${NC}"

# Activate venv
source venv/bin/activate

# Upgrade pip first (as the platform user if running as root)
if [ "$(id -u)" -eq 0 ] && [ "$PLATFORM_USER" != "root" ] && id "$PLATFORM_USER" &>/dev/null; then
    runuser -l "$PLATFORM_USER" -c "cd '$PROJECT_ROOT' && source venv/bin/activate && pip install --upgrade pip"
    # Fix ownership after pip upgrade (packages may have been installed as root)
    chown -R "$PLATFORM_USER:$PLATFORM_USER" venv 2>/dev/null || true
else
    pip install --upgrade pip
fi

# Install dependencies
if [ -f "$REQUIREMENTS_FILE" ]; then
    echo -e "${BLUE}Installing from $REQUIREMENTS_FILE...${NC}"
    if [ "$REQUIREMENTS_FILE" = "requirements-pi.txt" ]; then
        echo -e "${YELLOW}Note: You may be prompted to install:${NC}"
        echo -e "${YELLOW}  - Raspberry Pi hardware dependencies (RPi.GPIO) - Answer 'yes' to enable GPIO features${NC}"
        echo -e "${YELLOW}  - Notification dependencies (Twilio, Pushbullet) - Answer 'yes' to enable notifications${NC}"
        echo -e "${CYAN}   PyTorch installation on Raspberry Pi can take 15-30 minutes...${NC}"
        echo -e "${CYAN}   Please be patient and ensure you have a stable internet connection${NC}"
    fi
    
    # For Jetson, filter out torch packages if using system packages
    if [ "$USE_SYSTEM_SITE_PACKAGES" = "true" ] && [ "$REQUIREMENTS_FILE" = "requirements-jetson.txt" ]; then
        FILTERED_REQ=$(filter_jetson_requirements "$REQUIREMENTS_FILE")
        echo -e "${CYAN}   Filtered out torch/torchvision/torchaudio (using system CUDA versions)${NC}"
        
        # Remove any existing torch packages from venv BEFORE installation
        remove_torch_from_venv "$PROJECT_ROOT/venv"
        
        # Install filtered requirements (as the platform user if running as root)
        INSTALL_SUCCESS=false
        if [ "$(id -u)" -eq 0 ] && [ "$PLATFORM_USER" != "root" ] && id "$PLATFORM_USER" &>/dev/null; then
            if runuser -l "$PLATFORM_USER" -c "cd '$PROJECT_ROOT' && source venv/bin/activate && pip install --no-cache-dir -r '$FILTERED_REQ'"; then
                INSTALL_SUCCESS=true
            fi
            # Fix ownership after installation (packages may have been installed as root)
            chown -R "$PLATFORM_USER:$PLATFORM_USER" venv 2>/dev/null || true
        else
            if pip install --no-cache-dir -r "$FILTERED_REQ"; then
                INSTALL_SUCCESS=true
            fi
        fi
        
        if [ "$INSTALL_SUCCESS" = false ]; then
            echo -e "${RED}❌ Failed to install some packages from $FILTERED_REQ${NC}"
            echo -e "${YELLOW}   Continuing anyway...${NC}"
        fi
        
        # Aggressively remove torch packages AGAIN after installation
        echo -e "${CYAN}   Final cleanup: Ensuring no torch packages remain in venv...${NC}"
        remove_torch_from_venv "$PROJECT_ROOT/venv"
        
        rm -f "$FILTERED_REQ"
    else
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

echo -e "${BLUE}📦 Step 5: Making scripts executable...${NC}"
chmod +x scripts/*.sh 2>/dev/null || true
chmod +x scripts/*.py 2>/dev/null || true

echo -e "${BLUE}📦 Step 6: Creating necessary directories...${NC}"
mkdir -p logs
mkdir -p data/detections
mkdir -p models

# Raspberry Pi specific setup
if [ "$REQUIREMENTS_FILE" = "requirements-pi.txt" ]; then
    echo -e "${BLUE}📦 Step 7: Raspberry Pi specific setup...${NC}"
    
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
fi

# Verify PyTorch CUDA on Jetson
if [ "$REQUIREMENTS_FILE" = "requirements-jetson.txt" ]; then
    echo -e "\n${BLUE}🔍 Verifying PyTorch CUDA installation...${NC}"
    
    # Check if torch is installed in venv (should NOT be)
    TORCH_IN_VENV=$(python3 -c "
import sys
import os
try:
    import torch
    torch_path = os.path.abspath(torch.__file__)
    venv_path = os.path.abspath('$PROJECT_ROOT/venv')
    if venv_path in torch_path:
        print('venv')
    else:
        print('system')
except Exception as e:
    print('unknown')
" 2>/dev/null || echo "unknown")
    
    # Check CUDA availability
    PYTORCH_CHECK=$(python3 -c "import torch; print('CUDA' if torch.cuda.is_available() else 'CPU')" 2>/dev/null || echo "NOT_FOUND")
    
    if [ "$PYTORCH_CHECK" = "CUDA" ]; then
        CUDA_DEVICE=$(python3 -c "import torch; print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A')" 2>/dev/null)
        TORCH_VERSION=$(python3 -c "import torch; print(torch.__version__)" 2>/dev/null || echo "unknown")
        echo -e "${GREEN}   ✅ PyTorch CUDA is working!${NC}"
        echo -e "${CYAN}   Version: $TORCH_VERSION${NC}"
        echo -e "${CYAN}   Device: $CUDA_DEVICE${NC}"
        echo -e "${CYAN}   Source: $TORCH_IN_VENV${NC}"
        
        # Verify it's using system PyTorch, not venv version
        if [ "$TORCH_IN_VENV" = "venv" ]; then
            echo -e "${RED}   ❌ ERROR: PyTorch is installed in venv instead of using system version!${NC}"
            echo -e "${YELLOW}   This will cause CUDA issues. Aggressively removing venv-installed torch...${NC}"
            remove_torch_from_venv "$PROJECT_ROOT/venv"
            echo -e "${YELLOW}   ⚠️  Please verify system PyTorch is accessible and test again${NC}"
        elif [ "$TORCH_IN_VENV" = "system" ]; then
            echo -e "${GREEN}   ✅ Confirmed: Using system PyTorch (correct)${NC}"
        fi
    else
        echo -e "${RED}   ❌ PyTorch CUDA not available${NC}"
        echo -e "${CYAN}   Source detected: $TORCH_IN_VENV${NC}"
        
        if [ "$TORCH_IN_VENV" = "venv" ]; then
            echo -e "${RED}   ❌ CRITICAL: PyTorch is installed in venv (wrong version)${NC}"
            echo -e "${YELLOW}   Removing venv-installed torch packages...${NC}"
            remove_torch_from_venv "$PROJECT_ROOT/venv"
            echo -e "${CYAN}   Testing system PyTorch again...${NC}"
            PYTORCH_CHECK=$(python3 -c "import torch; print('CUDA' if torch.cuda.is_available() else 'CPU')" 2>/dev/null || echo "NOT_FOUND")
            if [ "$PYTORCH_CHECK" = "CUDA" ]; then
                echo -e "${GREEN}   ✅ Fixed! PyTorch CUDA now working from system${NC}"
            else
                echo -e "${YELLOW}   ⚠️  Still not working. Check that PyTorch was installed system-wide with CUDA support${NC}"
            fi
        else
            echo -e "${YELLOW}   ⚠️  Check that PyTorch was installed system-wide with CUDA support${NC}"
        fi
    fi
fi

echo ""
echo -e "${GREEN}✅ Installation complete!${NC}"
echo ""

# Final verification
echo -e "${BLUE}🔍 Verifying installation...${NC}"
VERIFICATION_FAILED=false

# Check if venv is working
if [ ! -f "venv/bin/python3" ]; then
    echo -e "${RED}❌ Virtual environment Python not found${NC}"
    VERIFICATION_FAILED=true
else
    echo -e "${GREEN}✅ Virtual environment is working${NC}"
fi

# Check critical packages
if [ "$REQUIREMENTS_FILE" = "requirements-pi.txt" ]; then
    echo -e "${CYAN}   Checking critical packages...${NC}"
    source venv/bin/activate
    
    for package in torch ultralytics opencv-python flask; do
        if python3 -c "import $package" 2>/dev/null; then
            VERSION=$(python3 -c "import $package; print($package.__version__)" 2>/dev/null || echo "installed")
            echo -e "${GREEN}   ✅ $package ($VERSION)${NC}"
        else
            echo -e "${RED}   ❌ $package not found${NC}"
            VERIFICATION_FAILED=true
        fi
    done
    
    deactivate
fi

if [ "$VERIFICATION_FAILED" = true ]; then
    echo ""
    echo -e "${YELLOW}⚠️  Some packages failed verification${NC}"
    echo -e "${CYAN}   You may need to install them manually:${NC}"
    echo -e "${CYAN}   source venv/bin/activate${NC}"
    echo -e "${CYAN}   pip install --no-cache-dir -r $REQUIREMENTS_FILE${NC}"
    echo ""
fi

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

if [ "$REQUIREMENTS_FILE" = "requirements-pi.txt" ]; then
    echo -e "${CYAN}💡 Raspberry Pi Tips:${NC}"
    echo "   - If GPIO doesn't work, logout and login again after adding to gpio group"
    echo "   - Monitor temperature: watch -n 1 vcgencmd measure_temp"
    echo "   - Check power supply: vcgencmd measure_volts"
    echo "   - For better performance, use a 5V/5A power supply"
    echo ""
fi