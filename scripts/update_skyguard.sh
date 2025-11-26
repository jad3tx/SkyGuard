#!/bin/bash
# SkyGuard Update Script
# Updates code from git without reinstalling venv or dependencies

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

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
    
    echo "$username"
}

# Print usage
usage() {
    echo "SkyGuard Update Script"
    echo "======================"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --path PATH       SkyGuard installation path (default: auto-detect)"
    echo "  --branch BRANCH   Branch to pull (default: main)"
    echo "  --help            Show this help message"
    echo ""
    echo "This script updates SkyGuard code from git without:"
    echo "  - Deleting the virtual environment"
    echo "  - Reinstalling dependencies"
    echo "  - Removing configuration files"
    echo ""
    echo "Examples:"
    echo "  $0                          # Update from main branch"
    echo "  $0 --branch develop         # Update from develop branch"
    echo "  $0 --path /opt/SkyGuard     # Update at custom path"
}

# Parse arguments
BRANCH="main"
SKYGUARD_PATH=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --path)
            SKYGUARD_PATH="$2"
            shift 2
            ;;
        --branch)
            BRANCH="$2"
            shift 2
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            usage
            exit 1
            ;;
    esac
done

# Detect platform
echo -e "${BLUE}🔍 Detecting platform...${NC}"
DETECTED_USERNAME=$(detect_platform)

# Determine SkyGuard path
if [ -z "$SKYGUARD_PATH" ]; then
    # Try to auto-detect: if script is in parent directory, look for SkyGuard sibling
    SCRIPT_DIR=$(dirname "$(readlink -f "$0" 2>/dev/null || realpath "$0" 2>/dev/null || echo "$0")")
    if [ -d "$SCRIPT_DIR/../SkyGuard" ]; then
        SKYGUARD_PATH=$(realpath "$SCRIPT_DIR/../SkyGuard")
        echo -e "${CYAN}Auto-detected SkyGuard directory: $SKYGUARD_PATH${NC}"
    else
        # Fall back to default path
        SKYGUARD_PATH="/home/$DETECTED_USERNAME/SkyGuard"
        echo -e "${CYAN}Using default SkyGuard path: $SKYGUARD_PATH${NC}"
    fi
fi

SKYGUARD_PATH=$(realpath "$SKYGUARD_PATH" 2>/dev/null || echo "$SKYGUARD_PATH")
echo -e "${CYAN}SkyGuard path: $SKYGUARD_PATH${NC}"

# Verify SkyGuard directory exists
if [ ! -d "$SKYGUARD_PATH" ]; then
    echo -e "${RED}❌ SkyGuard directory not found: $SKYGUARD_PATH${NC}"
    echo -e "${YELLOW}Please run the installation script first${NC}"
    exit 1
fi

# Verify it's a git repository
if [ ! -d "$SKYGUARD_PATH/.git" ]; then
    echo -e "${RED}❌ Not a git repository: $SKYGUARD_PATH${NC}"
    echo -e "${YELLOW}This directory doesn't appear to be a git repository${NC}"
    exit 1
fi

# Step 1: Stop SkyGuard processes
echo -e "\n${BLUE}🛑 Step 1: Stopping SkyGuard processes...${NC}"

# Function to stop processes gracefully
stop_processes() {
    local pattern="$1"
    local name="$2"
    
    if pgrep -f "$pattern" >/dev/null 2>&1; then
        echo -e "${CYAN}   Found running $name processes${NC}"
        
        # Try to stop as current user first
        if pkill -f "$pattern" 2>/dev/null; then
            sleep 1
            # Check if still running
            if pgrep -f "$pattern" >/dev/null 2>&1; then
                echo -e "${YELLOW}   ⚠️  Some processes still running, trying with sudo...${NC}"
                sudo pkill -f "$pattern" 2>/dev/null || true
                sleep 1
            fi
        else
            # If pkill failed, try with sudo
            echo -e "${YELLOW}   ⚠️  Permission denied, trying with sudo...${NC}"
            sudo pkill -f "$pattern" 2>/dev/null || true
            sleep 1
        fi
        
        # Final check
        if pgrep -f "$pattern" >/dev/null 2>&1; then
            echo -e "${YELLOW}   ⚠️  Some $name processes may still be running${NC}"
            echo -e "${CYAN}   You may need to stop them manually${NC}"
        else
            echo -e "${GREEN}   ✅ $name processes stopped${NC}"
        fi
    else
        echo -e "${CYAN}   No $name processes running${NC}"
    fi
}

stop_processes "python.*skyguard.main" "SkyGuard main"
stop_processes "skyguard.*web.*app" "SkyGuard web portal"

# Step 2: Update from git
echo -e "\n${BLUE}📥 Step 2: Updating code from git...${NC}"
cd "$SKYGUARD_PATH"

# Check current branch
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "")
echo -e "${CYAN}   Current branch: $CURRENT_BRANCH${NC}"
echo -e "${CYAN}   Target branch: $BRANCH${NC}"

# Stash any local changes
if [ -n "$(git status --porcelain 2>/dev/null)" ]; then
    echo -e "${YELLOW}   ⚠️  Uncommitted changes detected${NC}"
    echo -e "${CYAN}   Stashing local changes (including untracked files)...${NC}"
    
    # Try to stash with untracked files included
    if git stash push -u -m "Auto-stash before update $(date +%Y%m%d_%H%M%S)" 2>/dev/null; then
        echo -e "${GREEN}   ✅ Changes stashed${NC}"
    else
        # If that fails, try without untracked files
        echo -e "${CYAN}   Retrying stash (excluding untracked files)...${NC}"
        if git stash push -m "Auto-stash before update $(date +%Y%m%d_%H%M%S)" 2>/dev/null; then
            echo -e "${GREEN}   ✅ Changes stashed (untracked files preserved)${NC}"
        else
            # Last resort: check what's preventing the stash
            echo -e "${YELLOW}   ⚠️  Could not stash changes automatically${NC}"
            echo -e "${CYAN}   Checking git status...${NC}"
            git status --short
            
            # Ask user what to do
            echo ""
            echo -e "${YELLOW}   Options:${NC}"
            echo -e "${CYAN}   1. Commit your changes: git add . && git commit -m 'Your message'${NC}"
            echo -e "${CYAN}   2. Manually stash: git stash${NC}"
            echo -e "${CYAN}   3. Discard changes: git reset --hard HEAD${NC}"
            echo -e "${CYAN}   4. Continue anyway (may cause conflicts): Press Enter${NC}"
            read -p "   Choose option (1-4) or press Enter to continue: " -r
            echo
            
            if [[ $REPLY =~ ^[1-3]$ ]]; then
                echo -e "${YELLOW}   Please run the chosen option manually, then run this script again${NC}"
                exit 1
            else
                echo -e "${YELLOW}   ⚠️  Continuing with uncommitted changes (may cause conflicts)${NC}"
            fi
        fi
    fi
fi

# Switch to target branch if needed
if [ "$CURRENT_BRANCH" != "$BRANCH" ]; then
    echo -e "${CYAN}   Switching to branch: $BRANCH${NC}"
    git checkout "$BRANCH" || {
        echo -e "${RED}   ❌ Failed to switch to branch: $BRANCH${NC}"
        exit 1
    }
    echo -e "${GREEN}   ✅ Switched to branch: $BRANCH${NC}"
fi

# Pull latest changes
echo -e "${CYAN}   Pulling latest changes from origin/$BRANCH...${NC}"
git pull origin "$BRANCH" || {
    echo -e "${RED}   ❌ Failed to pull from git${NC}"
    echo -e "${YELLOW}   Check your network connection and git remote configuration${NC}"
    exit 1
}

echo -e "${GREEN}   ✅ Code updated successfully${NC}"

# Step 3: Update scripts permissions
echo -e "\n${BLUE}🔧 Step 3: Updating script permissions...${NC}"
chmod +x scripts/*.sh 2>/dev/null || true
chmod +x scripts/*.py 2>/dev/null || true
echo -e "${GREEN}   ✅ Script permissions updated${NC}"

# Step 4: Verify venv still works
echo -e "\n${BLUE}🔍 Step 4: Verifying virtual environment...${NC}"
if [ -d "venv" ]; then
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        echo -e "${GREEN}   ✅ Virtual environment is accessible${NC}"
        
        # Check if Python can import skyguard
        if python3 -c "import skyguard" 2>/dev/null; then
            echo -e "${GREEN}   ✅ SkyGuard module is importable${NC}"
        else
            echo -e "${YELLOW}   ⚠️  SkyGuard module not importable (may need to reinstall)${NC}"
        fi
        
        deactivate 2>/dev/null || true
    else
        echo -e "${YELLOW}   ⚠️  Virtual environment exists but activate script missing${NC}"
    fi
else
    echo -e "${YELLOW}   ⚠️  Virtual environment not found${NC}"
    echo -e "${CYAN}   You may need to run the installation script${NC}"
fi

# Step 5: Start SkyGuard services (optional)
echo -e "\n${BLUE}🚀 Step 5: Restarting SkyGuard services...${NC}"
read -p "   Restart SkyGuard services? (Y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    cd "$SKYGUARD_PATH"
    
    # Ensure logs directory exists
    mkdir -p logs
    
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
else
    echo -e "${CYAN}   Skipping service restart${NC}"
fi

# Final summary
echo -e "\n${GREEN}✅ SkyGuard update complete!${NC}"
echo ""
echo -e "${CYAN}📋 Summary:${NC}"
echo -e "   - SkyGuard path: $SKYGUARD_PATH"
echo -e "   - Branch: $BRANCH"
if [ -n "$MAIN_PID" ]; then
    echo -e "   - Main system PID: $MAIN_PID"
    echo -e "   - Web portal PID: $WEB_PID"
    echo -e "   - Web portal: http://localhost:8080"
fi
echo -e "   - Logs: $SKYGUARD_PATH/logs"
echo ""
echo -e "${CYAN}💡 Next steps:${NC}"
echo -e "   1. Check logs in: $SKYGUARD_PATH/logs"
if [ -n "$MAIN_PID" ]; then
    echo -e "   2. Access web portal at: http://$(hostname -I | awk '{print $1}'):8080"
    echo -e "   3. View main system logs: tail -f $SKYGUARD_PATH/logs/main.log"
    echo -e "   4. View web portal logs: tail -f $SKYGUARD_PATH/logs/web.log"
else
    echo -e "   2. Start services manually if needed"
fi

# Move update script to parent directory (peer of SkyGuard/)
echo -e "\n${BLUE}📦 Moving update script to parent directory...${NC}"
SCRIPT_NAME=$(basename "$0")
PARENT_DIR=$(dirname "$SKYGUARD_PATH")
TARGET_SCRIPT="$PARENT_DIR/$SCRIPT_NAME"

# Get absolute path of current script for comparison
SCRIPT_DIR=""
if SCRIPT_ABS=$(readlink -f "$0" 2>/dev/null); then
    SCRIPT_DIR=$(dirname "$SCRIPT_ABS")
elif SCRIPT_ABS=$(realpath "$0" 2>/dev/null); then
    SCRIPT_DIR=$(dirname "$SCRIPT_ABS")
else
    # Fallback: use cd and pwd to get absolute path
    SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
fi

# Only move if script is currently inside SkyGuard directory
if [ "$SCRIPT_DIR" != "$PARENT_DIR" ]; then
    if [ -f "$0" ]; then
        echo -e "${CYAN}   Moving $SCRIPT_NAME to $PARENT_DIR/${NC}"
        cp "$0" "$TARGET_SCRIPT" 2>/dev/null || {
            echo -e "${YELLOW}   ⚠️  Failed to copy script to parent directory${NC}"
            echo -e "${CYAN}   You may need to move it manually${NC}"
        }
        chmod +x "$TARGET_SCRIPT" 2>/dev/null || {
            echo -e "${YELLOW}   ⚠️  Failed to make script executable${NC}"
        }
        echo -e "${GREEN}   ✅ Update script moved to: $TARGET_SCRIPT${NC}"
    else
        echo -e "${YELLOW}   ⚠️  Could not determine script location${NC}"
    fi
else
    echo -e "${CYAN}   Script already in parent directory${NC}"
    chmod +x "$0" 2>/dev/null || true
fi

