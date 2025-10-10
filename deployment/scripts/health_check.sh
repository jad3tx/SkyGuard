#!/bin/bash
# SkyGuard Health Check Script
# Monitors service status, camera snapshots, and system health

set -e

# Configuration
SKYGUARD_DIR="/home/pi/skyguard"
SNAPSHOT_FILE="$SKYGUARD_DIR/data/camera_snapshot.jpg"
WEB_PORT="8080"
LOG_FILE="$SKYGUARD_DIR/logs/health_check.log"
MAX_SNAPSHOT_AGE=10  # seconds

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Check if service is running
check_service() {
    local service_name="$1"
    if systemctl is-active --quiet "$service_name"; then
        echo -e "${GREEN}✓${NC} $service_name is running"
        return 0
    else
        echo -e "${RED}✗${NC} $service_name is not running"
        return 1
    fi
}

# Check camera snapshot freshness
check_camera_snapshot() {
    if [ ! -f "$SNAPSHOT_FILE" ]; then
        echo -e "${RED}✗${NC} Camera snapshot file not found: $SNAPSHOT_FILE"
        return 1
    fi
    
    local file_age=$(($(date +%s) - $(stat -c %Y "$SNAPSHOT_FILE")))
    if [ $file_age -gt $MAX_SNAPSHOT_AGE ]; then
        echo -e "${RED}✗${NC} Camera snapshot is stale (${file_age}s old)"
        return 1
    else
        echo -e "${GREEN}✓${NC} Camera snapshot is fresh (${file_age}s old)"
        return 0
    fi
}

# Check web portal availability
check_web_portal() {
    if curl -s -f "http://localhost:$WEB_PORT/api/status" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Web portal is responding"
        return 0
    else
        echo -e "${RED}✗${NC} Web portal is not responding"
        return 1
    fi
}

# Check system resources
check_system_resources() {
    local memory_usage=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
    local disk_usage=$(df /home/pi | tail -1 | awk '{print $5}' | sed 's/%//')
    
    echo -e "${GREEN}✓${NC} Memory usage: ${memory_usage}%"
    echo -e "${GREEN}✓${NC} Disk usage: ${disk_usage}%"
    
    # Warn if resources are high
    if (( $(echo "$memory_usage > 90" | bc -l) )); then
        echo -e "${YELLOW}⚠${NC} High memory usage detected"
    fi
    
    if [ $disk_usage -gt 90 ]; then
        echo -e "${YELLOW}⚠${NC} High disk usage detected"
    fi
}

# Restart services if needed
restart_services() {
    echo -e "${YELLOW}🔄${NC} Restarting SkyGuard services..."
    
    # Stop services
    systemctl stop skyguard-web.service 2>/dev/null || true
    systemctl stop skyguard.service 2>/dev/null || true
    
    # Wait a moment
    sleep 2
    
    # Start services
    systemctl start skyguard.service
    sleep 5  # Give detection system time to start
    systemctl start skyguard-web.service
    
    echo -e "${GREEN}✓${NC} Services restarted"
}

# Main health check
main() {
    echo "🔍 SkyGuard Health Check - $(date)"
    echo "=================================="
    
    local issues=0
    
    # Check services
    echo "📋 Checking services..."
    if ! check_service "skyguard.service"; then
        ((issues++))
    fi
    
    if ! check_service "skyguard-web.service"; then
        ((issues++))
    fi
    
    # Check camera snapshot
    echo "📷 Checking camera snapshot..."
    if ! check_camera_snapshot; then
        ((issues++))
    fi
    
    # Check web portal
    echo "🌐 Checking web portal..."
    if ! check_web_portal; then
        ((issues++))
    fi
    
    # Check system resources
    echo "💻 Checking system resources..."
    check_system_resources
    
    # Summary
    echo "=================================="
    if [ $issues -eq 0 ]; then
        echo -e "${GREEN}✅ All checks passed${NC}"
        log "Health check: PASSED"
        exit 0
    else
        echo -e "${RED}❌ Found $issues issue(s)${NC}"
        log "Health check: FAILED ($issues issues)"
        
        # Auto-restart if requested
        if [ "$1" = "--auto-restart" ]; then
            restart_services
            echo "🔄 Waiting for services to stabilize..."
            sleep 10
            echo "🔍 Re-running health check..."
            main
        else
            echo "💡 Run with --auto-restart to attempt automatic recovery"
        fi
        
        exit 1
    fi
}

# Handle command line arguments
case "${1:-}" in
    --auto-restart)
        main --auto-restart
        ;;
    --restart)
        restart_services
        ;;
    --status)
        echo "📋 Service Status:"
        systemctl status skyguard.service --no-pager -l
        echo ""
        systemctl status skyguard-web.service --no-pager -l
        ;;
    --logs)
        echo "📄 Recent logs:"
        journalctl -u skyguard.service -u skyguard-web.service --since "1 hour ago" --no-pager
        ;;
    *)
        main
        ;;
esac

