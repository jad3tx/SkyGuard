#!/usr/bin/env python3
"""
SkyGuard AI Model Effectiveness Test

This script tests the AI model with various images to evaluate detection performance.
"""

import sys
import cv2
import numpy as np
from pathlib import Path
import time

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from skyguard.core.detector import RaptorDetector
from skyguard.core.config_manager import ConfigManager

def test_model_with_images():
    """Test the model with various test images."""
    print("🧪 Testing SkyGuard AI Model Effectiveness")
    print("=" * 50)
    
    # Load configuration
    config_manager = ConfigManager('config/skyguard.yaml')
    config = config_manager.get_config()
    
    # Initialize detector
    detector = RaptorDetector(config['ai'])
    if not detector.load_model():
        print("❌ Failed to load AI model")
        return
    
    print("✅ AI Model loaded successfully")
    print(f"📊 Model: {config['ai']['model_path']}")
    print(f"🎯 Confidence Threshold: {config['ai']['confidence_threshold']}")
    print(f"🏷️  Classes: {config['ai']['classes']}")
    print()
    
    # Test with camera feed
    print("📹 Testing with live camera feed...")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Camera not available")
        return
    
    print("✅ Camera connected")
    print("🔄 Processing frames for 30 seconds...")
    print("   (Look for detection results below)")
    print()
    
    start_time = time.time()
    frame_count = 0
    detection_count = 0
    
    while time.time() - start_time < 30:  # Test for 30 seconds
        ret, frame = cap.read()
        if not ret:
            print("❌ Failed to capture frame")
            continue
            
        frame_count += 1
        
        # Process frame with AI
        frame_start = time.time()
        detections = detector.detect(frame)
        processing_time = time.time() - frame_start
        
        # Check for detections
        if detections:
            detection_count += 1
            print(f"🦅 DETECTION #{detection_count} at {time.strftime('%H:%M:%S')}")
            for i, det in enumerate(detections):
                print(f"   Detection {i+1}:")
                print(f"   - Class: {det.get('class_name', 'unknown')}")
                print(f"   - Confidence: {det.get('confidence', 0):.3f}")
                print(f"   - Bounding Box: {det.get('bbox', [])}")
                print(f"   - Processing Time: {processing_time:.3f}s")
            print()
        
        # Show progress every 5 seconds
        elapsed = time.time() - start_time
        if int(elapsed) % 5 == 0 and int(elapsed) > 0:
            fps = frame_count / elapsed
            print(f"⏱️  {int(elapsed)}s elapsed - FPS: {fps:.1f} - Detections: {detection_count}")
    
    cap.release()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    print(f"🕐 Test Duration: 30 seconds")
    print(f"📹 Frames Processed: {frame_count}")
    print(f"🦅 Detections Found: {detection_count}")
    print(f"📈 Detection Rate: {detection_count/frame_count*100:.1f}%")
    print(f"⚡ Average FPS: {frame_count/30:.1f}")
    
    if detection_count > 0:
        print("✅ Model is detecting objects!")
    else:
        print("⚠️  No detections found - try:")
        print("   - Moving objects in camera view")
        print("   - Using bird-like objects")
        print("   - Lowering confidence threshold")
        print("   - Checking lighting conditions")

def test_with_static_images():
    """Test with static images if available."""
    print("\n🖼️  Testing with static images...")
    
    # Look for test images
    test_images = [
        "data/test_camera.jpg",
        "data/detections/*.jpg",
        "data/airbirds/samples/*.jpg"
    ]
    
    found_images = []
    for pattern in test_images:
        import glob
        found_images.extend(glob.glob(pattern))
    
    if not found_images:
        print("ℹ️  No test images found")
        return
    
    print(f"📁 Found {len(found_images)} test images")
    
    # Load configuration and detector
    config_manager = ConfigManager('config/skyguard.yaml')
    config = config_manager.get_config()
    detector = RaptorDetector(config['ai'])
    
    if not detector.load_model():
        print("❌ Failed to load AI model")
        return
    
    # Test each image
    for img_path in found_images[:5]:  # Test first 5 images
        print(f"\n🖼️  Testing: {img_path}")
        
        # Load image
        img = cv2.imread(img_path)
        if img is None:
            print(f"❌ Could not load image: {img_path}")
            continue
        
        # Process image
        start_time = time.time()
        detections = detector.detect(img)
        processing_time = time.time() - start_time
        
        print(f"⏱️  Processing time: {processing_time:.3f}s")
        
        if detections:
            print(f"🦅 Found {len(detections)} detection(s):")
            for i, det in enumerate(detections):
                print(f"   {i+1}. {det.get('class_name', 'unknown')} "
                      f"(confidence: {det.get('confidence', 0):.3f})")
        else:
            print("ℹ️  No detections in this image")

if __name__ == "__main__":
    print("🚀 SkyGuard AI Model Effectiveness Test")
    print("Choose test method:")
    print("1. Live camera test (30 seconds)")
    print("2. Static image test")
    print("3. Both tests")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        test_model_with_images()
    elif choice == "2":
        test_with_static_images()
    elif choice == "3":
        test_model_with_images()
        test_with_static_images()
    else:
        print("Invalid choice. Running live camera test...")
        test_model_with_images()

