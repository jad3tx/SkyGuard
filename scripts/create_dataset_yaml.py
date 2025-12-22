#!/usr/bin/env python3
"""
Create a YOLO dataset.yaml file from an existing dataset structure.

This script helps create the required dataset.yaml file for YOLO training
by detecting the dataset structure and generating the appropriate configuration.
"""

import sys
import argparse
from pathlib import Path
import yaml

# Add the project root to the Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def detect_dataset_structure(dataset_dir: Path) -> dict:
    """Detect the structure of a YOLO dataset.
    
    Args:
        dataset_dir: Root directory of the dataset
        
    Returns:
        Dictionary with detected structure information
    """
    structure = {
        'has_images': False,
        'has_labels': False,
        'train_images': None,
        'val_images': None,
        'train_labels': None,
        'val_labels': None,
        'image_count': {'train': 0, 'val': 0},
        'label_count': {'train': 0, 'val': 0},
    }
    
    # Check for images directory
    images_dir = dataset_dir / "images"
    if images_dir.exists():
        structure['has_images'] = True
        train_img_dir = images_dir / "train"
        val_img_dir = images_dir / "val"
        
        if train_img_dir.exists():
            structure['train_images'] = "images/train"
            # Count images
            structure['image_count']['train'] = len(list(train_img_dir.glob("*.jpg"))) + \
                                                len(list(train_img_dir.glob("*.png"))) + \
                                                len(list(train_img_dir.glob("*.JPG"))) + \
                                                len(list(train_img_dir.glob("*.PNG")))
        
        if val_img_dir.exists():
            structure['val_images'] = "images/val"
            structure['image_count']['val'] = len(list(val_img_dir.glob("*.jpg"))) + \
                                              len(list(val_img_dir.glob("*.png"))) + \
                                              len(list(val_img_dir.glob("*.JPG"))) + \
                                              len(list(val_img_dir.glob("*.PNG")))
    
    # Check for labels directory
    labels_dir = dataset_dir / "labels"
    if labels_dir.exists():
        structure['has_labels'] = True
        train_label_dir = labels_dir / "train"
        val_label_dir = labels_dir / "val"
        
        if train_label_dir.exists():
            structure['train_labels'] = "labels/train"
            structure['label_count']['train'] = len(list(train_label_dir.glob("*.txt")))
        
        if val_label_dir.exists():
            structure['val_labels'] = "labels/val"
            structure['label_count']['val'] = len(list(val_label_dir.glob("*.txt")))
    
    return structure


def create_dataset_yaml(
    dataset_dir: Path,
    output_path: Path = None,
    num_classes: int = 1,
    class_names: list = None,
    overwrite: bool = False,
) -> bool:
    """Create a dataset.yaml file for YOLO training.
    
    Args:
        dataset_dir: Root directory of the dataset
        output_path: Path to save dataset.yaml (default: dataset_dir/dataset.yaml)
        num_classes: Number of classes
        class_names: List of class names (default: ['bird'])
        overwrite: Whether to overwrite existing dataset.yaml
        
    Returns:
        True if successful, False otherwise
    """
    if output_path is None:
        output_path = dataset_dir / "dataset.yaml"
    
    if output_path.exists() and not overwrite:
        print(f"❌ Dataset YAML already exists: {output_path}")
        print("   Use --overwrite to replace it")
        return False
    
    # Detect dataset structure
    structure = detect_dataset_structure(dataset_dir)
    
    if not structure['has_images']:
        print(f"❌ No images directory found in {dataset_dir}")
        print("   Expected structure:")
        print("     dataset_dir/")
        print("     ├── images/")
        print("     │   ├── train/")
        print("     │   └── val/")
        print("     └── labels/")
        print("         ├── train/")
        print("         └── val/")
        return False
    
    if not structure['train_images']:
        print(f"❌ No train images found in {dataset_dir / 'images'}")
        return False
    
    if not structure['val_images']:
        print(f"⚠️  Warning: No validation images found. Training may fail.")
    
    # Default class names
    if class_names is None:
        if num_classes == 1:
            class_names = ['bird']
        else:
            class_names = [f'class_{i}' for i in range(num_classes)]
    
    if len(class_names) != num_classes:
        print(f"⚠️  Warning: Number of class names ({len(class_names)}) doesn't match num_classes ({num_classes})")
        print(f"   Using {len(class_names)} classes")
        num_classes = len(class_names)
    
    # Create dataset.yaml content
    dataset_path = str(dataset_dir.resolve())
    
    yaml_content = {
        'path': dataset_path,
        'train': structure['train_images'],
        'val': structure['val_images'] if structure['val_images'] else structure['train_images'],
        'nc': num_classes,
        'names': class_names,
    }
    
    # Save YAML file
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(yaml_content, f, default_flow_style=False, indent=2, allow_unicode=True)
        
        print("=" * 60)
        print("✅ Dataset YAML created successfully!")
        print("=" * 60)
        print(f"📁 Output: {output_path}")
        print(f"📊 Dataset structure:")
        print(f"   Train images: {structure['image_count']['train']}")
        print(f"   Val images: {structure['image_count']['val']}")
        if structure['has_labels']:
            print(f"   Train labels: {structure['label_count']['train']}")
            print(f"   Val labels: {structure['label_count']['val']}")
        print(f"   Classes: {num_classes}")
        print(f"   Class names: {class_names}")
        print()
        print("You can now train the model with:")
        print(f"   python -m skyguard.training.train_model --data-path {output_path.relative_to(PROJECT_ROOT)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create dataset.yaml: {e}")
        return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Create a YOLO dataset.yaml file from an existing dataset structure",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example usage:
  # Create dataset.yaml for a dataset in data/training
  python scripts/create_dataset_yaml.py --dataset-dir data/training
  
  # Specify custom class names
  python scripts/create_dataset_yaml.py \\
      --dataset-dir data/training \\
      --num-classes 3 \\
      --class-names bird raptor hawk
        """
    )
    parser.add_argument(
        "--dataset-dir",
        required=True,
        help="Root directory of the dataset (should contain images/ and labels/ subdirectories)",
    )
    parser.add_argument(
        "--output",
        help="Output path for dataset.yaml (default: <dataset-dir>/dataset.yaml)",
    )
    parser.add_argument(
        "--num-classes",
        type=int,
        default=1,
        help="Number of classes (default: 1)",
    )
    parser.add_argument(
        "--class-names",
        nargs='+',
        help="List of class names (default: ['bird'] for 1 class, or ['class_0', 'class_1', ...] for multiple)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing dataset.yaml file",
    )
    
    args = parser.parse_args()
    
    dataset_dir = Path(args.dataset_dir)
    if not dataset_dir.is_absolute():
        dataset_dir = PROJECT_ROOT / args.dataset_dir
    
    if not dataset_dir.exists():
        print(f"❌ Dataset directory not found: {dataset_dir}")
        return 1
    
    output_path = None
    if args.output:
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = PROJECT_ROOT / args.output
    
    success = create_dataset_yaml(
        dataset_dir=dataset_dir,
        output_path=output_path,
        num_classes=args.num_classes,
        class_names=args.class_names,
        overwrite=args.overwrite,
    )
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

