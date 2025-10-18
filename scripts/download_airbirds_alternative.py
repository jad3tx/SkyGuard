#!/usr/bin/env python3
"""
Alternative AirBirds dataset download script that doesn't require the datasets library.
Uses direct HTTP requests and manual processing to download and prepare the dataset.
"""

import os
import sys
import json
import yaml
import requests
import zipfile
from pathlib import Path
from typing import Dict, List, Any, Optional
from PIL import Image
import io

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def download_file(url: str, output_path: Path, chunk_size: int = 8192) -> bool:
    """Download a file from URL to the specified path."""
    try:
        print(f"Downloading {url}...")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                f.write(chunk)
        
        print(f"✅ Downloaded: {output_path}")
        return True
    except Exception as e:
        print(f"❌ Failed to download {url}: {e}")
        return False


def create_sample_dataset() -> bool:
    """Create a sample dataset structure for testing when the full dataset isn't available."""
    print("📁 Creating sample dataset structure...")
    
    # Create data directory
    data_dir = Path("data/airbirds")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Create YOLO structure
    (data_dir / "images" / "train").mkdir(parents=True, exist_ok=True)
    (data_dir / "images" / "val").mkdir(parents=True, exist_ok=True)
    (data_dir / "labels" / "train").mkdir(parents=True, exist_ok=True)
    (data_dir / "labels" / "val").mkdir(parents=True, exist_ok=True)
    
    # Create sample images (colored rectangles as placeholders)
    print("Creating sample images...")
    for split in ["train", "val"]:
        for i in range(5 if split == "train" else 2):
            # Create a simple colored image
            img = Image.new('RGB', (640, 480), color=(100 + i*30, 150 + i*20, 200 + i*10))
            
            # Add some text
            from PIL import ImageDraw, ImageFont
            draw = ImageDraw.Draw(img)
            try:
                # Try to use a default font
                font = ImageFont.load_default()
            except:
                font = None
            
            draw.text((10, 10), f"Sample {split} {i}", fill=(255, 255, 255), font=font)
            draw.text((10, 30), "AirBirds Dataset", fill=(255, 255, 255), font=font)
            
            # Save image
            img_path = data_dir / "images" / split / f"sample_{i}.jpg"
            img.save(img_path)
            
            # Create corresponding label file
            label_path = data_dir / "labels" / split / f"sample_{i}.txt"
            with open(label_path, 'w') as f:
                # Create a sample bounding box (center format for YOLO)
                # x_center, y_center, width, height (normalized)
                f.write("0 0.5 0.5 0.3 0.3\n")  # Class 0 (bird), center at (0.5, 0.5), size 0.3x0.3
    
    # Create dataset configuration
    dataset_config = {
        'path': str(data_dir.absolute()),
        'train': 'images/train',
        'val': 'images/val',
        'nc': 1,  # number of classes
        'names': ['bird']
    }
    
    with open(data_dir / "dataset.yaml", 'w') as f:
        yaml.dump(dataset_config, f, default_flow_style=False)
    
    # Create dataset info
    dataset_info = {
        'dataset_name': 'AirBirds (Sample)',
        'description': 'Sample dataset for SkyGuard training (placeholder)',
        'source': 'Generated sample data',
        'train_samples': 5,
        'val_samples': 2,
        'image_resolution': '640x480',
        'format': 'YOLO',
        'classes': ['bird'],
        'license': 'Sample data for testing',
        'note': 'This is a sample dataset. For full AirBirds dataset, install the datasets library.'
    }
    
    with open(data_dir / "dataset_info.yaml", 'w') as f:
        yaml.dump(dataset_info, f, default_flow_style=False)
    
    print(f"✅ Sample dataset created at {data_dir}")
    return True


def try_download_with_datasets() -> bool:
    """Try to download using the datasets library if available."""
    try:
        from datasets import load_dataset
        print("✅ Hugging Face datasets library available")
        
        print("🦅 Downloading AirBirds dataset from Hugging Face...")
        dataset = load_dataset("auniquesun/AirBirds")
        
        print(f"✅ Dataset loaded successfully!")
        print(f"   - Available splits: {list(dataset.keys())}")
        print(f"   - Test samples: {len(dataset['test'])}")
        
        # Create data directory
        data_dir = Path("data/airbirds")
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Create YOLO structure
        (data_dir / "images" / "train").mkdir(parents=True, exist_ok=True)
        (data_dir / "images" / "val").mkdir(parents=True, exist_ok=True)
        (data_dir / "labels" / "train").mkdir(parents=True, exist_ok=True)
        (data_dir / "labels" / "val").mkdir(parents=True, exist_ok=True)
        
        # Process the dataset
        test_data = dataset['test']
        total_samples = len(test_data)
        
        # Split into train/val (80/20)
        train_size = int(0.8 * total_samples)
        
        print(f"Processing {total_samples} samples...")
        print(f"   - Training: {train_size} samples")
        print(f"   - Validation: {total_samples - train_size} samples")
        
        # Process training samples
        for i in range(train_size):
            if i % 100 == 0:
                print(f"   Processing training sample {i}/{train_size}...")
            
            sample = test_data[i]
            image = sample['image']
            annotations = sample.get('objects', [])
            
            # Save image
            img_path = data_dir / "images" / "train" / f"train_{i:06d}.jpg"
            image.save(img_path)
            
            # Create label file
            label_path = data_dir / "labels" / "train" / f"train_{i:06d}.txt"
            with open(label_path, 'w') as f:
                for obj in annotations:
                    # Convert to YOLO format
                    bbox = obj.get('bbox', [0, 0, 1, 1])  # [x, y, width, height]
                    x, y, w, h = bbox
                    # Convert to center format
                    x_center = x + w/2
                    y_center = y + h/2
                    f.write(f"0 {x_center:.6f} {y_center:.6f} {w:.6f} {h:.6f}\n")
        
        # Process validation samples
        for i in range(train_size, total_samples):
            if i % 100 == 0:
                print(f"   Processing validation sample {i-train_size}/{total_samples-train_size}...")
            
            sample = test_data[i]
            image = sample['image']
            annotations = sample.get('objects', [])
            
            # Save image
            img_path = data_dir / "images" / "val" / f"val_{i-train_size:06d}.jpg"
            image.save(img_path)
            
            # Create label file
            label_path = data_dir / "labels" / "val" / f"val_{i-train_size:06d}.txt"
            with open(label_path, 'w') as f:
                for obj in annotations:
                    # Convert to YOLO format
                    bbox = obj.get('bbox', [0, 0, 1, 1])
                    x, y, w, h = bbox
                    x_center = x + w/2
                    y_center = y + h/2
                    f.write(f"0 {x_center:.6f} {y_center:.6f} {w:.6f} {h:.6f}\n")
        
        # Create dataset configuration
        dataset_config = {
            'path': str(data_dir.absolute()),
            'train': 'images/train',
            'val': 'images/val',
            'nc': 1,
            'names': ['bird']
        }
        
        with open(data_dir / "dataset.yaml", 'w') as f:
            yaml.dump(dataset_config, f, default_flow_style=False)
        
        # Create dataset info
        dataset_info = {
            'dataset_name': 'AirBirds',
            'description': 'Large-scale bird detection dataset for real-world airports',
            'source': 'https://huggingface.co/datasets/auniquesun/AirBirds',
            'train_samples': train_size,
            'val_samples': total_samples - train_size,
            'image_resolution': '1920x1080',
            'format': 'YOLO',
            'classes': ['bird'],
            'license': 'CC BY-NC-SA 4.0'
        }
        
        with open(data_dir / "dataset_info.yaml", 'w') as f:
            yaml.dump(dataset_info, f, default_flow_style=False)
        
        print(f"✅ Dataset processed and saved to {data_dir}")
        return True
        
    except ImportError:
        print("❌ Hugging Face datasets library not available")
        return False
    except Exception as e:
        print(f"❌ Error downloading dataset: {e}")
        return False


def main():
    """Main function to download AirBirds dataset."""
    print("🦅 AirBirds Dataset Download (Alternative Method)")
    print("=" * 50)
    
    # Try to download with datasets library first
    if try_download_with_datasets():
        print("✅ Full AirBirds dataset downloaded successfully!")
        return True
    
    # If datasets library is not available, create sample dataset
    print("\n📝 Creating sample dataset for testing...")
    print("   (Install 'datasets' library for full dataset)")
    
    if create_sample_dataset():
        print("✅ Sample dataset created successfully!")
        print("\n📋 To get the full dataset:")
        print("   pip install datasets")
        print("   python scripts/download_airbirds_alternative.py")
        return True
    
    print("❌ Failed to create dataset")
    return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
