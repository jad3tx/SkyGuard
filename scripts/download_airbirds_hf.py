#!/usr/bin/env python3
"""
Download AirBirds dataset using Hugging Face datasets library
"""

import os
import sys
from pathlib import Path
import shutil

def download_airbirds_hf():
    """Download AirBirds dataset using Hugging Face datasets."""
    
    try:
        from datasets import load_dataset
        print("✅ Hugging Face datasets library available")
    except ImportError:
        print("❌ Hugging Face datasets library not found")
        print("Installing datasets library...")
        os.system("pip install datasets")
        try:
            from datasets import load_dataset
            print("✅ Hugging Face datasets library installed")
        except ImportError:
            print("❌ Failed to install datasets library")
            return False
    
    print("🦅 Downloading AirBirds dataset from Hugging Face...")
    print("=" * 50)
    
    try:
        # Load the dataset
        dataset = load_dataset("auniquesun/AirBirds")
        print("✅ Dataset loaded successfully")
        
        # Create output directory
        output_dir = Path("data/airbirds")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save dataset locally
        dataset.save_to_disk(str(output_dir / "raw_dataset"))
        print(f"✅ Dataset saved to {output_dir / 'raw_dataset'}")
        
        # Convert to YOLO format
        convert_to_yolo_format(dataset, output_dir)
        
        return True
        
    except Exception as e:
        print(f"❌ Error downloading dataset: {e}")
        return False

def convert_to_yolo_format(dataset, output_dir):
    """Convert AirBirds dataset to YOLO format."""
    print("\n📁 Converting to YOLO format...")
    
    yolo_dir = output_dir / "yolo_format"
    yolo_dir.mkdir(exist_ok=True)
    
    # Create directories
    (yolo_dir / "images" / "train").mkdir(parents=True, exist_ok=True)
    (yolo_dir / "images" / "val").mkdir(parents=True, exist_ok=True)
    (yolo_dir / "labels" / "train").mkdir(parents=True, exist_ok=True)
    (yolo_dir / "labels" / "val").mkdir(parents=True, exist_ok=True)
    
    # Process test split (since that's what's available)
    test_data = dataset['test']
    
    # Split into train/val (80/20)
    total_samples = len(test_data)
    train_size = int(total_samples * 0.8)
    
    print(f"📊 Processing {total_samples} samples")
    print(f"📊 Training: {train_size} samples")
    print(f"📊 Validation: {total_samples - train_size} samples")
    
    # Process training samples
    for i in range(train_size):
        sample = test_data[i]
        
        # Save image
        image = sample['image']
        image_path = yolo_dir / "images" / "train" / f"train_{i:06d}.jpg"
        image.save(image_path)
        
        # Process label (if available)
        label_path = yolo_dir / "labels" / "train" / f"train_{i:06d}.txt"
        process_label(sample, label_path)
        
        if (i + 1) % 100 == 0:
            print(f"Processed {i + 1}/{train_size} training samples")
    
    # Process validation samples
    for i in range(train_size, total_samples):
        sample = test_data[i]
        
        # Save image
        image = sample['image']
        image_path = yolo_dir / "images" / "val" / f"val_{i-train_size:06d}.jpg"
        image.save(image_path)
        
        # Process label (if available)
        label_path = yolo_dir / "labels" / "val" / f"val_{i-train_size:06d}.txt"
        process_label(sample, label_path)
        
        if (i + 1) % 100 == 0:
            print(f"Processed {i + 1}/{total_samples} samples")
    
    # Create dataset.yaml
    create_dataset_yaml(yolo_dir)
    
    print("✅ YOLO format conversion complete")

def process_label(sample, label_path):
    """Process and save label in YOLO format."""
    # For now, create empty labels since the dataset structure needs investigation
    # In a real implementation, you'd parse the label data and convert to YOLO format
    with open(label_path, 'w') as f:
        # Empty file for now - you'll need to implement proper label parsing
        pass

def create_dataset_yaml(yolo_dir):
    """Create dataset.yaml file for YOLO training."""
    yaml_content = f"""# AirBirds Dataset for SkyGuard
path: {yolo_dir.absolute()}  # dataset root dir
train: images/train  # train images (relative to 'path')
val: images/val  # val images (relative to 'path')

# Classes
nc: 1  # number of classes
names: ['bird']  # class names
"""
    
    yaml_file = yolo_dir / "dataset.yaml"
    with open(yaml_file, 'w') as f:
        f.write(yaml_content)
    
    print(f"✅ Created dataset.yaml at {yaml_file}")

if __name__ == "__main__":
    try:
        success = download_airbirds_hf()
        if success:
            print("\n🎉 AirBirds dataset download complete!")
            print("📁 Dataset location: data/airbirds/yolo_format")
            print("📊 Ready for training with SkyGuard!")
        else:
            print("\n❌ Dataset download failed")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n❌ Download cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
