#!/usr/bin/env python3
"""
Diagnose camera snapshot issues on Raspberry Pi.
This script helps identify why the camera doesn't show in the web portal.
"""

import os
import sys
import time
import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from skyguard.core.camera import CameraManager
from skyguard.core.camera_snapshot import CameraSnapshotService
from skyguard.core.config_manager import ConfigManager


def check_system_status() -> Dict[str, Any]:
    """Check overall system status."""
    print("🔍 System Status Check")
    print("=" * 25)
    
    status = {
        'data_dir_exists': False,
        'snapshot_file_exists': False,
        'snapshot_file_recent': False,
        'snapshot_file_size': 0,
        'main_process_running': False,
        'web_process_running': False
    }
    
    # Check data directory
    data_dir = Path("data")
    status['data_dir_exists'] = data_dir.exists()
    print(f"📁 Data directory exists: {'✅' if status['data_dir_exists'] else '❌'}")
    
    # Check snapshot file
    snapshot_file = Path("data/camera_snapshot.jpg")
    status['snapshot_file_exists'] = snapshot_file.exists()
    print(f"📸 Snapshot file exists: {'✅' if status['snapshot_file_exists'] else '❌'}")
    
    if status['snapshot_file_exists']:
        # Check file size
        status['snapshot_file_size'] = snapshot_file.stat().st_size
        print(f"📏 Snapshot file size: {status['snapshot_file_size']} bytes")
        
        # Check if file is recent (within last 10 seconds)
        file_time = snapshot_file.stat().st_mtime
        current_time = time.time()
        age_seconds = current_time - file_time
        status['snapshot_file_recent'] = age_seconds < 10
        print(f"⏰ Snapshot age: {age_seconds:.1f} seconds {'✅' if status['snapshot_file_recent'] else '❌'}")
    
    # Check if main process is running
    import psutil
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        cmdline = ' '.join(proc.info['cmdline'] or [])
        if 'skyguard.main' in cmdline:
            status['main_process_running'] = True
            break
    
    print(f"🔄 Main process running: {'✅' if status['main_process_running'] else '❌'}")
    
    # Check if web process is running
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        cmdline = ' '.join(proc.info['cmdline'] or [])
        if 'start_web_portal.py' in cmdline:
            status['web_process_running'] = True
            break
    
    print(f"🌐 Web process running: {'✅' if status['web_process_running'] else '❌'}")
    
    return status


def test_camera_connection() -> bool:
    """Test camera connection."""
    print("\n📷 Camera Connection Test")
    print("=" * 25)
    
    try:
        # Try to initialize camera
        config_manager = ConfigManager("config/skyguard.yaml")
        camera_manager = CameraManager(config_manager.config)
        
        if camera_manager.initialize():
            print("✅ Camera initialized successfully")
            
            # Try to capture a frame
            frame = camera_manager.capture_frame()
            if frame is not None:
                print(f"✅ Frame captured: {frame.shape}")
                camera_manager.cleanup()
                return True
            else:
                print("❌ Failed to capture frame")
                camera_manager.cleanup()
                return False
        else:
            print("❌ Failed to initialize camera")
            return False
            
    except Exception as e:
        print(f"❌ Camera test failed: {e}")
        return False


def test_snapshot_service() -> bool:
    """Test snapshot service."""
    print("\n📸 Snapshot Service Test")
    print("=" * 25)
    
    try:
        # Create snapshot service
        snapshot_service = CameraSnapshotService()
        
        # Test creating a test snapshot
        snapshot_service._create_test_snapshot()
        
        # Check if snapshot was created
        snapshot_file = Path("data/camera_snapshot.jpg")
        if snapshot_file.exists():
            print("✅ Test snapshot created successfully")
            
            # Check if it's a valid image
            img = cv2.imread(str(snapshot_file))
            if img is not None:
                print(f"✅ Snapshot is valid image: {img.shape}")
                return True
            else:
                print("❌ Snapshot is not a valid image")
                return False
        else:
            print("❌ Test snapshot not created")
            return False
            
    except Exception as e:
        print(f"❌ Snapshot service test failed: {e}")
        return False


def test_web_api_endpoints() -> bool:
    """Test web API endpoints."""
    print("\n🌐 Web API Test")
    print("=" * 15)
    
    try:
        import requests
        
        # Test camera status endpoint
        try:
            response = requests.get("http://localhost:8080/api/camera/status", timeout=5)
            if response.status_code == 200:
                status_data = response.json()
                print(f"✅ Camera status API: {status_data}")
            else:
                print(f"❌ Camera status API failed: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print("❌ Web portal not running on localhost:8080")
            return False
        except Exception as e:
            print(f"❌ Camera status API error: {e}")
            return False
        
        # Test camera feed endpoint
        try:
            response = requests.get("http://localhost:8080/api/camera/feed", timeout=5)
            if response.status_code == 200:
                print(f"✅ Camera feed API: {len(response.content)} bytes")
                return True
            else:
                print(f"❌ Camera feed API failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Camera feed API error: {e}")
            return False
            
    except ImportError:
        print("❌ requests library not available")
        return False


def create_test_snapshot() -> bool:
    """Create a test snapshot for testing."""
    print("\n🛠️ Creating Test Snapshot")
    print("=" * 25)
    
    try:
        # Ensure data directory exists
        os.makedirs("data", exist_ok=True)
        
        # Create a test image
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Add gradient background
        for y in range(480):
            for x in range(640):
                img[y, x] = [int(255 * y / 480), int(255 * x / 640), 100]
        
        # Add text
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(img, 'SkyGuard Test Image', (50, 100), font, 1, (255, 255, 255), 2)
        cv2.putText(img, 'Camera Snapshot Test', (50, 150), font, 0.7, (200, 200, 200), 2)
        cv2.putText(img, f'Created: {time.strftime("%Y-%m-%d %H:%M:%S")}', (50, 200), font, 0.5, (150, 150, 150), 1)
        
        # Add some visual elements
        cv2.rectangle(img, (100, 250), (540, 350), (0, 255, 0), 2)
        cv2.circle(img, (320, 300), 50, (255, 0, 0), 2)
        
        # Save the test image
        cv2.imwrite("data/camera_snapshot.jpg", img)
        print("✅ Test snapshot created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create test snapshot: {e}")
        return False


def suggest_solutions(status: Dict[str, Any]) -> None:
    """Suggest solutions based on the diagnosis."""
    print("\n💡 Suggested Solutions")
    print("=" * 20)
    
    if not status['main_process_running']:
        print("1. Start the main SkyGuard process:")
        print("   ./scripts/start_skyguard.sh")
        print("   # or")
        print("   sudo systemctl start skyguard.service")
    
    if not status['web_process_running']:
        print("2. Start the web portal:")
        print("   ./scripts/start_skyguard.sh --web-only")
        print("   # or")
        print("   sudo systemctl start skyguard-web.service")
    
    if not status['snapshot_file_exists']:
        print("3. Create test snapshot:")
        print("   python scripts/diagnose_camera_snapshots.py --create-test")
    
    if status['snapshot_file_exists'] and not status['snapshot_file_recent']:
        print("4. Snapshot file is old - restart services:")
        print("   ./scripts/stop_skyguard.sh")
        print("   ./scripts/start_skyguard.sh")
    
    print("\n5. Check logs for errors:")
    print("   tail -f logs/skyguard.log")
    print("   tail -f logs/web.log")
    
    print("\n6. Test camera manually:")
    print("   python -c \"import cv2; cap = cv2.VideoCapture(0); print('OK' if cap.isOpened() else 'Failed')\"")


def main():
    """Main diagnostic function."""
    print("🔧 Camera Snapshot Diagnostic")
    print("=" * 30)
    print()
    
    # Check if we should create a test snapshot
    if len(sys.argv) > 1 and sys.argv[1] == "--create-test":
        create_test_snapshot()
        return True
    
    # Run all diagnostic checks
    status = check_system_status()
    camera_ok = test_camera_connection()
    snapshot_ok = test_snapshot_service()
    web_ok = test_web_api_endpoints()
    
    # Summary
    print("\n📊 Diagnostic Summary")
    print("=" * 20)
    print(f"System status: {'✅' if all([status['data_dir_exists'], status['snapshot_file_exists']]) else '❌'}")
    print(f"Camera connection: {'✅' if camera_ok else '❌'}")
    print(f"Snapshot service: {'✅' if snapshot_ok else '❌'}")
    print(f"Web API: {'✅' if web_ok else '❌'}")
    
    # Suggest solutions
    suggest_solutions(status)
    
    # Overall result
    overall_ok = all([status['data_dir_exists'], status['snapshot_file_exists'], 
                     status['snapshot_file_recent'], camera_ok, snapshot_ok, web_ok])
    
    if overall_ok:
        print("\n✅ All systems working correctly!")
    else:
        print("\n❌ Issues detected - see suggestions above")
    
    return overall_ok


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
