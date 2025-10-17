#!/usr/bin/env python3
"""
Test with a more realistic bird shape that YOLOv8n might recognize
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from skyguard.core.detector import RaptorDetector
from skyguard.core.config_manager import ConfigManager
import cv2
import numpy as np

def test_realistic_bird():
    """Test with a more realistic bird shape."""
    print("🧪 Testing with realistic bird shape")
    print("=" * 50)
    
    # Load config and detector
    config_manager = ConfigManager('config/skyguard.yaml')
    config = config_manager.get_config()
    detector = RaptorDetector(config['ai'])
    
    if not detector.load_model():
        print("❌ Failed to load model")
        return
    
    print("✅ Model loaded successfully")
    
    # Create a more realistic bird shape
    test_img = np.zeros((640, 640, 3), dtype=np.uint8)
    
    # Draw a bird-like shape with proper proportions
    # Body (oval)
    cv2.ellipse(test_img, (320, 350), (40, 60), 0, 0, 360, (100, 100, 100), -1)
    
    # Head (smaller circle)
    cv2.circle(test_img, (320, 280), 25, (120, 120, 120), -1)
    
    # Beak (triangle)
    pts = np.array([[320, 250], [310, 240], [330, 240]], np.int32)
    cv2.fillPoly(test_img, [pts], (200, 200, 0))
    
    # Wings (larger ovals)
    cv2.ellipse(test_img, (280, 320), (30, 50), -30, 0, 360, (80, 80, 80), -1)
    cv2.ellipse(test_img, (360, 320), (30, 50), 30, 0, 360, (80, 80, 80), -1)
    
    # Tail
    cv2.ellipse(test_img, (320, 400), (20, 40), 0, 0, 360, (90, 90, 90), -1)
    
    # Legs
    cv2.line(test_img, (310, 410), (300, 450), (150, 100, 50), 3)
    cv2.line(test_img, (330, 410), (340, 450), (150, 100, 50), 3)
    
    print("🧪 Testing realistic bird shape...")
    detections = detector.detect(test_img)
    
    if detections:
        print(f"✅ DETECTIONS FOUND: {len(detections)}")
        for det in detections:
            print(f"  - Class: {det['class_name']}, Confidence: {det['confidence']:.3f}")
    else:
        print("❌ NO DETECTIONS - Trying with even more realistic shape")
        
        # Try an even more realistic bird
        test_img2 = np.zeros((640, 640, 3), dtype=np.uint8)
        
        # Draw a bird in flight (side view)
        # Body (longer oval)
        cv2.ellipse(test_img2, (320, 320), (60, 25), 0, 0, 360, (100, 100, 100), -1)
        
        # Head
        cv2.circle(test_img2, (380, 320), 20, (120, 120, 120), -1)
        
        # Beak
        cv2.line(test_img2, (400, 320), (420, 320), (200, 200, 0), 4)
        
        # Wings (large and spread)
        cv2.ellipse(test_img2, (300, 300), (80, 30), -45, 0, 360, (80, 80, 80), -1)
        cv2.ellipse(test_img2, (300, 340), (80, 30), 45, 0, 360, (80, 80, 80), -1)
        
        # Tail
        cv2.ellipse(test_img2, (260, 320), (40, 15), 0, 0, 360, (90, 90, 90), -1)
        
        print("🧪 Testing bird in flight shape...")
        detections = detector.detect(test_img2)
        
        if detections:
            print(f"✅ DETECTIONS FOUND: {len(detections)}")
            for det in detections:
                print(f"  - Class: {det['class_name']}, Confidence: {det['confidence']:.3f}")
        else:
            print("❌ Still no detections")
            
            # Try with a very simple bird silhouette
            test_img3 = np.zeros((640, 640, 3), dtype=np.uint8)
            
            # Simple bird silhouette
            cv2.circle(test_img3, (320, 320), 50, (255, 255, 255), -1)
            cv2.circle(test_img3, (320, 280), 30, (255, 255, 255), -1)
            
            print("🧪 Testing simple bird silhouette...")
            detections = detector.detect(test_img3)
            
            if detections:
                print(f"✅ DETECTIONS FOUND: {len(detections)}")
                for det in detections:
                    print(f"  - Class: {det['class_name']}, Confidence: {det['confidence']:.3f}")
            else:
                print("❌ Still no detections - Model may need real bird images")

if __name__ == "__main__":
    test_realistic_bird()










