#!/bin/bash

# SkyGuard Service Cleanup Script
# Removes all SkyGuard services, cron jobs, and processes

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "🧹 SkyGuard Service Cleanup"
echo "============================"
echo ""

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    log_error "This script should not be run as root"
    exit 1
fi

# Stop and disable services
log_info "Stopping SkyGuard services..."
sudo systemctl stop skyguard.service 2>/dev/null || log_warning "skyguard.service not running"
sudo systemctl stop skyguard-web.service 2>/dev/null || log_warning "skyguard-web.service not running"

log_info "Disabling SkyGuard services..."
sudo systemctl disable skyguard.service 2>/dev/null || log_warning "skyguard.service not enabled"
sudo systemctl disable skyguard-web.service 2>/dev/null || log_warning "skyguard-web.service not enabled"

# Remove service files
log_info "Removing service files..."
sudo rm -f /etc/systemd/system/skyguard.service
sudo rm -f /etc/systemd/system/skyguard-web.service

# Reload systemd
log_info "Reloading systemd daemon..."
sudo systemctl daemon-reload

# Kill running processes
log_info "Stopping running SkyGuard processes..."
pkill -f skyguard 2>/dev/null || log_warning "No skyguard processes found"
pkill -f "start_web_portal.py" 2>/dev/null || log_warning "No web portal processes found"

# Remove cron jobs
log_info "Removing SkyGuard cron jobs..."
CURRENT_DIR=$(pwd)
# Create a temporary crontab without SkyGuard entries
crontab -l 2>/dev/null | grep -v "skyguard" | grep -v "$CURRENT_DIR" | crontab - 2>/dev/null || log_warning "No cron jobs to remove"

# Verify cleanup
log_info "Verifying cleanup..."

# Check services are gone
if ! systemctl is-active skyguard.service >/dev/null 2>&1; then
    log_success "skyguard.service stopped"
else
    log_warning "skyguard.service still active"
fi

if ! systemctl is-active skyguard-web.service >/dev/null 2>&1; then
    log_success "skyguard-web.service stopped"
else
    log_warning "skyguard-web.service still active"
fi

# Check no processes are running
if ! pgrep -f skyguard >/dev/null 2>&1; then
    log_success "No SkyGuard processes running"
else
    log_warning "SkyGuard processes still running"
fi

echo ""
log_success "SkyGuard cleanup completed!"
echo ""
echo "📋 Next steps:"
echo "   Run the install script again: ./scripts/install.sh"
echo "   Or start services manually:"
echo "     sudo systemctl start skyguard.service"
echo "     sudo systemctl start skyguard-web.service"
echo ""
