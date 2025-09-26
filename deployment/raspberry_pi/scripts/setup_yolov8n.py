#!/usr/bin/env python3
"""
Set up YOLOv8n model for immediate testing with SkyGuard.

This script configures SkyGuard to use the pre-trained YOLOv8n model
which can detect birds (including raptors) with reasonable accuracy.
"""

import sys
from pathlib import Path
import yaml

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def setup_yolov8n():
    """Set up YOLOv8n model for SkyGuard."""
    print("🤖 Setting up YOLOv8n model for SkyGuard...")
    
    try:
        from ultralytics import YOLO
        
        # Check if YOLOv8n model exists
        model_path = Path("models/yolov8n.pt")
        if not model_path.exists():
            print("Downloading YOLOv8n model...")
            model = YOLO('yolov8n.pt')
            print("✅ YOLOv8n model downloaded")
        else:
            print("✅ YOLOv8n model already exists")
        
        # Update SkyGuard configuration
        print("\n⚙️  Updating SkyGuard configuration...")
        config_path = Path("config/skyguard.yaml")
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Update AI config for YOLOv8n
            config['ai']['model_path'] = 'models/yolov8n.pt'
            config['ai']['model_type'] = 'yolo'
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
            config['ai']['confidence_threshold'] = 0.4  # Good balance for bird detection
            
            with open(config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, indent=2)
            
            print("✅ SkyGuard config updated!")
            print(f"   - Model: YOLOv8n (pre-trained)")
            print(f"   - Classes: {len(config['ai']['classes'])} (including 'bird')")
            print(f"   - Confidence threshold: {config['ai']['confidence_threshold']}")
        
        # Test the model
        print("\n🧪 Testing YOLOv8n model...")
        model = YOLO('yolov8n.pt')
        
        # Test on a sample image if available
        sample_dir = Path("data/airbirds/samples")
        if sample_dir.exists():
            sample_images = list(sample_dir.glob("*.jpg"))
            if sample_images:
                test_image = sample_images[0]
                print(f"Testing on: {test_image}")
                
                results = model(str(test_image))
                
                # Check for bird detections
                bird_detections = 0
                for result in results:
                    if result.boxes is not None:
                        for box in result.boxes:
                            class_id = int(box.cls[0].item())
                            conf = box.conf[0].item()
                            class_name = model.names[class_id]
                            
                            if class_name == 'bird' and conf > 0.4:
                                bird_detections += 1
                                print(f"   ✅ Bird detected! Confidence: {conf:.2f}")
                
                if bird_detections == 0:
                    print("   ℹ️  No birds detected in this sample (this is normal)")
        
        print("\n🎉 YOLOv8n setup complete!")
        print("\nThe model is now ready to detect birds (including raptors).")
        print("YOLOv8n can detect 80 different object classes including 'bird'.")
        print("\nNext steps:")
        print("1. Test SkyGuard: python -m skyguard.main")
        print("2. For better raptor detection, train a custom model: python scripts/train_airbirds_model.py")
        
        return True
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function."""
    print("🦅 YOLOv8n Model Setup for SkyGuard")
    print("=" * 50)
    
    success = setup_yolov8n()
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
