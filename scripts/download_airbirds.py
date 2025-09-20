#!/usr/bin/env python3
"""
Download and setup AirBirds dataset for SkyGuard training
"""

import os
import sys
import requests
import zipfile
from pathlib import Path
import shutil

def download_file(url, filename):
    """Download a file with progress bar."""
    print(f"Downloading {filename}...")
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    with open(filename, 'wb') as file:
        downloaded = 0
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                file.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    percent = (downloaded / total_size) * 100
                    print(f"\rProgress: {percent:.1f}%", end='', flush=True)
    print(f"\n✅ Downloaded {filename}")

def extract_zip(zip_path, extract_to):
    """Extract zip file to directory."""
    print(f"Extracting {zip_path}...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    print(f"✅ Extracted to {extract_to}")

def setup_airbirds_dataset():
    """Download and setup AirBirds dataset."""
    
    # Create directories
    data_dir = Path("data/airbirds")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # AirBirds dataset URLs (these are the actual download links)
    # Note: These URLs might need to be updated based on the actual Hugging Face dataset structure
    dataset_urls = {
        "images0.zip": "https://huggingface.co/datasets/auniquesun/AirBirds/resolve/main/images0.zip",
        "images1.zip": "https://huggingface.co/datasets/auniquesun/AirBirds/resolve/main/images1.zip", 
        "images2.zip": "https://huggingface.co/datasets/auniquesun/AirBirds/resolve/main/images2.zip",
        "images3.zip": "https://huggingface.co/datasets/auniquesun/AirBirds/resolve/main/images3.zip",
        "images4.zip": "https://huggingface.co/datasets/auniquesun/AirBirds/resolve/main/images4.zip",
        "labels0.zip": "https://huggingface.co/datasets/auniquesun/AirBirds/resolve/main/labels0.zip",
        "labels1.zip": "https://huggingface.co/datasets/auniquesun/AirBirds/resolve/main/labels1.zip",
        "labels2.zip": "https://huggingface.co/datasets/auniquesun/AirBirds/resolve/main/labels2.zip",
        "labels3.zip": "https://huggingface.co/datasets/auniquesun/AirBirds/resolve/main/labels3.zip",
        "labels4.zip": "https://huggingface.co/datasets/auniquesun/AirBirds/resolve/main/labels4.zip",
    }
    
    print("🦅 Setting up AirBirds dataset for SkyGuard...")
    print("=" * 50)
    
    # Download training data (first 5 sets for faster download)
    for filename, url in dataset_urls.items():
        file_path = data_dir / filename
        
        if file_path.exists():
            print(f"⏭️  {filename} already exists, skipping...")
            continue
            
        try:
            download_file(url, file_path)
            extract_zip(file_path, data_dir)
            # Remove zip file to save space
            file_path.unlink()
        except Exception as e:
            print(f"❌ Failed to download {filename}: {e}")
            continue
    
    # Organize the dataset structure
    organize_dataset(data_dir)
    
    print("\n🎉 AirBirds dataset setup complete!")
    print(f"📁 Dataset location: {data_dir}")
    print("📊 Ready for training with SkyGuard!")

def organize_dataset(data_dir):
    """Organize the dataset into proper YOLO format."""
    print("\n📁 Organizing dataset structure...")
    
    # Create YOLO format directories
    yolo_dir = data_dir / "yolo_format"
    yolo_dir.mkdir(exist_ok=True)
    
    (yolo_dir / "images" / "train").mkdir(parents=True, exist_ok=True)
    (yolo_dir / "images" / "val").mkdir(parents=True, exist_ok=True)
    (yolo_dir / "labels" / "train").mkdir(parents=True, exist_ok=True)
    (yolo_dir / "labels" / "val").mkdir(parents=True, exist_ok=True)
    
    # Move images and labels to YOLO format
    for i in range(5):  # First 5 sets for training
        images_dir = data_dir / f"images{i}"
        labels_dir = data_dir / f"labels{i}"
        
        if images_dir.exists():
            # Move 80% to train, 20% to val
            images = list(images_dir.glob("*.jpg"))
            split_idx = int(len(images) * 0.8)
            
            # Move training images
            for img in images[:split_idx]:
                shutil.move(str(img), yolo_dir / "images" / "train")
            
            # Move validation images
            for img in images[split_idx:]:
                shutil.move(str(img), yolo_dir / "images" / "val")
            
            # Remove empty directory
            images_dir.rmdir()
        
        if labels_dir.exists():
            # Move corresponding labels
            labels = list(labels_dir.glob("*.txt"))
            split_idx = int(len(labels) * 0.8)
            
            # Move training labels
            for label in labels[:split_idx]:
                shutil.move(str(label), yolo_dir / "labels" / "train")
            
            # Move validation labels
            for label in labels[split_idx:]:
                shutil.move(str(label), yolo_dir / "labels" / "val")
            
            # Remove empty directory
            labels_dir.rmdir()
    
    # Create dataset.yaml file
    create_dataset_yaml(yolo_dir)
    
    print("✅ Dataset organized in YOLO format")

def create_dataset_yaml(yolo_dir):
    """Create dataset.yaml file for YOLO training."""
    yaml_content = """# AirBirds Dataset for SkyGuard
path: {yolo_dir}  # dataset root dir
train: images/train  # train images (relative to 'path')
val: images/val  # val images (relative to 'path')

# Classes
nc: 1  # number of classes
names: ['bird']  # class names
""".format(yolo_dir=str(yolo_dir.absolute()))
    
    yaml_file = yolo_dir / "dataset.yaml"
    with open(yaml_file, 'w') as f:
        f.write(yaml_content)
    
    print(f"✅ Created dataset.yaml at {yaml_file}")

if __name__ == "__main__":
    try:
        setup_airbirds_dataset()
    except KeyboardInterrupt:
        print("\n❌ Download cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
