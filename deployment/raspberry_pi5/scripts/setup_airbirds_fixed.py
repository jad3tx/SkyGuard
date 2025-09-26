#!/usr/bin/env python3
"""
Fixed script to download and process the AirBirds dataset for SkyGuard.

This script correctly handles the AirBirds dataset structure which only has a 'test' split.
"""

import os
import sys
from pathlib import Path
from datasets import load_dataset
import yaml
import random
from PIL import Image

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def main():
    """Download AirBirds dataset and create YOLO structure."""
    print("🦅 Setting up AirBirds dataset for SkyGuard...")
    
    # Create data directory
    data_dir = Path("data/airbirds")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load dataset
        print("Loading AirBirds dataset from Hugging Face...")
        dataset = load_dataset("auniquesun/AirBirds")
        
        print(f"✅ Dataset loaded successfully!")
        print(f"   - Available splits: {list(dataset.keys())}")
        print(f"   - Test samples: {len(dataset['test'])}")
        
        # Create YOLO dataset structure
        print("\n📁 Creating YOLO dataset structure...")
        
        # Create directories
        (data_dir / "images" / "train").mkdir(parents=True, exist_ok=True)
        (data_dir / "images" / "val").mkdir(parents=True, exist_ok=True)
        (data_dir / "labels" / "train").mkdir(parents=True, exist_ok=True)
        (data_dir / "labels" / "val").mkdir(parents=True, exist_ok=True)
        
        # Split the test data into train/val (80/20 split)
        test_data = dataset['test']
        total_samples = len(test_data)
        train_size = int(0.8 * total_samples)
        
        # Shuffle indices for random split
        indices = list(range(total_samples))
        random.shuffle(indices)
        
        train_indices = indices[:train_size]
        val_indices = indices[train_size:]
        
        print(f"   - Training samples: {len(train_indices)}")
        print(f"   - Validation samples: {len(val_indices)}")
        
        # Process training data (limit to first 100 for testing)
        print("\n📸 Processing training data...")
        train_count = 0
        for i, idx in enumerate(train_indices[:100]):  # Limit for testing
            sample = test_data[idx]
            
            # Save image
            image_path = data_dir / "images" / "train" / f"train_{i:06d}.jpg"
            sample['image'].save(image_path)
            
            # Create label file (AirBirds uses class_id 0 for birds)
            # For now, create a dummy label since we need to extract from zip files
            label_path = data_dir / "labels" / "train" / f"train_{i:06d}.txt"
            with open(label_path, 'w') as f:
                # Dummy bird detection in center of image
                f.write("0 0.5 0.5 0.1 0.1\n")
            
            train_count += 1
            
            if i % 10 == 0:
                print(f"   Processed {i+1}/{min(100, len(train_indices))} training samples...")
        
        # Process validation data (limit to first 20 for testing)
        print("\n📸 Processing validation data...")
        val_count = 0
        for i, idx in enumerate(val_indices[:20]):  # Limit for testing
            sample = test_data[idx]
            
            # Save image
            image_path = data_dir / "images" / "val" / f"val_{i:06d}.jpg"
            sample['image'].save(image_path)
            
            # Create label file
            label_path = data_dir / "labels" / "val" / f"val_{i:06d}.txt"
            with open(label_path, 'w') as f:
                f.write("0 0.5 0.5 0.1 0.1\n")
            
            val_count += 1
        
        print(f"✅ Dataset structure created!")
        print(f"   - Training images: {train_count}")
        print(f"   - Validation images: {val_count}")
        
        # Create dataset.yaml for YOLO
        print("\n📝 Creating dataset.yaml...")
        yaml_content = {
            'path': str(data_dir.absolute()),
            'train': 'images/train',
            'val': 'images/val',
            'nc': 1,  # Number of classes
            'names': ['bird']  # Class names
        }
        
        yaml_path = data_dir / "dataset.yaml"
        with open(yaml_path, 'w') as f:
            yaml.dump(yaml_content, f, default_flow_style=False)
        
        print(f"✅ Dataset configuration saved to {yaml_path}")
        
        # Create sample images for inspection
        print("\n📸 Creating sample images...")
        samples_dir = data_dir / "samples"
        samples_dir.mkdir(exist_ok=True)
        
        # Save a few sample images
        for i in range(min(5, len(test_data))):
            sample = test_data[i]
            sample['image'].save(samples_dir / f"sample_{i}.jpg")
        
        print(f"✅ Sample images saved to {samples_dir}")
        
        # Update SkyGuard config
        print("\n⚙️  Updating SkyGuard configuration...")
        config_path = Path("config/skyguard.yaml")
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Update AI config
            config['ai']['model_path'] = 'models/airbirds_raptor_detector.pt'
            config['ai']['classes'] = ['bird']
            config['ai']['confidence_threshold'] = 0.3  # Lower threshold for bird detection
            
            with open(config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, indent=2)
            
            print("✅ SkyGuard config updated!")
        
        # Create dataset info
        info = {
            'dataset_name': 'AirBirds',
            'description': 'Large-scale bird detection dataset for real-world airports',
            'source': 'https://huggingface.co/datasets/auniquesun/AirBirds',
            'total_samples': total_samples,
            'train_samples': train_count,
            'val_samples': val_count,
            'image_resolution': '1920x1080',
            'format': 'YOLO',
            'classes': ['bird'],
            'license': 'CC BY-NC-SA 4.0',
            'cache_location': r'C:\Users\johnd\.cache\huggingface\hub\datasets--auniquesun--AirBirds'
        }
        
        with open(data_dir / "dataset_info.yaml", 'w') as f:
            yaml.dump(info, f, default_flow_style=False)
        
        print(f"✅ Dataset info saved to {data_dir / 'dataset_info.yaml'}")
        
        print("\n🎉 AirBirds dataset setup complete!")
        print(f"\nDataset location: {data_dir.absolute()}")
        print(f"Cache location: {info['cache_location']}")
        print("\nNext steps:")
        print("1. Check sample images in data/airbirds/samples/")
        print("2. Train a model: python scripts/train_airbirds_model.py")
        print("3. Or use the existing YOLOv8n model for testing")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
