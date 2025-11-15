#!/usr/bin/env python3
"""
Merge multiple training datasets into one combined dataset.

This script merges datasets from different sources (e.g., video-extracted frames
and NABirds dataset) into a single training dataset.
"""

import sys
from pathlib import Path
from typing import Dict, List, Set
import shutil
import argparse
import yaml

# Add the project root to the Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def get_classes_from_dataset(dataset_dir: Path) -> Set[str]:
    """Get all class names from a dataset directory.
    
    Args:
        dataset_dir: Dataset directory containing train/val subdirectories
        
    Returns:
        Set of class names found in the dataset
    """
    classes = set()
    
    train_dir = dataset_dir / "train"
    val_dir = dataset_dir / "val"
    
    if train_dir.exists():
        classes.update(d.name for d in train_dir.iterdir() if d.is_dir())
    
    if val_dir.exists():
        classes.update(d.name for d in val_dir.iterdir() if d.is_dir())
    
    return classes


def merge_datasets(
    dataset_dirs: List[Path],
    output_dir: Path,
    val_split_ratio: float = 0.2,
) -> bool:
    """Merge multiple datasets into one combined dataset.
    
    Args:
        dataset_dirs: List of dataset directories to merge
        output_dir: Output directory for merged dataset
        val_split_ratio: Ratio of data to use for validation (0.0-1.0)
        
    Returns:
        True if successful, False otherwise
    """
    import random
    random.seed(42)  # For reproducibility
    
    # Create output directories
    train_dir = output_dir / "train"
    val_dir = output_dir / "val"
    
    train_dir.mkdir(parents=True, exist_ok=True)
    val_dir.mkdir(parents=True, exist_ok=True)
    
    # Track statistics
    stats = {
        'classes': {},
        'total_samples': 0,
        'train_samples': 0,
        'val_samples': 0,
        'sources': {},
    }
    
    all_classes = set()
    
    # First pass: collect all classes and count samples
    print("[INFO] Analyzing datasets...")
    for dataset_dir in dataset_dirs:
        if not dataset_dir.exists():
            print(f"   [WARNING] Dataset directory not found: {dataset_dir}")
            continue
        
        dataset_name = dataset_dir.name
        print(f"   Processing: {dataset_name}")
        
        classes = get_classes_from_dataset(dataset_dir)
        all_classes.update(classes)
        
        # Count samples per class
        for class_name in classes:
            train_class_dir = dataset_dir / "train" / class_name
            val_class_dir = dataset_dir / "val" / class_name
            
            train_count = 0
            val_count = 0
            
            if train_class_dir.exists():
                train_count = len(list(train_class_dir.glob("*.jpg"))) + \
                             len(list(train_class_dir.glob("*.png"))) + \
                             len(list(train_class_dir.glob("*.JPG"))) + \
                             len(list(train_class_dir.glob("*.PNG")))
            
            if val_class_dir.exists():
                val_count = len(list(val_class_dir.glob("*.jpg"))) + \
                           len(list(val_class_dir.glob("*.png"))) + \
                           len(list(val_class_dir.glob("*.JPG"))) + \
                           len(list(val_class_dir.glob("*.PNG")))
            
            if class_name not in stats['classes']:
                stats['classes'][class_name] = {
                    'train': 0,
                    'val': 0,
                    'sources': []
                }
            
            stats['classes'][class_name]['train'] += train_count
            stats['classes'][class_name]['val'] += val_count
            stats['classes'][class_name]['sources'].append(dataset_name)
        
        stats['sources'][dataset_name] = {
            'classes': len(classes),
            'total_samples': sum(
                stats['classes'][c]['train'] + stats['classes'][c]['val']
                for c in classes
            )
        }
    
    print(f"   Found {len(all_classes)} unique classes across all datasets")
    
    # Second pass: merge files
    print("\n[INFO] Merging datasets...")
    
    for class_name in sorted(all_classes):
        print(f"   Merging class: {class_name}")
        
        train_class_dir = train_dir / class_name
        val_class_dir = val_dir / class_name
        
        train_class_dir.mkdir(parents=True, exist_ok=True)
        val_class_dir.mkdir(parents=True, exist_ok=True)
        
        # Collect all images for this class
        all_train_images = []
        all_val_images = []
        
        for dataset_dir in dataset_dirs:
            if not dataset_dir.exists():
                continue
            
            train_class_source = dataset_dir / "train" / class_name
            val_class_source = dataset_dir / "val" / class_name
            
            if train_class_source.exists():
                for ext in ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']:
                    all_train_images.extend(train_class_source.glob(f"*{ext}"))
            
            if val_class_source.exists():
                for ext in ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']:
                    all_val_images.extend(val_class_source.glob(f"*{ext}"))
        
        # Copy train images
        train_count = 0
        for img_path in all_train_images:
            # Create unique filename to avoid conflicts
            filename = f"{img_path.parent.parent.name}_{img_path.name}"
            dest_path = train_class_dir / filename
            
            if not dest_path.exists():
                shutil.copy2(img_path, dest_path)
                train_count += 1
        
        # Copy val images
        val_count = 0
        for img_path in all_val_images:
            # Create unique filename to avoid conflicts
            filename = f"{img_path.parent.parent.name}_{img_path.name}"
            dest_path = val_class_dir / filename
            
            if not dest_path.exists():
                shutil.copy2(img_path, dest_path)
                val_count += 1
        
        # Update statistics
        stats['classes'][class_name]['train'] = train_count
        stats['classes'][class_name]['val'] = val_count
        stats['total_samples'] += train_count + val_count
        stats['train_samples'] += train_count
        stats['val_samples'] += val_count
        
        print(f"      {class_name}: {train_count} train, {val_count} val")
    
    # Create dataset info
    create_merged_dataset_info(output_dir, stats)
    
    # Print summary
    print("\n" + "=" * 60)
    print("[SUCCESS] Dataset merge completed!")
    print("=" * 60)
    print(f"Output directory: {output_dir}")
    print(f"Total classes: {len(all_classes)}")
    print(f"Total samples: {stats['total_samples']}")
    print(f"Train samples: {stats['train_samples']}")
    print(f"Val samples: {stats['val_samples']}")
    print("\nSources:")
    for source_name, source_stats in stats['sources'].items():
        print(f"  {source_name}: {source_stats['classes']} classes, {source_stats['total_samples']} samples")
    
    return True


def create_merged_dataset_info(
    output_dir: Path,
    stats: Dict,
) -> None:
    """Create dataset info YAML file for merged dataset.
    
    Args:
        output_dir: Dataset directory
        stats: Statistics dictionary
    """
    class_names = sorted(stats['classes'].keys())
    
    info = {
        'dataset_name': 'Merged Bird Species Dataset',
        'source': 'Multiple sources (merged)',
        'format': 'YOLO Classification',
        'num_classes': len(class_names),
        'total_samples': stats['total_samples'],
        'train_samples': stats['train_samples'],
        'val_samples': stats['val_samples'],
        'classes': class_names,
        'path': str(output_dir.resolve()),
        'sources': stats['sources'],
        'class_stats': stats['classes'],
    }
    
    # Save YAML
    info_path = output_dir / "dataset_info.yaml"
    with open(info_path, 'w', encoding='utf-8') as f:
        yaml.dump(info, f, default_flow_style=False, indent=2, allow_unicode=True)
    
    print(f"\n[INFO] Dataset info saved to: {info_path}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Merge multiple training datasets into one",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This script merges multiple datasets (e.g., video-extracted frames and NABirds)
into a single training dataset.

Example usage:
  python scripts/merge_training_datasets.py \\
      --datasets data/bird_species data/nabirds_prepared \\
      --output-dir data/bird_species_merged
        """
    )
    parser.add_argument(
        "--datasets",
        nargs='+',
        required=True,
        help="List of dataset directories to merge",
    )
    parser.add_argument(
        "--output-dir",
        default=str(PROJECT_ROOT / "data" / "bird_species_merged"),
        help="Output directory for merged dataset",
    )
    parser.add_argument(
        "--val-split",
        type=float,
        default=0.2,
        help="Ratio of data to use for validation (0.0-1.0, default: 0.2)",
    )
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Run non-interactively",
    )
    
    args = parser.parse_args()
    
    dataset_dirs = [Path(d) for d in args.datasets]
    output_dir = Path(args.output_dir)
    
    print("=" * 60)
    print("Dataset Merger")
    print("=" * 60)
    print(f"Input datasets: {len(dataset_dirs)}")
    for d in dataset_dirs:
        print(f"  - {d}")
    print(f"Output directory: {output_dir}")
    print()
    
    if not args.yes:
        try:
            response = input("Do you want to proceed? (y/N): ").strip().lower()
        except EOFError:
            response = "n"
        if response not in ["y", "yes"]:
            print("Cancelled.")
            return 0
    
    # Merge datasets
    success = merge_datasets(
        dataset_dirs=dataset_dirs,
        output_dir=output_dir,
        val_split_ratio=args.val_split,
    )
    
    if success:
        print("\n" + "=" * 60)
        print("[SUCCESS] Dataset merge completed!")
        print("=" * 60)
        print("\nNext steps:")
        print(f"1. Train the species classification model:")
        print(f"   python scripts/train_bird_species_classifier.py --data-dir {output_dir}")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())


