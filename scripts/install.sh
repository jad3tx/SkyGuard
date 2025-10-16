#!/bin/bash

# SkyGuard Installation Script
# Automated installation for the SkyGuard raptor alert system

set -e  # Exit on any error

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

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "This script should not be run as root"
        exit 1
    fi
}

# Detect platform
detect_platform() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        if [[ "$ID" == "raspbian" ]] || [[ "$ID" == "debian" ]] && [[ -f /proc/device-tree/model ]]; then
            if grep -q "Raspberry Pi" /proc/device-tree/model; then
                PLATFORM="raspberry_pi"
            else
                PLATFORM="debian"
            fi
        elif [[ "$ID" == "ubuntu" ]]; then
            PLATFORM="ubuntu"
        else
            PLATFORM="unknown"
        fi
    else
        PLATFORM="unknown"
    fi
    
    log_info "Detected platform: $PLATFORM"
}

# Update system packages
update_system() {
    log_info "Updating system packages..."
    
    if [[ "$PLATFORM" == "raspberry_pi" ]] || [[ "$PLATFORM" == "debian" ]]; then
        sudo apt update && sudo apt upgrade -y
    elif [[ "$PLATFORM" == "ubuntu" ]]; then
        sudo apt update && sudo apt upgrade -y
    else
        log_warning "Unknown platform, skipping system update"
    fi
}

# Install system dependencies
install_dependencies() {
    log_info "Installing system dependencies..."
    
    if [[ "$PLATFORM" == "raspberry_pi" ]] || [[ "$PLATFORM" == "debian" ]]; then
        # Install core packages first
        sudo apt install -y \
            python3 \
            python3-pip \
            python3-venv \
            python3-dev \
            python3-opencv \
            libopencv-dev \
            git \
            wget \
            curl \
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
            libcanberra-gtk3-module
        
        # Try to install BLAS/LAPACK libraries (libatlas-base-dev may not be available on newer systems)
        log_info "Installing BLAS/LAPACK libraries..."
        if sudo apt install -y libatlas-base-dev 2>/dev/null; then
            log_success "libatlas-base-dev installed successfully"
        else
            log_warning "libatlas-base-dev not available, trying alternative..."
            if sudo apt install -y libopenblas-dev 2>/dev/null; then
                log_success "libopenblas-dev installed as alternative"
            else
                log_warning "BLAS/LAPACK libraries not available, continuing without them"
                log_warning "Some scientific computing features may be limited"
            fi
        fi
        
        # Try to install additional GTK/Canberra packages (may not be available on newer systems)
        log_info "Installing additional GTK/Canberra packages..."
        if sudo apt install -y libcanberra-gtk-dev libcanberra-gtk-module 2>/dev/null; then
            log_success "Canberra GTK packages installed successfully"
        else
            log_warning "Canberra GTK packages not available, continuing without them"
            log_warning "Some audio/notification features may be limited"
        fi
        
    elif [[ "$PLATFORM" == "ubuntu" ]]; then
        sudo apt install -y \
            python3 \
            python3-pip \
            python3-venv \
            python3-dev \
            python3-opencv \
            libopencv-dev \
            git \
            wget \
            curl \
            build-essential \
            cmake \
            pkg-config
    else
        log_error "Unsupported platform for automatic dependency installation"
        exit 1
    fi
}

# Setup Python virtual environment
setup_python_env() {
    log_info "Setting up Python virtual environment..."
    
    if [[ -d "venv" ]]; then
        log_warning "Virtual environment already exists, removing..."
        rm -rf venv
    fi
    
    python3 -m venv venv
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    log_success "Python virtual environment created"
}

# Install Python packages
install_python_packages() {
    log_info "Installing Python packages..."
    
    source venv/bin/activate
    
    # Install requirements
    log_info "Installing core dependencies..."
    if [[ -f "requirements-minimal.txt" ]]; then
        pip install -r requirements-minimal.txt
    else
        log_error "requirements-minimal.txt not found"
        exit 1
    fi
    
    # Ask user about AI framework
    echo ""
    echo "Choose your AI framework:"
    echo "1. PyTorch + YOLO (Recommended)"
    echo "2. TensorFlow (Alternative)"
    echo "3. Skip AI dependencies (dummy mode only)"
    read -p "Enter choice [1-3] [1]: " ai_choice
    ai_choice=${ai_choice:-1}
    
    case $ai_choice in
        1)
            log_info "Installing PyTorch + YOLO..."
            pip install torch torchvision ultralytics
            ;;
        2)
            log_info "Installing TensorFlow..."
            pip install tensorflow>=2.13.0
            ;;
        3)
            log_warning "Skipping AI dependencies - will use dummy mode"
            ;;
        *)
            log_warning "Invalid choice, skipping AI dependencies"
            ;;
    esac
    
    # Ask about hardware dependencies
    read -p "Install Raspberry Pi hardware dependencies? [y/N]: " hardware_choice
    if [[ "$hardware_choice" =~ ^[Yy]$ ]]; then
        log_info "Installing hardware dependencies..."
        pip install RPi.GPIO picamera2 adafruit-circuitpython-neopixel pyserial imutils
    fi
    
    # Ask about notification dependencies
    read -p "Install notification dependencies (SMS, push)? [y/N]: " notification_choice
    if [[ "$notification_choice" =~ ^[Yy]$ ]]; then
        log_info "Installing notification dependencies..."
        pip install twilio pushbullet.py
    fi
    
    # Install web interface dependencies
    log_info "Installing web interface dependencies..."
    pip install flask flask-cors werkzeug requests python-dotenv
    
    # Install SkyGuard in development mode
    pip install -e .
    
    log_success "Python packages installed"
}

# Configure Raspberry Pi specific settings
configure_raspberry_pi() {
    if [[ "$PLATFORM" == "raspberry_pi" ]]; then
        log_info "Configuring Raspberry Pi specific settings..."
        
        # Enable camera interface
        if ! grep -q "start_x=1" /boot/config.txt; then
            echo "start_x=1" | sudo tee -a /boot/config.txt
        fi
        
        if ! grep -q "gpu_mem=128" /boot/config.txt; then
            echo "gpu_mem=128" | sudo tee -a /boot/config.txt
        fi
        
        # Add user to video group
        sudo usermod -a -G video $USER
        
        # Add user to gpio group
        sudo usermod -a -G gpio $USER
        
        log_success "Raspberry Pi configuration completed"
        log_warning "Reboot required for camera interface changes to take effect"
    fi
}

# Create systemd service
create_systemd_service() {
    log_info "Creating systemd service..."
    
    SERVICE_FILE="/etc/systemd/system/skyguard.service"
    CURRENT_DIR=$(pwd)
    USER_NAME=$(whoami)
    
    sudo tee $SERVICE_FILE > /dev/null <<EOF
[Unit]
Description=SkyGuard Raptor Alert System
After=network.target

[Service]
Type=simple
User=$USER_NAME
WorkingDirectory=$CURRENT_DIR
Environment=PATH=$CURRENT_DIR/venv/bin
ExecStart=$CURRENT_DIR/venv/bin/python -m skyguard.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable skyguard.service
    
    log_success "Systemd service created and enabled"
}

# Test installation
test_installation() {
    log_info "Testing installation..."
    
    source venv/bin/activate
    
    # Test Python imports
    python -c "import skyguard; print('SkyGuard import successful')" || {
        log_error "SkyGuard import failed"
        exit 1
    }
    
    # Test camera (if available)
    python -c "
import cv2
cap = cv2.VideoCapture(0)
if cap.isOpened():
    print('Camera test: OK')
    cap.release()
else:
    print('Camera test: No camera detected')
" || {
        log_warning "Camera test failed - this is normal if no camera is connected"
    }
    
    log_success "Installation test completed"
}

# Start web interface
start_web_interface() {
    log_info "Starting SkyGuard web interface..."
    
    # Get the Pi's IP address
    if [[ "$PLATFORM" == "raspberry_pi" ]]; then
        pi_ip=$(hostname -I | awk '{print $1}')
        echo ""
        echo "🌐 SkyGuard Web Interface"
        echo "=========================="
        echo "Web interface will be available at:"
        echo "   http://$pi_ip:8080"
        echo ""
        echo "Press Ctrl+C to stop the web interface"
        echo ""
    fi
    
    # Start the web portal in the background
    source venv/bin/activate
    python scripts/start_web_portal.py --host 0.0.0.0 --port 8080 &
    web_pid=$!
    
    # Wait a moment for the server to start
    sleep 3
    
    if kill -0 $web_pid 2>/dev/null; then
        log_success "Web interface started successfully!"
        echo "Web interface is running in the background (PID: $web_pid)"
        echo "To stop it later, run: kill $web_pid"
    else
        log_error "Failed to start web interface"
    fi
}

# Main installation function
main() {
    log_info "Starting SkyGuard installation..."
    
    check_root
    detect_platform
    
    # Check if already in SkyGuard directory
    if [[ ! -f "setup.py" ]] || [[ ! -d "skyguard" ]]; then
        log_error "Please run this script from the SkyGuard root directory"
        exit 1
    fi
    
    update_system
    install_dependencies
    setup_python_env
    install_python_packages
    configure_raspberry_pi
    create_systemd_service
    test_installation
    
    log_success "SkyGuard installation completed successfully!"
    
    # Ask if user wants to start web interface
    echo ""
    read -p "Start web interface now? [Y/n]: " web_choice
    web_choice=${web_choice:-Y}
    
    if [[ "$web_choice" =~ ^[Yy]$ ]]; then
        start_web_interface
    fi
    
    echo ""
    echo "Next steps:"
    echo "1. Configure SkyGuard: skyguard-setup"
    echo "2. Test the system: skyguard --test-system"
    echo "3. Start SkyGuard: skyguard"
    echo "4. Start web interface: python scripts/start_web_portal.py"
    echo "5. Enable auto-start: sudo systemctl start skyguard.service"
    echo ""
    
    if [[ "$PLATFORM" == "raspberry_pi" ]]; then
        echo "Note: A reboot is recommended to enable camera interface"
    fi
}

# Run main function
main "$@"
