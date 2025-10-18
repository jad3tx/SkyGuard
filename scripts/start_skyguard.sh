#!/bin/bash
# SkyGuard System Startup Script
# Starts both the main detection system and web portal

set -e

# Configuration
SKYGUARD_DIR="/home/pi/skyguard"
VENV_DIR="$SKYGUARD_DIR/venv"
LOG_FILE="$SKYGUARD_DIR/logs/startup.log"

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
    echo "SkyGuard System Startup"
    echo "======================="
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --main-only     Start only the main detection system"
    echo "  --web-only      Start only the web portal"
    echo "  --background    Run services in background"
    echo "  --no-wait       Don't wait for services to stabilize"
    echo "  --verbose       Enable verbose output"
    echo "  --help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                    # Start both services"
    echo "  $0 --main-only        # Start only detection system"
    echo "  $0 --web-only         # Start only web portal"
    echo "  $0 --background       # Start services in background"
}

# Check if running as pi user
check_user() {
    if [ "$USER" != "pi" ]; then
        echo -e "${RED}❌ This script should be run as the 'pi' user${NC}"
        echo "Please run: su - pi"
        exit 1
    fi
}

# Check if SkyGuard directory exists
check_skyguard_dir() {
    if [ ! -d "$SKYGUARD_DIR" ]; then
        echo -e "${RED}❌ SkyGuard directory not found: $SKYGUARD_DIR${NC}"
        echo "Please run the installation script first:"
        echo "  ./deployment/install_pi5_unified.sh"
        exit 1
    fi
}

# Check if virtual environment exists
check_venv() {
    if [ ! -d "$VENV_DIR" ]; then
        echo -e "${RED}❌ Virtual environment not found: $VENV_DIR${NC}"
        echo "Please run the installation script first:"
        echo "  ./deployment/install_pi5_unified.sh"
        exit 1
    fi
}

# Check if services are already running
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
    
    if [ "$main_running" = true ] && [ "$web_running" = true ]; then
        echo -e "${YELLOW}⚠️ Both services are already running${NC}"
        echo "Use 'stop_skyguard.sh' to stop them first, or use '--force' to restart"
        return 1
    elif [ "$main_running" = true ]; then
        echo -e "${YELLOW}⚠️ Main detection system is already running${NC}"
    elif [ "$web_running" = true ]; then
        echo -e "${YELLOW}⚠️ Web portal is already running${NC}"
    fi
}

# Start main detection system
start_main_system() {
    echo -e "${BLUE}🔍 Starting SkyGuard detection system...${NC}"
    log "Starting main detection system"
    
    # Change to SkyGuard directory
    cd "$SKYGUARD_DIR"
    
    # Activate virtual environment
    source "$VENV_DIR/bin/activate"
    
    # Start main system
    if [ "$BACKGROUND" = true ]; then
        nohup python -m skyguard.main --config config/skyguard.yaml > logs/main.log 2>&1 &
        local main_pid=$!
        echo "Main system started in background (PID: $main_pid)"
        log "Main system started in background (PID: $main_pid)"
    else
        echo "Starting main system in foreground (Ctrl+C to stop)..."
        python -m skyguard.main --config config/skyguard.yaml
    fi
}

# Start web portal
start_web_portal() {
    echo -e "${BLUE}🌐 Starting SkyGuard web portal...${NC}"
    log "Starting web portal"
    
    # Change to SkyGuard directory
    cd "$SKYGUARD_DIR"
    
    # Activate virtual environment
    source "$VENV_DIR/bin/activate"
    
    # Start web portal
    if [ "$BACKGROUND" = true ]; then
        nohup python scripts/start_web_portal.py --host 0.0.0.0 --port 8080 > logs/web.log 2>&1 &
        local web_pid=$!
        echo "Web portal started in background (PID: $web_pid)"
        log "Web portal started in background (PID: $web_pid)"
    else
        echo "Starting web portal in foreground (Ctrl+C to stop)..."
        python scripts/start_web_portal.py --host 0.0.0.0 --port 8080
    fi
}

# Wait for services to stabilize
wait_for_services() {
    if [ "$NO_WAIT" = true ]; then
        return 0
    fi
    
    echo -e "${BLUE}⏳ Waiting for services to stabilize...${NC}"
    sleep 5
    
    # Check if services are running
    local main_running=false
    local web_running=false
    
    if pgrep -f "python.*skyguard.main" >/dev/null 2>&1; then
        main_running=true
    fi
    
    if pgrep -f "start_web_portal.py" >/dev/null 2>&1; then
        web_running=true
    fi
    
    if [ "$main_running" = true ] && [ "$web_running" = true ]; then
        echo -e "${GREEN}✅ Both services are running successfully${NC}"
        log "Both services started successfully"
    elif [ "$main_running" = true ]; then
        echo -e "${GREEN}✅ Main detection system is running${NC}"
        log "Main detection system started successfully"
    elif [ "$web_running" = true ]; then
        echo -e "${GREEN}✅ Web portal is running${NC}"
        log "Web portal started successfully"
    else
        echo -e "${RED}❌ Services failed to start${NC}"
        log "Services failed to start"
        return 1
    fi
}

# Show service information
show_service_info() {
    echo ""
    echo -e "${BLUE}📋 Service Information${NC}"
    echo "======================"
    echo ""
    
    if [ "$MAIN_ONLY" = false ] && [ "$WEB_ONLY" = false ]; then
        echo "🔍 Detection System:"
        echo "   - Main process: python -m skyguard.main"
        echo "   - Config: config/skyguard.yaml"
        echo "   - Logs: logs/skyguard.log"
        echo ""
        echo "🌐 Web Portal:"
        echo "   - URL: http://$(hostname -I | awk '{print $1}'):8080"
        echo "   - Local: http://localhost:8080"
        echo "   - Logs: logs/web.log"
    elif [ "$MAIN_ONLY" = true ]; then
        echo "🔍 Detection System:"
        echo "   - Main process: python -m skyguard.main"
        echo "   - Config: config/skyguard.yaml"
        echo "   - Logs: logs/skyguard.log"
    elif [ "$WEB_ONLY" = true ]; then
        echo "🌐 Web Portal:"
        echo "   - URL: http://$(hostname -I | awk '{print $1}'):8080"
        echo "   - Local: http://localhost:8080"
        echo "   - Logs: logs/web.log"
    fi
    
    echo ""
    echo "📊 Monitoring:"
    echo "   - View logs: tail -f logs/skyguard.log"
    echo "   - Check status: ps aux | grep skyguard"
    echo "   - Stop services: ./scripts/stop_skyguard.sh"
}

# Main function
main() {
    # Parse command line arguments
    MAIN_ONLY=false
    WEB_ONLY=false
    BACKGROUND=false
    NO_WAIT=false
    VERBOSE=false
    FORCE=false
    
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
            --background)
                BACKGROUND=true
                shift
                ;;
            --no-wait)
                NO_WAIT=true
                shift
                ;;
            --verbose)
                VERBOSE=true
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
    
    # Validate options
    if [ "$MAIN_ONLY" = true ] && [ "$WEB_ONLY" = true ]; then
        echo -e "${RED}❌ Cannot specify both --main-only and --web-only${NC}"
        exit 1
    fi
    
    # Show startup banner
    echo "🛡️ SkyGuard System Startup"
    echo "=========================="
    echo ""
    
    # Run checks
    check_user
    check_skyguard_dir
    check_venv
    
    # Check for running services (unless force is specified)
    if [ "$FORCE" = false ]; then
        check_running_services
    fi
    
    # Create logs directory if it doesn't exist
    mkdir -p "$SKYGUARD_DIR/logs"
    
    # Start services based on options
    if [ "$MAIN_ONLY" = true ]; then
        start_main_system
    elif [ "$WEB_ONLY" = true ]; then
        start_web_portal
    else
        # Start both services
        if [ "$BACKGROUND" = true ]; then
            # Start main system first
            start_main_system
            sleep 3
            # Then start web portal
            start_web_portal
        else
            # Start main system in background, then web portal in foreground
            start_main_system &
            sleep 3
            start_web_portal
        fi
    fi
    
    # Wait for services to stabilize
    if [ "$BACKGROUND" = true ]; then
        wait_for_services
    fi
    
    # Show service information
    show_service_info
    
    echo ""
    echo -e "${GREEN}✅ SkyGuard startup completed!${NC}"
    log "SkyGuard startup completed successfully"
}

# Run main function with all arguments
main "$@"
