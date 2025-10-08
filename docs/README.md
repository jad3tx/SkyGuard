# SkyGuard Documentation

![SkyGuard Logo](../skyGuardShield.png)

Welcome to the comprehensive documentation for SkyGuard, the open-source raptor alert system that protects small poultry farms with AI-powered detection.

## 📚 Documentation Overview

This documentation provides everything you need to understand, install, configure, and use SkyGuard effectively.

### 🚀 Getting Started

- **[Installation Guide](INSTALLATION.md)** - Complete setup instructions for all platforms
- **[Hardware Guide](HARDWARE.md)** - Hardware requirements and recommendations
- **[Web Portal Guide](WEB_PORTAL.md)** - Web interface management and monitoring

### 🔧 Configuration & Integration

- **[API Documentation](API.md)** - REST API reference for integration
- **[Model Integration Guide](MODEL_INTEGRATION.md)** - AI model setup and training
- **[Testing Guide](TESTING.md)** - Comprehensive testing suite

## 🎯 Quick Start

1. **Install SkyGuard**: Follow the [Installation Guide](INSTALLATION.md)
2. **Configure Hardware**: Check the [Hardware Guide](HARDWARE.md)
3. **Set Up AI Models**: Use the [Model Integration Guide](MODEL_INTEGRATION.md)
4. **Access Web Portal**: See the [Web Portal Guide](WEB_PORTAL.md)
5. **Test Your System**: Follow the [Testing Guide](TESTING.md)

## 🌟 Key Features

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
- **Camera**: USB webcam or Raspberry Pi camera module
- **Controller**: Raspberry Pi 5 (recommended)
- **Storage**: 32GB+ microSD card
- **Power**: 5V/3A power supply

### Software
- **OS**: Raspberry Pi OS (recommended) or Ubuntu 20.04+
- **Python**: 3.8 or higher
- **RAM**: 4GB minimum (8GB recommended)
- **Storage**: 10GB free space

## 🛠️ Installation

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/johndaughtridge/skyguard.git
   cd skyguard
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the system**
   ```bash
   python -m skyguard.setup.configure
   ```

4. **Run SkyGuard**
   ```bash
   python -m skyguard.main
   ```

### Detailed Installation

See [INSTALLATION.md](INSTALLATION.md) for detailed setup instructions including:
- Hardware assembly
- Software installation
- Configuration options
- Troubleshooting

## ⚙️ Configuration

SkyGuard is configured through the `config/skyguard.yaml` file. Key settings include:

- **Camera settings**: Resolution, FPS, rotation
- **AI model parameters**: Confidence thresholds, detection classes
- **Notification preferences**: Audio, SMS, email, push notifications
- **Storage options**: Database location, image retention
- **Hardware configuration**: GPIO pins, platform-specific settings

## 🎮 Usage

### Basic Operation

1. **Start the system**
   ```bash
   python -m skyguard.main
   ```

2. **Access the web portal**
   ```bash
   python scripts/start_web_portal.py
   # Open http://localhost:8080 in your browser
   ```

3. **Monitor detections**
   - View real-time detection feed
   - Check alert notifications
   - Review detection logs
   - Use the web interface for easy management

4. **Test alerts**
   ```bash
   python -m skyguard.main --test-alerts
   ```

### Web Portal Features

- **Dashboard**: Real-time system status and statistics
- **Detection Management**: Browse and export detection history
- **Configuration**: Easy system configuration through web interface
- **System Monitoring**: Test camera, AI model, and alert systems
- **API Access**: REST API for integration and automation

## 📊 Performance Metrics

SkyGuard is designed to achieve:
- **>80% detection accuracy** for common raptor species
- **<1 second response time** from detection to alert
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

We welcome contributions! Please see [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

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
- [x] REST API
- [x] Comprehensive testing suite

### Phase 2 (Maybe...ish?)
- [ ] Model training pipeline
- [ ] Mobile app
- [ ] Multi-camera support
- [ ] Advanced analytics

### Phase 3 (Future...maybe)
- [ ] Weather integration
- [ ] Machine learning improvements
- [ ] Commercial deployment tools

## 🤝 Support

- **Issues**: [GitHub Issues](https://github.com/johndaughtridge/skyguard/issues)
- **Discussions**: [GitHub Discussions](https://github.com/johndaughtridge/skyguard/discussions)
- **Email**: johnd@tamu.edu

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

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
