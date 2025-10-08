#!/usr/bin/env python3
"""
Test the YOLOv8n model to see if it can detect objects
"""

from ultralytics import YOLO
import numpy as np
import cv2

def test_yolov8n():
    """Test the YOLOv8n model."""
    print("🧪 Testing YOLOv8n model...")
    
    try:
        model = YOLO('models/yolov8n.pt')
        print("✅ YOLOv8n model loaded")
        print(f"📊 Classes: {model.names}")
        
        # Create test image with a person-like shape
        test_img = np.zeros((640, 640, 3), dtype=np.uint8)
        # Draw a simple person shape
        cv2.circle(test_img, (320, 200), 30, (0, 255, 0), -1)  # Head
        cv2.rectangle(test_img, (300, 230), (340, 400), (0, 255, 0), -1)  # Body
        cv2.line(test_img, (300, 300), (250, 400), (0, 255, 0), 5)  # Left arm
        cv2.line(test_img, (340, 300), (390, 400), (0, 255, 0), 5)  # Right arm
        cv2.line(test_img, (320, 400), (300, 500), (0, 255, 0), 5)  # Left leg
        cv2.line(test_img, (320, 400), (340, 500), (0, 255, 0), 5)  # Right leg
        
        print("🧪 Running detection...")
        results = model(test_img)
        print(f"📊 Results: {len(results)}")
        
        for i, result in enumerate(results):
            if result.boxes is not None and len(result.boxes) > 0:
                print(f"✅ Found {len(result.boxes)} detections")
                for j, box in enumerate(result.boxes):
                    conf = box.conf.item()
                    cls = int(box.cls.item())
                    class_name = model.names[cls]
                    print(f"  - Detection {j}: {class_name} (confidence: {conf:.3f})")
            else:
                print("❌ No detections")
        
        # Test with a simple circle (should detect as something)
        print("\n🧪 Testing with simple circle...")
        circle_img = np.zeros((640, 640, 3), dtype=np.uint8)
        cv2.circle(circle_img, (320, 320), 100, (255, 255, 255), -1)
        
        results = model(circle_img)
        for i, result in enumerate(results):
            if result.boxes is not None and len(result.boxes) > 0:
                print(f"✅ Found {len(result.boxes)} detections in circle")
                for j, box in enumerate(result.boxes):
                    conf = box.conf.item()
                    cls = int(box.cls.item())
                    class_name = model.names[cls]
                    print(f"  - Detection {j}: {class_name} (confidence: {conf:.3f})")
            else:
                print("❌ No detections in circle")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_yolov8n()

