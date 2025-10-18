#!/bin/bash
# SkyGuard System Stop Script
# Stops both the main detection system and web portal

set -e

# Configuration
SKYGUARD_DIR="/home/pi/skyguard"
LOG_FILE="$SKYGUARD_DIR/logs/stop.log"

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
    echo "SkyGuard System Stop"
    echo "===================="
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --main-only     Stop only the main detection system"
    echo "  --web-only      Stop only the web portal"
    echo "  --force         Force stop (kill processes)"
    echo "  --verbose       Enable verbose output"
    echo "  --help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    # Stop both services"
    echo "  $0 --main-only        # Stop only detection system"
    echo "  $0 --web-only         # Stop only web portal"
    echo "  $0 --force            # Force stop all processes"
}

# Check if running as pi user
check_user() {
    if [ "$USER" != "pi" ]; then
        echo -e "${RED}❌ This script should be run as the 'pi' user${NC}"
        echo "Please run: su - pi"
        exit 1
    fi
}

# Stop main detection system
stop_main_system() {
    echo -e "${BLUE}🛑 Stopping SkyGuard detection system...${NC}"
    log "Stopping main detection system"
    
    # Stop systemd service
    if systemctl is-active --quiet skyguard.service 2>/dev/null; then
        sudo systemctl stop skyguard.service
        echo "✓ Stopped skyguard.service"
    fi
    
    # Kill any running processes
    if pgrep -f "python.*skyguard.main" >/dev/null 2>&1; then
        if [ "$FORCE" = true ]; then
            pkill -9 -f "python.*skyguard.main" 2>/dev/null || true
            echo "✓ Force killed main system processes"
        else
            pkill -f "python.*skyguard.main" 2>/dev/null || true
            echo "✓ Stopped main system processes"
        fi
    fi
    
    echo -e "${GREEN}✅ Main detection system stopped${NC}"
    log "Main detection system stopped successfully"
}

# Stop web portal
stop_web_portal() {
    echo -e "${BLUE}🛑 Stopping SkyGuard web portal...${NC}"
    log "Stopping web portal"
    
    # Stop systemd service
    if systemctl is-active --quiet skyguard-web.service 2>/dev/null; then
        sudo systemctl stop skyguard-web.service
        echo "✓ Stopped skyguard-web.service"
    fi
    
    # Kill any running processes
    if pgrep -f "start_web_portal.py" >/dev/null 2>&1; then
        if [ "$FORCE" = true ]; then
            pkill -9 -f "start_web_portal.py" 2>/dev/null || true
            echo "✓ Force killed web portal processes"
        else
            pkill -f "start_web_portal.py" 2>/dev/null || true
            echo "✓ Stopped web portal processes"
        fi
    fi
    
    echo -e "${GREEN}✅ Web portal stopped${NC}"
    log "Web portal stopped successfully"
}

# Check if services are running
check_running_services() {
    local main_running=false
    local web_running=false
    
    # Check for main process
    if pgrep -f "python.*skyguard.main" >/dev/null 2>&1; then
        main_running=true
    fi
    
    # Check for web portal process
    if pgrep -f "start_web_portal.py" >/dev/null 2>&1; then
        web_running=true
    fi
    
    if [ "$main_running" = false ] && [ "$web_running" = false ]; then
        echo -e "${YELLOW}⚠️ No SkyGuard services are currently running${NC}"
        return 1
    fi
    
    return 0
}

# Show service status
show_status() {
    echo ""
    echo -e "${BLUE}📋 Service Status${NC}"
    echo "=================="
    echo ""
    
    # Check main system
    if pgrep -f "python.*skyguard.main" >/dev/null 2>&1; then
        echo -e "🔍 Detection System: ${RED}Running${NC}"
    else
        echo -e "🔍 Detection System: ${GREEN}Stopped${NC}"
    fi
    
    # Check web portal
    if pgrep -f "start_web_portal.py" >/dev/null 2>&1; then
        echo -e "🌐 Web Portal: ${RED}Running${NC}"
    else
        echo -e "🌐 Web Portal: ${GREEN}Stopped${NC}"
    fi
    
    echo ""
    echo "📊 Systemd Services:"
    systemctl is-active skyguard.service 2>/dev/null || echo "skyguard.service: inactive"
    systemctl is-active skyguard-web.service 2>/dev/null || echo "skyguard-web.service: inactive"
}

# Main function
main() {
    # Parse command line arguments
    MAIN_ONLY=false
    WEB_ONLY=false
    FORCE=false
    VERBOSE=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --main-only)
                MAIN_ONLY=true
                shift
                ;;
            --web-only)
                WEB_ONLY=true
                shift
                ;;
            --force)
                FORCE=true
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
    
    # Validate options
    if [ "$MAIN_ONLY" = true ] && [ "$WEB_ONLY" = true ]; then
        echo -e "${RED}❌ Cannot specify both --main-only and --web-only${NC}"
        exit 1
    fi
    
    # Show stop banner
    echo "🛑 SkyGuard System Stop"
    echo "======================="
    echo ""
    
    # Run checks
    check_user
    
    # Create logs directory if it doesn't exist
    mkdir -p "$SKYGUARD_DIR/logs" 2>/dev/null || true
    
    # Check if services are running
    if ! check_running_services; then
        echo -e "${YELLOW}⚠️ No services to stop${NC}"
        exit 0
    fi
    
    # Stop services based on options
    if [ "$MAIN_ONLY" = true ]; then
        stop_main_system
    elif [ "$WEB_ONLY" = true ]; then
        stop_web_portal
    else
        # Stop both services
        stop_web_portal
        sleep 2
        stop_main_system
    fi
    
    # Show final status
    show_status
    
    echo ""
    echo -e "${GREEN}✅ SkyGuard stop completed!${NC}"
    log "SkyGuard stop completed successfully"
}

# Run main function with all arguments
main "$@"
