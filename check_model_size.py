#!/usr/bin/env python3
"""Check which model size is being used."""

from skyguard.core.detector import RaptorDetector
from skyguard.core.config_manager import ConfigManager
from ultralytics import YOLO

# Load config and detector
cfg = ConfigManager('config/skyguard.yaml').get_config()
det = RaptorDetector(cfg.get('ai', {}))
det.load_model()

print("=" * 60)
print("Model Information")
print("=" * 60)

# Detection model
print("\n📦 Detection Model (Segmentation):")
print(f"   Path: {cfg['ai']['model_path']}")
print(f"   Type: yolo11n-seg.pt (nano size - for fast detection)")

# Species model
print("\n🐦 Species Classification Model:")
print(f"   Path: {det.species_model_path}")
print(f"   Loaded: {det.species_model is not None}")

if det.species_model:
    # Get model info
    try:
        info = det.species_model.info()
        print(f"   Summary: {info}")
        
        # Try to get model architecture info
        if hasattr(det.species_model, 'model'):
            model_str = str(det.species_model.model)
            if 'YOLO11s' in model_str or 'yolo11s' in model_str:
                print("   ✅ Model size: SMALL (s) - Correct!")
            elif 'YOLO11n' in model_str or 'yolo11n' in model_str:
                print("   ⚠️  Model size: NANO (n) - This is wrong!")
            else:
                print(f"   Model type: {model_str[:100]}...")
    except Exception as e:
        print(f"   Error getting info: {e}")
    
    # Check the actual file
    try:
        import torch
        ckpt = torch.load(det.species_model_path, map_location='cpu', weights_only=False)
        if 'train_args' in ckpt:
            train_model = ckpt['train_args'].get('model', 'unknown')
            print(f"   Training model: {train_model}")
            if 'yolo11s' in train_model.lower():
                print("   ✅ Confirmed: Model was trained with YOLO11s (small)")
            elif 'yolo11n' in train_model.lower():
                print("   ⚠️  WARNING: Model was trained with YOLO11n (nano)")
        
        if 'model' in ckpt and hasattr(ckpt['model'], 'yaml'):
            yaml_data = ckpt['model'].yaml
            if isinstance(yaml_data, dict):
                scale = yaml_data.get('scale', 'unknown')
                print(f"   Architecture scale: {scale}")
                if scale == 's':
                    print("   ✅ Confirmed: Architecture is SMALL (s)")
                elif scale == 'n':
                    print("   ⚠️  WARNING: Architecture is NANO (n)")
    except Exception as e:
        print(f"   Error checking file: {e}")

print("\n" + "=" * 60)
print("Note: The detection model (yolo11n-seg.pt) is SUPPOSED to be")
print("nano size for fast detection. The species model should be")
print("small (s) size for better accuracy.")
print("=" * 60)

