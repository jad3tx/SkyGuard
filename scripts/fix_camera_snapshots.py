#!/usr/bin/env python3
"""
Fix camera snapshot issues on Raspberry Pi.
This script automatically resolves common camera snapshot problems.
"""

import os
import sys
import time
import cv2
import numpy as np
import subprocess
from pathlib import Path
from typing import Dict, Any

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def ensure_data_directory() -> bool:
    """Ensure data directory exists."""
    print("📁 Ensuring data directory exists...")
    
    try:
        os.makedirs("data", exist_ok=True)
        print("✅ Data directory ready")
        return True
    except Exception as e:
        print(f"❌ Failed to create data directory: {e}")
        return False


def create_test_snapshot() -> bool:
    """Create a test snapshot."""
    print("📸 Creating test snapshot...")
    
    try:
        # Create a test image
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Add gradient background
        for y in range(480):
            for x in range(640):
                img[y, x] = [int(255 * y / 480), int(255 * x / 640), 100]
        
        # Add text
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(img, 'SkyGuard Camera Feed', (50, 100), font, 1, (255, 255, 255), 2)
        cv2.putText(img, 'Test Image - Camera Not Available', (50, 150), font, 0.7, (200, 200, 200), 2)
        cv2.putText(img, f'Created: {time.strftime("%Y-%m-%d %H:%M:%S")}', (50, 200), font, 0.5, (150, 150, 150), 1)
        
        # Add some visual elements
        cv2.rectangle(img, (100, 250), (540, 350), (0, 255, 0), 2)
        cv2.circle(img, (320, 300), 50, (255, 0, 0), 2)
        
        # Add a simple pattern
        for i in range(0, 640, 50):
            cv2.line(img, (i, 250), (i, 350), (100, 100, 100), 1)
        
        # Save the test image
        cv2.imwrite("data/camera_snapshot.jpg", img)
        print("✅ Test snapshot created")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create test snapshot: {e}")
        return False


def restart_services() -> bool:
    """Restart SkyGuard services."""
    print("🔄 Restarting SkyGuard services...")
    
    try:
        # Stop services
        print("   Stopping services...")
        subprocess.run(["./scripts/stop_skyguard.sh"], check=True, capture_output=True)
        
        # Wait a moment
        time.sleep(2)
        
        # Start services
        print("   Starting services...")
        subprocess.run(["./scripts/start_skyguard.sh", "--background"], check=True, capture_output=True)
        
        print("✅ Services restarted")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to restart services: {e}")
        return False
    except Exception as e:
        print(f"❌ Error restarting services: {e}")
        return False


def check_camera_permissions() -> bool:
    """Check camera permissions."""
    print("📷 Checking camera permissions...")
    
    try:
        # Test camera access
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            print("✅ Camera accessible")
            cap.release()
            return True
        else:
            print("❌ Camera not accessible")
            return False
            
    except Exception as e:
        print(f"❌ Camera permission check failed: {e}")
        return False


def fix_file_permissions() -> bool:
    """Fix file permissions for data directory."""
    print("🔧 Fixing file permissions...")
    
    try:
        # Set permissions on data directory
        os.chmod("data", 0o755)
        
        # If snapshot file exists, set its permissions
        snapshot_file = Path("data/camera_snapshot.jpg")
        if snapshot_file.exists():
            os.chmod(str(snapshot_file), 0o644)
        
        print("✅ File permissions fixed")
        return True
        
    except Exception as e:
        print(f"❌ Failed to fix permissions: {e}")
        return False


def test_web_endpoints() -> bool:
    """Test web endpoints."""
    print("🌐 Testing web endpoints...")
    
    try:
        import requests
        
        # Test camera status
        response = requests.get("http://localhost:8080/api/camera/status", timeout=5)
        if response.status_code == 200:
            print("✅ Camera status endpoint working")
        else:
            print(f"❌ Camera status endpoint failed: {response.status_code}")
            return False
        
        # Test camera feed
        response = requests.get("http://localhost:8080/api/camera/feed", timeout=5)
        if response.status_code == 200:
            print(f"✅ Camera feed endpoint working: {len(response.content)} bytes")
            return True
        else:
            print(f"❌ Camera feed endpoint failed: {response.status_code}")
            return False
            
    except ImportError:
        print("❌ requests library not available")
        return False
    except Exception as e:
        print(f"❌ Web endpoint test failed: {e}")
        return False


def main():
    """Main fix function."""
    print("🛠️ Camera Snapshot Fix Tool")
    print("=" * 30)
    print()
    
    # Run all fixes
    fixes = [
        ("Ensure data directory", ensure_data_directory),
        ("Create test snapshot", create_test_snapshot),
        ("Fix file permissions", fix_file_permissions),
        ("Check camera permissions", check_camera_permissions),
    ]
    
    results = {}
    for name, fix_func in fixes:
        print(f"\n🔧 {name}...")
        results[name] = fix_func()
    
    # Test web endpoints
    print(f"\n🌐 Testing web endpoints...")
    web_ok = test_web_endpoints()
    results["Web endpoints"] = web_ok
    
    # Summary
    print("\n📊 Fix Summary")
    print("=" * 15)
    
    all_fixed = True
    for name, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {name}")
        if not success:
            all_fixed = False
    
    if all_fixed:
        print("\n✅ All fixes applied successfully!")
        print("\n🌐 Try accessing the web portal now:")
        print("   http://<PI_IP_ADDRESS>:8080")
    else:
        print("\n⚠️ Some fixes failed - you may need to:")
        print("   1. Restart services: ./scripts/restart_skyguard.sh")
        print("   2. Check logs: tail -f logs/skyguard.log")
        print("   3. Run diagnostic: python scripts/diagnose_camera_snapshots.py")
    
    return all_fixed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
