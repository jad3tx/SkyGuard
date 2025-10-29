# SkyGuard - Open-Source Raptor Alert System

![SkyGuard Logo](skyGuardShield.png)

**Protecting Small Poultry Farms with AI-Powered Raptor Detection**

SkyGuard is an open-source artificial intelligence solution that alerts small flock owners when raptors are circling above their coops. Built for affordability and accessibility, it uses low-cost hardware and modern computer vision to protect your poultry from airborne predators.

## 🎯 Project Overview

**Author:** John Daughtridge  

### The Problem

- 11M Homes in the US keep chickens for food and companionship
- 49% of surveyed chicken owners cite hawks and other airborne predators as their #1 concern
- Rising egg prices and supply concerns drive more families to backyard chicken farming
- Existing deterrent systems are costly and sized for airports or industrial farms
- Small-scale farmers lack affordable protective solutions

### The Solution

SkyGuard provides a low-cost, AI-driven alert system that:
- Uses generic webcams and inexpensive microcontrollers (ESP32/Raspberry Pi)
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
- **Controller**: Raspberry Pi 5 (recommended)
- **Storage**: 32GB+ microSD card
- **Power**: 5V/3A power supply (5V/5A


### Software
- **OS**: Raspberry Pi OS (recommended) or Ubuntu 20.04+
- **Python**: 3.8 or higher
- **RAM**: 4GB minimum (8GB recommended)
- **Storage**: 10GB free space

## 🛠️ Installation

**SkyGuard is optimized for Raspberry Pi 5.**

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/jad3tx/SkyGuard.git
   cd SkyGuard
   ```

2. **Follow the installation guide**
   See **[Raspberry Pi 5 Setup Guide](docs/RASPBERRY_PI_SETUP.md)** for complete step-by-step instructions:
   - OS imaging and initial setup
   - System configuration
   - SkyGuard installation
   - Auto-startup configuration
   - Troubleshooting

### Installation Guide

The [Raspberry Pi 5 Setup Guide](docs/RASPBERRY_PI_SETUP.md) covers:
- ✅ Complete setup from OS imaging to deployment
- ✅ Pi 5 optimizations and performance tuning
- ✅ Auto-startup with systemd services
- ✅ Web portal configuration
- ✅ Comprehensive troubleshooting

For general installation overview, see [INSTALLATION.md](docs/INSTALLATION.md)

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

1. **Configure the system**
   ```bash
   ./skyguard-setup
   ```

2. **Start the detection system**
   ```bash
   ./skyguard-main
   ```

3. **Access the web portal**
   ```bash
   python scripts/start_web_portal.py
   # Open http://<PI_IP>:8080 in your browser
   ```

4. **Monitor detections**
   - View real-time detection feed
   - Check alert notifications
   - Review detection logs
   - Use the web interface for easy management

### Service Management

The installer sets up systemd services for automatic startup:

```bash
# Start services
sudo systemctl start skyguard.service
sudo systemctl start skyguard-web.service

# Check status
sudo systemctl status skyguard.service

# Stop services
sudo systemctl stop skyguard.service
sudo systemctl stop skyguard-web.service

# Enable/disable auto-start
sudo systemctl enable skyguard.service
sudo systemctl disable skyguard.service
```

### Cleanup (if needed)

```bash
# Remove all services for testing
./scripts/cleanup_skyguard.sh
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

- **[Raspberry Pi 5 Setup Guide](docs/RASPBERRY_PI_SETUP.md)** - Complete installation guide (recommended)
- [Installation Overview](docs/INSTALLATION.md)
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
