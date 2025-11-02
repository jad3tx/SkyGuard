#!/usr/bin/env python3
"""
Convert NABirds dataset to YOLO classification format for SkyGuard.

This script reads NABirds label files and organizes images by class
into train/val/test splits for YOLO classification training.
"""

import sys
from pathlib import Path
from typing import Dict, Tuple, Optional
import shutil
from collections import defaultdict

# Add the project root to the Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def load_classes(classes_file: Path) -> Dict[str, str]:
    """Load class ID to class name mapping.
    
    Args:
        classes_file: Path to classes.txt
        
    Returns:
        Dictionary mapping class_id -> class_name
    """
    classes = {}
    with open(classes_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(' ', 1)
            if len(parts) >= 2:
                class_id = parts[0]
                class_name = parts[1]
                classes[class_id] = class_name
    return classes


def load_image_labels(labels_file: Path) -> Dict[str, str]:
    """Load image ID to class ID mapping.
    
    Args:
        labels_file: Path to image_class_labels.txt
        
    Returns:
        Dictionary mapping image_id -> class_id
    """
    labels = {}
    with open(labels_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 2:
                image_id = parts[0]
                class_id = parts[1]
                labels[image_id] = class_id
    return labels


def load_image_paths(images_file: Path) -> Dict[str, str]:
    """Load image ID to image path mapping.
    
    Args:
        images_file: Path to images.txt
        
    Returns:
        Dictionary mapping image_id -> relative_path
    """
    paths = {}
    with open(images_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(' ', 1)
            if len(parts) >= 2:
                image_id = parts[0]
                rel_path = parts[1]
                paths[image_id] = rel_path
    return paths


def load_train_test_split(split_file: Path) -> Dict[str, int]:
    """Load train/test split.
    
    Args:
        split_file: Path to train_test_split.txt
        
    Returns:
        Dictionary mapping image_id -> 1 (train) or 0 (test)
    """
    splits = {}
    with open(split_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 2:
                image_id = parts[0]
                is_train = int(parts[1])
                splits[image_id] = is_train
    return splits


def prepare_nabirds_dataset(
    nabirds_root: Path,
    output_dir: Path,
    val_split_ratio: float = 0.2,
    create_symlinks: bool = False,
) -> bool:
    """Prepare NABirds dataset for YOLO classification training.
    
    Args:
        nabirds_root: Root directory of NABirds dataset (contains nabirds/ subdirectory)
        output_dir: Output directory for YOLO format dataset
        val_split_ratio: Ratio of training data to use for validation (0.0-1.0)
        create_symlinks: If True, create symlinks instead of copying files (faster, requires admin on Windows)
        
    Returns:
        True if successful, False otherwise
    """
    nabirds_dir = nabirds_root / "nabirds"
    if not nabirds_dir.exists():
        # Try if nabirds_root already points to nabirds directory
        if (nabirds_root / "images.txt").exists():
            nabirds_dir = nabirds_root
        else:
            print(f"[ERROR] NABirds directory not found: {nabirds_dir}")
            print("   Expected structure: <nabirds_root>/nabirds/ or <nabirds_root> contains label files")
            return False
    
    # Load label files
    print("[INFO] Loading NABirds label files...")
    
    classes_file = nabirds_dir / "classes.txt"
    labels_file = nabirds_dir / "image_class_labels.txt"
    images_file = nabirds_dir / "images.txt"
    split_file = nabirds_dir / "train_test_split.txt"
    
    if not all(f.exists() for f in [classes_file, labels_file, images_file, split_file]):
        print("[ERROR] Required label files not found:")
        for f in [classes_file, labels_file, images_file, split_file]:
            if not f.exists():
                print(f"   Missing: {f}")
        return False
    
    classes = load_classes(classes_file)
    image_labels = load_image_labels(labels_file)
    image_paths = load_image_paths(images_file)
    splits = load_train_test_split(split_file)
    
    print(f"   Loaded {len(classes)} classes")
    print(f"   Loaded {len(image_labels)} image labels")
    print(f"   Loaded {len(image_paths)} image paths")
    print(f"   Loaded {len(splits)} split assignments")
    
    # Create output directories
    train_dir = output_dir / "train"
    val_dir = output_dir / "val"
    test_dir = output_dir / "test"
    
    train_dir.mkdir(parents=True, exist_ok=True)
    val_dir.mkdir(parents=True, exist_ok=True)
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # Organize images by class and split
    print("\n[INFO] Organizing images by class and split...")
    
    # Track images per class per split
    split_images = {
        'train': defaultdict(list),
        'val': defaultdict(list),
        'test': defaultdict(list),
    }
    
    images_base = nabirds_dir / "images"
    
    processed = 0
    skipped = 0
    
    for image_id, class_id in image_labels.items():
        if image_id not in image_paths:
            skipped += 1
            continue
        
        if image_id not in splits:
            skipped += 1
            continue
        
        class_name = classes.get(class_id, f"class_{class_id}")
        # Make class name filesystem-safe
        class_name_safe = class_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
        
        # Get image path
        rel_path = image_paths[image_id]
        source_path = images_base / rel_path
        
        if not source_path.exists():
            skipped += 1
            continue
        
        # Determine split
        is_train = splits[image_id] == 1
        
        if is_train:
            # Split training data into train/val if val_split_ratio > 0
            import random
            random.seed(42)  # For reproducibility
            use_val = random.random() < val_split_ratio
            split_key = 'val' if use_val else 'train'
        else:
            split_key = 'test'
        
        split_images[split_key][class_name_safe].append((image_id, source_path))
        processed += 1
        
        if processed % 1000 == 0:
            print(f"   Processed {processed} images...")
    
    print(f"   Processed {processed} images, skipped {skipped}")
    
    # Copy/symlink images to output directories
    print("\n[INFO] Copying images to output directories...")
    
    copy_func = shutil.copy2 if not create_symlinks else create_symlink_safe
    
    for split_name, split_dir in [('train', train_dir), ('val', val_dir), ('test', test_dir)]:
        print(f"\n   Processing {split_name} split...")
        split_data = split_images[split_name]
        
        for class_name, image_list in split_data.items():
            class_dir = split_dir / class_name
            class_dir.mkdir(parents=True, exist_ok=True)
            
            for image_id, source_path in image_list:
                # Generate filename
                ext = source_path.suffix or '.jpg'
                filename = f"{image_id}{ext}"
                dest_path = class_dir / filename
                
                try:
                    if not dest_path.exists():
                        copy_func(source_path, dest_path)
                except Exception as e:
                    print(f"   [WARNING] Failed to copy {source_path}: {e}")
                    continue
        
        total_images = sum(len(images) for images in split_data.values())
        print(f"   [OK] {split_name}: {len(split_data)} classes, {total_images} images")
    
    # Create dataset info
    create_dataset_info(output_dir, classes, split_images)
    
    print(f"\n[OK] NABirds dataset prepared at: {output_dir}")
    return True


def create_symlink_safe(source: Path, dest: Path) -> None:
    """Create symlink with fallback to copy if symlink fails.
    
    Args:
        source: Source file path
        dest: Destination symlink path
    """
    try:
        if dest.exists() or dest.is_symlink():
            dest.unlink()
        dest.symlink_to(source.resolve())
    except (OSError, NotImplementedError):
        # Fallback to copy if symlink fails (Windows without admin)
        shutil.copy2(source, dest)


def create_dataset_info(
    output_dir: Path,
    classes: Dict[str, str],
    split_images: Dict[str, Dict[str, list]],
) -> None:
    """Create dataset info YAML file.
    
    Args:
        output_dir: Dataset directory
        classes: Class ID to name mapping
        split_images: Dictionary of split -> class -> images
    """
    import yaml
    
    # Get all class names (filesystem-safe)
    class_names = []
    for class_id, class_name in sorted(classes.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0):
        class_name_safe = class_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
        if class_name_safe not in class_names:
            class_names.append(class_name_safe)
    
    # Count samples per split
    train_count = sum(len(images) for images in split_images['train'].values())
    val_count = sum(len(images) for images in split_images['val'].values())
    test_count = sum(len(images) for images in split_images['test'].values())
    
    info = {
        'dataset_name': 'NABirds (North American Birds)',
        'source': 'http://www.vision.caltech.edu/visipedia',
        'format': 'YOLO Classification',
        'num_classes': len(class_names),
        'total_samples': train_count + val_count + test_count,
        'train_samples': train_count,
        'val_samples': val_count,
        'test_samples': test_count,
        'classes': class_names,
        'path': str(output_dir.resolve()),
    }
    
    # Save YAML
    info_path = output_dir / "dataset_info.yaml"
    with open(info_path, 'w', encoding='utf-8') as f:
        yaml.dump(info, f, default_flow_style=False, indent=2, allow_unicode=True)
    
    print(f"\n[INFO] Dataset info saved to: {info_path}")
    print(f"   Classes: {len(class_names)}")
    print(f"   Train: {train_count}, Val: {val_count}, Test: {test_count}")


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Prepare NABirds dataset for YOLO classification training",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This script converts NABirds dataset from its original format to YOLO 
classification format (organized by class in train/val/test directories).

Example usage:
  python scripts/prepare_nabirds_dataset.py --nabirds-root "d:/NABirds" --output-dir "data/bird_species"
        """
    )
    parser.add_argument(
        "--nabirds-root",
        required=True,
        help="Root directory of NABirds dataset (contains nabirds/ subdirectory or label files)",
    )
    parser.add_argument(
        "--output-dir",
        default=str(PROJECT_ROOT / "data" / "bird_species"),
        help="Output directory for YOLO format dataset",
    )
    parser.add_argument(
        "--val-split-ratio",
        type=float,
        default=0.2,
        help="Ratio of training data to use for validation (0.0-1.0, default: 0.2)",
    )
    parser.add_argument(
        "--symlinks",
        action="store_true",
        help="Create symlinks instead of copying files (faster, requires admin on Windows)",
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
    print("NABirds Dataset Preparation")
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
    
    # Prepare dataset
    success = prepare_nabirds_dataset(
        nabirds_root=nabirds_root,
        output_dir=output_dir,
        val_split_ratio=args.val_split_ratio,
        create_symlinks=args.symlinks,
    )
    
    if success:
        print("\n" + "=" * 60)
        print("[OK] Dataset preparation completed!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Train the species classification model:")
        print(f"   python scripts/train_bird_species_classifier.py --data-dir {output_dir}")
        print("\n2. Or train manually:")
        print("   from ultralytics import YOLO")
        print("   model = YOLO('yolo11n-cls.pt')")
        print(f"   model.train(data='{output_dir}', epochs=100, imgsz=224)")
        print("\n3. Update config/skyguard.yaml with the trained model path")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

