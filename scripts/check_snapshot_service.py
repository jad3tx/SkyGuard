#!/usr/bin/env python3
"""
Check SkyGuard Snapshot Service Status
This script helps you verify if the camera snapshot service is running properly.
"""

import os
import sys
import time
import psutil
from pathlib import Path
from typing import Dict, Any, Optional

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def check_main_process() -> bool:
    """Check if the main SkyGuard process is running."""
    print("🔍 Checking main SkyGuard process...")
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        cmdline = ' '.join(proc.info['cmdline'] or [])
        if 'skyguard.main' in cmdline:
            print(f"✅ Main process running (PID: {proc.info['pid']})")
            return True
    
    print("❌ Main process not running")
    return False


def check_snapshot_file() -> Dict[str, Any]:
    """Check the snapshot file status."""
    print("\n📸 Checking snapshot file...")
    
    snapshot_path = Path("data/camera_snapshot.jpg")
    status = {
        'exists': False,
        'recent': False,
        'size': 0,
        'age_seconds': 0
    }
    
    if snapshot_path.exists():
        status['exists'] = True
        status['size'] = snapshot_path.stat().st_size
        
        # Check file age
        file_time = snapshot_path.stat().st_mtime
        current_time = time.time()
        age_seconds = current_time - file_time
        status['age_seconds'] = age_seconds
        status['recent'] = age_seconds < 10  # Recent if less than 10 seconds old
        
        print(f"✅ Snapshot file exists")
        print(f"   Size: {status['size']} bytes")
        print(f"   Age: {age_seconds:.1f} seconds")
        print(f"   Recent: {'✅' if status['recent'] else '❌'}")
    else:
        print("❌ Snapshot file not found")
    
    return status


def check_systemd_services() -> Dict[str, bool]:
    """Check systemd service status."""
    print("\n🔧 Checking systemd services...")
    
    services = {
        'skyguard': False,
        'skyguard-web': False
    }
    
    try:
        # Check skyguard service
        result = os.system("systemctl is-active skyguard.service >/dev/null 2>&1")
        services['skyguard'] = (result == 0)
        print(f"skyguard.service: {'✅ Active' if services['skyguard'] else '❌ Inactive'}")
        
        # Check skyguard-web service
        result = os.system("systemctl is-active skyguard-web.service >/dev/null 2>&1")
        services['skyguard-web'] = (result == 0)
        print(f"skyguard-web.service: {'✅ Active' if services['skyguard-web'] else '❌ Inactive'}")
        
    except Exception as e:
        print(f"❌ Error checking systemd services: {e}")
    
    return services


def check_logs() -> None:
    """Check recent logs for snapshot service activity."""
    print("\n📋 Checking recent logs...")
    
    log_files = [
        "logs/skyguard.log",
        "logs/web.log"
    ]
    
    for log_file in log_files:
        if os.path.exists(log_file):
            print(f"\n📄 Recent entries from {log_file}:")
            try:
                # Get last 10 lines
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    recent_lines = lines[-10:] if len(lines) > 10 else lines
                    for line in recent_lines:
                        if 'snapshot' in line.lower() or 'camera' in line.lower():
                            print(f"   {line.strip()}")
            except Exception as e:
                print(f"   Error reading log: {e}")
        else:
            print(f"❌ Log file not found: {log_file}")


def test_snapshot_api() -> bool:
    """Test the snapshot API endpoint."""
    print("\n🌐 Testing snapshot API...")
    
    try:
        import requests
        
        # Test camera status endpoint
        response = requests.get("http://localhost:8080/api/camera/status", timeout=5)
        if response.status_code == 200:
            print("✅ Camera status API working")
            status_data = response.json()
            print(f"   Connected: {status_data.get('connected', False)}")
        else:
            print(f"❌ Camera status API failed: {response.status_code}")
            return False
        
        # Test camera feed endpoint
        response = requests.get("http://localhost:8080/api/camera/feed", timeout=5)
        if response.status_code == 200:
            print(f"✅ Camera feed API working: {len(response.content)} bytes")
            return True
        else:
            print(f"❌ Camera feed API failed: {response.status_code}")
            return False
            
    except ImportError:
        print("❌ requests library not available")
        return False
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False


def suggest_fixes(status: Dict[str, Any]) -> None:
    """Suggest fixes based on the status."""
    print("\n💡 Suggested Fixes")
    print("=" * 20)
    
    if not status['main_process_running']:
        print("1. Start the main system:")
        print("   ./scripts/start_skyguard.sh")
        print("   # or")
        print("   sudo systemctl start skyguard.service")
    
    if not status['snapshot_file_exists']:
        print("2. Create test snapshot:")
        print("   python scripts/quick_fix_camera.py")
    
    if status['snapshot_file_exists'] and not status['snapshot_file_recent']:
        print("3. Snapshot file is old - restart services:")
        print("   ./scripts/stop_skyguard.sh")
        print("   ./scripts/start_skyguard.sh")
    
    if not status['web_service_running']:
        print("4. Start web portal:")
        print("   ./scripts/start_skyguard.sh --web-only")
        print("   # or")
        print("   sudo systemctl start skyguard-web.service")
    
    print("\n5. Check logs for errors:")
    print("   tail -f logs/skyguard.log")
    print("   sudo journalctl -u skyguard.service -f")


def main():
    """Main function to check snapshot service status."""
    print("🔍 SkyGuard Snapshot Service Check")
    print("=" * 35)
    print()
    
    # Check all components
    main_running = check_main_process()
    snapshot_status = check_snapshot_file()
    systemd_status = check_systemd_services()
    api_working = test_snapshot_api()
    
    # Check logs
    check_logs()
    
    # Summary
    print("\n📊 Summary")
    print("=" * 10)
    
    status = {
        'main_process_running': main_running,
        'snapshot_file_exists': snapshot_status['exists'],
        'snapshot_file_recent': snapshot_status['recent'],
        'web_service_running': systemd_status['skyguard-web'],
        'api_working': api_working
    }
    
    print(f"Main process: {'✅' if status['main_process_running'] else '❌'}")
    print(f"Snapshot file: {'✅' if status['snapshot_file_exists'] else '❌'}")
    print(f"Recent snapshot: {'✅' if status['snapshot_file_recent'] else '❌'}")
    print(f"Web service: {'✅' if status['web_service_running'] else '❌'}")
    print(f"API working: {'✅' if status['api_working'] else '❌'}")
    
    # Overall status
    overall_ok = all([
        status['main_process_running'],
        status['snapshot_file_exists'],
        status['snapshot_file_recent'],
        status['api_working']
    ])
    
    if overall_ok:
        print("\n✅ Snapshot service is working correctly!")
    else:
        print("\n❌ Snapshot service has issues")
        suggest_fixes(status)
    
    return overall_ok


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
