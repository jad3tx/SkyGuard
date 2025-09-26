#!/usr/bin/env python3
"""
Transfer SkyGuard to Raspberry Pi

This script helps transfer SkyGuard files to a Raspberry Pi.
"""

import os
import sys
import subprocess
from pathlib import Path

def transfer_to_pi(pi_ip, pi_user="pi", pi_path="~/skyguard"):
    """Transfer SkyGuard to Raspberry Pi."""
    print(f"🍓 Transferring SkyGuard to Raspberry Pi at {pi_ip}")
    
    # Create deployment package first
    print("📦 Creating deployment package...")
    result = subprocess.run([sys.executable, "scripts/deploy_to_pi.py"], 
                          capture_output=True, text=True)
    if result.returncode != 0:
        print(f"❌ Failed to create deployment package: {result.stderr}")
        return False
    
    # Transfer files
    print("📤 Transferring files...")
    deploy_dir = Path("deployment/raspberry_pi")
    
    # Create transfer command
    transfer_cmd = [
        "scp", "-r", 
        str(deploy_dir) + "/*",
        f"{pi_user}@{pi_ip}:{pi_path}/"
    ]
    
    print(f"Running: {' '.join(transfer_cmd)}")
    result = subprocess.run(transfer_cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Transfer failed: {result.stderr}")
        return False
    
    print("✅ Transfer completed!")
    
    # Create remote installation command
    install_cmd = f"""
    ssh {pi_user}@{pi_ip} << 'EOF'
    cd {pi_path}
    chmod +x install_on_pi.sh
    ./install_on_pi.sh
    EOF
    """
    
    print("\n🚀 To complete installation on Raspberry Pi, run:")
    print(f"ssh {pi_user}@{pi_ip}")
    print(f"cd {pi_path}")
    print("chmod +x install_on_pi.sh")
    print("./install_on_pi.sh")
    
    return True

def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/transfer_to_pi.py <PI_IP_ADDRESS> [USER] [PATH]")
        print("Example: python scripts/transfer_to_pi.py 192.168.1.100")
        print("Example: python scripts/transfer_to_pi.py 192.168.1.100 pi ~/skyguard")
        return False
    
    pi_ip = sys.argv[1]
    pi_user = sys.argv[2] if len(sys.argv) > 2 else "pi"
    pi_path = sys.argv[3] if len(sys.argv) > 3 else "~/skyguard"
    
    return transfer_to_pi(pi_ip, pi_user, pi_path)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
