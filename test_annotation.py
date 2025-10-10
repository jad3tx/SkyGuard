#!/usr/bin/env python3
"""Test script to verify bounding box annotation is working."""

import cv2
import numpy as np
from pathlib import Path

def test_annotation():
    """Create a test image with a bounding box to verify annotation works."""
    
    # Create a test image (1920x1080)
    img = np.zeros((1080, 1920, 3), dtype=np.uint8)
    img.fill(128)  # Gray background
    
    # Draw a test bounding box
    x1, y1, x2, y2 = 100, 100, 300, 200
    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 5)  # Red box
    
    # Add label
    label = "bird: 0.85"
    font_scale = 0.8
    thickness = 2
    label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)[0]
    
    # Draw label background
    cv2.rectangle(img, 
                (x1, y1 - label_size[1] - 10),
                (x1 + label_size[0], y1),
                (0, 0, 255), -1)
    
    # Draw label text
    cv2.putText(img, label,
              (x1, y1 - 5),
              cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), thickness)
    
    # Save test image
    test_path = Path("test_annotation.jpg")
    cv2.imwrite(str(test_path), img)
    print(f"Test annotation saved to: {test_path}")
    print(f"Image size: {img.shape}")
    print(f"Bounding box: ({x1},{y1}) to ({x2},{y2})")
    
    return test_path

if __name__ == "__main__":
    test_annotation()




