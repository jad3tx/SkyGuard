#!/usr/bin/env python3
"""
Test the model file directly to see if it can detect anything
"""

import torch
from ultralytics import YOLO
import numpy as np
import cv2

def test_model_file():
    """Test the model file directly."""
    print("🔍 Testing model file directly...")
    
    try:
        model = YOLO('models/airbirds_raptor_detector.pt')
        print("✅ Model file loads with YOLO")
        
        # Test with a simple image
        test_img = np.zeros((640, 640, 3), dtype=np.uint8)
        cv2.circle(test_img, (320, 320), 50, (0, 255, 0), -1)
        cv2.putText(test_img, 'TEST', (300, 400), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
        
        print("🧪 Running detection on test image...")
        results = model(test_img)
        print(f"📊 Results: {len(results)}")
        
        for i, result in enumerate(results):
            print(f"Result {i}:")
            boxes = result.boxes
            if boxes is not None and len(boxes) > 0:
                print(f"✅ Found {len(boxes)} detections")
                for j, box in enumerate(boxes):
                    conf = box.conf.item()
                    cls = int(box.cls.item())
                    print(f"  - Detection {j}: Class {cls}, Confidence {conf:.3f}")
            else:
                print("❌ No detections found")
        
        # Test with a more complex image
        print("\n🧪 Testing with more complex image...")
        complex_img = np.zeros((640, 640, 3), dtype=np.uint8)
        # Draw multiple shapes
        cv2.circle(complex_img, (200, 200), 30, (0, 255, 0), -1)
        cv2.circle(complex_img, (400, 300), 40, (0, 255, 0), -1)
        cv2.rectangle(complex_img, (100, 100), (150, 150), (255, 0, 0), -1)
        
        results = model(complex_img)
        for i, result in enumerate(results):
            boxes = result.boxes
            if boxes is not None and len(boxes) > 0:
                print(f"✅ Found {len(boxes)} detections in complex image")
                for j, box in enumerate(boxes):
                    conf = box.conf.item()
                    cls = int(box.cls.item())
                    print(f"  - Detection {j}: Class {cls}, Confidence {conf:.3f}")
            else:
                print("❌ No detections in complex image")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_model_file()

