#!/usr/bin/env python3
"""
Setup and integrate AI models for SkyGuard
"""

import os
import sys
import shutil
from pathlib import Path

def setup_pre_trained_model():
    """Setup pre-trained YOLO model for SkyGuard."""
    print("🦅 Setting up pre-trained YOLO model for SkyGuard...")
    
    # Check if model exists
    model_path = Path("models/yolov8n.pt")
    if not model_path.exists():
        print("❌ YOLOv8n model not found. Downloading...")
        try:
            from ultralytics import YOLO
            model = YOLO('yolov8n.pt')
            print("✅ YOLOv8n model downloaded")
        except Exception as e:
            print(f"❌ Failed to download model: {e}")
            return False
    
    # Copy to SkyGuard model location
    skyguard_model = Path("models/raptor_detector.pt")
    shutil.copy2(model_path, skyguard_model)
    print(f"✅ Model copied to {skyguard_model}")
    
    # Update configuration
    update_config_for_model(skyguard_model)
    
    return True

def update_config_for_model(model_path: Path):
    """Update SkyGuard configuration to use the model."""
    print("🔧 Updating SkyGuard configuration...")
    
    try:
        import yaml
        
        config_path = Path("config/skyguard.yaml")
        if not config_path.exists():
            print("⚠️  Config file not found, creating default...")
            create_default_config()
            return
        
        # Load config
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Update model settings
        config['ai']['model_path'] = str(model_path)
        config['ai']['model_type'] = 'yolo'
        config['ai']['confidence_threshold'] = 0.5
        config['ai']['classes'] = [
            'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat',
            'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat',
            'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack',
            'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball',
            'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket',
            'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
            'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake',
            'chair', 'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop',
            'mouse', 'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink',
            'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier', 'toothbrush'
        ]
        
        # Save updated config
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
        
        print("✅ Configuration updated successfully")
        
    except Exception as e:
        print(f"❌ Failed to update configuration: {e}")

def create_default_config():
    """Create default configuration if it doesn't exist."""
    from skyguard.core.config_manager import ConfigManager
    
    config_manager = ConfigManager("config/skyguard.yaml")
    config_manager._create_default_config()
    config_manager.save_config()
    print("✅ Default configuration created")

def test_model():
    """Test the model with SkyGuard."""
    print("🧪 Testing model integration...")
    
    try:
        from skyguard.core.detector import RaptorDetector
        from skyguard.core.config_manager import ConfigManager
        
        # Load config
        config_manager = ConfigManager("config/skyguard.yaml")
        config = config_manager.get_config()
        
        # Test detector
        detector = RaptorDetector(config['ai'])
        success = detector.load_model()
        
        if success:
            print("✅ Model loaded successfully")
            
            # Test with dummy detection
            import numpy as np
            dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            detections = detector.detect(dummy_frame)
            
            print(f"✅ Detection test passed - {len(detections)} detections")
            return True
        else:
            print("❌ Model loading failed")
            return False
            
    except Exception as e:
        print(f"❌ Model test failed: {e}")
        return False

def main():
    """Main setup function."""
    print("🚀 SkyGuard Model Setup")
    print("=" * 40)
    
    # Setup pre-trained model
    if not setup_pre_trained_model():
        print("❌ Model setup failed")
        sys.exit(1)
    
    # Test the model
    if not test_model():
        print("❌ Model test failed")
        sys.exit(1)
    
    print("\n🎉 Model setup complete!")
    print("📊 SkyGuard is now ready with AI detection")
    print("\nNext steps:")
    print("1. Run: python -m skyguard.main")
    print("2. Test with your camera")
    print("3. Adjust confidence threshold in config if needed")

if __name__ == "__main__":
    main()
