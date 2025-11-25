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
    # This handles:
    #   - "torch>=2.0", "torch!=2.0", "torch~=2.0" (all version operators)
    #   - "torch[cuda]>=2.0", "torch[cpu]!=2.0" (extras syntax)
    #   - " torch>=2.0", "# torch>=2.0" (with leading whitespace/comments)
    # Character class [>=<~!#] covers: >=, <=, ==, !=, ~=, and # (comment)
    # Also match lines that are just "torch" or "torchvision" or "torchaudio" without operators
    grep -v -E "^[[:space:]#]*(torch|torchvision|torchaudio)(\[[^\]]+\])?[[:space:]]*([>=<~!#]|$)" "$req_file" > "$filtered_file" 2>/dev/null || cp "$req_file" "$filtered_file"
    echo "$filtered_file"
}

# Install requirements while preventing torch installation
install_jetson_requirements_safely() {
    local req_file="$1"
    local venv_path="$2"
    
    echo -e "${CYAN}   Installing requirements while preventing torch installation...${NC}"
    
    # Activate venv
    source "$venv_path/bin/activate"
    
    # CRITICAL: Clear pip cache to prevent using cached torch packages
    echo -e "${CYAN}   Clearing pip cache to prevent cached torch installation...${NC}"
    pip cache purge 2>/dev/null || true
    
    # FIRST: Install numpy==1.26.0 explicitly before anything else
    # This ensures numpy is pinned and won't be upgraded by other packages
    echo -e "${CYAN}   Installing numpy==1.26.0 first (required for Jetson)...${NC}"
    pip install --no-cache-dir --force-reinstall "numpy==1.26.0" || {
        echo -e "${YELLOW}   ⚠️  Failed to install numpy==1.26.0, trying without force...${NC}"
        pip install --no-cache-dir "numpy==1.26.0" || true
    }
    
    # Read requirements file and install packages one by one
    # This allows us to catch and handle torch installation attempts
    while IFS= read -r line || [ -n "$line" ]; do
        # Skip empty lines and comments
        [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
        
        # Remove inline comments and whitespace
        package=$(echo "$line" | sed 's/#.*$//' | xargs)
        [[ -z "$package" ]] && continue
        
        # Skip if it's a torch package
        if [[ "$package" =~ ^(torch|torchvision|torchaudio) ]]; then
            echo -e "${CYAN}     Skipping $package (using system version)${NC}"
            continue
        fi
        
        # Skip numpy - already installed above
        if [[ "$package" =~ ^numpy ]]; then
            echo -e "${CYAN}     Skipping $package (already installed as numpy==1.26.0)${NC}"
            # Ensure it's still the correct version
            pip install --no-cache-dir --force-reinstall "numpy==1.26.0" 2>/dev/null || true
            continue
        fi
        
        # Install package
        echo -e "${CYAN}     Installing $package...${NC}"
        
        # For ultralytics, install with --no-deps first, then install its dependencies manually (excluding torch)
        if [[ "$package" =~ ^ultralytics ]]; then
            echo -e "${CYAN}       Installing ultralytics without dependencies (to avoid torch)...${NC}"
            
            # Try installing with --no-deps and --no-cache-dir
            if pip install --no-cache-dir --no-deps "$package" 2>/dev/null; then
                echo -e "${GREEN}       ✅ ultralytics installed without dependencies${NC}"
            else
                echo -e "${YELLOW}       ⚠️  Failed to install ultralytics without deps${NC}"
                echo -e "${CYAN}       Installing ultralytics normally, will remove torch if installed...${NC}"
                pip install --no-cache-dir "$package" 2>/dev/null || true
                
                # IMMEDIATELY check and remove torch
                sleep 1  # Give pip a moment to finish
                TORCH_INSTALLED=false
                for site_packages in "$venv_path"/lib/python*/site-packages; do
                    if [ -d "$site_packages" ] && ([ -d "$site_packages/torch" ] || [ -d "$site_packages/torchvision" ] || [ -d "$site_packages/torchaudio" ]); then
                        TORCH_INSTALLED=true
                        break
                    fi
                done
                
                if [ "$TORCH_INSTALLED" = true ]; then
                    echo -e "${RED}       ❌ ultralytics pulled in torch - removing immediately...${NC}"
                    # Detect if running as root
                    local USE_SUDO=""
                    if [ "$(id -u)" -eq 0 ]; then
                        USE_SUDO="sudo"
                    fi
                    pip uninstall -y torch torchvision torchaudio 2>/dev/null || true
                    if [ -n "$USE_SUDO" ]; then
                        $USE_SUDO pip uninstall -y torch torchvision torchaudio 2>/dev/null || true
                    fi
                    # Aggressive filesystem removal
                    for site_packages in "$venv_path"/lib/python*/site-packages; do
                        if [ -d "$site_packages" ]; then
                            $USE_SUDO rm -rf "$site_packages/torch" 2>/dev/null || true
                            $USE_SUDO rm -rf "$site_packages/torchvision" 2>/dev/null || true
                            $USE_SUDO rm -rf "$site_packages/torchaudio" 2>/dev/null || true
                            $USE_SUDO rm -rf "$site_packages"/torch*.dist-info 2>/dev/null || true
                            $USE_SUDO rm -rf "$site_packages"/torch*.egg-info 2>/dev/null || true
                            $USE_SUDO rm -rf "$site_packages"/torchvision*.dist-info 2>/dev/null || true
                            $USE_SUDO rm -rf "$site_packages"/torchvision*.egg-info 2>/dev/null || true
                            $USE_SUDO rm -rf "$site_packages"/torchaudio*.dist-info 2>/dev/null || true
                            $USE_SUDO rm -rf "$site_packages"/torchaudio*.egg-info 2>/dev/null || true
                            # Remove torch.libs directory
                            $USE_SUDO rm -rf "$site_packages"/torch.libs 2>/dev/null || true
                        fi
                    done
                    echo -e "${GREEN}       ✅ torch removed${NC}"
                fi
            fi
            
            # Install ultralytics dependencies manually (excluding torch)
            echo -e "${CYAN}       Installing ultralytics dependencies (excluding torch)...${NC}"
            # Common ultralytics dependencies (excluding torch/torchvision)
            # Use --no-deps and --no-cache-dir for each to prevent transitive torch installation
            for dep in pillow pyyaml requests tqdm pandas opencv-python-headless; do
                pip install --no-cache-dir --no-deps "$dep" 2>/dev/null || pip install --no-cache-dir "$dep" 2>/dev/null || true
                # Immediately check for torch after each dependency
                sleep 0.5
                # Check for torch using proper loop (quoted glob pattern)
                TORCH_FOUND=false
                for site_packages in "$venv_path"/lib/python*/site-packages; do
                    if [ -d "$site_packages/torch" ] 2>/dev/null; then
                        TORCH_FOUND=true
                        break
                    fi
                done
                if [ "$TORCH_FOUND" = true ]; then
                    echo -e "${RED}       ❌ $dep pulled in torch - removing...${NC}"
                    local USE_SUDO=""
                    if [ "$(id -u)" -eq 0 ]; then
                        USE_SUDO="sudo"
                    fi
                    pip uninstall -y torch torchvision torchaudio 2>/dev/null || true
                    if [ -n "$USE_SUDO" ]; then
                        $USE_SUDO pip uninstall -y torch torchvision torchaudio 2>/dev/null || true
                    fi
                    for site_packages in "$venv_path"/lib/python*/site-packages; do
                        if [ -d "$site_packages" ]; then
                            $USE_SUDO rm -rf "$site_packages/torch"* 2>/dev/null || true
                            $USE_SUDO rm -rf "$site_packages"/torch*.dist-info 2>/dev/null || true
                            $USE_SUDO rm -rf "$site_packages"/torch*.egg-info 2>/dev/null || true
                        fi
                    done
                fi
            done
        else
            # For other packages, install normally but check immediately for torch
            # Try installing with --no-deps first to avoid pulling in dependencies
            pip install "$package" --no-deps 2>/dev/null || {
                # If --no-deps fails, try normal install but check immediately
                pip install "$package" 2>/dev/null || {
                    echo -e "${YELLOW}       ⚠️  Failed to install $package${NC}"
                }
            }
            
            # Wait a moment for pip to finish
            sleep 0.5
            
            # Check if torch was installed and remove it immediately
            # Check by looking for torch in site-packages directly (more reliable)
            TORCH_INSTALLED=false
            for site_packages in "$venv_path"/lib/python*/site-packages; do
                if [ -d "$site_packages" ] && ([ -d "$site_packages/torch" ] || [ -d "$site_packages/torchvision" ] || [ -d "$site_packages/torchaudio" ]); then
                    TORCH_INSTALLED=true
                    break
                fi
            done
            
            if [ "$TORCH_INSTALLED" = true ]; then
                echo -e "${YELLOW}       ⚠️  $package pulled in torch - removing it...${NC}"
                # Detect if running as root
                local USE_SUDO=""
                if [ "$(id -u)" -eq 0 ]; then
                    USE_SUDO="sudo"
                fi
                pip uninstall -y torch torchvision torchaudio 2>/dev/null || true
                if [ -n "$USE_SUDO" ]; then
                    $USE_SUDO pip uninstall -y torch torchvision torchaudio 2>/dev/null || true
                fi
                # Also remove physically
                for site_packages in "$venv_path"/lib/python*/site-packages; do
                    if [ -d "$site_packages" ]; then
                        $USE_SUDO rm -rf "$site_packages/torch" 2>/dev/null || true
                        $USE_SUDO rm -rf "$site_packages/torchvision" 2>/dev/null || true
                        $USE_SUDO rm -rf "$site_packages/torchaudio" 2>/dev/null || true
                        $USE_SUDO rm -rf "$site_packages"/torch*.dist-info 2>/dev/null || true
                        $USE_SUDO rm -rf "$site_packages"/torch*.egg-info 2>/dev/null || true
                        $USE_SUDO rm -rf "$site_packages"/torchvision*.dist-info 2>/dev/null || true
                        $USE_SUDO rm -rf "$site_packages"/torchvision*.egg-info 2>/dev/null || true
                        $USE_SUDO rm -rf "$site_packages"/torchaudio*.dist-info 2>/dev/null || true
                        $USE_SUDO rm -rf "$site_packages"/torchaudio*.egg-info 2>/dev/null || true
                    fi
                done
            fi
        fi
        
        # After each package, verify numpy is still 1.26.0 and reinstall if needed
        # Check if numpy is missing OR has wrong version (both cases need reinstall)
        NUMPY_VERSION=$(python3 -c "import numpy; print(numpy.__version__)" 2>/dev/null || echo "not_installed")
        if [ "$NUMPY_VERSION" != "1.26.0" ]; then
            if [ "$NUMPY_VERSION" = "not_installed" ]; then
                echo -e "${YELLOW}       ⚠️  numpy is missing, installing 1.26.0...${NC}"
            else
                echo -e "${YELLOW}       ⚠️  numpy was upgraded to $NUMPY_VERSION, reinstalling 1.26.0...${NC}"
            fi
            pip install --no-cache-dir --force-reinstall "numpy==1.26.0" 2>/dev/null || true
        fi
    done < "$req_file"
    
    # Final check: ensure numpy is 1.26.0
    echo -e "${CYAN}   Verifying numpy version...${NC}"
    NUMPY_VERSION=$(python3 -c "import numpy; print(numpy.__version__)" 2>/dev/null || echo "not_installed")
    if [ "$NUMPY_VERSION" = "1.26.0" ]; then
        echo -e "${GREEN}   ✅ numpy is correctly version 1.26.0${NC}"
    else
        echo -e "${YELLOW}   ⚠️  numpy version is $NUMPY_VERSION, forcing reinstall to 1.26.0...${NC}"
        pip install --no-cache-dir --force-reinstall "numpy==1.26.0" || {
            echo -e "${RED}   ❌ Failed to install numpy==1.26.0${NC}"
        }
    fi
    
    # CRITICAL: Final torch check - verify torch is NOT in venv
    echo -e "${CYAN}   Final verification: Checking for torch in venv...${NC}"
    
    # Check 1: Filesystem check
    TORCH_IN_VENV=false
    for site_packages in "$venv_path"/lib/python*/site-packages; do
        if [ -d "$site_packages" ] && ([ -d "$site_packages/torch" ] || [ -d "$site_packages/torchvision" ] || [ -d "$site_packages/torchaudio" ]); then
            TORCH_IN_VENV=true
            break
        fi
    done
    
    # Check 2: Try to import torch from venv (more reliable - catches even if files exist but shouldn't be used)
    TORCH_IMPORTABLE=false
    TORCH_VERSION_VENV=$(python3 -c "import sys; sys.path.insert(0, '$venv_path/lib/python3.' + str(sys.version_info[1]) + '/site-packages'); import torch; print(torch.__version__)" 2>/dev/null || echo "")
    if [ -n "$TORCH_VERSION_VENV" ]; then
        # Check if this is coming from venv (not system)
        TORCH_PATH=$(python3 -c "import sys; sys.path.insert(0, '$venv_path/lib/python3.' + str(sys.version_info[1]) + '/site-packages'); import torch; print(torch.__file__)" 2>/dev/null || echo "")
        if echo "$TORCH_PATH" | grep -q "$venv_path"; then
            TORCH_IMPORTABLE=true
            echo -e "${RED}   ❌ CRITICAL: torch $TORCH_VERSION_VENV is importable from venv!${NC}"
        fi
    fi
    
    if [ "$TORCH_IN_VENV" = true ] || [ "$TORCH_IMPORTABLE" = true ]; then
        echo -e "${RED}   ❌ CRITICAL: torch is still in venv after installation!${NC}"
        echo -e "${YELLOW}   Performing emergency removal...${NC}"
        # Detect if running as root
        local USE_SUDO=""
        if [ "$(id -u)" -eq 0 ]; then
            USE_SUDO="sudo"
        fi
        pip uninstall -y torch torchvision torchaudio 2>/dev/null || true
        if [ -n "$USE_SUDO" ]; then
            $USE_SUDO pip uninstall -y torch torchvision torchaudio 2>/dev/null || true
        fi
        # Aggressive filesystem removal
        for site_packages in "$venv_path"/lib/python*/site-packages; do
            if [ -d "$site_packages" ]; then
                $USE_SUDO rm -rf "$site_packages/torch" 2>/dev/null || true
                $USE_SUDO rm -rf "$site_packages/torchvision" 2>/dev/null || true
                $USE_SUDO rm -rf "$site_packages/torchaudio" 2>/dev/null || true
                $USE_SUDO rm -rf "$site_packages"/torch*.dist-info 2>/dev/null || true
                $USE_SUDO rm -rf "$site_packages"/torch*.egg-info 2>/dev/null || true
                $USE_SUDO rm -rf "$site_packages"/torchvision*.dist-info 2>/dev/null || true
                $USE_SUDO rm -rf "$site_packages"/torchvision*.egg-info 2>/dev/null || true
                $USE_SUDO rm -rf "$site_packages"/torchaudio*.dist-info 2>/dev/null || true
                $USE_SUDO rm -rf "$site_packages"/torchaudio*.egg-info 2>/dev/null || true
                $USE_SUDO rm -rf "$site_packages"/torch.libs 2>/dev/null || true
                # Remove any torch-related .so files
                $USE_SUDO find "$site_packages" -name "*torch*.so" -delete 2>/dev/null || true
            fi
        done
        echo -e "${GREEN}   ✅ Emergency torch removal completed${NC}"
        
        # Verify removal
        sleep 1
        TORCH_STILL_THERE=false
        for site_packages in "$venv_path"/lib/python*/site-packages; do
            if [ -d "$site_packages" ] && ([ -d "$site_packages/torch" ] || [ -d "$site_packages/torchvision" ] || [ -d "$site_packages/torchaudio" ]); then
                TORCH_STILL_THERE=true
                break
            fi
        done
        if [ "$TORCH_STILL_THERE" = true ]; then
            echo -e "${RED}   ⚠️  WARNING: torch still detected after removal - manual cleanup may be needed${NC}"
        else
            echo -e "${GREEN}   ✅ Verified: torch removed from venv${NC}"
        fi
    else
        echo -e "${GREEN}   ✅ Confirmed: No torch packages in venv${NC}"
    fi
    
    deactivate 2>/dev/null || true
}

# Aggressively remove torch packages from venv (both via pip and filesystem)
remove_torch_from_venv() {
    local venv_path="$1"
    
    if [ ! -d "$venv_path" ]; then
        return 0
    fi
    
    echo -e "${CYAN}   Aggressively removing torch packages from venv...${NC}"
    
    # Detect if running as root (packages may have been installed as root)
    local USE_SUDO=""
    if [ "$(id -u)" -eq 0 ]; then
        USE_SUDO="sudo"
        echo -e "${CYAN}   Running as root - using sudo for package removal${NC}"
    fi
    
    # First, try pip uninstall if venv is activated
    if [ -f "$venv_path/bin/activate" ]; then
        source "$venv_path/bin/activate"
        # Try normal uninstall first
        pip uninstall -y torch torchvision torchaudio 2>/dev/null || true
        # If running as root, also try with sudo (in case packages were installed as root)
        if [ -n "$USE_SUDO" ]; then
            $USE_SUDO pip uninstall -y torch torchvision torchaudio 2>/dev/null || true
        fi
        deactivate 2>/dev/null || true
    fi
    
    # Then physically remove from site-packages directories
    # Use sudo if running as root (packages may have been installed as root)
    for site_packages in "$venv_path"/lib/python*/site-packages; do
        if [ -d "$site_packages" ]; then
            # Remove torch directories (with sudo if needed)
            $USE_SUDO rm -rf "$site_packages/torch" 2>/dev/null || true
            $USE_SUDO rm -rf "$site_packages/torchvision" 2>/dev/null || true
            $USE_SUDO rm -rf "$site_packages/torchaudio" 2>/dev/null || true
            $USE_SUDO rm -rf "$site_packages/torch-"* 2>/dev/null || true
            $USE_SUDO rm -rf "$site_packages/torchvision-"* 2>/dev/null || true
            $USE_SUDO rm -rf "$site_packages/torchaudio-"* 2>/dev/null || true
            
            # Remove torch egg-info and dist-info (with sudo if needed)
            $USE_SUDO rm -rf "$site_packages"/torch*.egg-info 2>/dev/null || true
            $USE_SUDO rm -rf "$site_packages"/torch*.dist-info 2>/dev/null || true
            $USE_SUDO rm -rf "$site_packages"/torchvision*.egg-info 2>/dev/null || true
            $USE_SUDO rm -rf "$site_packages"/torchvision*.dist-info 2>/dev/null || true
            $USE_SUDO rm -rf "$site_packages"/torchaudio*.egg-info 2>/dev/null || true
            $USE_SUDO rm -rf "$site_packages"/torchaudio*.dist-info 2>/dev/null || true
        fi
    done
    
    echo -e "${GREEN}   ✅ Torch packages removed from venv${NC}"
}

# Verify venv configuration for Jetson
verify_jetson_venv_config() {
    local venv_path="$1"
    
    if [ ! -f "$venv_path/pyvenv.cfg" ]; then
        echo -e "${RED}   ❌ ERROR: venv/pyvenv.cfg not found${NC}"
        return 1
    fi
    
    if ! grep -q "include-system-site-packages = true" "$venv_path/pyvenv.cfg" 2>/dev/null; then
        echo -e "${RED}   ❌ ERROR: venv does NOT have system-site-packages enabled${NC}"
        echo -e "${YELLOW}   This is required for Jetson to access system CUDA PyTorch${NC}"
        return 1
    fi
    
    echo -e "${GREEN}   ✅ venv configured with system-site-packages${NC}"
    return 0
}

# Check if PyTorch is installed system-wide
check_system_pytorch() {
    python3 -c "import torch; print('CUDA' if torch.cuda.is_available() else 'CPU')" 2>/dev/null || echo "NOT_FOUND"
}

# Check if torchvision is installed system-wide
check_system_torchvision() {
    python3 -c "import torchvision; print('FOUND')" 2>/dev/null || echo "NOT_FOUND"
}

# Install PyTorch system-wide for Jetson
install_jetson_pytorch() {
    echo -e "${BLUE}📦 Installing PyTorch for Jetson (system-wide)...${NC}"
    
    # Detect Python version
    PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
    PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
    PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
    PYTHON_TAG="cp${PYTHON_MAJOR}${PYTHON_MINOR}"
    
    echo -e "${CYAN}   Detected Python version: $PYTHON_VERSION ($PYTHON_TAG)${NC}"
    
    # For JetPack 6.1, use the specific wheel URL
    TORCH_WHEEL="torch-2.5.0a0+872d972e41.nv24.08.17622132-${PYTHON_TAG}-${PYTHON_TAG}-linux_aarch64.whl"
    TORCH_URL="https://developer.download.nvidia.com/compute/redist/jp/v61/pytorch/${TORCH_WHEEL}"
    
    echo -e "${CYAN}   Downloading PyTorch wheel from NVIDIA...${NC}"
    echo -e "${CYAN}   URL: $TORCH_URL${NC}"
    
    # Download the wheel to a writable location
    DOWNLOAD_DIR="/tmp"
    if [ ! -w "$DOWNLOAD_DIR" ]; then
        DOWNLOAD_DIR="$HOME"
    fi
    
    if wget -q --spider "$TORCH_URL" 2>/dev/null; then
        wget "$TORCH_URL" -O "${DOWNLOAD_DIR}/${TORCH_WHEEL}" || {
            echo -e "${RED}   ❌ Failed to download PyTorch wheel${NC}"
            return 1
        }
        
        echo -e "${CYAN}   Installing PyTorch wheel...${NC}"
        pip3 install "${DOWNLOAD_DIR}/${TORCH_WHEEL}" || {
            echo -e "${RED}   ❌ Failed to install PyTorch wheel${NC}"
            rm -f "${DOWNLOAD_DIR}/${TORCH_WHEEL}"
            return 1
        }
        
        echo -e "${CYAN}   Installing NVIDIA torchvision wheel for JetPack 6.1...${NC}"
        # First, uninstall any existing torchvision that might be incompatible
        pip3 uninstall -y torchvision 2>/dev/null || true
        
        # Try to download NVIDIA's torchvision wheel for JetPack 6.1
        TORCHVISION_WHEEL="torchvision-0.20.0+nv24.08.17622132-${PYTHON_TAG}-${PYTHON_TAG}-linux_aarch64.whl"
        TORCHVISION_URL="https://developer.download.nvidia.com/compute/redist/jp/v61/pytorch/${TORCHVISION_WHEEL}"
        
        echo -e "${CYAN}   Trying NVIDIA torchvision wheel: $TORCHVISION_URL${NC}"
        
        if wget -q --spider "$TORCHVISION_URL" 2>/dev/null; then
            wget "$TORCHVISION_URL" -O "${DOWNLOAD_DIR}/${TORCHVISION_WHEEL}" || {
                echo -e "${YELLOW}   ⚠️  Failed to download NVIDIA torchvision wheel${NC}"
                echo -e "${CYAN}   Trying PyPI torchvision 0.20.0 with --no-deps...${NC}"
                pip3 install --no-deps torchvision==0.20.0 || {
                    echo -e "${RED}   ❌ Failed to install torchvision${NC}"
                    echo -e "${YELLOW}   You may need to install torchvision manually${NC}"
                    return 1
                }
            }
            
            if [ -f "${DOWNLOAD_DIR}/${TORCHVISION_WHEEL}" ]; then
                echo -e "${CYAN}   Installing NVIDIA torchvision wheel...${NC}"
                pip3 install "${DOWNLOAD_DIR}/${TORCHVISION_WHEEL}" || {
                    echo -e "${YELLOW}   ⚠️  Failed to install NVIDIA torchvision wheel${NC}"
                    echo -e "${CYAN}   Trying PyPI torchvision 0.20.0 with --no-deps...${NC}"
                    pip3 install --no-deps torchvision==0.20.0 || {
                        echo -e "${RED}   ❌ Failed to install torchvision${NC}"
                        rm -f "${DOWNLOAD_DIR}/${TORCHVISION_WHEEL}"
                        return 1
                    }
                }
                rm -f "${DOWNLOAD_DIR}/${TORCHVISION_WHEEL}"
            fi
        else
            echo -e "${YELLOW}   ⚠️  NVIDIA torchvision wheel not available, trying PyPI version...${NC}"
            echo -e "${CYAN}   Installing torchvision 0.20.0 with --no-deps...${NC}"
            pip3 install --no-deps torchvision==0.20.0 || {
                echo -e "${RED}   ❌ Failed to install torchvision${NC}"
                echo -e "${YELLOW}   You may need to install torchvision manually${NC}"
                return 1
            }
        fi
        
        # Verify torchvision is installed AND torch wasn't replaced
        if python3 -c "import torchvision" 2>/dev/null; then
            TV_VERSION=$(python3 -c "import torchvision; print(torchvision.__version__)" 2>/dev/null || echo "unknown")
            TORCH_VERSION=$(python3 -c "import torch; print(torch.__version__)" 2>/dev/null || echo "unknown")
            echo -e "${GREEN}   ✅ torchvision installed: $TV_VERSION${NC}"
            
            # Check if torch is still the NVIDIA version
            if echo "$TORCH_VERSION" | grep -q "2.5.0a0.*nv24"; then
                echo -e "${GREEN}   ✅ torch is still NVIDIA CUDA version: $TORCH_VERSION${NC}"
            else
                echo -e "${RED}   ❌ WARNING: torch was replaced with: $TORCH_VERSION${NC}"
                echo -e "${YELLOW}   Reinstalling NVIDIA torch...${NC}"
                pip3 install "${DOWNLOAD_DIR}/${TORCH_WHEEL}" --force-reinstall || {
                    echo -e "${RED}   ❌ Failed to reinstall NVIDIA torch${NC}"
                    rm -f "${DOWNLOAD_DIR}/${TORCH_WHEEL}"
                    return 1
                }
                echo -e "${GREEN}   ✅ NVIDIA torch reinstalled${NC}"
            fi
        else
            echo -e "${YELLOW}   ⚠️  torchvision installation verification failed${NC}"
        fi
        
        rm -f "${DOWNLOAD_DIR}/${TORCH_WHEEL}"
        
        # Verify installation
        PYTORCH_CHECK=$(check_system_pytorch)
        if [ "$PYTORCH_CHECK" = "CUDA" ]; then
            echo -e "${GREEN}   ✅ PyTorch CUDA installed successfully!${NC}"
            return 0
        elif [ "$PYTORCH_CHECK" = "CPU" ]; then
            echo -e "${YELLOW}   ⚠️  PyTorch installed but CUDA not available${NC}"
            return 0
        else
            echo -e "${RED}   ❌ PyTorch installation verification failed${NC}"
            return 1
        fi
    else
        echo -e "${YELLOW}   ⚠️  Could not download PyTorch wheel (URL may not exist for this Python version)${NC}"
        echo -e "${CYAN}   Please install PyTorch manually:${NC}"
        echo -e "${CYAN}   See: https://forums.developer.nvidia.com/t/pytorch-for-jetson/${NC}"
        return 1
    fi
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
    # Try to auto-detect: if script is in parent directory, look for SkyGuard sibling
    SCRIPT_DIR=$(dirname "$(readlink -f "$0" 2>/dev/null || realpath "$0" 2>/dev/null || echo "$0")")
    if [ -d "$SCRIPT_DIR/SkyGuard" ]; then
        SKYGUARD_PATH="$SCRIPT_DIR/SkyGuard"
        echo -e "${CYAN}Auto-detected SkyGuard directory: $SKYGUARD_PATH${NC}"
    else
        # Fall back to default path
        SKYGUARD_PATH="/home/$DETECTED_USERNAME/SkyGuard"
        echo -e "${CYAN}Using default SkyGuard path: $SKYGUARD_PATH${NC}"
    fi
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

# Check for system PyTorch on Jetson (BEFORE creating venv)
if [ "$DETECTED_PLATFORM" = "jetson" ]; then
    echo -e "${CYAN}   Checking for system-installed PyTorch...${NC}"
    PYTORCH_STATUS=$(check_system_pytorch)
    TORCHVISION_STATUS=$(check_system_torchvision)
    
    if [ "$PYTORCH_STATUS" = "CUDA" ]; then
        echo -e "${GREEN}   ✅ Found CUDA-enabled PyTorch in system${NC}"
        if [ "$TORCHVISION_STATUS" = "FOUND" ]; then
            echo -e "${GREEN}   ✅ Found torchvision in system${NC}"
        else
            echo -e "${YELLOW}   ⚠️  torchvision not found - will install it${NC}"
            pip3 install torchvision || {
                echo -e "${YELLOW}   ⚠️  Failed to install torchvision automatically${NC}"
                echo -e "${CYAN}   Please install manually: pip3 install torchvision${NC}"
            }
        fi
        USE_SYSTEM_SITE_PACKAGES=true
    elif [ "$PYTORCH_STATUS" = "CPU" ]; then
        echo -e "${YELLOW}   ⚠️  Found PyTorch but CUDA not available - will use system packages anyway${NC}"
        if [ "$TORCHVISION_STATUS" != "FOUND" ]; then
            echo -e "${YELLOW}   ⚠️  torchvision not found - installing...${NC}"
            pip3 install torchvision || true
        fi
        USE_SYSTEM_SITE_PACKAGES=true
    else
        echo -e "${YELLOW}   ⚠️  No system PyTorch found${NC}"
        echo -e "${CYAN}   PyTorch must be installed system-wide for Jetson (not in venv)${NC}"
        echo ""
        echo -e "${BLUE}   Would you like to install PyTorch now?${NC}"
        echo -e "${CYAN}   This will install PyTorch system-wide (required for CUDA support)${NC}"
        read -p "   Install PyTorch? (Y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Nn]$ ]]; then
            if install_jetson_pytorch; then
                # Re-check after installation
                PYTORCH_STATUS=$(check_system_pytorch)
                if [ "$PYTORCH_STATUS" != "NOT_FOUND" ]; then
                    USE_SYSTEM_SITE_PACKAGES=true
                    echo -e "${GREEN}   ✅ PyTorch installed - will use system packages${NC}"
                else
                    echo -e "${RED}   ❌ PyTorch installation failed${NC}"
                    echo -e "${YELLOW}   Please install PyTorch manually before continuing${NC}"
                    exit 1
                fi
            else
                echo -e "${RED}   ❌ PyTorch installation failed${NC}"
                echo -e "${YELLOW}   Please install PyTorch manually:${NC}"
                echo -e "${CYAN}   For JetPack 6.1:${NC}"
                echo -e "${CYAN}   wget https://developer.download.nvidia.com/compute/redist/jp/v61/pytorch/torch-2.5.0a0+872d972e41.nv24.08.17622132-cp310-cp310-linux_aarch64.whl${NC}"
                echo -e "${CYAN}   pip3 install torch-2.5.0a0+872d972e41.nv24.08.17622132-cp310-cp310-linux_aarch64.whl${NC}"
                echo -e "${CYAN}   pip3 install torchvision${NC}"
                exit 1
            fi
        else
            echo -e "${YELLOW}   ⚠️  Skipping PyTorch installation${NC}"
            echo -e "${YELLOW}   You must install PyTorch system-wide before continuing${NC}"
            echo -e "${CYAN}   See: https://forums.developer.nvidia.com/t/pytorch-for-jetson/${NC}"
            exit 1
        fi
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
        
        # Verify it was created correctly
        if [ -f "venv/pyvenv.cfg" ]; then
            if grep -q "include-system-site-packages = true" venv/pyvenv.cfg 2>/dev/null; then
                echo -e "${GREEN}   ✅ Venv created with --system-site-packages${NC}"
            else
                echo -e "${RED}   ❌ ERROR: Venv created but system-site-packages not enabled!${NC}"
                echo -e "${YELLOW}   Recreating with python3 -m venv...${NC}"
                rm -rf venv
                python3 -m venv --system-site-packages venv
                if [ -f "venv/pyvenv.cfg" ] && grep -q "include-system-site-packages = true" venv/pyvenv.cfg 2>/dev/null; then
                    echo -e "${GREEN}   ✅ Venv recreated with --system-site-packages${NC}"
                else
                    echo -e "${RED}   ❌ CRITICAL: Failed to create venv with --system-site-packages${NC}"
                    exit 1
                fi
            fi
        else
            echo -e "${RED}   ❌ ERROR: Venv created but pyvenv.cfg missing!${NC}"
            exit 1
        fi
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
            echo -e "${CYAN}   Installing packages carefully to prevent torch installation as dependency${NC}"
            
            # Uninstall any existing torch packages from venv BEFORE installation
            remove_torch_from_venv "$SKYGUARD_PATH/venv"
            
            # Use safe installation method that handles torch dependencies
            install_jetson_requirements_safely "$FILTERED_REQ" "$SKYGUARD_PATH/venv"
            
            # Aggressively remove torch packages AGAIN after installation (in case dependencies pulled them in)
            echo -e "${CYAN}   Final cleanup: Ensuring no torch packages remain in venv...${NC}"
            remove_torch_from_venv "$SKYGUARD_PATH/venv"
            
            rm -f "$FILTERED_REQ"
        else
            uv pip install -r "$REQ_FILE"
        fi
    elif [ -f "requirements.txt" ]; then
        echo -e "${CYAN}   Using fallback requirements file: requirements.txt${NC}"
        if [ "$USE_SYSTEM_SITE_PACKAGES" = "true" ] && [ "$DETECTED_PLATFORM" = "jetson" ]; then
            FILTERED_REQ=$(filter_jetson_requirements "requirements.txt")
            echo -e "${CYAN}   Filtered out torch/torchvision/torchaudio (using system CUDA versions)${NC}"
            echo -e "${CYAN}   Installing packages carefully to prevent torch installation as dependency${NC}"
            
            # Uninstall any existing torch packages from venv BEFORE installation
            remove_torch_from_venv "$SKYGUARD_PATH/venv"
            
            # Use safe installation method that handles torch dependencies
            install_jetson_requirements_safely "$FILTERED_REQ" "$SKYGUARD_PATH/venv"
            
            # Aggressively remove torch packages AGAIN after installation (in case dependencies pulled them in)
            echo -e "${CYAN}   Final cleanup: Ensuring no torch packages remain in venv...${NC}"
            remove_torch_from_venv "$SKYGUARD_PATH/venv"
            
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
        
        # Verify it was created correctly
        if [ -f "venv/pyvenv.cfg" ]; then
            if grep -q "include-system-site-packages = true" venv/pyvenv.cfg 2>/dev/null; then
                echo -e "${GREEN}   ✅ Venv created with --system-site-packages${NC}"
            else
                echo -e "${RED}   ❌ ERROR: Venv created but system-site-packages not enabled!${NC}"
                echo -e "${YELLOW}   Recreating...${NC}"
                rm -rf venv
                python3 -m venv --system-site-packages venv
                if [ -f "venv/pyvenv.cfg" ] && grep -q "include-system-site-packages = true" venv/pyvenv.cfg 2>/dev/null; then
                    echo -e "${GREEN}   ✅ Venv recreated with --system-site-packages${NC}"
                else
                    echo -e "${RED}   ❌ CRITICAL: Failed to create venv with --system-site-packages${NC}"
                    exit 1
                fi
            fi
        else
            echo -e "${RED}   ❌ ERROR: Venv created but pyvenv.cfg missing!${NC}"
            exit 1
        fi
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
            echo -e "${CYAN}   Installing packages carefully to prevent torch installation as dependency${NC}"
            
            # Uninstall any existing torch packages from venv BEFORE installation
            remove_torch_from_venv "$SKYGUARD_PATH/venv"
            
            # Use safe installation method that handles torch dependencies
            install_jetson_requirements_safely "$FILTERED_REQ" "$SKYGUARD_PATH/venv"
            
            # Aggressively remove torch packages AGAIN after installation (in case dependencies pulled them in)
            echo -e "${CYAN}   Final cleanup: Ensuring no torch packages remain in venv...${NC}"
            remove_torch_from_venv "$SKYGUARD_PATH/venv"
            
            rm -f "$FILTERED_REQ"
        else
            pip install -r "$REQ_FILE"
        fi
    elif [ -f "requirements.txt" ]; then
        echo -e "${CYAN}   Using fallback requirements file: requirements.txt${NC}"
        if [ "$USE_SYSTEM_SITE_PACKAGES" = "true" ] && [ "$DETECTED_PLATFORM" = "jetson" ]; then
            FILTERED_REQ=$(filter_jetson_requirements "requirements.txt")
            echo -e "${CYAN}   Filtered out torch/torchvision/torchaudio (using system CUDA versions)${NC}"
            echo -e "${CYAN}   Installing packages carefully to prevent torch installation as dependency${NC}"
            
            # Uninstall any existing torch packages from venv BEFORE installation
            remove_torch_from_venv "$SKYGUARD_PATH/venv"
            
            # Use safe installation method that handles torch dependencies
            install_jetson_requirements_safely "$FILTERED_REQ" "$SKYGUARD_PATH/venv"
            
            # Aggressively remove torch packages AGAIN after installation (in case dependencies pulled them in)
            echo -e "${CYAN}   Final cleanup: Ensuring no torch packages remain in venv...${NC}"
            remove_torch_from_venv "$SKYGUARD_PATH/venv"
            
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
    
    # First, verify venv configuration - if wrong, fix it and reinstall packages
    if ! verify_jetson_venv_config "$SKYGUARD_PATH/venv"; then
        echo -e "${RED}   ❌ CRITICAL: venv configuration is incorrect${NC}"
        echo -e "${YELLOW}   Recreating venv with correct configuration and reinstalling packages...${NC}"
        
        # Backup installed packages list
        source venv/bin/activate 2>/dev/null || true
        INSTALLED_PACKAGES=$(pip freeze 2>/dev/null | grep -v "^torch\|^torchvision\|^torchaudio" || true)
        deactivate 2>/dev/null || true
        
        # Remove and recreate venv
        rm -rf "$SKYGUARD_PATH/venv"
        if [ "$USE_SYSTEM_SITE_PACKAGES" = "true" ]; then
            python3 -m venv --system-site-packages "$SKYGUARD_PATH/venv"
        else
            python3 -m venv "$SKYGUARD_PATH/venv"
        fi
        
        # Reinstall packages
        source venv/bin/activate
        pip install --upgrade pip
        
        # Reinstall using the safe method
        REQ_FILE=$(get_requirements_file)
        if [ -f "$REQ_FILE" ]; then
            FILTERED_REQ=$(filter_jetson_requirements "$REQ_FILE")
            install_jetson_requirements_safely "$FILTERED_REQ" "$SKYGUARD_PATH/venv"
            rm -f "$FILTERED_REQ"
        fi
        
        echo -e "${GREEN}   ✅ Venv recreated and packages reinstalled${NC}"
    fi
    
    source venv/bin/activate
    
    # Check if torch is installed in venv (should NOT be)
    TORCH_IN_VENV=$(python3 -c "
import sys
import os
try:
    import torch
    torch_path = os.path.abspath(torch.__file__)
    venv_path = os.path.abspath('$SKYGUARD_PATH/venv')
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
            deactivate 2>/dev/null || true
            remove_torch_from_venv "$SKYGUARD_PATH/venv"
            
            # Verify removal worked
            source venv/bin/activate
            sleep 1
            TORCH_IN_VENV_AFTER=$(python3 -c "
import sys
import os
try:
    import torch
    torch_path = os.path.abspath(torch.__file__)
    venv_path = os.path.abspath('$SKYGUARD_PATH/venv')
    if venv_path in torch_path:
        print('venv')
    else:
        print('system')
except Exception:
    print('not_found')
" 2>/dev/null || echo "unknown")
            
            if [ "$TORCH_IN_VENV_AFTER" = "system" ]; then
                echo -e "${GREEN}   ✅ Successfully removed venv torch, now using system PyTorch${NC}"
                PYTORCH_CHECK=$(python3 -c "import torch; print('CUDA' if torch.cuda.is_available() else 'CPU')" 2>/dev/null || echo "NOT_FOUND")
                if [ "$PYTORCH_CHECK" = "CUDA" ]; then
                    echo -e "${GREEN}   ✅ CUDA is now available!${NC}"
                fi
            elif [ "$TORCH_IN_VENV_AFTER" = "not_found" ]; then
                # Torch not found - check if venv has system-site-packages
                if [ -f "$SKYGUARD_PATH/venv/pyvenv.cfg" ] && grep -q "include-system-site-packages = true" "$SKYGUARD_PATH/venv/pyvenv.cfg" 2>/dev/null; then
                    echo -e "${YELLOW}   ⚠️  Torch removed from venv, but system torch not accessible${NC}"
                    echo -e "${YELLOW}   This may indicate system PyTorch is not installed or not accessible${NC}"
                    echo -e "${CYAN}   Verify system PyTorch: python3 -c 'import torch; print(torch.__version__)'${NC}"
                else
                    echo -e "${GREEN}   ✅ Torch removed from venv${NC}"
                    echo -e "${RED}   ❌ CRITICAL: venv doesn't have --system-site-packages!${NC}"
                    echo -e "${YELLOW}   Recreating venv with --system-site-packages...${NC}"
                    deactivate 2>/dev/null || true
                    rm -rf "$SKYGUARD_PATH/venv"
                    python3 -m venv --system-site-packages "$SKYGUARD_PATH/venv"
                    echo -e "${YELLOW}   ⚠️  Please re-run the installation step${NC}"
                fi
            elif [ "$TORCH_IN_VENV_AFTER" = "venv" ]; then
                echo -e "${RED}   ❌ CRITICAL: Torch still in venv after removal attempt!${NC}"
                echo -e "${YELLOW}   Manual cleanup required. Run:${NC}"
                echo -e "${CYAN}   cd $SKYGUARD_PATH && source venv/bin/activate${NC}"
                echo -e "${CYAN}   pip uninstall -y torch torchvision torchaudio${NC}"
                echo -e "${CYAN}   rm -rf venv/lib/python*/site-packages/torch*${NC}"
            else
                echo -e "${RED}   ❌ CRITICAL: Could not verify torch removal status!${NC}"
                echo -e "${YELLOW}   Manual verification required${NC}"
            fi
        elif [ "$TORCH_IN_VENV" = "system" ]; then
            echo -e "${GREEN}   ✅ Confirmed: Using system PyTorch (correct)${NC}"
        fi
    else
        echo -e "${RED}   ❌ PyTorch CUDA not available${NC}"
        echo -e "${CYAN}   Source detected: $TORCH_IN_VENV${NC}"
        
        if [ "$TORCH_IN_VENV" = "venv" ]; then
            echo -e "${RED}   ❌ CRITICAL: PyTorch is installed in venv (wrong version)${NC}"
            echo -e "${YELLOW}   Removing venv-installed torch packages...${NC}"
            deactivate 2>/dev/null || true
            remove_torch_from_venv "$SKYGUARD_PATH/venv"
            source venv/bin/activate
            echo -e "${CYAN}   Testing system PyTorch again...${NC}"
            PYTORCH_CHECK=$(python3 -c "import torch; print('CUDA' if torch.cuda.is_available() else 'CPU')" 2>/dev/null || echo "NOT_FOUND")
            if [ "$PYTORCH_CHECK" = "CUDA" ]; then
                echo -e "${GREEN}   ✅ Fixed! PyTorch CUDA now working from system${NC}"
            else
                echo -e "${YELLOW}   ⚠️  Still not working. Check that PyTorch was installed system-wide with CUDA support${NC}"
                if [ "$USE_SYSTEM_SITE_PACKAGES" != "true" ]; then
                    echo -e "${YELLOW}   venv was created without --system-site-packages${NC}"
                    echo -e "${YELLOW}   Run: ./scripts/fix_jetson_venv.sh to fix it${NC}"
                fi
            fi
        elif [ "$USE_SYSTEM_SITE_PACKAGES" != "true" ]; then
            echo -e "${YELLOW}   venv was created without --system-site-packages${NC}"
            echo -e "${YELLOW}   Run: ./scripts/fix_jetson_venv.sh to fix it${NC}"
        else
            echo -e "${YELLOW}   Check that PyTorch was installed system-wide with CUDA support${NC}"
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
# Final verification: Check if torch is in venv (CRITICAL CHECK)
if [ "$DETECTED_PLATFORM" = "jetson" ] && [ -d "$SKYGUARD_PATH/venv" ]; then
    echo -e "\n${BLUE}🔍 Final verification: Checking for torch in venv...${NC}"
    cd "$SKYGUARD_PATH"
    
    # First, verify venv has --system-site-packages
    if [ -f "venv/pyvenv.cfg" ]; then
        if ! grep -q "include-system-site-packages = true" venv/pyvenv.cfg 2>/dev/null; then
            echo -e "${RED}   ❌ CRITICAL: venv doesn't have --system-site-packages!${NC}"
            echo -e "${YELLOW}   Recreating venv with --system-site-packages...${NC}"
            deactivate 2>/dev/null || true
            rm -rf venv
            python3 -m venv --system-site-packages venv
            echo -e "${GREEN}   ✅ Venv recreated with --system-site-packages${NC}"
            echo -e "${YELLOW}   ⚠️  Packages will need to be reinstalled${NC}"
            # Reinstall packages
            source venv/bin/activate
            pip install --upgrade pip
            REQ_FILE=$(get_requirements_file)
            if [ -f "$REQ_FILE" ]; then
                FILTERED_REQ=$(filter_jetson_requirements "$REQ_FILE")
                install_jetson_requirements_safely "$FILTERED_REQ" "$SKYGUARD_PATH/venv"
                rm -f "$FILTERED_REQ"
            fi
        fi
    fi
    
    source venv/bin/activate 2>/dev/null || true
    
    # Check where torch is coming from
    TORCH_SOURCE=$(python3 -c "
import sys
import os
try:
    import torch
    torch_path = os.path.abspath(torch.__file__)
    venv_path = os.path.abspath('$SKYGUARD_PATH/venv')
    if venv_path in torch_path:
        print('venv')
    else:
        print('system')
    print(torch.__version__)
except Exception as e:
    print('not_found')
" 2>/dev/null || echo "unknown")
    
    TORCH_VERSION=$(echo "$TORCH_SOURCE" | tail -1)
    TORCH_LOCATION=$(echo "$TORCH_SOURCE" | head -1)
    
    if [ "$TORCH_LOCATION" = "venv" ]; then
        echo -e "${RED}   ❌ CRITICAL: torch $TORCH_VERSION is installed in venv!${NC}"
        echo -e "${YELLOW}   Aggressively removing venv-installed torch...${NC}"
        deactivate 2>/dev/null || true
        
        # Multiple removal attempts
        for attempt in 1 2 3; do
            echo -e "${CYAN}   Removal attempt $attempt...${NC}"
            remove_torch_from_venv "$SKYGUARD_PATH/venv"
            sleep 2
            
            # Verify it's gone
            source venv/bin/activate 2>/dev/null || true
            TORCH_CHECK=$(python3 -c "
import sys
import os
try:
    import torch
    torch_path = os.path.abspath(torch.__file__)
    venv_path = os.path.abspath('$SKYGUARD_PATH/venv')
    if venv_path in torch_path:
        print('venv')
    else:
        print('system')
except Exception:
    print('not_found')
" 2>/dev/null || echo "unknown")
            
            if [ "$TORCH_CHECK" != "venv" ]; then
                break
            fi
            deactivate 2>/dev/null || true
        done
        
        # Final check
        source venv/bin/activate 2>/dev/null || true
        sleep 1
        TORCH_AFTER=$(python3 -c "
import sys
import os
try:
    import torch
    torch_path = os.path.abspath(torch.__file__)
    venv_path = os.path.abspath('$SKYGUARD_PATH/venv')
    if venv_path in torch_path:
        print('venv')
    else:
        print('system')
    print(torch.__version__)
except Exception:
    print('not_found')
" 2>/dev/null || echo "unknown")
        
        # Parse the result
        TORCH_AFTER_LOCATION=$(echo "$TORCH_AFTER" | head -1)
        TORCH_AFTER_VERSION=$(echo "$TORCH_AFTER" | tail -1)
        
        if [ "$TORCH_AFTER_LOCATION" = "system" ]; then
            echo -e "${GREEN}   ✅ Fixed! Now using system PyTorch $TORCH_AFTER_VERSION${NC}"
            # Verify CUDA
            CUDA_CHECK=$(python3 -c "import torch; print('CUDA' if torch.cuda.is_available() else 'CPU')" 2>/dev/null || echo "NOT_FOUND")
            if [ "$CUDA_CHECK" = "CUDA" ]; then
                echo -e "${GREEN}   ✅ CUDA is available!${NC}"
            else
                echo -e "${YELLOW}   ⚠️  CUDA not available (this may be expected)${NC}"
            fi
        elif [ "$TORCH_AFTER_LOCATION" = "not_found" ]; then
            # Torch not found - check if venv has system-site-packages
            if [ -f "$SKYGUARD_PATH/venv/pyvenv.cfg" ] && grep -q "include-system-site-packages = true" "$SKYGUARD_PATH/venv/pyvenv.cfg" 2>/dev/null; then
                echo -e "${YELLOW}   ⚠️  Torch removed from venv, but system torch not accessible${NC}"
                echo -e "${YELLOW}   This may indicate system PyTorch is not installed or not accessible${NC}"
                echo -e "${CYAN}   Verify system PyTorch: python3 -c 'import torch; print(torch.__version__)'${NC}"
            else
                echo -e "${GREEN}   ✅ Torch removed from venv${NC}"
                echo -e "${RED}   ❌ CRITICAL: venv doesn't have --system-site-packages!${NC}"
                echo -e "${YELLOW}   Recreating venv...${NC}"
                deactivate 2>/dev/null || true
                rm -rf venv
                python3 -m venv --system-site-packages venv
                echo -e "${YELLOW}   ⚠️  Please re-run installation${NC}"
            fi
        elif [ "$TORCH_AFTER_LOCATION" = "venv" ]; then
            echo -e "${RED}   ❌ CRITICAL: Torch still in venv after removal attempts!${NC}"
            echo -e "${YELLOW}   Manual cleanup required. Run:${NC}"
            echo -e "${CYAN}   cd $SKYGUARD_PATH${NC}"
            echo -e "${CYAN}   source venv/bin/activate${NC}"
            echo -e "${CYAN}   pip uninstall -y torch torchvision torchaudio${NC}"
            echo -e "${CYAN}   rm -rf venv/lib/python*/site-packages/torch*${NC}"
            echo -e "${CYAN}   deactivate${NC}"
        else
            echo -e "${RED}   ❌ WARNING: Could not verify torch removal status${NC}"
            echo -e "${YELLOW}   Manual verification may be required${NC}"
        fi
        deactivate 2>/dev/null || true
    elif [ "$TORCH_LOCATION" = "system" ]; then
        echo -e "${GREEN}   ✅ Good: Using system PyTorch $TORCH_VERSION${NC}"
        # Verify CUDA
        CUDA_CHECK=$(python3 -c "import torch; print('CUDA' if torch.cuda.is_available() else 'CPU')" 2>/dev/null || echo "NOT_FOUND")
        if [ "$CUDA_CHECK" = "CUDA" ]; then
            echo -e "${GREEN}   ✅ CUDA is available!${NC}"
        else
            echo -e "${YELLOW}   ⚠️  CUDA not available${NC}"
        fi
        deactivate 2>/dev/null || true
    elif [ "$TORCH_LOCATION" = "not_found" ]; then
        # Check if venv has system-site-packages
        if [ -f "$SKYGUARD_PATH/venv/pyvenv.cfg" ] && grep -q "include-system-site-packages = true" "$SKYGUARD_PATH/venv/pyvenv.cfg" 2>/dev/null; then
            echo -e "${YELLOW}   ⚠️  Torch not found in venv, but system torch should be accessible${NC}"
            echo -e "${CYAN}   Verify system PyTorch: python3 -c 'import torch; print(torch.__version__)'${NC}"
        else
            echo -e "${RED}   ❌ CRITICAL: venv doesn't have --system-site-packages!${NC}"
            echo -e "${YELLOW}   Recreating venv with --system-site-packages...${NC}"
            deactivate 2>/dev/null || true
            rm -rf venv
            python3 -m venv --system-site-packages venv
            echo -e "${YELLOW}   ⚠️  Please re-run installation${NC}"
        fi
        deactivate 2>/dev/null || true
    fi
fi

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

