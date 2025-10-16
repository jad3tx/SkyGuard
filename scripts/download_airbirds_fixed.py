#!/usr/bin/env python3
"""
Fixed script to download AirBirds dataset and prepare it for SkyGuard.
Windows-compatible version without emoji characters.
"""

import os
from pathlib import Path
from datasets import load_dataset
import yaml


def main():
    """Download AirBirds dataset and create basic structure."""
    print("Downloading AirBirds dataset...")
    
    # Create data directory
    data_dir = Path("data/airbirds")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load dataset
        print("Loading dataset from Hugging Face...")
        dataset = load_dataset("auniquesun/AirBirds")
        
        print("Dataset loaded successfully!")
        print(f"   - Available splits: {list(dataset.keys())}")
        print(f"   - Test samples: {len(dataset['test'])}")
        
        # Save a few sample images for testing
        print("\nSaving sample images...")
        samples_dir = data_dir / "samples"
        samples_dir.mkdir(exist_ok=True)
        
        # Save first 5 test images as samples
        for i in range(min(5, len(dataset['test']))):
            image = dataset['test'][i]['image']
            image.save(samples_dir / f"sample_{i}.jpg")
        
        print(f"Sample images saved to {samples_dir}")
        
        # Create basic dataset info
        info = {
            'dataset_name': 'AirBirds',
            'description': 'Large-scale bird detection dataset for real-world airports',
            'source': 'https://huggingface.co/datasets/auniquesun/AirBirds',
            'available_splits': list(dataset.keys()),
            'test_samples': len(dataset['test']),
            'image_resolution': '1920x1080',
            'format': 'YOLO',
            'classes': ['bird'],
            'license': 'CC BY-NC-SA 4.0'
        }
        
        with open(data_dir / "dataset_info.yaml", 'w') as f:
            yaml.dump(info, f, default_flow_style=False)
        
        print(f"Dataset info saved to {data_dir / 'dataset_info.yaml'}")
        
        # Update SkyGuard config to use the dataset
        print("\nUpdating SkyGuard configuration...")
        config_path = Path("config/skyguard.yaml")
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Update AI config to point to a model we'll create
            config['ai']['model_path'] = 'models/airbirds_raptor_detector.pt'
            config['ai']['classes'] = ['bird']
            
            with open(config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, indent=2)
            
            print("SkyGuard config updated!")
        
        print("\nAirBirds dataset setup complete!")
        print("\nNext steps:")
        print("1. Check sample images in data/airbirds/samples/")
        print("2. Train a model: python scripts/train_airbirds_model.py")
        print("3. Or use the pre-trained YOLOv8n model for testing")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False


if __name__ == "__main__":
    main()
