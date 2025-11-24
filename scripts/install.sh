#!/bin/bash
# SkyGuard Installation Script
# Supports Raspberry Pi, NVIDIA Jetson, and other Linux platforms

set -e

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
sudo apt update
sudo apt upgrade -y

echo -e "${BLUE}📦 Step 2: Installing system dependencies...${NC}"
# Install core dependencies (required)
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
    libx264-dev

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
    fi
    
    # For Jetson, filter out torch packages if using system packages
    if [ "$USE_SYSTEM_SITE_PACKAGES" = "true" ] && [ "$REQUIREMENTS_FILE" = "requirements-jetson.txt" ]; then
        FILTERED_REQ=$(filter_jetson_requirements "$REQUIREMENTS_FILE")
        echo -e "${CYAN}   Filtered out torch/torchvision/torchaudio (using system CUDA versions)${NC}"
        
        # Remove any existing torch packages from venv BEFORE installation
        remove_torch_from_venv "$PROJECT_ROOT/venv"
        
        # Install filtered requirements (as the platform user if running as root)
        if [ "$(id -u)" -eq 0 ] && [ "$PLATFORM_USER" != "root" ] && id "$PLATFORM_USER" &>/dev/null; then
            runuser -l "$PLATFORM_USER" -c "cd '$PROJECT_ROOT' && source venv/bin/activate && pip install -r '$FILTERED_REQ'"
            # Fix ownership after installation (packages may have been installed as root)
            chown -R "$PLATFORM_USER:$PLATFORM_USER" venv 2>/dev/null || true
        else
            pip install -r "$FILTERED_REQ"
        fi
        
        # Aggressively remove torch packages AGAIN after installation
        echo -e "${CYAN}   Final cleanup: Ensuring no torch packages remain in venv...${NC}"
        remove_torch_from_venv "$PROJECT_ROOT/venv"
        
        rm -f "$FILTERED_REQ"
    else
        if [ "$(id -u)" -eq 0 ] && [ "$PLATFORM_USER" != "root" ] && id "$PLATFORM_USER" &>/dev/null; then
            runuser -l "$PLATFORM_USER" -c "cd '$PROJECT_ROOT' && source venv/bin/activate && pip install -r '$REQUIREMENTS_FILE'"
            # Fix ownership after installation
            chown -R "$PLATFORM_USER:$PLATFORM_USER" venv 2>/dev/null || true
        else
            pip install -r "$REQUIREMENTS_FILE"
        fi
    fi
else
    echo -e "${YELLOW}⚠️  $REQUIREMENTS_FILE not found, using requirements.txt...${NC}"
    if [ "$(id -u)" -eq 0 ] && [ "$PLATFORM_USER" != "root" ] && id "$PLATFORM_USER" &>/dev/null; then
        runuser -l "$PLATFORM_USER" -c "cd '$PROJECT_ROOT' && source venv/bin/activate && pip install -r requirements.txt"
        # Fix ownership after installation
        chown -R "$PLATFORM_USER:$PLATFORM_USER" venv 2>/dev/null || true
    else
        pip install -r requirements.txt
    fi
fi

echo -e "${BLUE}📦 Step 5: Making scripts executable...${NC}"
chmod +x scripts/*.sh 2>/dev/null || true
chmod +x scripts/*.py 2>/dev/null || true

echo -e "${BLUE}📦 Step 6: Creating necessary directories...${NC}"
mkdir -p logs
mkdir -p data/detections
mkdir -p models

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
