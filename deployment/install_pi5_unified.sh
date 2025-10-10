#!/bin/bash
# SkyGuard Unified Pi 5 Installation Script
# Uses main codebase with systemd services for auto-startup

set -e

echo "🛡️ SkyGuard Unified Pi 5 Installation"
echo "======================================"
echo ""

# Configuration
SKYGUARD_DIR="/home/pi/skyguard"
VENV_DIR="$SKYGUARD_DIR/venv"
REQUIREMENTS_FILE="$SKYGUARD_DIR/requirements-pi5.txt"
CONFIG_FILE="$SKYGUARD_DIR/config/skyguard.yaml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$SKYGUARD_DIR/logs/install.log"
}

# Check if running as pi user
check_user() {
    if [ "$USER" != "pi" ]; then
        echo -e "${RED}❌ This script must be run as the 'pi' user${NC}"
        echo "Please run: su - pi"
        exit 1
    fi
}

# Check system requirements
check_requirements() {
    echo -e "${BLUE}🔍 Checking system requirements...${NC}"
    
    # Check if running on Raspberry Pi
    if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
        echo -e "${YELLOW}⚠️ Warning: This doesn't appear to be a Raspberry Pi${NC}"
    fi
    
    # Check available memory
    local memory_gb=$(free -g | awk '/^Mem:/{print $2}')
    if [ $memory_gb -lt 4 ]; then
        echo -e "${YELLOW}⚠️ Warning: Less than 4GB RAM detected. Performance may be limited.${NC}"
    fi
    
    # Check disk space
    local disk_gb=$(df -BG /home/pi | tail -1 | awk '{print $4}' | sed 's/G//')
    if [ $disk_gb -lt 10 ]; then
        echo -e "${RED}❌ Insufficient disk space. Need at least 10GB free.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ System requirements check passed${NC}"
}

# Update system packages
update_system() {
    echo -e "${BLUE}📦 Updating system packages...${NC}"
    log "Updating system packages"
    
    sudo apt update
    sudo apt upgrade -y
    
    echo -e "${GREEN}✅ System packages updated${NC}"
}

# Install system dependencies
install_dependencies() {
    echo -e "${BLUE}📦 Installing system dependencies...${NC}"
    log "Installing system dependencies"
    
    # Core dependencies
    sudo apt install -y \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        python3-opencv \
        libopencv-dev \
        git \
        curl \
        wget \
        build-essential \
        cmake \
        pkg-config \
        libjpeg-dev \
        libtiff5-dev \
        libpng-dev \
        libavcodec-dev \
        libavformat-dev \
        libswscale-dev \
        libv4l-dev \
        libxvidcore-dev \
        libx264-dev \
        libgtk-3-dev \
        libcanberra-gtk3-dev \
        libcanberra-gtk3-module \
        libcanberra-gtk-dev \
        libcanberra-gtk-module \
        ffmpeg \
        v4l-utils \
        bc \
        htop \
        jq
    
    # Pi 5 specific optimizations
    echo -e "${BLUE}🔧 Applying Pi 5 optimizations...${NC}"
    
    # Enable camera interface
    sudo raspi-config nonint do_camera 0
    
    # Enable I2C and SPI
    sudo raspi-config nonint do_i2c 0
    sudo raspi-config nonint do_spi 0
    
    # Optimize GPU memory split for Pi 5
    if ! grep -q "gpu_mem=256" /boot/config.txt; then
        echo "gpu_mem=256" | sudo tee -a /boot/config.txt
    fi
    
    # Enable hardware acceleration
    if ! grep -q "dtoverlay=vc4-kms-v3d" /boot/config.txt; then
        echo "dtoverlay=vc4-kms-v3d" | sudo tee -a /boot/config.txt
    fi
    
    if ! grep -q "dtoverlay=vc4-kms-v3d-pi5" /boot/config.txt; then
        echo "dtoverlay=vc4-kms-v3d-pi5" | sudo tee -a /boot/config.txt
    fi
    
    echo -e "${GREEN}✅ System dependencies installed${NC}"
}

# Setup SkyGuard directory
setup_skyguard_directory() {
    echo -e "${BLUE}📁 Setting up SkyGuard directory...${NC}"
    log "Setting up SkyGuard directory"
    
    # Create directory if it doesn't exist
    mkdir -p "$SKYGUARD_DIR"
    cd "$SKYGUARD_DIR"
    
    # Create necessary subdirectories
    mkdir -p logs data/detections data/training models config
    
    echo -e "${GREEN}✅ SkyGuard directory setup complete${NC}"
}

# Create Python virtual environment
setup_python_environment() {
    echo -e "${BLUE}🐍 Setting up Python environment...${NC}"
    log "Setting up Python environment"
    
    cd "$SKYGUARD_DIR"
    
    # Create virtual environment
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install requirements
    if [ -f "$REQUIREMENTS_FILE" ]; then
        echo "Installing from $REQUIREMENTS_FILE..."
        pip install -r "$REQUIREMENTS_FILE"
    else
        echo "Installing minimal requirements..."
        pip install \
            opencv-python \
            numpy \
            pillow \
            pyyaml \
            flask \
            flask-cors \
            psutil \
            requests \
            ultralytics \
            torch \
            torchvision
    fi
    
    echo -e "${GREEN}✅ Python environment setup complete${NC}"
}

# Install systemd services
install_systemd_services() {
    echo -e "${BLUE}⚙️ Installing systemd services...${NC}"
    log "Installing systemd services"
    
    # Copy service files
    if [ -f "$SKYGUARD_DIR/deployment/systemd/skyguard.service" ]; then
        sudo cp "$SKYGUARD_DIR/deployment/systemd/skyguard.service" /etc/systemd/system/
        echo "✓ Copied skyguard.service"
    else
        echo -e "${RED}❌ skyguard.service not found${NC}"
        return 1
    fi
    
    if [ -f "$SKYGUARD_DIR/deployment/systemd/skyguard-web.service" ]; then
        sudo cp "$SKYGUARD_DIR/deployment/systemd/skyguard-web.service" /etc/systemd/system/
        echo "✓ Copied skyguard-web.service"
    else
        echo -e "${RED}❌ skyguard-web.service not found${NC}"
        return 1
    fi
    
    # Reload systemd
    sudo systemctl daemon-reload
    
    # Enable services
    sudo systemctl enable skyguard.service
    sudo systemctl enable skyguard-web.service
    
    echo -e "${GREEN}✅ Systemd services installed and enabled${NC}"
}

# Setup log rotation
setup_log_rotation() {
    echo -e "${BLUE}📄 Setting up log rotation...${NC}"
    log "Setting up log rotation"
    
    # Create logrotate configuration
    sudo tee /etc/logrotate.d/skyguard > /dev/null <<EOF
$SKYGUARD_DIR/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    create 644 pi pi
    postrotate
        systemctl reload skyguard.service skyguard-web.service > /dev/null 2>&1 || true
    endscript
}
EOF
    
    echo -e "${GREEN}✅ Log rotation configured${NC}"
}

# Create configuration file
create_config() {
    echo -e "${BLUE}⚙️ Creating configuration file...${NC}"
    log "Creating configuration file"
    
    if [ ! -f "$CONFIG_FILE" ]; then
        # Create default configuration for Pi 5
        cat > "$CONFIG_FILE" <<EOF
ai:
  classes:
  - bird
  confidence_threshold: 0.48
  input_size: 1080
  model_path: models/yolov8n.pt
  model_type: yolo
  nms_threshold: 0.5

camera:
  brightness: 0
  contrast: 0
  flip_horizontal: false
  flip_vertical: false
  focus_mode: infinity
  focus_value: 0
  fps: 30
  height: 1080
  live_view: false
  rotation: '0'
  source: '0'
  width: 1920

hardware:
  gpio_enabled: false
  platform: raspberry_pi5

logging:
  backup_count: 5
  console_output: true
  file: logs/skyguard.log
  level: INFO
  max_size_mb: 10

notifications:
  audio:
    enabled: true
    repeat_count: 3
    repeat_interval: 2.0
    sound_file: sounds/raptor_alert.wav
    volume: 0.5
  email:
    enabled: false
    from_email: ''
    password: ''
    smtp_port: 587
    smtp_server: smtp.gmail.com
    to_emails: []
    username: ''
  push:
    api_key: ''
    device_id: ''
    enabled: false
  sms:
    account_sid: ''
    auth_token: ''
    enabled: false
    from_number: ''
    to_numbers: []

rate_limiting:
  cooldown_period: 300
  max_alerts_per_hour: 10
  min_alert_interval: 30

storage:
  compress_images: true
  database_path: data/skyguard.db
  detection_image_retention_days: 7
  detection_images_path: data/detections
  log_retention_days: 30
  max_image_size_mb: 5

system:
  debug_mode: false
  detection_interval: 1
  max_detection_history: 1000
  save_detection_frames: true

training:
  augmentations:
    brightness: 0.2
    contrast: 0.2
    enabled: true
    rotation: 15
    saturation: 0.2
  batch_size: 16
  data_path: data/training
  epochs: 100
  image_size:
  - 1080
  - 1080
  learning_rate: 0.001
  validation_split: 0.2
EOF
        echo "✓ Created default configuration"
    else
        echo "✓ Configuration file already exists"
    fi
    
    echo -e "${GREEN}✅ Configuration setup complete${NC}"
}

# Setup control script
setup_control_script() {
    echo -e "${BLUE}🔧 Setting up control script...${NC}"
    log "Setting up control script"
    
    # Make control script executable
    chmod +x "$SKYGUARD_DIR/deployment/scripts/skyguard-control.sh"
    chmod +x "$SKYGUARD_DIR/deployment/scripts/health_check.sh"
    
    # Create symlink for easy access
    sudo ln -sf "$SKYGUARD_DIR/deployment/scripts/skyguard-control.sh" /usr/local/bin/skyguard-control
    
    echo -e "${GREEN}✅ Control script setup complete${NC}"
}

# Test installation
test_installation() {
    echo -e "${BLUE}🧪 Testing installation...${NC}"
    log "Testing installation"
    
    # Test Python environment
    source "$VENV_DIR/bin/activate"
    python -c "import cv2, numpy, yaml, flask; print('✓ Python dependencies OK')"
    
    # Test systemd services
    if systemctl is-enabled skyguard.service > /dev/null 2>&1; then
        echo "✓ Detection service enabled"
    else
        echo -e "${YELLOW}⚠ Detection service not enabled${NC}"
    fi
    
    if systemctl is-enabled skyguard-web.service > /dev/null 2>&1; then
        echo "✓ Web portal service enabled"
    else
        echo -e "${YELLOW}⚠ Web portal service not enabled${NC}"
    fi
    
    echo -e "${GREEN}✅ Installation test complete${NC}"
}

# Main installation
main() {
    echo "Starting SkyGuard unified installation..."
    echo ""
    
    # Run installation steps
    check_user
    check_requirements
    update_system
    install_dependencies
    setup_skyguard_directory
    setup_python_environment
    install_systemd_services
    setup_log_rotation
    create_config
    setup_control_script
    test_installation
    
    echo ""
    echo -e "${GREEN}🎉 SkyGuard installation complete!${NC}"
    echo ""
    echo "📋 Next steps:"
    echo "1. Configure SkyGuard: skyguard-control status"
    echo "2. Test the system: skyguard-control health"
    echo "3. Start services: skyguard-control start"
    echo "4. View logs: skyguard-control logs"
    echo ""
    echo "🌐 Web portal will be available at: http://$(hostname -I | awk '{print $1}'):8080"
    echo ""
    echo "📚 For more information, see the deployment documentation."
    
    log "Installation completed successfully"
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        echo "SkyGuard Unified Pi 5 Installation"
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --help, -h    Show this help message"
        echo "  --test-only   Only run tests, don't install"
        echo ""
        exit 0
        ;;
    --test-only)
        test_installation
        ;;
    *)
        main
        ;;
esac

