#!/usr/bin/env python3
"""
SkyGuard AI Model Performance Test

Tests processing speed, accuracy, and resource usage.
"""

import sys
import cv2
import time
import psutil
import numpy as np
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from skyguard.core.detector import RaptorDetector
from skyguard.core.config_manager import ConfigManager

def test_processing_speed():
    """Test how fast the model processes frames."""
    print("⚡ Testing AI Model Processing Speed")
    print("=" * 40)
    
    # Load configuration
    config_manager = ConfigManager('config/skyguard.yaml')
    config = config_manager.get_config()
    
    # Initialize detector
    detector = RaptorDetector(config['ai'])
    if not detector.load_model():
        print("❌ Failed to load AI model")
        return
    
    print("✅ Model loaded")
    
    # Test with camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Camera not available")
        return
    
    print("📹 Testing with live camera...")
    print("🔄 Processing 50 frames...")
    
    processing_times = []
    detection_count = 0
    
    for i in range(50):
        ret, frame = cap.read()
        if not ret:
            continue
        
        # Measure processing time
        start_time = time.time()
        detections = detector.detect(frame)
        processing_time = time.time() - start_time
        
        processing_times.append(processing_time)
        
        if detections:
            detection_count += 1
        
        if i % 10 == 0:
            print(f"   Frame {i+1}/50 processed")
    
    cap.release()
    
    # Calculate statistics
    avg_time = sum(processing_times) / len(processing_times)
    min_time = min(processing_times)
    max_time = max(processing_times)
    fps = 1.0 / avg_time
    
    print("\n📊 PERFORMANCE RESULTS")
    print("=" * 40)
    print(f"⚡ Average processing time: {avg_time:.3f}s")
    print(f"🚀 Fastest processing: {min_time:.3f}s")
    print(f"🐌 Slowest processing: {max_time:.3f}s")
    print(f"📈 Theoretical FPS: {fps:.1f}")
    print(f"🦅 Detections found: {detection_count}/50")
    
    # Performance rating
    if avg_time < 0.1:
        print("🏆 EXCELLENT - Real-time capable")
    elif avg_time < 0.5:
        print("✅ GOOD - Near real-time")
    elif avg_time < 1.0:
        print("⚠️  FAIR - Some delay expected")
    else:
        print("❌ SLOW - Significant delay")

def test_resource_usage():
    """Test CPU and memory usage during processing."""
    print("\n💻 Testing Resource Usage")
    print("=" * 40)
    
    # Get initial resource usage
    process = psutil.Process()
    initial_cpu = process.cpu_percent()
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    print(f"📊 Initial CPU: {initial_cpu:.1f}%")
    print(f"💾 Initial Memory: {initial_memory:.1f} MB")
    
    # Load model and measure resource usage
    config_manager = ConfigManager('config/skyguard.yaml')
    config = config_manager.get_config()
    detector = RaptorDetector(config['ai'])
    
    if detector.load_model():
        after_load_cpu = process.cpu_percent()
        after_load_memory = process.memory_info().rss / 1024 / 1024
        
        print(f"📊 After model load - CPU: {after_load_cpu:.1f}%")
        print(f"💾 After model load - Memory: {after_load_memory:.1f} MB")
        print(f"📈 Memory increase: {after_load_memory - initial_memory:.1f} MB")
        
        # Test processing resource usage
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            print("\n🔄 Testing processing resource usage...")
            
            cpu_usage = []
            memory_usage = []
            
            for i in range(20):
                ret, frame = cap.read()
                if ret:
                    # Measure resources during processing
                    start_cpu = process.cpu_percent()
                    start_memory = process.memory_info().rss / 1024 / 1024
                    
                    detections = detector.detect(frame)
                    
                    end_cpu = process.cpu_percent()
                    end_memory = process.memory_info().rss / 1024 / 1024
                    
                    cpu_usage.append(end_cpu)
                    memory_usage.append(end_memory)
            
            cap.release()
            
            avg_cpu = sum(cpu_usage) / len(cpu_usage)
            avg_memory = sum(memory_usage) / len(memory_usage)
            
            print(f"📊 Average CPU during processing: {avg_cpu:.1f}%")
            print(f"💾 Average Memory during processing: {avg_memory:.1f} MB")
            
            # Resource efficiency rating
            if avg_cpu < 50 and avg_memory < 1000:
                print("🏆 EXCELLENT - Low resource usage")
            elif avg_cpu < 80 and avg_memory < 2000:
                print("✅ GOOD - Moderate resource usage")
            else:
                print("⚠️  HIGH - Consider optimization")

if __name__ == "__main__":
    print("🚀 SkyGuard AI Model Performance Test")
    print("This will test processing speed and resource usage")
    
    input("Press Enter to start...")
    
    test_processing_speed()
    test_resource_usage()
    
    print("\n✅ Performance test complete!")

