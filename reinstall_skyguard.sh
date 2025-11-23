#!/bin/bash
# SkyGuard Reinstallation Script
# Complete uninstall and fresh install from GitHub
# Supports Raspberry Pi and NVIDIA Jetson devices

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default values
SKYGUARD_PATH=""
GITHUB_REPO="https://github.com/jad3tx/SkyGuard.git"
BRANCH="main"
SKIP_BACKUP=true
FORCE=false

# Platform detection
detect_platform() {
    local platform="unknown"
    local username=""
    
    # Check for Jetson
    if [ -f "/etc/nv_tegra_release" ]; then
        platform="jetson"
        username="jad3"
        echo -e "${GREEN}✅ NVIDIA Jetson detected${NC}" >&2
    elif [ -f "/proc/device-tree/model" ]; then
        model=$(cat /proc/device-tree/model 2>/dev/null || echo "")
        if echo "$model" | grep -qi "jetson\|tegra"; then
            platform="jetson"
            username="jad3"
            echo -e "${GREEN}✅ NVIDIA Jetson detected: $model${NC}" >&2
        elif echo "$model" | grep -qi "raspberry pi"; then
            platform="raspberry_pi"
            username="pi"
            echo -e "${GREEN}✅ Raspberry Pi detected: $model${NC}" >&2
        fi
    elif [ -f "/etc/os-release" ]; then
        if grep -qi "raspbian\|raspberry" /etc/os-release 2>/dev/null; then
            platform="raspberry_pi"
            username="pi"
            echo -e "${GREEN}✅ Raspberry Pi detected${NC}" >&2
        fi
    fi
    
    # Fallback: use current user if platform not detected
    if [ -z "$username" ]; then
        username=$(whoami)
        echo -e "${YELLOW}⚠️  Platform not detected, using current user: $username${NC}" >&2
    fi
    
    # Store platform globally for requirements file selection
    DETECTED_PLATFORM="$platform"
    
    echo "$username"
}

# Get requirements file based on platform
get_requirements_file() {
    if [ "$DETECTED_PLATFORM" = "jetson" ]; then
        echo "requirements-jetson.txt"
    elif [ "$DETECTED_PLATFORM" = "raspberry_pi" ]; then
        echo "requirements-pi.txt"
    else
        echo "requirements.txt"
    fi
}

# Filter out PyTorch packages for Jetson (use system-installed CUDA versions)
filter_jetson_requirements() {
    local req_file="$1"
    local filtered_file="${req_file}.filtered"
    
    # Create filtered requirements file excluding torch/torchvision/torchaudio
    # Remove lines that start with torch, torchvision, or torchaudio (with optional whitespace/comments)
    # This handles: "torch>=2.0", " torch>=2.0", "# torch>=2.0", etc.
    grep -v -E "^[[:space:]#]*(torch|torchvision|torchaudio)[[:space:]]*[>=<#]" "$req_file" > "$filtered_file" 2>/dev/null || cp "$req_file" "$filtered_file"
    echo "$filtered_file"
}

# Check if PyTorch is installed system-wide
check_system_pytorch() {
    python3 -c "import torch; print('CUDA' if torch.cuda.is_available() else 'CPU')" 2>/dev/null
}

# Detect platform and get username
echo -e "${BLUE}🔍 Detecting platform...${NC}"
DETECTED_USERNAME=$(detect_platform)
echo -e "${CYAN}   Using username: $DETECTED_USERNAME${NC}"

# Print usage
usage() {
    echo "SkyGuard Reinstallation Script"
    echo "=============================="
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    DEFAULT_PATH="/home/$DETECTED_USERNAME/SkyGuard"
    echo "  --path PATH       SkyGuard installation path (default: $DEFAULT_PATH)"
    echo "  --repo URL        GitHub repository URL (default: https://github.com/jad3tx/SkyGuard.git)"
    echo "  --branch BRANCH   Branch to clone (default: main)"
    echo "  --backup          Create backup before removal (default: no backup)"
    echo "  --skip-backup     Skip creating backup before removal (default behavior)"
    echo "  --force           Force removal without confirmation"
    echo "  --help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Reinstall at default location"
    echo "  $0 --path /opt/SkyGuard              # Reinstall at custom path"
    echo "  $0 --skip-backup --force              # Skip backup and force removal"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --path)
            SKYGUARD_PATH="$2"
            shift 2
            ;;
        --repo)
            GITHUB_REPO="$2"
            shift 2
            ;;
        --branch)
            BRANCH="$2"
            shift 2
            ;;
        --backup)
            SKIP_BACKUP=false
            shift
            ;;
        --skip-backup)
            SKIP_BACKUP=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Unknown option: $1${NC}"
            usage
            exit 1
            ;;
    esac
done

# Determine SkyGuard path
if [ -z "$SKYGUARD_PATH" ]; then
    SKYGUARD_PATH="/home/$DETECTED_USERNAME/SkyGuard"
fi

SKYGUARD_PATH=$(realpath "$SKYGUARD_PATH" 2>/dev/null || echo "$SKYGUARD_PATH")
echo -e "${CYAN}SkyGuard path: $SKYGUARD_PATH${NC}"

# Step 1: Stop all SkyGuard processes
echo -e "\n${BLUE}🛑 Step 1: Stopping all SkyGuard processes...${NC}"
if pgrep -f "python.*skyguard.main" >/dev/null 2>&1; then
    echo -e "${CYAN}   Found running SkyGuard main processes${NC}"
    pkill -f "python.*skyguard.main" || true
    sleep 2
    echo -e "${GREEN}   ✅ Main processes stopped${NC}"
else
    echo -e "${CYAN}   No running main processes found${NC}"
fi

if pgrep -f "skyguard.*web.*app" >/dev/null 2>&1; then
    echo -e "${CYAN}   Found running SkyGuard web portal processes${NC}"
    pkill -f "skyguard.*web.*app" || true
    sleep 2
    echo -e "${GREEN}   ✅ Web portal processes stopped${NC}"
else
    echo -e "${CYAN}   No running web portal processes found${NC}"
fi

# Step 2: Stop systemd services (if they exist)
echo -e "\n${BLUE}🔧 Step 2: Checking for systemd services...${NC}"
if systemctl list-units --type=service --all | grep -q "skyguard.service"; then
    echo -e "${CYAN}   Found skyguard.service${NC}"
    if systemctl is-active --quiet skyguard.service 2>/dev/null; then
        echo -e "${CYAN}   Stopping skyguard.service${NC}"
        sudo systemctl stop skyguard.service || true
    fi
    echo -e "${CYAN}   Disabling skyguard.service${NC}"
    sudo systemctl disable skyguard.service || true
    echo -e "${GREEN}   ✅ skyguard.service disabled${NC}"
fi

if systemctl list-units --type=service --all | grep -q "skyguard-web.service"; then
    echo -e "${CYAN}   Found skyguard-web.service${NC}"
    if systemctl is-active --quiet skyguard-web.service 2>/dev/null; then
        echo -e "${CYAN}   Stopping skyguard-web.service${NC}"
        sudo systemctl stop skyguard-web.service || true
    fi
    echo -e "${CYAN}   Disabling skyguard-web.service${NC}"
    sudo systemctl disable skyguard-web.service || true
    echo -e "${GREEN}   ✅ skyguard-web.service disabled${NC}"
fi

# Step 3: Backup configuration (optional)
if [ "$SKIP_BACKUP" = false ] && [ -d "$SKYGUARD_PATH" ]; then
    echo -e "\n${BLUE}💾 Step 3: Creating backup of configuration...${NC}"
    BACKUP_PATH="${SKYGUARD_PATH}.backup.$(date +%Y%m%d_%H%M%S)"
    
    if [ -d "$SKYGUARD_PATH/config" ] || [ -d "$SKYGUARD_PATH/models" ]; then
        mkdir -p "$BACKUP_PATH"
        
        if [ -d "$SKYGUARD_PATH/config" ]; then
            cp -r "$SKYGUARD_PATH/config" "$BACKUP_PATH/" 2>/dev/null || true
            echo -e "${GREEN}   ✅ Configuration backed up to: $BACKUP_PATH${NC}"
        fi
        
        if [ -d "$SKYGUARD_PATH/models" ]; then
            cp -r "$SKYGUARD_PATH/models" "$BACKUP_PATH/" 2>/dev/null || true
            echo -e "${GREEN}   ✅ Models backed up to: $BACKUP_PATH${NC}"
        fi
    else
        echo -e "${CYAN}   No configuration or models to backup${NC}"
    fi
fi

# Step 4: Remove SkyGuard directory
echo -e "\n${BLUE}🗑️  Step 4: Removing SkyGuard directory...${NC}"
if [ -d "$SKYGUARD_PATH" ]; then
    if [ "$FORCE" = true ]; then
        REMOVE="y"
    else
        read -p "   Remove directory '$SKYGUARD_PATH'? (y/N): " REMOVE
    fi
    
    if [ "$REMOVE" = "y" ] || [ "$REMOVE" = "Y" ]; then
        echo -e "${CYAN}   Removing: $SKYGUARD_PATH${NC}"
        rm -rf "$SKYGUARD_PATH"
        sleep 1
        echo -e "${GREEN}   ✅ Directory removed${NC}"
    else
        echo -e "${YELLOW}   ⚠️  Skipping directory removal${NC}"
        exit 0
    fi
else
    echo -e "${CYAN}   Directory does not exist, skipping removal${NC}"
fi

# Step 5: Clone GitHub repository
echo -e "\n${BLUE}📥 Step 5: Cloning GitHub repository...${NC}"

# Check if git is available
if ! command -v git &> /dev/null; then
    echo -e "${RED}   ❌ Git is not installed${NC}"
    echo -e "${YELLOW}   Installing git...${NC}"
    sudo apt update
    sudo apt install -y git
fi

PARENT_PATH=$(dirname "$SKYGUARD_PATH")
mkdir -p "$PARENT_PATH"

echo -e "${CYAN}   Repository: $GITHUB_REPO${NC}"
echo -e "${CYAN}   Branch: $BRANCH${NC}"
echo -e "${CYAN}   Destination: $SKYGUARD_PATH${NC}"
echo -e "${CYAN}   Cloning repository...${NC}"

cd "$PARENT_PATH"
git clone -b "$BRANCH" "$GITHUB_REPO" "$SKYGUARD_PATH"

if [ $? -ne 0 ]; then
    echo -e "${RED}   ❌ Failed to clone repository${NC}"
    exit 1
fi

echo -e "${GREEN}   ✅ Repository cloned successfully${NC}"

# Step 6: Fix Jetson venv if needed (BEFORE installation)
if [ "$DETECTED_PLATFORM" = "jetson" ] && [ -d "$SKYGUARD_PATH/venv" ]; then
    echo -e "\n${BLUE}🔧 Step 6a: Fixing Jetson virtual environment...${NC}"
    
    # Check if venv has system site packages enabled
    if [ -f "$SKYGUARD_PATH/venv/pyvenv.cfg" ]; then
        if grep -q "include-system-site-packages = true" "$SKYGUARD_PATH/venv/pyvenv.cfg" 2>/dev/null; then
            echo -e "${GREEN}   ✅ Virtual environment already configured with system site packages${NC}"
        else
            echo -e "${YELLOW}   ⚠️  Virtual environment exists but does NOT have system site packages${NC}"
            echo -e "${CYAN}   This will prevent access to system-installed CUDA PyTorch${NC}"
            echo -e "${CYAN}   Removing old venv to recreate with system site packages...${NC}"
            
            # Remove old venv
            rm -rf "$SKYGUARD_PATH/venv"
            echo -e "${GREEN}   ✅ Old venv removed${NC}"
        fi
    else
        echo -e "${YELLOW}   ⚠️  Virtual environment exists but configuration unclear${NC}"
        echo -e "${CYAN}   Removing venv to ensure clean installation...${NC}"
        rm -rf "$SKYGUARD_PATH/venv"
        echo -e "${GREEN}   ✅ Old venv removed${NC}"
    fi
    
    # Also check for and remove any torch packages that might have been installed in venv
    if [ -d "$SKYGUARD_PATH/venv" ]; then
        echo -e "${CYAN}   Checking for venv-installed torch packages...${NC}"
        if [ -f "$SKYGUARD_PATH/venv/bin/activate" ]; then
            source "$SKYGUARD_PATH/venv/bin/activate"
            # Check if torch is installed in venv (not system)
            if python3 -c "import torch; import sys; print('venv' if 'venv' in sys.executable else 'system')" 2>/dev/null | grep -q "venv"; then
                echo -e "${YELLOW}   ⚠️  Found torch installed in venv - will be removed when venv is recreated${NC}"
            fi
            deactivate 2>/dev/null || true
        fi
    fi
fi

# Step 6: Run installation
echo -e "\n${BLUE}📦 Step 6: Running installation...${NC}"
cd "$SKYGUARD_PATH"

# Check for system PyTorch on Jetson
if [ "$DETECTED_PLATFORM" = "jetson" ]; then
    echo -e "${CYAN}   Checking for system-installed PyTorch...${NC}"
    PYTORCH_STATUS=$(check_system_pytorch)
    if [ "$PYTORCH_STATUS" = "CUDA" ]; then
        echo -e "${GREEN}   ✅ Found CUDA-enabled PyTorch in system${NC}"
        USE_SYSTEM_SITE_PACKAGES=true
    elif [ "$PYTORCH_STATUS" = "CPU" ]; then
        echo -e "${YELLOW}   ⚠️  Found PyTorch but CUDA not available - will use system packages anyway${NC}"
        USE_SYSTEM_SITE_PACKAGES=true
    else
        echo -e "${YELLOW}   ⚠️  No system PyTorch found - will install from requirements${NC}"
        USE_SYSTEM_SITE_PACKAGES=false
    fi
else
    USE_SYSTEM_SITE_PACKAGES=false
fi

# Check for uv (recommended package manager)
if command -v uv &> /dev/null; then
    echo -e "${CYAN}   Using uv for installation...${NC}"
    echo -e "${CYAN}   Creating virtual environment...${NC}"
    
    # For Jetson with system PyTorch, use --system-site-packages
    # Also remove venv if it exists without system site packages
    if [ "$USE_SYSTEM_SITE_PACKAGES" = "true" ] && [ -d "venv" ]; then
        # Double-check: if venv exists but doesn't have system site packages, remove it
        if [ -f "venv/pyvenv.cfg" ]; then
            if ! grep -q "include-system-site-packages = true" venv/pyvenv.cfg 2>/dev/null; then
                echo -e "${YELLOW}   ⚠️  Existing venv does not have system site packages - removing it${NC}"
                rm -rf venv
            fi
        fi
    fi
    
    if [ "$USE_SYSTEM_SITE_PACKAGES" = "true" ]; then
        echo -e "${CYAN}   Creating venv with system site packages (to use CUDA PyTorch)${NC}"
        uv venv --system-site-packages
    else
        uv venv
    fi
    
    echo -e "${CYAN}   Installing dependencies...${NC}"
    # Select requirements file based on detected platform
    REQ_FILE=$(get_requirements_file)
    if [ -f "$REQ_FILE" ]; then
        echo -e "${CYAN}   Using requirements file: $REQ_FILE${NC}"
        
        # For Jetson, filter out torch packages if using system packages
        if [ "$USE_SYSTEM_SITE_PACKAGES" = "true" ] && [ "$DETECTED_PLATFORM" = "jetson" ]; then
            FILTERED_REQ=$(filter_jetson_requirements "$REQ_FILE")
            echo -e "${CYAN}   Filtered out torch/torchvision/torchaudio (using system CUDA versions)${NC}"
            
            # Uninstall any existing torch packages from venv BEFORE installation
            echo -e "${CYAN}   Removing any existing venv-installed torch packages...${NC}"
            uv pip uninstall -y torch torchvision torchaudio 2>/dev/null || true
            
            # Install filtered requirements
            uv pip install -r "$FILTERED_REQ"
            
            # Uninstall torch packages AGAIN after installation (in case dependencies pulled them in)
            echo -e "${CYAN}   Ensuring no torch packages were installed in venv...${NC}"
            uv pip uninstall -y torch torchvision torchaudio 2>/dev/null || true
            
            rm -f "$FILTERED_REQ"
        else
            uv pip install -r "$REQ_FILE"
        fi
    elif [ -f "requirements.txt" ]; then
        echo -e "${CYAN}   Using fallback requirements file: requirements.txt${NC}"
        if [ "$USE_SYSTEM_SITE_PACKAGES" = "true" ] && [ "$DETECTED_PLATFORM" = "jetson" ]; then
            FILTERED_REQ=$(filter_jetson_requirements "requirements.txt")
            echo -e "${CYAN}   Filtered out torch/torchvision/torchaudio (using system CUDA versions)${NC}"
            
            # Uninstall any existing torch packages from venv BEFORE installation
            echo -e "${CYAN}   Removing any existing venv-installed torch packages...${NC}"
            uv pip uninstall -y torch torchvision torchaudio 2>/dev/null || true
            
            # Install filtered requirements
            uv pip install -r "$FILTERED_REQ"
            
            # Uninstall torch packages AGAIN after installation (in case dependencies pulled them in)
            echo -e "${CYAN}   Ensuring no torch packages were installed in venv...${NC}"
            uv pip uninstall -y torch torchvision torchaudio 2>/dev/null || true
            
            rm -f "$FILTERED_REQ"
        else
            uv pip install -r requirements.txt
        fi
    else
        echo -e "${RED}   ❌ No requirements file found${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}   ✅ Installation complete with uv${NC}"
else
    echo -e "${CYAN}   Using pip for installation...${NC}"
    
    # Check for Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}   ❌ Python3 is not installed${NC}"
        echo -e "${YELLOW}   Installing Python3...${NC}"
        sudo apt update
        sudo apt install -y python3 python3-pip python3-venv
    fi
    
    echo -e "${CYAN}   Creating virtual environment...${NC}"
    
    # For Jetson with system PyTorch, use --system-site-packages
    # Also remove venv if it exists without system site packages
    if [ "$USE_SYSTEM_SITE_PACKAGES" = "true" ] && [ -d "venv" ]; then
        # Double-check: if venv exists but doesn't have system site packages, remove it
        if [ -f "venv/pyvenv.cfg" ]; then
            if ! grep -q "include-system-site-packages = true" venv/pyvenv.cfg 2>/dev/null; then
                echo -e "${YELLOW}   ⚠️  Existing venv does not have system site packages - removing it${NC}"
                rm -rf venv
            fi
        fi
    fi
    
    if [ "$USE_SYSTEM_SITE_PACKAGES" = "true" ]; then
        echo -e "${CYAN}   Creating venv with system site packages (to use CUDA PyTorch)${NC}"
        python3 -m venv --system-site-packages venv
    else
        python3 -m venv venv
    fi
    
    echo -e "${CYAN}   Activating virtual environment...${NC}"
    source venv/bin/activate
    
    echo -e "${CYAN}   Upgrading pip...${NC}"
    pip install --upgrade pip
    
    echo -e "${CYAN}   Installing dependencies...${NC}"
    # Select requirements file based on detected platform
    REQ_FILE=$(get_requirements_file)
    if [ -f "$REQ_FILE" ]; then
        echo -e "${CYAN}   Using requirements file: $REQ_FILE${NC}"
        
        # For Jetson, filter out torch packages if using system packages
        if [ "$USE_SYSTEM_SITE_PACKAGES" = "true" ] && [ "$DETECTED_PLATFORM" = "jetson" ]; then
            FILTERED_REQ=$(filter_jetson_requirements "$REQ_FILE")
            echo -e "${CYAN}   Filtered out torch/torchvision/torchaudio (using system CUDA versions)${NC}"
            
            # Uninstall any existing torch packages from venv BEFORE installation
            echo -e "${CYAN}   Removing any existing venv-installed torch packages...${NC}"
            pip uninstall -y torch torchvision torchaudio 2>/dev/null || true
            
            # Install filtered requirements
            pip install -r "$FILTERED_REQ"
            
            # Uninstall torch packages AGAIN after installation (in case dependencies pulled them in)
            echo -e "${CYAN}   Ensuring no torch packages were installed in venv...${NC}"
            pip uninstall -y torch torchvision torchaudio 2>/dev/null || true
            
            rm -f "$FILTERED_REQ"
        else
            pip install -r "$REQ_FILE"
        fi
    elif [ -f "requirements.txt" ]; then
        echo -e "${CYAN}   Using fallback requirements file: requirements.txt${NC}"
        if [ "$USE_SYSTEM_SITE_PACKAGES" = "true" ] && [ "$DETECTED_PLATFORM" = "jetson" ]; then
            FILTERED_REQ=$(filter_jetson_requirements "requirements.txt")
            echo -e "${CYAN}   Filtered out torch/torchvision/torchaudio (using system CUDA versions)${NC}"
            
            # Uninstall any existing torch packages from venv BEFORE installation
            echo -e "${CYAN}   Removing any existing venv-installed torch packages...${NC}"
            pip uninstall -y torch torchvision torchaudio 2>/dev/null || true
            
            # Install filtered requirements
            pip install -r "$FILTERED_REQ"
            
            # Uninstall torch packages AGAIN after installation (in case dependencies pulled them in)
            echo -e "${CYAN}   Ensuring no torch packages were installed in venv...${NC}"
            pip uninstall -y torch torchvision torchaudio 2>/dev/null || true
            
            rm -f "$FILTERED_REQ"
        else
            pip install -r requirements.txt
        fi
    else
        echo -e "${RED}   ❌ No requirements file found${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}   ✅ Installation complete with pip${NC}"
fi

# Verify PyTorch CUDA on Jetson
if [ "$DETECTED_PLATFORM" = "jetson" ]; then
    echo -e "\n${BLUE}🔍 Verifying PyTorch CUDA installation...${NC}"
    source venv/bin/activate
    
    # Check if torch is installed in venv (should NOT be)
    TORCH_IN_VENV=$(python3 -c "import sys, os; venv_pkgs = [p for p in sys.path if 'venv' in p and 'site-packages' in p]; exec('try:\n    import torch\n    torch_path = torch.__file__\n    result = \"venv\" if any(vp in torch_path for vp in venv_pkgs) else \"system\"\n    print(result)\nexcept:\n    print(\"unknown\")')" 2>/dev/null || echo "unknown")
    
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
            echo -e "${YELLOW}   This will cause CUDA issues. Removing venv-installed torch...${NC}"
            pip uninstall -y torch torchvision torchaudio 2>/dev/null || true
            echo -e "${YELLOW}   Please verify system PyTorch is accessible and run the script again${NC}"
        elif [ "$TORCH_IN_VENV" = "system" ]; then
            echo -e "${GREEN}   ✅ Confirmed: Using system PyTorch (correct)${NC}"
        fi
    else
        echo -e "${YELLOW}   ⚠️  PyTorch CUDA not available${NC}"
        if [ "$USE_SYSTEM_SITE_PACKAGES" != "true" ]; then
            echo -e "${YELLOW}   This may be because venv was created without --system-site-packages${NC}"
            echo -e "${YELLOW}   Run: ./scripts/fix_jetson_venv.sh to fix it${NC}"
        else
            echo -e "${YELLOW}   Check that PyTorch was installed system-wide with CUDA support${NC}"
            echo -e "${YELLOW}   Source detected: $TORCH_IN_VENV${NC}"
        fi
    fi
fi

# Create necessary directories
echo -e "${CYAN}   Creating necessary directories...${NC}"
mkdir -p logs
mkdir -p data/detections
mkdir -p models
mkdir -p data/bird_species

# Make scripts executable
echo -e "${CYAN}   Making scripts executable...${NC}"
chmod +x scripts/*.sh 2>/dev/null || true
chmod +x scripts/*.py 2>/dev/null || true

# Step 7: Restore configuration backup (if available)
if [ "$SKIP_BACKUP" = false ]; then
    echo -e "\n${BLUE}📋 Step 7: Restoring configuration backup...${NC}"
    BACKUP_DIR=$(ls -td "${SKYGUARD_PATH}".backup.* 2>/dev/null | head -1)
    
    if [ -n "$BACKUP_DIR" ] && [ -d "$BACKUP_DIR" ]; then
        echo -e "${CYAN}   Found backup: $BACKUP_DIR${NC}"
        
        if [ -d "$BACKUP_DIR/config" ]; then
            echo -e "${CYAN}   Restoring configuration...${NC}"
            cp -r "$BACKUP_DIR/config"/* "$SKYGUARD_PATH/config/" 2>/dev/null || true
            echo -e "${GREEN}   ✅ Configuration restored${NC}"
        fi
        
        if [ -d "$BACKUP_DIR/models" ]; then
            echo -e "${CYAN}   Restoring models...${NC}"
            cp -r "$BACKUP_DIR/models"/* "$SKYGUARD_PATH/models/" 2>/dev/null || true
            echo -e "${GREEN}   ✅ Models restored${NC}"
        fi
    else
        echo -e "${CYAN}   No backup found, skipping restore${NC}"
    fi
fi

# Step 8: Start SkyGuard services
echo -e "\n${BLUE}🚀 Step 8: Starting SkyGuard services...${NC}"
cd "$SKYGUARD_PATH"

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# Start main system
echo -e "${CYAN}   Starting main detection system...${NC}"
nohup python3 -m skyguard.main --config config/skyguard.yaml > logs/main.log 2>&1 &
MAIN_PID=$!
sleep 2

if ps -p $MAIN_PID > /dev/null 2>&1; then
    echo -e "${GREEN}   ✅ Main system started (PID: $MAIN_PID)${NC}"
else
    echo -e "${YELLOW}   ⚠️  Main system may have failed to start (check logs/main.log)${NC}"
fi

# Start web portal
echo -e "${CYAN}   Starting web portal...${NC}"
nohup python3 skyguard/web/app.py > logs/web.log 2>&1 &
WEB_PID=$!
sleep 2

if ps -p $WEB_PID > /dev/null 2>&1; then
    echo -e "${GREEN}   ✅ Web portal started (PID: $WEB_PID)${NC}"
else
    echo -e "${YELLOW}   ⚠️  Web portal may have failed to start (check logs/web.log)${NC}"
fi

# Final summary
echo -e "\n${GREEN}✅ SkyGuard reinstallation complete!${NC}"
echo -e "\n${CYAN}📋 Summary:${NC}"
echo -e "   - SkyGuard path: $SKYGUARD_PATH"
echo -e "   - Main system PID: $MAIN_PID"
echo -e "   - Web portal PID: $WEB_PID"
echo -e "   - Web portal: http://localhost:8080"
echo -e "   - Logs: $SKYGUARD_PATH/logs"
echo -e "\n${CYAN}💡 Next steps:${NC}"
echo -e "   1. Check logs in: $SKYGUARD_PATH/logs"
echo -e "   2. Access web portal at: http://$(hostname -I | awk '{print $1}'):8080"
echo -e "   3. Configure system in: $SKYGUARD_PATH/config/skyguard.yaml"
echo -e "   4. View main system logs: tail -f $SKYGUARD_PATH/logs/main.log"
echo -e "   5. View web portal logs: tail -f $SKYGUARD_PATH/logs/web.log"

