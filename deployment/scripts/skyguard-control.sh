#!/bin/bash
# SkyGuard Service Control Script
# Unified management for SkyGuard detection and web services

set -e

# Configuration
SKYGUARD_DIR="/home/pi/skyguard"
HEALTH_SCRIPT="$SKYGUARD_DIR/deployment/scripts/health_check.sh"
LOG_FILE="$SKYGUARD_DIR/logs/control.log"

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
    echo "SkyGuard Service Control"
    echo "========================"
    echo ""
    echo "Usage: $0 <command>"
    echo ""
    echo "Commands:"
    echo "  start       Start all SkyGuard services"
    echo "  stop        Stop all SkyGuard services"
    echo "  restart     Restart all SkyGuard services"
    echo "  status      Show service status"
    echo "  logs        View service logs"
    echo "  health      Run health check"
    echo "  install     Install systemd services"
    echo "  uninstall   Remove systemd services"
    echo "  enable      Enable auto-start on boot"
    echo "  disable     Disable auto-start on boot"
    echo ""
    echo "Examples:"
    echo "  $0 start"
    echo "  $0 status"
    echo "  $0 logs --follow"
    echo "  $0 health --auto-restart"
}

# Start services
start_services() {
    echo -e "${BLUE}🚀 Starting SkyGuard services...${NC}"
    log "Starting services"
    
    # Start detection system first
    echo "Starting detection system..."
    systemctl start skyguard.service
    sleep 3
    
    # Start web portal
    echo "Starting web portal..."
    systemctl start skyguard-web.service
    
    # Wait for services to stabilize
    sleep 5
    
    # Check status
    if systemctl is-active --quiet skyguard.service && systemctl is-active --quiet skyguard-web.service; then
        echo -e "${GREEN}✅ All services started successfully${NC}"
        log "Services started successfully"
    else
        echo -e "${RED}❌ Some services failed to start${NC}"
        log "Service start failed"
        return 1
    fi
}

# Stop services
stop_services() {
    echo -e "${BLUE}🛑 Stopping SkyGuard services...${NC}"
    log "Stopping services"
    
    # Stop web portal first
    systemctl stop skyguard-web.service 2>/dev/null || true
    sleep 2
    
    # Stop detection system
    systemctl stop skyguard.service 2>/dev/null || true
    
    echo -e "${GREEN}✅ All services stopped${NC}"
    log "Services stopped"
}

# Restart services
restart_services() {
    echo -e "${BLUE}🔄 Restarting SkyGuard services...${NC}"
    log "Restarting services"
    
    stop_services
    sleep 3
    start_services
}

# Show service status
show_status() {
    echo -e "${BLUE}📋 SkyGuard Service Status${NC}"
    echo "================================"
    echo ""
    
    # Detection service
    echo "🔍 Detection System:"
    systemctl status skyguard.service --no-pager -l
    echo ""
    
    # Web portal service
    echo "🌐 Web Portal:"
    systemctl status skyguard-web.service --no-pager -l
    echo ""
    
    # Quick summary
    echo "📊 Quick Summary:"
    if systemctl is-active --quiet skyguard.service; then
        echo -e "  Detection: ${GREEN}✓ Running${NC}"
    else
        echo -e "  Detection: ${RED}✗ Stopped${NC}"
    fi
    
    if systemctl is-active --quiet skyguard-web.service; then
        echo -e "  Web Portal: ${GREEN}✓ Running${NC}"
    else
        echo -e "  Web Portal: ${RED}✗ Stopped${NC}"
    fi
}

# View logs
view_logs() {
    local follow_flag=""
    if [ "$1" = "--follow" ] || [ "$1" = "-f" ]; then
        follow_flag="-f"
    fi
    
    echo -e "${BLUE}📄 SkyGuard Service Logs${NC}"
    echo "=========================="
    echo ""
    
    if [ -n "$follow_flag" ]; then
        echo "Following logs (Ctrl+C to stop)..."
        journalctl -u skyguard.service -u skyguard-web.service $follow_flag
    else
        echo "Recent logs (last 50 lines):"
        journalctl -u skyguard.service -u skyguard-web.service --lines=50 --no-pager
    fi
}

# Run health check
run_health_check() {
    echo -e "${BLUE}🔍 Running SkyGuard Health Check${NC}"
    echo "===================================="
    echo ""
    
    if [ -f "$HEALTH_SCRIPT" ]; then
        bash "$HEALTH_SCRIPT" "$@"
    else
        echo -e "${RED}❌ Health check script not found: $HEALTH_SCRIPT${NC}"
        return 1
    fi
}

# Install systemd services
install_services() {
    echo -e "${BLUE}📦 Installing SkyGuard systemd services...${NC}"
    log "Installing systemd services"
    
    # Check if running as root or with sudo
    if [ "$EUID" -ne 0 ]; then
        echo -e "${RED}❌ This command requires root privileges${NC}"
        echo "Please run: sudo $0 install"
        return 1
    fi
    
    # Copy service files
    if [ -f "$SKYGUARD_DIR/deployment/systemd/skyguard.service" ]; then
        cp "$SKYGUARD_DIR/deployment/systemd/skyguard.service" /etc/systemd/system/
        echo "✓ Copied skyguard.service"
    else
        echo -e "${RED}❌ skyguard.service not found${NC}"
        return 1
    fi
    
    if [ -f "$SKYGUARD_DIR/deployment/systemd/skyguard-web.service" ]; then
        cp "$SKYGUARD_DIR/deployment/systemd/skyguard-web.service" /etc/systemd/system/
        echo "✓ Copied skyguard-web.service"
    else
        echo -e "${RED}❌ skyguard-web.service not found${NC}"
        return 1
    fi
    
    # Reload systemd
    systemctl daemon-reload
    echo "✓ Reloaded systemd daemon"
    
    echo -e "${GREEN}✅ Systemd services installed successfully${NC}"
    log "Systemd services installed"
}

# Uninstall systemd services
uninstall_services() {
    echo -e "${BLUE}🗑️ Removing SkyGuard systemd services...${NC}"
    log "Uninstalling systemd services"
    
    # Check if running as root or with sudo
    if [ "$EUID" -ne 0 ]; then
        echo -e "${RED}❌ This command requires root privileges${NC}"
        echo "Please run: sudo $0 uninstall"
        return 1
    fi
    
    # Stop and disable services
    systemctl stop skyguard-web.service 2>/dev/null || true
    systemctl stop skyguard.service 2>/dev/null || true
    systemctl disable skyguard-web.service 2>/dev/null || true
    systemctl disable skyguard.service 2>/dev/null || true
    
    # Remove service files
    rm -f /etc/systemd/system/skyguard.service
    rm -f /etc/systemd/system/skyguard-web.service
    
    # Reload systemd
    systemctl daemon-reload
    
    echo -e "${GREEN}✅ Systemd services removed successfully${NC}"
    log "Systemd services removed"
}

# Enable auto-start
enable_auto_start() {
    echo -e "${BLUE}🔧 Enabling SkyGuard auto-start on boot...${NC}"
    log "Enabling auto-start"
    
    systemctl enable skyguard.service
    systemctl enable skyguard-web.service
    
    echo -e "${GREEN}✅ Auto-start enabled${NC}"
    log "Auto-start enabled"
}

# Disable auto-start
disable_auto_start() {
    echo -e "${BLUE}🔧 Disabling SkyGuard auto-start on boot...${NC}"
    log "Disabling auto-start"
    
    systemctl disable skyguard.service
    systemctl disable skyguard-web.service
    
    echo -e "${GREEN}✅ Auto-start disabled${NC}"
    log "Auto-start disabled"
}

# Main command handler
main() {
    case "${1:-}" in
        start)
            start_services
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        status)
            show_status
            ;;
        logs)
            shift
            view_logs "$@"
            ;;
        health)
            shift
            run_health_check "$@"
            ;;
        install)
            install_services
            ;;
        uninstall)
            uninstall_services
            ;;
        enable)
            enable_auto_start
            ;;
        disable)
            disable_auto_start
            ;;
        help|--help|-h)
            usage
            ;;
        "")
            echo -e "${YELLOW}⚠️ No command specified${NC}"
            echo ""
            usage
            exit 1
            ;;
        *)
            echo -e "${RED}❌ Unknown command: $1${NC}"
            echo ""
            usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"

