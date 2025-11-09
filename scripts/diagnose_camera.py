#!/usr/bin/env python3
"""
Camera Diagnostic Script for SkyGuard

This script helps diagnose camera issues on Raspberry Pi.
"""

import sys
import os
import subprocess
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def check_video_devices() -> None:
    """Check for available video devices."""
    print("\n=== Checking Video Devices ===")
    try:
        result = subprocess.run(['ls', '/dev/video*'], capture_output=True, text=True, stderr=subprocess.STDOUT)
        if result.returncode == 0:
            print("Found video devices:")
            for line in result.stdout.strip().split('\n'):
                if line:
                    print(f"  {line}")
        else:
            print("No /dev/video* devices found")
    except Exception as e:
        print(f"Error checking video devices: {e}")

def check_usb_cameras() -> None:
    """Check for USB cameras."""
    print("\n=== Checking USB Cameras ===")
    try:
        result = subprocess.run(['lsusb'], capture_output=True, text=True)
        if result.returncode == 0:
            cameras = [line for line in result.stdout.split('\n') if 'camera' in line.lower() or 'webcam' in line.lower() or 'video' in line.lower()]
            if cameras:
                print("Found USB cameras:")
                for cam in cameras:
                    print(f"  {cam}")
            else:
                print("No USB cameras detected in lsusb output")
                print("Full lsusb output:")
                for line in result.stdout.split('\n'):
                    if line:
                        print(f"  {line}")
    except Exception as e:
        print(f"Error checking USB cameras: {e}")

def check_user_groups() -> None:
    """Check if user is in video group."""
    print("\n=== Checking User Groups ===")
    try:
        import getpass
        username = getpass.getuser()
        result = subprocess.run(['groups'], capture_output=True, text=True)
        if result.returncode == 0:
            groups = result.stdout.strip().split()
            print(f"User '{username}' is in groups: {', '.join(groups)}")
            if 'video' in groups:
                print("✓ User is in 'video' group")
            else:
                print("✗ User is NOT in 'video' group")
                print("  Fix with: sudo usermod -a -G video $USER")
                print("  Then logout/login or reboot")
        else:
            print("Could not determine user groups")
    except Exception as e:
        print(f"Error checking user groups: {e}")

def check_pi_camera() -> None:
    """Check if Pi camera is enabled."""
    print("\n=== Checking Raspberry Pi Camera ===")
    try:
        # Check if we're on a Pi
        if os.path.exists('/proc/device-tree/model'):
            with open('/proc/device-tree/model', 'r') as f:
                model = f.read().strip()
                if 'Raspberry Pi' in model:
                    print(f"Detected: {model}")
                    
                    # Check if camera is enabled
                    if os.path.exists('/boot/config.txt'):
                        with open('/boot/config.txt', 'r') as f:
                            config = f.read()
                            if 'camera_auto_detect=1' in config or 'start_x=1' in config:
                                print("✓ Camera appears to be enabled in config.txt")
                            else:
                                print("✗ Camera may not be enabled")
                                print("  Enable with: sudo raspi-config")
                                print("  Navigate to: Interface Options → Camera → Enable")
                    
                    # Try libcamera-hello
                    try:
                        result = subprocess.run(['libcamera-hello', '--list-cameras'], 
                                               capture_output=True, text=True, timeout=5)
                        if result.returncode == 0:
                            print("✓ libcamera-hello found cameras:")
                            print(result.stdout)
                        else:
                            print("✗ libcamera-hello failed or no cameras found")
                    except FileNotFoundError:
                        print("libcamera-hello not found (may need to install)")
                    except subprocess.TimeoutExpired:
                        print("libcamera-hello timed out")
                    except Exception as e:
                        print(f"Error running libcamera-hello: {e}")
                else:
                    print(f"Not a Raspberry Pi: {model}")
        else:
            print("Not running on Raspberry Pi")
    except Exception as e:
        print(f"Error checking Pi camera: {e}")

def test_opencv_camera() -> None:
    """Test OpenCV camera access."""
    print("\n=== Testing OpenCV Camera Access ===")
    try:
        import cv2
        print(f"OpenCV version: {cv2.__version__}")
        
        # Try different camera sources
        for source in [0, 1, 2]:
            print(f"\nTrying camera source {source}...")
            try:
                cap = cv2.VideoCapture(source)
                if cap.isOpened():
                    print(f"  ✓ Camera {source} opened successfully")
                    
                    # Try to read a frame
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        h, w = frame.shape[:2]
                        print(f"  ✓ Successfully captured frame: {w}x{h}")
                    else:
                        print(f"  ✗ Could not capture frame from camera {source}")
                    
                    # Get camera properties
                    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    print(f"  Camera properties: {width}x{height} @ {fps:.1f}fps")
                    
                    cap.release()
                    print(f"  ✓ Camera {source} works!")
                    return
                else:
                    print(f"  ✗ Camera {source} failed to open")
                    cap.release()
            except Exception as e:
                print(f"  ✗ Error with camera {source}: {e}")
        
        print("\n✗ No working cameras found with OpenCV")
        print("  This could mean:")
        print("  - Camera not connected")
        print("  - Camera permissions issue (user not in 'video' group)")
        print("  - Wrong camera source number")
        print("  - Camera driver issue")
        
    except ImportError:
        print("✗ OpenCV not installed")
        print("  Install with: pip install opencv-python")
    except Exception as e:
        print(f"✗ Error testing OpenCV: {e}")

def check_camera_permissions() -> None:
    """Check camera device permissions."""
    print("\n=== Checking Camera Device Permissions ===")
    try:
        import glob
        video_devices = glob.glob('/dev/video*')
        if video_devices:
            for device in sorted(video_devices):
                try:
                    stat = os.stat(device)
                    print(f"{device}:")
                    print(f"  Owner: {stat.st_uid}")
                    print(f"  Group: {stat.st_gid}")
                    print(f"  Permissions: {oct(stat.st_mode)}")
                    
                    # Check if readable
                    if os.access(device, os.R_OK):
                        print(f"  ✓ Readable")
                    else:
                        print(f"  ✗ NOT readable")
                except Exception as e:
                    print(f"  Error checking {device}: {e}")
        else:
            print("No /dev/video* devices found")
    except Exception as e:
        print(f"Error checking permissions: {e}")

def main() -> None:
    """Run all diagnostic checks."""
    print("=" * 60)
    print("SkyGuard Camera Diagnostic Tool")
    print("=" * 60)
    
    check_video_devices()
    check_usb_cameras()
    check_user_groups()
    check_camera_permissions()
    check_pi_camera()
    test_opencv_camera()
    
    print("\n" + "=" * 60)
    print("Diagnostic Complete")
    print("=" * 60)
    print("\nIf camera still doesn't work, check the logs:")
    print("  tail -f logs/skyguard.log")

if __name__ == '__main__':
    main()

