#!/usr/bin/env python3
"""
Simple Raspberry Pi Deployment Script

Creates a deployment package for Raspberry Pi without emoji characters.
"""

import os
import sys
import shutil
from pathlib import Path

def create_simple_pi_package():
    """Create a simple deployment package for Raspberry Pi."""
    print("Creating Raspberry Pi deployment package...")
    
    # Create deployment directory
    deploy_dir = Path("deployment/raspberry_pi")
    deploy_dir.mkdir(parents=True, exist_ok=True)
    
    # Files to include
    files_to_copy = [
        "skyguard/",
        "config/",
        "models/",
        "requirements-minimal.txt",
        "requirements-hardware.txt",
        "setup.py",
        "README.md",
    ]
    
    print("Copying files...")
    for item in files_to_copy:
        src = Path(item)
        dst = deploy_dir / item
        
        if src.is_file():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            print(f"  Copied {item}")
        elif src.is_dir():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            print(f"  Copied {item}/")
    
    # Create simple install script
    install_script = deploy_dir / "install.sh"
    with open(install_script, 'w') as f:
        f.write("""#!/bin/bash
# SkyGuard Raspberry Pi Installation

set -e

echo "SkyGuard Raspberry Pi Installation"
echo "=================================="

# Update system
echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install system dependencies
echo "Installing system dependencies..."
sudo apt install -y python3 python3-pip python3-venv python3-dev python3-opencv libopencv-dev git

# Enable camera interface
echo "Enabling camera interface..."
sudo raspi-config nonint do_camera 0

# Create virtual environment
echo "Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install requirements
echo "Installing Python packages..."
pip install -r requirements-minimal.txt
pip install -r requirements-hardware.txt

# Install SkyGuard
echo "Installing SkyGuard..."
pip install -e .

echo "Installation complete!"
echo ""
echo "Next steps:"
echo "1. Configure: ./venv/bin/python -m skyguard.setup.configure"
echo "2. Test: ./venv/bin/python -m skyguard.main --test-system"
echo "3. Run: ./venv/bin/python -m skyguard.main"
""")
    
    # Make script executable
    os.chmod(install_script, 0o755)
    
    print(f"Deployment package created at {deploy_dir}")
    return deploy_dir

def main():
    """Main function."""
    print("SkyGuard Raspberry Pi Deployment")
    print("=" * 40)
    
    deploy_dir = create_simple_pi_package()
    
    print("\nDeployment package created successfully!")
    print(f"Location: {deploy_dir.absolute()}")
    print("\nTo deploy to Raspberry Pi:")
    print("1. Copy the deployment folder to your Pi")
    print("2. Run: chmod +x install.sh && ./install.sh")
    print("3. Configure: ./venv/bin/python -m skyguard.setup.configure")
    print("4. Run: ./venv/bin/python -m skyguard.main")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
