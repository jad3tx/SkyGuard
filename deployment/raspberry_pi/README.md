# SkyGuard - Open-Source Raptor Alert System

![SkyGuard Logo](docs/images/skyguard_logo.png)

**Protecting Small Poultry Farms with AI-Powered Raptor Detection**

SkyGuard is an open-source artificial intelligence solution that alerts small flock owners when raptors are circling above their coops. Built for affordability and accessibility, it uses low-cost hardware and modern computer vision to protect your poultry from airborne predators.

## 🎯 Project Overview

**Author:** John Daughtridge  

### The Problem

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
   git clone https://github.com/jad3tx/SkyGuard.git
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

See [INSTALLATION.md](docs/INSTALLATION.md) for detailed setup instructions including:
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

See [CONFIGURATION.md](docs/CONFIGURATION.md) for detailed configuration options.

## 🎮 Usage

### Basic Operation

1. **Start the system**
   ```bash
   python -m skyguard.main
   ```

2. **Monitor detections**
   - View real-time detection feed
   - Check alert notifications
   - Review detection logs

3. **Test alerts**
   ```bash
   python -m skyguard.main --test-alerts
   ```

### Advanced Features

- **Custom model training**: See [TRAINING.md](docs/TRAINING.md)
- **Multi-camera setup**: Configure multiple detection zones
- **Remote monitoring**: Web interface for remote system management
- **Data export**: Export detection data for analysis

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

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

1. **Install development dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -e .[dev]
   ```

2. **Run tests**
   ```bash
   pytest tests/
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

### Phase 2 (Q1 2026)
- [ ] Model training pipeline
- [ ] Web interface
- [ ] Mobile app
- [ ] Multi-camera support

### Phase 3 (Q2 2026)
- [ ] Automated deterrents
- [ ] Weather integration
- [ ] Machine learning improvements
- [ ] Commercial deployment tools

## 📚 Documentation

- [Installation Guide](docs/INSTALLATION.md)
- [Configuration Reference](docs/CONFIGURATION.md)
- [Model Training](docs/TRAINING.md)
- [API Documentation](docs/API.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
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