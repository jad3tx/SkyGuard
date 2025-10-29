# SkyGuard Deployment Scripts

**⚠️ Important: SkyGuard installation scripts have been consolidated.**

## Recommended Installation Script

Use the main installation script from the SkyGuard root directory:

```bash
cd SkyGuard
./scripts/install.sh
```

This script automatically detects Raspberry Pi 5 and applies all necessary optimizations.

See [Raspberry Pi 5 Setup Guide](../docs/RASPBERRY_PI_SETUP.md) for complete installation instructions.

## Script Status

### ✅ Active Scripts

- **`scripts/install.sh`** - Main installation script (recommended)
  - Automatically detects Raspberry Pi platform
  - Applies Pi 5 optimizations when detected
  - Handles all dependencies and setup

- **`deployment/install_pi5_unified.sh`** - Unified Pi 5 installer (alternative)
  - More comprehensive installation option
  - Uses main codebase with systemd services
  - Can be used if you need more control

- **`deployment/scripts/skyguard-control.sh`** - Service management script
  - Start/stop/restart services
  - Check status
  - View logs

- **`deployment/scripts/health_check.sh`** - Health monitoring script
  - Check system health
  - Monitor services
  - Auto-recovery

### ⚠️ Removed Scripts

The following deprecated scripts have been removed:

- `deployment/raspberry_pi5/install_pi5.sh` - Removed (use main installer)
- `deployment/raspberry_pi/install.sh` - Removed (Pi 5 only supported)
- `deployment/raspberry_pi/install_on_pi.sh` - Removed (Pi 5 only supported)
- `deployment/raspberry_pi5/scripts/install.sh` - Removed (use main installer)
- `deployment/raspberry_pi/scripts/install.sh` - Removed (use main installer)

## Installation Instructions

For complete installation instructions, see:

- **[Raspberry Pi 5 Setup Guide](../docs/RASPBERRY_PI_SETUP.md)** - Complete step-by-step guide

## Service Management

After installation, use the control scripts:

```bash
# Start services
./deployment/scripts/skyguard-control.sh start

# Check status
./deployment/scripts/skyguard-control.sh status

# View logs
./deployment/scripts/skyguard-control.sh logs

# Health check
./deployment/scripts/health_check.sh
```

## Directory Structure

```
deployment/
├── install_pi5_unified.sh    # Unified installer (alternative)
├── scripts/                    # Service management scripts
│   ├── skyguard-control.sh   # Service control
│   └── health_check.sh       # Health monitoring
├── systemd/                   # Systemd service files
│   ├── skyguard.service      # Main detection service
│   └── skyguard-web.service  # Web portal service
├── raspberry_pi5/            # Pi 5 specific files (config, models)
└── raspberry_pi/              # Older Pi files (config, models - legacy)
```

