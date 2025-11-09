# SkyGuard - Open-Source Raptor Alert System

![SkyGuard Logo](skyGuardShield.png)

**Protecting Small Poultry Farms with AI-Powered Raptor Detection**

SkyGuard is an open-source artificial intelligence solution that alerts small flock owners when raptors are circling above their coops. Built for affordability and accessibility, it uses low-cost hardware and modern computer vision to protect your poultry from airborne predators.

## 🎯 Project Overview

**Author:** John Daughtridge  github:jad3tx

### The Problem

- 11M Homes in the US keep chickens for food and companionship
- 49% of surveyed chicken owners cite hawks and other airborne predators as their #1 concern
- Rising egg prices and supply concerns drive more families to backyard chicken farming
- Existing deterrent systems are costly and sized for airports or industrial farms
- Small-scale farmers lack affordable protective solutions

### The Solution

SkyGuard provides a low-cost, AI-driven alert system that:
- Uses generic webcams and inexpensive microcontrollers (Raspberry Pi)
- Runs real-time computer vision models to detect raptors
- Sends immediate alerts via audio, push notifications, or SMS
- Logs detection events for analysis and improvement
- Is completely open-source and self-contained

## 🚀 Features

- **Real-time Detection**: AI-powered computer vision using YOLO models
- **Multiple Alert Types**: Audio, push notifications, SMS, and email alerts
- **Event Logging**: Comprehensive detection history and statistics
- **Web Portal**: Full-featured web interface for system management
- **REST API**: Complete API for integration and automation
- **Comprehensive Testing**: Extensive test suite for reliability
- **Low Cost**: ~$150 per unit using affordable hardware
- **Easy Setup**: Complete documentation and automated configuration
- **Open Source**: Full source code available on GitHub
- **Extensible**: Modular design for future enhancements

## 📋 System Requirements

### Hardware
- **Camera**: USB webcam
- **Controller**: Raspberry Pi 5
- **Storage**: 32GB+ microSD card
- **Power**: 5V/3A power supply (5V/5A recommended)


### Software
- **OS**: Raspberry Pi 64bit OS (recommended) or Ubuntu 20.04+
- **Python**: 3.8 or higher
- **RAM**: 4GB minimum (8GB recommended)
- **Storage**: 10GB free space

## 🛠️ Installation

**SkyGuard is optimized for Raspberry Pi 5.**

### Step 1: Prepare the Raspberry Pi OS

1. **Download and install Raspberry Pi Imager**
   - Download from: https://www.raspberrypi.org/downloads/
   - Install on your computer

2. **Write Raspberry Pi OS to microSD card**
   - Insert your microSD card (32GB+ recommended)
   - Open Raspberry Pi Imager
   - Click "Choose OS" and select:
     - **Raspberry Pi OS (64-bit)** → **Raspberry Pi OS Lite (64-bit)**
   - Click "Choose Storage" and select your microSD card
   - Click the gear icon (⚙️) to configure advanced options:
     - **Enable SSH**: Check this box
     - **Set username**: Enter `pi`
     - **Set password**: Choose a secure password
     - **Configure WiFi**: 
       - Enter your WiFi SSID (network name)
       - Enter your WiFi password
       - Select your country
     - **Set locale settings**: Choose your timezone and keyboard layout
   - Click "Write" to image the card
   - Wait for the write process to complete

3. **Boot your Raspberry Pi**
   - Insert the microSD card into your Raspberry Pi 5
   - Connect power and boot the Pi
   - Wait a few minutes for the Pi to boot and connect to WiFi
   - Find your Pi's IP address (check your router's admin panel or use a network scanner)

### Step 2: Connect to Your Raspberry Pi

1. **SSH into your Pi**
   ```bash
   ssh pi@<PI_IP_ADDRESS>
   ```
   Replace `<PI_IP_ADDRESS>` with your Pi's actual IP address.
   - Default password is the one you set in Raspberry Pi Imager

### Step 3: Install Git and GitHub CLI

1. **Update system packages**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. **Install Git and GitHub CLI**
   ```bash
   sudo apt install git gh -y
   ```

3. **Authenticate with GitHub**
   ```bash
   gh auth login
   ```
   
   Follow the prompts:
   - **What account do you want to log into?** → Select `GitHub.com`
   - **What is your preferred protocol for Git operations?** → Select `HTTPS`
   - **Authenticate Git with your GitHub credentials?** → Select `Yes`
   - **How would you like to authenticate GitHub CLI?** → Select `Login with a web browser`
   - You'll be given a one-time code. Copy it.
   - A URL will be displayed. Open it in a web browser on another device (your computer, phone, etc.)
   - Enter the one-time code when prompted
   - Authorize GitHub CLI to access your account
   
   **Alternative:** If you can't use a web browser, you can use a personal access token:
   - Go to https://github.com/settings/tokens
   - Generate a new token with `repo` permissions
   - When prompted, select `Paste an authentication token` and paste your token

4. **Verify authentication**
   ```bash
   gh auth status
   ```
   
   You should see: `✓ Logged in to github.com as <your-username>`

### Step 4: Clone the Repository

1. **Clone the SkyGuard repository**
   ```bash
   git clone https://github.com/jad3tx/SkyGuard.git
   cd SkyGuard
   ```

### Step 5: Install SkyGuard

1. **Run the installation script**
   ```bash
   cd SkyGuard
   chmod +x scripts/install.sh
   ./scripts/install.sh
   ```

   This script will:
   - Install all system dependencies
   - Create a Python virtual environment
   - Install all Python packages
   - Set up necessary directories
   - Make scripts executable

   **Important:** During the Python package installation, you may be prompted to install:
   - **Raspberry Pi hardware dependencies** (such as RPi.GPIO) - **Answer "yes" or "y"** to enable GPIO features for LED indicators and buzzers
   - **Notification dependencies** (such as Twilio or Pushbullet) - **Answer "yes" or "y"** to enable SMS and push notification features

   **Note:** The installation may take 15-30 minutes depending on your internet connection and Pi model.

2. **Configure SkyGuard Services** 
   ```bash
   source venv/bin/activate
   python -m skyguard.setup.configure
   ```

### Step 6: Start SkyGuard

1. **Start the system**
   ```bash
   ./scripts/start_skyguard.sh
   ```

   This will start both the detection system and web portal.

2. **Access the web portal**
   - Open your web browser
   - Navigate to: `http://<PI_IP_ADDRESS>:8080`
   - You should see the SkyGuard dashboard

### Managing SkyGuard

**Start SkyGuard:**
```bash
./scripts/start_skyguard.sh
```

**Stop SkyGuard:**
```bash
./scripts/stop_skyguard.sh
```

**Start only the detection system:**
```bash
./scripts/start_skyguard.sh --main-only
```

**Start only the web portal:**
```bash
./scripts/start_skyguard.sh --web-only
```

**Stop only the detection system:**
```bash
./scripts/stop_skyguard.sh --main-only
```

**Stop only the web portal:**
```bash
./scripts/stop_skyguard.sh --web-only
```

## 🔧 Troubleshooting

### Camera Not Working

If you see "ERROR - Failed to open camera source: 0", try these steps:

1. **Check if camera is connected (USB webcam):**
   ```bash
   lsusb | grep -i camera
   ls /dev/video*
   ```

2. **Check camera permissions:**
   ```bash
   # Add user to video group
   sudo usermod -a -G video pi
   
   # Log out and log back in, or reboot
   sudo reboot
   ```

3. **Test camera manually:**
   ```bash
   source venv/bin/activate
   python -c "import cv2; cap = cv2.VideoCapture(0); print('OK' if cap.isOpened() else 'Failed'); cap.release()"
   ```

4. **For Raspberry Pi Camera Module:**
   ```bash
   # Enable camera interface
   sudo raspi-config
   # Navigate to: Interface Options → Camera → Enable
   # Reboot after enabling
   sudo reboot
   
   # Test Pi camera
   libcamera-hello --list-cameras
   ```

5. **Try different camera sources:**
   - Edit `config/skyguard.yaml` and change `camera.source` to try 0, 1, or 2
   - The system will automatically try multiple sources if source 0 fails

6. **Check logs for detailed error messages:**
   ```bash
   tail -f logs/skyguard.log
   ```

## ⚙️ Configuration

SkyGuard is configured through the `config/skyguard.yaml` file. Key settings include:

- **Camera settings**: Resolution, FPS, rotation
- **AI model parameters**: Confidence thresholds, detection classes
- **Notification preferences**: Audio, SMS, email, push notifications
- **Storage options**: Database location, image retention
- **Hardware configuration**: GPIO pins, platform-specific settings

See [CONFIGURATION.md](docs/CONFIGURATION.md) for detailed configuration options.

## 🎮 Usage

### Basic Operation

Once SkyGuard is installed and running:

1. **Access the web portal**
   - Open your web browser
   - Navigate to: `http://<PI_IP_ADDRESS>:8080`
   - You'll see the SkyGuard dashboard with:
     - Real-time system status
     - Detection history
     - System configuration
     - Camera feed

2. **Monitor detections**
   - View real-time detection feed
   - Check alert notifications
   - Review detection logs
   - Use the web interface for easy management

3. **Configure the system**
   - Use the web interface to adjust settings
   - Or edit `config/skyguard.yaml` directly
   - Restart SkyGuard after making changes:
     ```bash
     ./scripts/stop_skyguard.sh
     ./scripts/start_skyguard.sh
     ```


### Web Portal Features

- **Dashboard**: Real-time system status and statistics
- **Detection Management**: Browse and export detection history
- **Configuration**: Easy system configuration through web interface
- **System Monitoring**: Test camera, AI model, and alert systems
- **API Access**: REST API for integration and automation

### Advanced Features

- **Custom model training**: See [TRAINING.md](docs/TRAINING.md)
- **Multi-camera setup**: Configure multiple detection zones
- **Remote monitoring**: Web interface for remote system management
- **Data export**: Export detection data for analysis
- **API integration**: Use REST API for custom applications

## 📊 Performance Metrics

SkyGuard is designed to achieve:
- **>80% detection accuracy** for common raptor species
- **<2 second response time** from detection to alert
- **24/7 operation** with minimal maintenance
- **Low power consumption** for continuous operation

## 🔧 Development

### Project Structure

```
skyguard/
├── core/           # Core system components
├── ai/             # AI model training and inference
├── hardware/       # Hardware interface modules
├── notifications/  # Alert system components
├── storage/        # Data storage and logging
├── utils/          # Utility functions
├── tests/          # Test suite
├── docs/           # Documentation
└── scripts/        # Setup and utility scripts
```

### Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

1. **Install development dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -e .[dev]
   ```

2. **Run tests**
   ```bash
   # Run all tests
   pytest tests/ -v
   
   # Run specific test suites
   pytest tests/test_web_api.py -v      # API tests
   pytest tests/test_web_ui.py -v      # UI tests
   pytest tests/test_camera_connection.py -v  # Camera tests
   pytest tests/test_core.py -v        # Core component tests
   ```

3. **Code formatting**
   ```bash
   black skyguard/
   flake8 skyguard/
   ```

## 📈 Roadmap

### Phase 1 (Current)
- [x] Core detection system
- [x] Basic alert functionality
- [x] Event logging
- [x] Configuration management
- [x] Web interface
- [x] Comprehensive testing suite

### Phase 2 (Q1 2026)
- [ ] Model training pipeline
- [ ] Mobile app
- [ ] Multi-camera support
- [ ] Advanced analytics

## 📚 Documentation

- [API Documentation](docs/API.md)
- [Web Portal Guide](docs/WEB_PORTAL.md)
- [Hardware Guide](docs/HARDWARE.md)

## 🤝 Support

- **Issues**: [GitHub Issues](https://github.com/jad3tx/SkyGuard/issues)
- **Discussions**: [GitHub Discussions](https://github.com/jad3tx/SkyGuard/discussions)
- **Email**: johnd@tamu.edu

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Texas A&M University** for academic support
- **Professor Rustom Mody** for project guidance
- **Sarah Collins** for sponsorship and real-world testing
- **Open source community** for the amazing tools and libraries
- **Small farm owners** who provided valuable feedback and requirements

## 📊 Project Status

**Current Status**: Development Phase  
**Target Completion**: March 2026  
**Pilot Testing**: January-February 2026  

---

*Protecting poultry, one detection at a time.* 🦅🐔
