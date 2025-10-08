#!/usr/bin/env python3
"""
Direct detector test to verify if the AI model can actually detect birds
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from skyguard.core.detector import RaptorDetector
from skyguard.core.config_manager import ConfigManager
import cv2
import numpy as np

def test_detector():
    """Test the detector with synthetic and real images."""
    print("🧪 Testing SkyGuard Detector Directly")
    print("=" * 50)
    
    # Load config and detector
    config_manager = ConfigManager('config/skyguard.yaml')
    config = config_manager.get_config()
    detector = RaptorDetector(config['ai'])
    
    if not detector.load_model():
        print("❌ Failed to load model")
        return
    
    print("✅ Model loaded successfully")
    print(f"📊 Confidence threshold: {config['ai']['confidence_threshold']}")
    print(f"🏷️ Classes: {config['ai']['classes']}")
    
    # Test 1: Synthetic bird image
    print("\n🧪 Test 1: Synthetic bird image")
    test_img = np.zeros((480, 640, 3), dtype=np.uint8)
    # Draw a simple bird shape
    cv2.circle(test_img, (320, 240), 30, (0, 255, 0), -1)  # Green circle body
    cv2.circle(test_img, (320, 200), 20, (0, 255, 0), -1)  # Head
    cv2.line(test_img, (350, 220), (380, 200), (0, 255, 0), 3)  # Wing
    cv2.putText(test_img, 'TEST BIRD', (250, 300), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    detections = detector.detect(test_img)
    
    if detections:
        print(f"✅ DETECTIONS FOUND: {len(detections)}")
        for det in detections:
            print(f"  - Class: {det['class_name']}, Confidence: {det['confidence']:.3f}")
    else:
        print("❌ NO DETECTIONS - Model may not be working properly")
    
    # Test 2: Empty image
    print("\n🧪 Test 2: Empty image")
    empty_img = np.zeros((480, 640, 3), dtype=np.uint8)
    detections = detector.detect(empty_img)
    
    if detections:
        print(f"⚠️ FALSE POSITIVES: {len(detections)}")
        for det in detections:
            print(f"  - Class: {det['class_name']}, Confidence: {det['confidence']:.3f}")
    else:
        print("✅ No false positives on empty image")
    
    # Test 3: Try with lower confidence threshold
    print("\n🧪 Test 3: Lower confidence threshold (0.3)")
    original_threshold = config['ai']['confidence_threshold']
    config['ai']['confidence_threshold'] = 0.3
    detector = RaptorDetector(config['ai'])
    detector.load_model()
    
    detections = detector.detect(test_img)
    
    if detections:
        print(f"✅ DETECTIONS FOUND with lower threshold: {len(detections)}")
        for det in detections:
            print(f"  - Class: {det['class_name']}, Confidence: {det['confidence']:.3f}")
    else:
        print("❌ Still no detections even with lower threshold")
    
    # Test 4: Try with existing detection images
    print("\n🧪 Test 4: Existing detection images")
    detection_dir = Path("data/detections")
    if detection_dir.exists():
        for img_path in detection_dir.glob("*.jpg"):
            print(f"Testing: {img_path.name}")
            img = cv2.imread(str(img_path))
            if img is not None:
                detections = detector.detect(img)
                if detections:
                    print(f"  ✅ Found {len(detections)} detections")
                    for det in detections:
                        print(f"    - Class: {det['class_name']}, Confidence: {det['confidence']:.3f}")
                else:
                    print(f"  ❌ No detections")
            else:
                print(f"  ❌ Could not load image")
    
    print("\n🎯 Detector test complete!")

if __name__ == "__main__":
    test_detector()

