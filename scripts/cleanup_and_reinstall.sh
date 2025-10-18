#!/bin/bash
# SkyGuard Cleanup and Fresh Installation Script
# Stops services, removes directory, clones fresh repository, and installs with defaults

set -e

# Configuration
SKYGUARD_DIR="/home/pi/skyguard"
REPO_URL="https://github.com/jad3tx/SkyGuard.git"
LOG_FILE="/tmp/skyguard_cleanup_reinstall.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Print usage information
usage() {
    echo "SkyGuard Cleanup and Fresh Installation"
    echo "========================================"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --force           Force cleanup even if services are running"
    echo "  --no-backup       Don't create backup of current installation"
    echo "  --skip-git        Skip git clone (use existing directory)"
    echo "  --install-only    Skip cleanup, only run installation"
    echo "  --verbose         Enable verbose output"
    echo "  --help            Show this help message"
    echo ""
    echo "This script will:"
    echo "  1. Stop all SkyGuard services"
    echo "  2. Remove /home/pi/skyguard directory"
    echo "  3. Clone fresh repository from GitHub"
    echo "  4. Run installation with default values"
    echo "  5. Start services automatically"
    echo ""
    echo "Examples:"
    echo "  $0                    # Full cleanup and reinstall"
    echo "  $0 --no-backup        # Skip backup creation"
    echo "  $0 --install-only      # Only run installation"
}

# Check if running as pi user
check_user() {
    if [ "$USER" != "pi" ]; then
        echo -e "${RED}❌ This script should be run as the 'pi' user${NC}"
        echo "Please run: su - pi"
        exit 1
    fi
}

# Check if git is available
check_git() {
    if ! command -v git &> /dev/null; then
        echo -e "${RED}❌ Git is not installed${NC}"
        echo "Please install git first:"
        echo "  sudo apt update && sudo apt install -y git"
        exit 1
    fi
}

# Create backup of current installation
create_backup() {
    if [ "$NO_BACKUP" = true ]; then
        return 0
    fi
    
    if [ -d "$SKYGUARD_DIR" ]; then
        echo -e "${BLUE}📦 Creating backup of current installation...${NC}"
        log "Creating backup of current installation"
        
        local backup_dir="/home/pi/skyguard_backup_$(date +%Y%m%d_%H%M%S)"
        
        # Create backup directory
        mkdir -p "$backup_dir"
        
        # Copy important files
        if [ -f "$SKYGUARD_DIR/config/skyguard.yaml" ]; then
            cp "$SKYGUARD_DIR/config/skyguard.yaml" "$backup_dir/"
            echo "✓ Backed up configuration file"
        fi
        
        if [ -d "$SKYGUARD_DIR/data" ]; then
            cp -r "$SKYGUARD_DIR/data" "$backup_dir/"
            echo "✓ Backed up data directory"
        fi
        
        if [ -d "$SKYGUARD_DIR/logs" ]; then
            cp -r "$SKYGUARD_DIR/logs" "$backup_dir/"
            echo "✓ Backed up logs directory"
        fi
        
        echo -e "${GREEN}✅ Backup created: $backup_dir${NC}"
        log "Backup created: $backup_dir"
    fi
}

# Stop all SkyGuard services
stop_services() {
    echo -e "${BLUE}🛑 Stopping SkyGuard services...${NC}"
    log "Stopping SkyGuard services"
    
    # Stop systemd services
    sudo systemctl stop skyguard.service 2>/dev/null || true
    sudo systemctl stop skyguard-web.service 2>/dev/null || true
    
    # Kill any running processes
    pkill -f "python.*skyguard.main" 2>/dev/null || true
    pkill -f "start_web_portal.py" 2>/dev/null || true
    pkill -f "skyguard" 2>/dev/null || true
    
    # Wait a moment for processes to stop
    sleep 2
    
    echo -e "${GREEN}✅ Services stopped${NC}"
    log "Services stopped successfully"
}

# Remove SkyGuard directory
remove_skyguard_dir() {
    if [ -d "$SKYGUARD_DIR" ]; then
        echo -e "${BLUE}🗑️ Removing SkyGuard directory...${NC}"
        log "Removing SkyGuard directory: $SKYGUARD_DIR"
        
        # Remove directory
        rm -rf "$SKYGUARD_DIR"
        
        echo -e "${GREEN}✅ SkyGuard directory removed${NC}"
        log "SkyGuard directory removed successfully"
    else
        echo -e "${YELLOW}⚠️ SkyGuard directory not found: $SKYGUARD_DIR${NC}"
        log "SkyGuard directory not found"
    fi
}

# Clone fresh repository
clone_repository() {
    if [ "$SKIP_GIT" = true ]; then
        echo -e "${YELLOW}⚠️ Skipping git clone (using existing directory)${NC}"
        return 0
    fi
    
    echo -e "${BLUE}📥 Cloning fresh repository...${NC}"
    log "Cloning repository from: $REPO_URL"
    
    # Clone repository
    git clone "$REPO_URL" "$SKYGUARD_DIR"
    
    # Change to directory
    cd "$SKYGUARD_DIR"
    
    echo -e "${GREEN}✅ Repository cloned successfully${NC}"
    log "Repository cloned successfully"
}

# Run installation with default values
run_installation() {
    echo -e "${BLUE}🔧 Running installation with default values...${NC}"
    log "Running installation with default values"
    
    # Change to SkyGuard directory
    cd "$SKYGUARD_DIR"
    
    # Make installer executable
    chmod +x deployment/install_pi5_unified.sh
    
    # Run installation script with default values
    echo "Running installer with default values..."
    echo "This may take several minutes..."
    
    # Run the installer
    ./deployment/install_pi5_unified.sh
    
    echo -e "${GREEN}✅ Installation completed${NC}"
    log "Installation completed successfully"
}

# Start services
start_services() {
    echo -e "${BLUE}🚀 Starting SkyGuard services...${NC}"
    log "Starting SkyGuard services"
    
    # Change to SkyGuard directory
    cd "$SKYGUARD_DIR"
    
    # Start services using the control script
    if [ -f "deployment/scripts/skyguard-control.sh" ]; then
        chmod +x deployment/scripts/skyguard-control.sh
        ./deployment/scripts/skyguard-control.sh start
    else
        # Fallback: start services manually
        sudo systemctl start skyguard.service
        sudo systemctl start skyguard-web.service
    fi
    
    # Wait for services to stabilize
    sleep 5
    
    # Check if services are running
    if systemctl is-active --quiet skyguard.service && systemctl is-active --quiet skyguard-web.service; then
        echo -e "${GREEN}✅ All services started successfully${NC}"
        log "All services started successfully"
    else
        echo -e "${YELLOW}⚠️ Some services may not have started properly${NC}"
        log "Some services may not have started properly"
    fi
}

# Show final information
show_final_info() {
    echo ""
    echo -e "${BLUE}📋 Installation Complete${NC}"
    echo "========================"
    echo ""
    echo "🌐 Web Portal:"
    echo "   - URL: http://$(hostname -I | awk '{print $1}'):8080"
    echo "   - Local: http://localhost:8080"
    echo ""
    echo "🔍 Detection System:"
    echo "   - Status: Check with 'sudo systemctl status skyguard.service'"
    echo "   - Logs: tail -f $SKYGUARD_DIR/logs/skyguard.log"
    echo ""
    echo "📊 Management:"
    echo "   - Start: ./scripts/start_skyguard.sh"
    echo "   - Stop: ./scripts/stop_skyguard.sh"
    echo "   - Status: sudo systemctl status skyguard.service skyguard-web.service"
    echo ""
    echo "📁 Directory: $SKYGUARD_DIR"
    echo "📄 Logs: $SKYGUARD_DIR/logs/"
    echo "⚙️ Config: $SKYGUARD_DIR/config/skyguard.yaml"
}

# Main function
main() {
    # Parse command line arguments
    FORCE=false
    NO_BACKUP=false
    SKIP_GIT=false
    INSTALL_ONLY=false
    VERBOSE=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --force)
                FORCE=true
                shift
                ;;
            --no-backup)
                NO_BACKUP=true
                shift
                ;;
            --skip-git)
                SKIP_GIT=true
                shift
                ;;
            --install-only)
                INSTALL_ONLY=true
                shift
                ;;
            --verbose)
                VERBOSE=true
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
    
    # Show banner
    echo "🧹 SkyGuard Cleanup and Fresh Installation"
    echo "==========================================="
    echo ""
    
    # Run checks
    check_user
    check_git
    
    # Create backup if not skipping
    if [ "$INSTALL_ONLY" = false ]; then
        create_backup
    fi
    
    # Stop services if not install-only
    if [ "$INSTALL_ONLY" = false ]; then
        stop_services
    fi
    
    # Remove directory if not install-only
    if [ "$INSTALL_ONLY" = false ]; then
        remove_skyguard_dir
    fi
    
    # Clone repository if not skipping
    if [ "$SKIP_GIT" = false ]; then
        clone_repository
    fi
    
    # Run installation
    run_installation
    
    # Start services
    start_services
    
    # Show final information
    show_final_info
    
    echo ""
    echo -e "${GREEN}✅ SkyGuard cleanup and reinstallation completed!${NC}"
    log "SkyGuard cleanup and reinstallation completed successfully"
}

# Run main function with all arguments
main "$@"
