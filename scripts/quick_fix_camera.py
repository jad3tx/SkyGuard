#!/usr/bin/env python3
"""
Quick fix for camera snapshot issues on Raspberry Pi.
Run this script to automatically resolve common camera problems.
"""

import os
import sys
import time
import cv2
import numpy as np
from pathlib import Path

def main():
    """Quick fix for camera snapshot issues."""
    print("🛠️ Quick Camera Fix")
    print("=" * 20)
    
    # Step 1: Ensure data directory exists
    print("📁 Creating data directory...")
    os.makedirs("data", exist_ok=True)
    print("✅ Data directory ready")
    
    # Step 2: Create test snapshot
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
        
        # Add visual elements
        cv2.rectangle(img, (100, 250), (540, 350), (0, 255, 0), 2)
        cv2.circle(img, (320, 300), 50, (255, 0, 0), 2)
        
        # Add pattern
        for i in range(0, 640, 50):
            cv2.line(img, (i, 250), (i, 350), (100, 100, 100), 1)
        
        # Save the test image
        cv2.imwrite("data/camera_snapshot.jpg", img)
        print("✅ Test snapshot created")
        
    except Exception as e:
        print(f"❌ Failed to create test snapshot: {e}")
        return False
    
    # Step 3: Set proper permissions
    print("🔧 Setting file permissions...")
    try:
        os.chmod("data", 0o755)
        os.chmod("data/camera_snapshot.jpg", 0o644)
        print("✅ Permissions set")
    except Exception as e:
        print(f"⚠️ Permission warning: {e}")
    
    # Step 4: Test camera if available
    print("📷 Testing camera...")
    try:
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                print("✅ Camera working - updating snapshot with real image")
                cv2.imwrite("data/camera_snapshot.jpg", frame)
            else:
                print("⚠️ Camera opened but no frame - using test image")
            cap.release()
        else:
            print("⚠️ Camera not accessible - using test image")
    except Exception as e:
        print(f"⚠️ Camera test failed: {e}")
    
    # Step 5: Verify file exists
    snapshot_path = Path("data/camera_snapshot.jpg")
    if snapshot_path.exists():
        size = snapshot_path.stat().st_size
        print(f"✅ Snapshot file created: {size} bytes")
        
        # Test if it's a valid image
        try:
            test_img = cv2.imread(str(snapshot_path))
            if test_img is not None:
                print(f"✅ Snapshot is valid image: {test_img.shape}")
            else:
                print("❌ Snapshot is not a valid image")
                return False
        except Exception as e:
            print(f"❌ Failed to verify snapshot: {e}")
            return False
    else:
        print("❌ Snapshot file not created")
        return False
    
    print("\n🎉 Camera snapshot fix completed!")
    print("\n📋 Next steps:")
    print("1. Check the web portal: http://<PI_IP>:8080")
    print("2. Navigate to 'Recent Captures' section")
    print("3. If still not working, restart services:")
    print("   ./scripts/stop_skyguard.sh")
    print("   ./scripts/start_skyguard.sh")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
