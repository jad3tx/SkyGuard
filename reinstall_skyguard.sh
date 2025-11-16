#!/bin/bash
# SkyGuard Reinstallation Script for Raspberry Pi
# Complete uninstall and fresh install from GitHub

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
SKIP_BACKUP=false
FORCE=false

# Print usage
usage() {
    echo "SkyGuard Reinstallation Script"
    echo "=============================="
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --path PATH       SkyGuard installation path (default: /home/pi/SkyGuard)"
    echo "  --repo URL        GitHub repository URL (default: https://github.com/jad3tx/SkyGuard.git)"
    echo "  --branch BRANCH   Branch to clone (default: main)"
    echo "  --skip-backup     Skip creating backup before removal"
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
    SKYGUARD_PATH="/home/pi/SkyGuard"
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
if [ "$SKIP_BACKUP" = true ] && [ -d "$SKYGUARD_PATH" ]; then
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

# Step 6: Run installation
echo -e "\n${BLUE}📦 Step 6: Running installation...${NC}"
cd "$SKYGUARD_PATH"

# Check for uv (recommended package manager)
if command -v uv &> /dev/null; then
    echo -e "${CYAN}   Using uv for installation...${NC}"
    echo -e "${CYAN}   Creating virtual environment...${NC}"
    uv venv
    
    echo -e "${CYAN}   Installing dependencies...${NC}"
    uv pip install -r requirements.txt
    
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
    python3 -m venv venv
    
    echo -e "${CYAN}   Activating virtual environment...${NC}"
    source venv/bin/activate
    
    echo -e "${CYAN}   Upgrading pip...${NC}"
    pip install --upgrade pip
    
    echo -e "${CYAN}   Installing dependencies...${NC}"
    # Use requirements-pi.txt if available, otherwise requirements.txt
    if [ -f "requirements-pi.txt" ]; then
        pip install -r requirements-pi.txt
    else
        pip install -r requirements.txt
    fi
    
    echo -e "${GREEN}   ✅ Installation complete with pip${NC}"
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

