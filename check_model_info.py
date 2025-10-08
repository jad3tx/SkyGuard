#!/usr/bin/env python3
"""
Check the model file to understand what we're working with
"""

from ultralytics import YOLO
import torch

def check_model():
    """Check model information."""
    print("🔍 Checking model file information...")
    
    try:
        model = YOLO('models/airbirds_raptor_detector.pt')
        print("✅ Model file loads successfully")
        
        print(f"📊 Model Info:")
        print(f"  - Model type: {type(model.model)}")
        print(f"  - Classes: {model.names}")
        print(f"  - Number of classes: {len(model.names)}")
        
        # Check if it's a custom model or pretrained
        if hasattr(model, 'names'):
            print(f"  - Class names: {list(model.names.values())}")
        
        # Try to get model architecture info
        if hasattr(model.model, 'model'):
            print(f"  - Model architecture: {type(model.model.model)}")
        
        # Check if model has been trained
        print(f"  - Model device: {model.device}")
        
        # Test with a simple image to see what happens
        import numpy as np
        import cv2
        
        test_img = np.ones((640, 640, 3), dtype=np.uint8) * 128  # Gray image
        results = model(test_img, verbose=False)
        
        print(f"  - Test results: {len(results)}")
        for result in results:
            if hasattr(result, 'boxes') and result.boxes is not None:
                print(f"    - Detections: {len(result.boxes)}")
            else:
                print(f"    - No detections")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_model()

