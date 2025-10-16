#!/usr/bin/env python3
"""
Windows Camera Test Script for SkyGuard
Tests camera detection and provides troubleshooting information.
"""

import cv2
import sys
from pathlib import Path

def test_camera_detection():
    """Test for available cameras."""
    print("Testing Camera Detection")
    print("=" * 40)
    
    available_cameras = []
    
    # Test camera indices 0-10
    for i in range(11):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                height, width = frame.shape[:2]
                print(f"Camera {i}: {width}x{height} - Working")
                available_cameras.append(i)
            else:
                print(f"Camera {i}: Opened but no frame capture")
            cap.release()
        else:
            print(f"Camera {i}: Not available")
    
    return available_cameras

def test_camera_backends():
    """Test different camera backends for Windows."""
    print("\nTesting Camera Backends")
    print("=" * 40)
    
    backends = [
        (cv2.CAP_DSHOW, "DirectShow (Windows)"),
        (cv2.CAP_MSMF, "Microsoft Media Foundation"),
        (cv2.CAP_ANY, "Any available")
    ]
    
    for backend, name in backends:
        cap = cv2.VideoCapture(0, backend)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                print(f"{name}: Working")
            else:
                print(f"{name}: Opened but no frame")
        else:
            print(f"{name}: Not available")
        cap.release()

def create_test_image():
    """Create a test image when no camera is available."""
    print("\nCreating Test Image")
    print("=" * 40)
    
    import numpy as np
    
    # Create a test image with text
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    img[:] = (50, 50, 50)  # Dark gray background
    
    # Add text
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(img, "SkyGuard Test Image", (50, 100), font, 1, (255, 255, 255), 2)
    cv2.putText(img, "No Camera Detected", (50, 150), font, 0.8, (0, 255, 255), 2)
    cv2.putText(img, "Check USB connection", (50, 200), font, 0.6, (0, 255, 0), 2)
    
    # Add some shapes
    cv2.rectangle(img, (100, 250), (300, 350), (255, 0, 0), 2)
    cv2.circle(img, (200, 300), 50, (0, 0, 255), 2)
    
    # Save test image
    test_dir = Path("data")
    test_dir.mkdir(exist_ok=True)
    test_path = test_dir / "camera_snapshot.jpg"
    cv2.imwrite(str(test_path), img)
    print(f"Test image saved to: {test_path}")
    
    return test_path

def main():
    """Main camera test function."""
    print("SkyGuard Camera Test - Windows")
    print("=" * 50)
    
    # Test camera detection
    available_cameras = test_camera_detection()
    
    if available_cameras:
        print(f"\nFound {len(available_cameras)} working camera(s): {available_cameras}")
        print(f"\nRecommended camera index: {available_cameras[0]}")
        print("Update your config/skyguard.yaml:")
        print(f"camera:")
        print(f"  source: {available_cameras[0]}")
        
    else:
        print("\nNo cameras detected!")
        print("\nTroubleshooting steps:")
        print("1. Check USB cable connection")
        print("2. Try a different USB port")
        print("3. Check if camera is recognized in Device Manager")
        print("4. Try unplugging and reconnecting the camera")
        print("5. Restart your computer")
        
        # Test different backends
        test_camera_backends()
        
        # Create test image
        create_test_image()
        
        print("\nFallback: Using test image mode")
        print("SkyGuard will use a test image instead of live camera")
    
    print("\n" + "=" * 50)
    print("Camera test complete!")

if __name__ == "__main__":
    main()
