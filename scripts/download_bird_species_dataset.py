#!/usr/bin/env python3
"""
Download and prepare the Ez-Clap/bird-species dataset for SkyGuard species classification.

This script downloads the bird species dataset from Hugging Face and converts it
to YOLO classification format.
"""

import sys
from pathlib import Path
from typing import Optional
import os

# Add the project root to the Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def get_hf_token() -> Optional[str]:
    """Get Hugging Face token from environment or CLI.
    
    Checks in order:
    1. HF_TOKEN environment variable
    2. HUGGINGFACE_HUB_TOKEN environment variable
    3. Hugging Face CLI cache (~/.huggingface/token)
    
    Returns:
        Token string or None if not found
    """
    import os
    from pathlib import Path
    
    # Check environment variables
    token = os.environ.get('HF_TOKEN') or os.environ.get('HUGGINGFACE_HUB_TOKEN')
    if token:
        return token
    
    # Check Hugging Face CLI cache
    hf_cache = Path.home() / ".huggingface" / "token"
    if hf_cache.exists():
        try:
            with open(hf_cache, 'r') as f:
                token = f.read().strip()
                if token:
                    return token
        except Exception:
            pass
    
    return None


def download_dataset(output_dir: Path, token: Optional[str] = None) -> bool:
    """Download the Ez-Clap/bird-species dataset from Hugging Face.
    
    Args:
        output_dir: Directory to save the dataset
        token: Optional Hugging Face token (if None, will try to find automatically)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        from datasets import load_dataset
        
        print("[INFO] Downloading Ez-Clap/bird-species dataset from Hugging Face...")
        print("This may take a while depending on your internet connection...")
        
        # Get token if not provided
        if token is None:
            token = get_hf_token()
        
        # Prepare load arguments
        load_kwargs = {"path": "Ez-Clap/bird-species"}
        if token:
            load_kwargs["token"] = token
            print("   [OK] Using Hugging Face token for authentication")
        else:
            print("   [INFO] No token provided - using public access")
            print("   [INFO] Tip: Set HF_TOKEN environment variable or use 'huggingface-cli login'")
        
        # Disable symlinks on Windows (avoids privilege errors)
        import sys
        import os
        import time
        if sys.platform == "win32":
            # Set environment variable to disable symlinks
            os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
            # Try to set symlink preference in huggingface_hub
            try:
                from huggingface_hub import configure_hf_cache_dir
                # The datasets library should respect this
                print("   [INFO] Configuring for Windows (symlinks disabled)")
            except ImportError:
                pass
        
        # Load the dataset with retry logic for rate limiting
        print("   Downloading from Hugging Face...")
        print("   [INFO] This may take a while due to rate limiting. Be patient...")
        max_retries = 3
        retry_delay = 60  # Start with 60 seconds
        
        for attempt in range(max_retries):
            try:
                ds = load_dataset(**load_kwargs)
                break
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "Too Many Requests" in error_str:
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (2 ** attempt)
                        print(f"\n   [WARNING] Rate limit hit. Waiting {wait_time} seconds before retry {attempt + 1}/{max_retries}...")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"\n   [ERROR] Rate limit exceeded after {max_retries} attempts.")
                        print("   [INFO] Please wait a few minutes and try again, or upgrade to HuggingFace Pro.")
                        raise
                else:
                    raise
        
        print(f"[OK] Dataset loaded successfully!")
        print(f"   Dataset type: {type(ds)}")
        print(f"   Available splits: {list(ds.keys())}")
        
        # Handle DatasetDict structure
        if hasattr(ds, 'keys'):
            for split_name in ds.keys():
                print(f"   {split_name} split: {len(ds[split_name])} samples")
        
        # Create output directories
        train_dir = output_dir / "train"
        val_dir = output_dir / "val"
        test_dir = output_dir / "test"
        
        train_dir.mkdir(parents=True, exist_ok=True)
        val_dir.mkdir(parents=True, exist_ok=True)
        test_dir.mkdir(parents=True, exist_ok=True)
        
        # Process each split
        split_mapping = {
            'train': train_dir,
            'validation': val_dir,
            'val': val_dir,
            'test': test_dir,
        }
        
        for split_name, target_dir in split_mapping.items():
            if split_name in ds:
                print(f"\n📦 Processing {len(ds[split_name])} {split_name} samples...")
                process_split(ds[split_name], target_dir, split_name=split_name)
        
        # Check if any splits were processed
        if not any((train_dir / d).is_dir() for d in train_dir.iterdir()):
            print("\n[WARNING] No training data was processed. Checking dataset structure...")
            # Try to inspect first sample
            if hasattr(ds, 'keys') and len(ds.keys()) > 0:
                first_split = list(ds.keys())[0]
                first_sample = ds[first_split][0]
                print(f"   First sample keys: {list(first_sample.keys())}")
                print(f"   First sample: {first_sample}")
        
        print(f"\n[OK] Dataset prepared at: {output_dir}")
        return True
        
    except ImportError:
        print("[ERROR] datasets library not found. Install it with:")
        print("   pip install datasets")
        return False
    except Exception as e:
        print(f"[ERROR] Failed to download dataset: {e}")
        import traceback
        traceback.print_exc()
        return False


def process_split(split_data, output_dir: Path, split_name: str) -> None:
    """Process a dataset split and save images organized by class.
    
    Args:
        split_data: Dataset split to process
        output_dir: Output directory for this split
        split_name: Name of the split (for progress display)
    """
    from PIL import Image
    import os
    
    # Inspect first sample to understand structure
    first_sample = split_data[0] if len(split_data) > 0 else {}
    print(f"   Dataset features: {list(first_sample.keys())}")
    
    # Determine label key
    label_key = None
    possible_label_keys = ['label', 'species', 'class', 'name', 'bird_species', 'labels']
    for key in possible_label_keys:
        if key in first_sample:
            label_key = key
            break
    
        if label_key is None:
            print(f"   [WARNING] Could not find label field. Available keys: {list(first_sample.keys())}")
            # Try to guess from available keys
            if 'image' in first_sample or 'img' in first_sample:
                print("   [INFO] Dataset may need manual inspection")
    
    # Get unique classes
    classes = set()
    for idx, sample in enumerate(split_data):
        label = None
        if label_key:
            label = sample.get(label_key)
        
        if label is not None:
            # Handle string, int, or list labels
            if isinstance(label, list):
                label = label[0] if len(label) > 0 else None
            elif isinstance(label, (int, float)):
                # If numeric, might need to map to class names
                label = str(label)
            
            if label:
                classes.add(str(label))
    
    print(f"   Found {len(classes)} unique species")
    
    # Create class directories
    for class_name in classes:
        class_dir = output_dir / str(class_name).replace(' ', '_').replace('/', '_')
        class_dir.mkdir(parents=True, exist_ok=True)
    
    # Save images
    saved_count = 0
    for idx, sample in enumerate(split_data):
        if (idx + 1) % 100 == 0:
            print(f"   Processed {idx + 1}/{len(split_data)} samples...")
        
        # Get image
        image = None
        if 'image' in sample:
            image = sample['image']
        elif 'img' in sample:
            image = sample['img']
        elif 'photo' in sample:
            image = sample['photo']
        
        if not isinstance(image, Image.Image):
            # Try to load from path
            if 'image_path' in sample:
                image_path = sample['image_path']
                try:
                    image = Image.open(image_path)
                except Exception:
                    continue
            else:
                continue
        
        # Get label using determined label key
        label = None
        if label_key:
            label = sample.get(label_key)
            if isinstance(label, list):
                label = label[0] if len(label) > 0 else None
            elif isinstance(label, (int, float)):
                label = str(label)
        
        if not label:
            continue
        
        label = str(label)
        
        # Save image
        label_safe = str(label).replace(' ', '_').replace('/', '_')
        class_dir = output_dir / label_safe
        
        # Generate filename
        filename = f"{split_name}_{idx:06d}.jpg"
        output_path = class_dir / filename
        
        try:
            # Convert to RGB if needed and save
            if image.mode != 'RGB':
                image = image.convert('RGB')
            image.save(output_path, 'JPEG', quality=95)
            saved_count += 1
        except Exception as e:
            print(f"   [WARNING] Failed to save image {idx}: {e}")
            continue
    
    print(f"   [OK] Saved {saved_count} images from {split_name} split")


def create_dataset_info(output_dir: Path) -> None:
    """Create dataset info YAML file.
    
    Args:
        output_dir: Dataset directory
    """
    import yaml
    
    # Count classes and samples
    train_dir = output_dir / "train"
    classes = []
    total_samples = 0
    
    if train_dir.exists():
        for class_dir in sorted(train_dir.iterdir()):
            if class_dir.is_dir():
                class_name = class_dir.name.replace('_', ' ')
                sample_count = len(list(class_dir.glob("*.jpg"))) + len(list(class_dir.glob("*.png")))
                classes.append(class_name)
                total_samples += sample_count
    
    # Create info dict
    info = {
        'dataset_name': 'Ez-Clap Bird Species',
        'source': 'https://huggingface.co/datasets/Ez-Clap/bird-species',
        'format': 'YOLO Classification',
        'num_classes': len(classes),
        'total_samples': total_samples,
        'classes': classes,
        'path': str(output_dir.resolve()),
    }
    
    # Save YAML
    info_path = output_dir / "dataset_info.yaml"
    with open(info_path, 'w', encoding='utf-8') as f:
        yaml.dump(info, f, default_flow_style=False, indent=2, allow_unicode=True)
    
    print(f"\n[INFO] Dataset info saved to: {info_path}")
    print(f"   Classes: {len(classes)}")
    print(f"   Total samples: {total_samples}")


def main():
    """Main function."""
    import argparse
    import os
    
    parser = argparse.ArgumentParser(
        description="Download Ez-Clap/bird-species dataset for SkyGuard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Authentication Options:
  1. Environment variable (recommended):
     export HF_TOKEN=your_token_here
     python scripts/download_bird_species_dataset.py
  
  2. Hugging Face CLI login:
     huggingface-cli login
     python scripts/download_bird_species_dataset.py
  
  3. Command-line argument (less secure):
     python scripts/download_bird_species_dataset.py --token your_token_here

The script will automatically detect tokens from environment variables or
Hugging Face CLI cache if available.
        """
    )
    parser.add_argument(
        "--output-dir",
        default=str(PROJECT_ROOT / "data" / "bird_species"),
        help="Output directory for the dataset",
    )
    parser.add_argument(
        "--token",
        help="Hugging Face access token (not recommended - use environment variable instead)",
    )
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Run non-interactively",
    )
    
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    
    print("=" * 60)
    print("Bird Species Dataset Download")
    print("=" * 60)
    print(f"Dataset: Ez-Clap/bird-species")
    print(f"Output: {output_dir}")
    
    # Handle token
    token = args.token
    if token:
        print("   [WARNING] Using token from command line (consider using environment variable)")
    else:
        token = get_hf_token()
        if token:
            print("   [OK] Found Hugging Face token")
        else:
            print("   [INFO] No token found - will try public access")
            print("   [INFO] Set HF_TOKEN environment variable for private datasets")
    
    print()
    
    if not args.yes:
        try:
            response = input("Do you want to proceed? (y/N): ").strip().lower()
        except EOFError:
            response = "n"
        if response not in ["y", "yes"]:
            print("Cancelled.")
            return 0
    
    # Check if datasets library is available
    try:
        import datasets
    except ImportError:
        print("[ERROR] datasets library not found.")
        print("\nInstall it with:")
        print("   pip install datasets")
        print("\nOr with Pillow for image handling:")
        print("   pip install datasets pillow")
        return 1
    
    # Download dataset
    success = download_dataset(output_dir, token=token)
    
    if success:
        # Create dataset info
        create_dataset_info(output_dir)
        
        print("\n" + "=" * 60)
        print("[OK] Dataset download completed!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Train the species classification model:")
        print("   python scripts/train_bird_species_classifier.py")
        print("\n2. Or train manually:")
        print("   from ultralytics import YOLO")
        print("   model = YOLO('yolo11n-cls.pt')")
        print(f"   model.train(data='{output_dir}', epochs=100, imgsz=224)")
        print("\n3. Update config/skyguard.yaml with the trained model path")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

