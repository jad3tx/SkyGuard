#!/usr/bin/env python3
"""
Comprehensive diagnostic for snapshot service issues on Raspberry Pi.
This script identifies why the camera snapshot service isn't working.
"""

import os
import sys
import time
import cv2
import psutil
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def check_system_info() -> Dict[str, Any]:
    """Check basic system information."""
    print("🖥️ System Information")
    print("=" * 20)
    
    info = {
        'platform': sys.platform,
        'python_version': sys.version,
        'working_directory': os.getcwd(),
        'user': os.getenv('USER', 'unknown'),
        'home_directory': os.path.expanduser('~')
    }
    
    print(f"Platform: {info['platform']}")
    print(f"Python: {info['python_version']}")
    print(f"Working Directory: {info['working_directory']}")
    print(f"User: {info['user']}")
    print(f"Home: {info['home_directory']}")
    
    return info


def check_processes() -> Dict[str, bool]:
    """Check if relevant processes are running."""
    print("\n🔄 Process Check")
    print("=" * 15)
    
    processes = {
        'main_process': False,
        'web_process': False,
        'python_processes': 0
    }
    
    # Check for main process
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        cmdline = ' '.join(proc.info['cmdline'] or [])
        if 'skyguard.main' in cmdline:
            processes['main_process'] = True
            print(f"✅ Main process running (PID: {proc.info['pid']})")
        elif 'start_web_portal.py' in cmdline:
            processes['web_process'] = True
            print(f"✅ Web process running (PID: {proc.info['pid']})")
        elif 'python' in proc.info['name'].lower():
            processes['python_processes'] += 1
    
    if not processes['main_process']:
        print("❌ Main process not running")
    if not processes['web_process']:
        print("❌ Web process not running")
    
    print(f"Total Python processes: {processes['python_processes']}")
    return processes


def check_systemd_services() -> Dict[str, Any]:
    """Check systemd service status."""
    print("\n🔧 Systemd Services")
    print("=" * 18)
    
    services = {
        'skyguard': {'active': False, 'enabled': False, 'status': 'unknown'},
        'skyguard-web': {'active': False, 'enabled': False, 'status': 'unknown'}
    }
    
    for service in services:
        try:
            # Check if service is active
            result = subprocess.run(['systemctl', 'is-active', f'{service}.service'], 
                                 capture_output=True, text=True)
            services[service]['active'] = (result.returncode == 0)
            
            # Check if service is enabled
            result = subprocess.run(['systemctl', 'is-enabled', f'{service}.service'], 
                                 capture_output=True, text=True)
            services[service]['enabled'] = (result.returncode == 0)
            
            # Get detailed status
            result = subprocess.run(['systemctl', 'status', f'{service}.service', '--no-pager'], 
                                 capture_output=True, text=True)
            services[service]['status'] = result.stdout
            
            status_icon = "✅" if services[service]['active'] else "❌"
            print(f"{status_icon} {service}.service: {'Active' if services[service]['active'] else 'Inactive'}")
            
        except Exception as e:
            print(f"❌ Error checking {service}.service: {e}")
    
    return services


def check_camera_hardware() -> Dict[str, Any]:
    """Check camera hardware availability."""
    print("\n📷 Camera Hardware Check")
    print("=" * 25)
    
    camera_info = {
        'video_devices': [],
        'camera_accessible': False,
        'opencv_camera': False,
        'permissions_ok': False
    }
    
    # Check video devices
    try:
        video_devices = [f for f in os.listdir('/dev') if f.startswith('video')]
        camera_info['video_devices'] = video_devices
        print(f"Video devices: {video_devices}")
    except Exception as e:
        print(f"❌ Error listing video devices: {e}")
    
    # Check camera permissions
    try:
        for device in camera_info['video_devices']:
            device_path = f"/dev/{device}"
            if os.access(device_path, os.R_OK | os.W_OK):
                camera_info['permissions_ok'] = True
                print(f"✅ {device_path} accessible")
            else:
                print(f"❌ {device_path} not accessible")
    except Exception as e:
        print(f"❌ Error checking permissions: {e}")
    
    # Test OpenCV camera
    try:
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            camera_info['opencv_camera'] = True
            ret, frame = cap.read()
            if ret:
                print(f"✅ Camera working - frame shape: {frame.shape}")
            else:
                print("⚠️ Camera opened but no frame")
            cap.release()
        else:
            print("❌ Camera not accessible via OpenCV")
    except Exception as e:
        print(f"❌ Camera test failed: {e}")
    
    return camera_info


def check_snapshot_file() -> Dict[str, Any]:
    """Check snapshot file status."""
    print("\n📸 Snapshot File Check")
    print("=" * 22)
    
    snapshot_path = Path("data/camera_snapshot.jpg")
    status = {
        'exists': False,
        'recent': False,
        'size': 0,
        'age_seconds': 0,
        'readable': False,
        'valid_image': False
    }
    
    if snapshot_path.exists():
        status['exists'] = True
        status['size'] = snapshot_path.stat().st_size
        
        # Check file age
        file_time = snapshot_path.stat().st_mtime
        current_time = time.time()
        age_seconds = current_time - file_time
        status['age_seconds'] = age_seconds
        status['recent'] = age_seconds < 10
        
        print(f"✅ Snapshot file exists")
        print(f"   Size: {status['size']} bytes")
        print(f"   Age: {age_seconds:.1f} seconds")
        print(f"   Recent: {'✅' if status['recent'] else '❌'}")
        
        # Check if readable
        try:
            with open(snapshot_path, 'rb') as f:
                data = f.read(100)  # Read first 100 bytes
                status['readable'] = len(data) > 0
                print(f"   Readable: {'✅' if status['readable'] else '❌'}")
        except Exception as e:
            print(f"   Readable: ❌ ({e})")
        
        # Check if valid image
        try:
            img = cv2.imread(str(snapshot_path))
            if img is not None:
                status['valid_image'] = True
                print(f"   Valid image: ✅ ({img.shape})")
            else:
                print(f"   Valid image: ❌")
        except Exception as e:
            print(f"   Valid image: ❌ ({e})")
    else:
        print("❌ Snapshot file not found")
    
    return status


def check_directories() -> Dict[str, bool]:
    """Check if required directories exist."""
    print("\n📁 Directory Check")
    print("=" * 17)
    
    directories = {
        'data_dir': False,
        'logs_dir': False,
        'config_dir': False,
        'writable': False
    }
    
    # Check data directory
    data_dir = Path("data")
    directories['data_dir'] = data_dir.exists()
    print(f"data/: {'✅' if directories['data_dir'] else '❌'}")
    
    # Check logs directory
    logs_dir = Path("logs")
    directories['logs_dir'] = logs_dir.exists()
    print(f"logs/: {'✅' if directories['logs_dir'] else '❌'}")
    
    # Check config directory
    config_dir = Path("config")
    directories['config_dir'] = config_dir.exists()
    print(f"config/: {'✅' if directories['config_dir'] else '❌'}")
    
    # Check if data directory is writable
    try:
        test_file = data_dir / "test_write.tmp"
        test_file.write_text("test")
        test_file.unlink()
        directories['writable'] = True
        print(f"data/ writable: ✅")
    except Exception as e:
        print(f"data/ writable: ❌ ({e})")
    
    return directories


def check_logs() -> Dict[str, List[str]]:
    """Check recent logs for errors."""
    print("\n📋 Log Analysis")
    print("=" * 15)
    
    log_files = {
        'skyguard.log': [],
        'web.log': [],
        'systemd.log': []
    }
    
    # Check SkyGuard logs
    for log_name in ['skyguard.log', 'web.log']:
        log_path = Path(f"logs/{log_name}")
        if log_path.exists():
            try:
                with open(log_path, 'r') as f:
                    lines = f.readlines()
                    # Get last 20 lines
                    recent_lines = lines[-20:] if len(lines) > 20 else lines
                    log_files[log_name] = [line.strip() for line in recent_lines]
                    
                    # Look for error patterns
                    error_lines = [line for line in recent_lines 
                                 if any(keyword in line.lower() for keyword in 
                                       ['error', 'failed', 'exception', 'traceback'])]
                    if error_lines:
                        print(f"\n❌ Errors in {log_name}:")
                        for line in error_lines[-5:]:  # Show last 5 errors
                            print(f"   {line.strip()}")
                    else:
                        print(f"✅ No recent errors in {log_name}")
            except Exception as e:
                print(f"❌ Error reading {log_name}: {e}")
        else:
            print(f"❌ Log file not found: {log_name}")
    
    # Check systemd logs
    try:
        result = subprocess.run(['journalctl', '-u', 'skyguard.service', '--no-pager', '-n', '10'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            log_files['systemd.log'] = result.stdout.split('\n')
            print("✅ Systemd logs available")
        else:
            print("❌ Systemd logs not available")
    except Exception as e:
        print(f"❌ Error reading systemd logs: {e}")
    
    return log_files


def check_dependencies() -> Dict[str, bool]:
    """Check if required dependencies are available."""
    print("\n📦 Dependencies Check")
    print("=" * 20)
    
    dependencies = {
        'opencv': False,
        'numpy': False,
        'psutil': False,
        'flask': False
    }
    
    for dep in dependencies:
        try:
            __import__(dep)
            dependencies[dep] = True
            print(f"✅ {dep}")
        except ImportError:
            print(f"❌ {dep}")
    
    return dependencies


def suggest_solutions(diagnosis: Dict[str, Any]) -> None:
    """Suggest solutions based on diagnosis."""
    print("\n💡 Suggested Solutions")
    print("=" * 20)
    
    if not diagnosis['processes']['main_process']:
        print("1. Start the main system:")
        print("   ./scripts/start_skyguard.sh")
        print("   # or")
        print("   sudo systemctl start skyguard.service")
    
    if not diagnosis['camera']['opencv_camera']:
        print("2. Fix camera issues:")
        print("   # Check camera permissions")
        print("   ls -la /dev/video*")
        print("   # Add user to video group")
        print("   sudo usermod -a -G video pi")
        print("   # Test camera manually")
        print("   python -c \"import cv2; cap = cv2.VideoCapture(0); print('OK' if cap.isOpened() else 'Failed')\"")
    
    if not diagnosis['snapshot']['exists']:
        print("3. Create test snapshot:")
        print("   python scripts/quick_fix_camera.py")
    
    if not diagnosis['directories']['writable']:
        print("4. Fix directory permissions:")
        print("   sudo chown -R pi:pi /home/pi/skyguard")
        print("   chmod -R 755 /home/pi/skyguard")
    
    if not diagnosis['systemd']['skyguard']['active']:
        print("5. Restart systemd services:")
        print("   sudo systemctl daemon-reload")
        print("   sudo systemctl restart skyguard.service")
    
    print("\n6. Check logs for specific errors:")
    print("   tail -f logs/skyguard.log")
    print("   sudo journalctl -u skyguard.service -f")


def main():
    """Main diagnostic function."""
    print("🔧 Snapshot Service Diagnostic")
    print("=" * 30)
    print()
    
    # Run all diagnostic checks
    diagnosis = {
        'system': check_system_info(),
        'processes': check_processes(),
        'systemd': check_systemd_services(),
        'camera': check_camera_hardware(),
        'snapshot': check_snapshot_file(),
        'directories': check_directories(),
        'logs': check_logs(),
        'dependencies': check_dependencies()
    }
    
    # Summary
    print("\n📊 Diagnostic Summary")
    print("=" * 20)
    
    issues = []
    if not diagnosis['processes']['main_process']:
        issues.append("Main process not running")
    if not diagnosis['camera']['opencv_camera']:
        issues.append("Camera not accessible")
    if not diagnosis['snapshot']['exists']:
        issues.append("Snapshot file missing")
    if not diagnosis['snapshot']['recent']:
        issues.append("Snapshot file outdated")
    if not diagnosis['directories']['writable']:
        issues.append("Directory permissions issue")
    
    if issues:
        print("❌ Issues found:")
        for issue in issues:
            print(f"   - {issue}")
    else:
        print("✅ No obvious issues found")
    
    # Suggest solutions
    suggest_solutions(diagnosis)
    
    return len(issues) == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
