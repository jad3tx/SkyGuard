#!/usr/bin/env python3
"""
Simple NABirds dataset preparation when label files are missing.

This script organizes NABirds images by their numeric class IDs into
train/val splits for YOLO classification training.
"""

import sys
import random
import shutil
import argparse
from pathlib import Path
from typing import Dict, List
import yaml

# Add the project root to the Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def prepare_nabirds_simple(
    nabirds_root: Path,
    output_dir: Path,
    val_split_ratio: float = 0.2,
) -> bool:
    """Prepare NABirds dataset from images organized by numeric class IDs.
    
    Args:
        nabirds_root: Root directory containing images/ subdirectory
        output_dir: Output directory for YOLO format dataset
        val_split_ratio: Ratio of data to use for validation (0.0-1.0)
        
    Returns:
        True if successful, False otherwise
    """
    images_dir = nabirds_root / "images"
    if not images_dir.exists():
        print(f"[ERROR] Images directory not found: {images_dir}")
        return False
    
    # Set random seed for reproducibility
    random.seed(42)
    
    # Create output directories
    train_dir = output_dir / "train"
    val_dir = output_dir / "val"
    
    train_dir.mkdir(parents=True, exist_ok=True)
    val_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all class directories (numeric IDs)
    class_dirs = [d for d in images_dir.iterdir() if d.is_dir()]
    
    if not class_dirs:
        print(f"[ERROR] No class directories found in {images_dir}")
        return False
    
    print(f"[INFO] Found {len(class_dirs)} class directories")
    
    # Track statistics
    stats = {
        'classes': {},
        'total_samples': 0,
        'train_samples': 0,
        'val_samples': 0,
    }
    
    # Process each class
    for class_dir in sorted(class_dirs):
        class_id = class_dir.name
        print(f"   Processing class: {class_id}")
        
        # Find all images in this class directory
        image_files = []
        for ext in ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']:
            image_files.extend(class_dir.glob(f"*{ext}"))
        
        if not image_files:
            print(f"      [WARNING] No images found in {class_id}")
            continue
        
        # Shuffle and split
        random.shuffle(image_files)
        split_idx = int(len(image_files) * (1 - val_split_ratio))
        train_images = image_files[:split_idx]
        val_images = image_files[split_idx:]
        
        # Create class directories in output
        train_class_dir = train_dir / class_id
        val_class_dir = val_dir / class_id
        
        train_class_dir.mkdir(parents=True, exist_ok=True)
        val_class_dir.mkdir(parents=True, exist_ok=True)
        
        # Copy train images
        for img_path in train_images:
            dest_path = train_class_dir / img_path.name
            if not dest_path.exists():
                shutil.copy2(img_path, dest_path)
        
        # Copy val images
        for img_path in val_images:
            dest_path = val_class_dir / img_path.name
            if not dest_path.exists():
                shutil.copy2(img_path, dest_path)
        
        # Update statistics
        stats['classes'][class_id] = {
            'train': len(train_images),
            'val': len(val_images),
            'total': len(image_files),
        }
        stats['total_samples'] += len(image_files)
        stats['train_samples'] += len(train_images)
        stats['val_samples'] += len(val_images)
        
        print(f"      {len(train_images)} train, {len(val_images)} val")
    
    # Create dataset info
    class_names = sorted(stats['classes'].keys())
    
    info = {
        'dataset_name': 'NABirds (Simple - Numeric IDs)',
        'source': 'NABirds dataset (organized by numeric class IDs)',
        'format': 'YOLO Classification',
        'num_classes': len(class_names),
        'total_samples': stats['total_samples'],
        'train_samples': stats['train_samples'],
        'val_samples': stats['val_samples'],
        'classes': class_names,
        'path': str(output_dir.resolve()),
        'note': 'Class names are numeric IDs. Label files (classes.txt) not available.',
    }
    
    # Save YAML
    info_path = output_dir / "dataset_info.yaml"
    with open(info_path, 'w', encoding='utf-8') as f:
        yaml.dump(info, f, default_flow_style=False, indent=2, allow_unicode=True)
    
    print(f"\n[INFO] Dataset info saved to: {info_path}")
    print(f"   Classes: {len(class_names)}")
    print(f"   Train: {stats['train_samples']}, Val: {stats['val_samples']}")
    
    print(f"\n[OK] NABirds dataset prepared at: {output_dir}")
    return True


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Prepare NABirds dataset (simple version without label files)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--nabirds-root",
        required=True,
        help="Root directory of NABirds dataset (contains images/ subdirectory)",
    )
    parser.add_argument(
        "--output-dir",
        default=str(PROJECT_ROOT / "data" / "nabirds_prepared"),
        help="Output directory for YOLO format dataset",
    )
    parser.add_argument(
        "--val-split",
        type=float,
        default=0.2,
        dest="val_split_ratio",
        help="Ratio of data to use for validation (0.0-1.0, default: 0.2)",
    )
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Run non-interactively",
    )
    
    args = parser.parse_args()
    
    nabirds_root = Path(args.nabirds_root)
    output_dir = Path(args.output_dir)
    
    print("=" * 60)
    print("NABirds Dataset Preparation (Simple)")
    print("=" * 60)
    print(f"NABirds root: {nabirds_root}")
    print(f"Output: {output_dir}")
    print(f"Validation split: {args.val_split_ratio * 100:.1f}%")
    print()
    
    if not args.yes:
        try:
            response = input("Do you want to proceed? (y/N): ").strip().lower()
        except EOFError:
            response = "n"
        if response not in ["y", "yes"]:
            print("Cancelled.")
            return 0
    
    success = prepare_nabirds_simple(
        nabirds_root=nabirds_root,
        output_dir=output_dir,
        val_split_ratio=args.val_split_ratio,
    )
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

