#!/usr/bin/env python3
"""
Train a YOLO classification model on the Ez-Clap/bird-species dataset.

This script trains a bird species classification model that can identify
different bird species from cropped bird images.
"""

import sys
from pathlib import Path
import argparse
from typing import Optional

# Add the project root to the Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def train_classifier(
    data_dir: Path,
    model_size: str = "n",
    epochs: int = 100,
    imgsz: int = 224,
    batch_size: int = 16,
    device: str = "auto",
    output_dir: Optional[Path] = None,
) -> bool:
    """Train a YOLO classification model on bird species.
    
    Args:
        data_dir: Directory containing the dataset (with train/val subdirectories)
        model_size: YOLO model size ('n', 's', 'm', 'l', 'x')
        epochs: Number of training epochs
        imgsz: Image size for training (224 is standard for classification)
        batch_size: Batch size for training
        device: Device to use ('auto', 'cpu', 'cuda', '0', etc.)
        output_dir: Output directory for trained model
        
    Returns:
        True if training successful, False otherwise
    """
    try:
        from ultralytics import YOLO
    except ImportError:
        print("❌ ultralytics library not found. Install it with:")
        print("   pip install ultralytics")
        return False
    
    # Check dataset exists
    train_dir = data_dir / "train"
    val_dir = data_dir / "val"
    test_dir = data_dir / "test"
    
    if not train_dir.exists():
        print(f"❌ Training data not found: {train_dir}")
        print("   Please run: python scripts/prepare_nabirds_dataset.py or download_bird_species_dataset.py")
        return False
    
    # If val is empty but test exists, copy test to val for validation
    val_dirs = [d for d in val_dir.iterdir() if d.is_dir()] if val_dir.exists() else []
    if len(val_dirs) == 0 and test_dir.exists():
        test_dirs = [d for d in test_dir.iterdir() if d.is_dir()]
        if len(test_dirs) > 0:
            print(f"[INFO] Validation directory is empty, copying test split to val for validation...")
            import shutil
            if val_dir.exists():
                # Remove empty val if it exists
                try:
                    for item in val_dir.iterdir():
                        if item.is_dir():
                            shutil.rmtree(item)
                        else:
                            item.unlink()
                except Exception as e:
                    print(f"   [WARNING] Could not clear val directory: {e}")
            else:
                val_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy test data to val
            for test_class_dir in test_dirs:
                val_class_dir = val_dir / test_class_dir.name
                if not val_class_dir.exists():
                    shutil.copytree(test_class_dir, val_class_dir)
            print(f"   [OK] Copied {len(test_dirs)} classes from test to val")
    
    # Count classes
    classes = [d.name for d in train_dir.iterdir() if d.is_dir()]
    num_classes = len(classes)
    
    if num_classes == 0:
        print(f"❌ No classes found in {train_dir}")
        print("   Expected structure: data_dir/train/class1/, data_dir/train/class2/, ...")
        return False
    
    print(f"✅ Found {num_classes} bird species")
    
    # Count samples (handle both uppercase and lowercase extensions)
    train_samples = sum(
        len(list(class_dir.glob("*.jpg"))) + 
        len(list(class_dir.glob("*.png"))) +
        len(list(class_dir.glob("*.JPG"))) + 
        len(list(class_dir.glob("*.PNG")))
        for class_dir in train_dir.iterdir()
        if class_dir.is_dir()
    )
    val_samples = 0
    if val_dir.exists():
        val_samples = sum(
            len(list(class_dir.glob("*.jpg"))) + 
            len(list(class_dir.glob("*.png"))) +
            len(list(class_dir.glob("*.JPG"))) + 
            len(list(class_dir.glob("*.PNG")))
            for class_dir in val_dir.iterdir()
            if class_dir.is_dir()
        )
    
    print(f"   Training samples: {train_samples}")
    if val_samples > 0:
        print(f"   Validation samples: {val_samples}")
    else:
        print("   ⚠️  No validation split found (YOLO will auto-split)")
    
    # Load base model
    model_name = f"yolo11{model_size}-cls.pt"
    print(f"\n📥 Loading base model: {model_name}")
    
    try:
        model = YOLO(model_name)
    except Exception as e:
        print(f"❌ Failed to load model {model_name}: {e}")
        print("   Trying to download automatically...")
        return False
    
    # Set output directory
    if output_dir is None:
        output_dir = PROJECT_ROOT / "models" / "training" / "bird_species_classifier"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Auto-detect device if not specified
    if device == "auto" or device is None:
        try:
            import torch
            if torch.cuda.is_available():
                device = "cuda"
                print(f"[INFO] CUDA detected: {torch.cuda.get_device_name(0)}")
            else:
                device = "cpu"
                print("[INFO] CUDA not available, using CPU")
                print("[INFO] To force CUDA, use --device cuda (will fail if GPU not available)")
        except ImportError:
            device = "cpu"
            print("[INFO] PyTorch not available for device detection, using CPU")
    
    # If user explicitly requested CUDA, use it even if not detected
    # (They might have GPU but need PyTorch with CUDA support installed)
    if device and device.lower() in ["cuda", "gpu"] and device != "cpu":
        device = "cuda"  # Normalize to cuda
        try:
            import torch
            if not torch.cuda.is_available():
                print("[WARNING] CUDA requested but not available in PyTorch")
                print("[INFO] You may need to install PyTorch with CUDA support:")
                print("   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121")
                print("[INFO] Attempting to use CUDA anyway (may fail)...")
        except ImportError:
            pass
    
    # Training parameters
    print("\n🚀 Starting training...")
    print("=" * 60)
    print(f"Dataset: {data_dir}")
    print(f"Model: YOLO11{model_size}-cls")
    print(f"Classes: {num_classes}")
    print(f"Epochs: {epochs}")
    print(f"Image size: {imgsz}")
    print(f"Batch size: {batch_size}")
    print(f"Device: {device}")
    print(f"Output: {output_dir}")
    print("=" * 60)
    
    try:
        # Train the model
        results = model.train(
            data=str(data_dir),  # Path to dataset root (contains train/val)
            epochs=epochs,
            imgsz=imgsz,
            batch=batch_size,
            device=device,
            project=str(output_dir.parent),
            name="bird_species_classifier",
            exist_ok=True,
            save=True,
            save_period=10,  # Save checkpoint every 10 epochs
            patience=20,  # Early stopping patience
            workers=4,
            verbose=True,
        )
        
        # Find best model (YOLO saves to output_dir/weights/ or output_dir/name/weights/)
        # Try both possible locations
        best_model_path = output_dir / "weights" / "best.pt"
        if not best_model_path.exists():
            best_model_path = output_dir / "bird_species_classifier" / "weights" / "best.pt"
        
        if not best_model_path.exists():
            last_model_path = output_dir / "weights" / "last.pt"
            if not last_model_path.exists():
                last_model_path = output_dir / "bird_species_classifier" / "weights" / "last.pt"
            if last_model_path.exists():
                best_model_path = last_model_path
            else:
                print(f"❌ Trained model not found in expected location")
                print(f"   Checked: {output_dir / 'weights' / 'best.pt'}")
                print(f"   Checked: {output_dir / 'bird_species_classifier' / 'weights' / 'best.pt'}")
                return False
        
        # Copy to main models directory
        final_model_path = PROJECT_ROOT / "models" / "bird_species_classifier.pt"
        import shutil
        shutil.copy2(best_model_path, final_model_path)
        
        print("\n" + "=" * 60)
        print("✅ Training completed!")
        print("=" * 60)
        print(f"📁 Best model: {best_model_path}")
        print(f"📁 Final model: {final_model_path}")
        
        # Print training results
        if hasattr(results, 'results_dict'):
            print("\n📊 Training Results:")
            for key, value in results.results_dict.items():
                if isinstance(value, float):
                    print(f"   {key}: {value:.4f}")
        
        # Save results.csv for analytics
        # Ultralytics should generate this automatically, but we'll ensure it exists
        results_csv_path = output_dir / "results.csv"
        alt_csv_path = output_dir / "bird_species_classifier" / "results.csv"
        
        # Check if CSV already exists (Ultralytics generates it automatically)
        if results_csv_path.exists():
            print(f"📊 Results CSV found at: {results_csv_path}")
        elif alt_csv_path.exists():
            print(f"📊 Results CSV found at: {alt_csv_path}")
        else:
            # Try to extract CSV from results object
            try:
                import pandas as pd
                # Ultralytics results object has a csv property that contains the CSV string
                if hasattr(results, 'csv') and results.csv:
                    results_csv_path = output_dir / "results.csv"
                    with open(results_csv_path, 'w') as f:
                        f.write(results.csv)
                    print(f"📊 Results CSV saved to: {results_csv_path}")
                elif hasattr(results, 'results_dict'):
                    # Fallback: create CSV from results_dict if available
                    # Note: This may not have epoch-by-epoch data
                    df = pd.DataFrame([results.results_dict])
                    results_csv_path = output_dir / "results.csv"
                    df.to_csv(results_csv_path, index=False)
                    print(f"📊 Results CSV saved to: {results_csv_path}")
                    print("   Note: This CSV contains final metrics only. For epoch-by-epoch data,")
                    print("   check the training output directory after training completes.")
            except ImportError:
                print("⚠️  pandas not available, skipping CSV export")
                print("   Install with: pip install pandas")
            except Exception as e:
                print(f"⚠️  Could not save results CSV: {e}")
                print(f"   Ultralytics should generate results.csv automatically in: {output_dir}")
        
        # Update config
        update_config(final_model_path)
        
        return True
        
    except Exception as e:
        print(f"❌ Training failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def update_config(model_path: Path) -> None:
    """Update SkyGuard configuration with the species model.
    
    Args:
        model_path: Path to the trained species classification model
    """
    try:
        import yaml
        
        config_path = PROJECT_ROOT / "config" / "skyguard.yaml"
        if not config_path.exists():
            print("⚠️  Config file not found, skipping update")
            return
        
        # Load config
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Ensure AI section exists
        if 'ai' not in config:
            config['ai'] = {}
        
        # Update species classification settings
        config['ai']['species_backend'] = 'ultralytics'
        config['ai']['species_model_path'] = str(model_path.relative_to(PROJECT_ROOT))
        config['ai']['species_input_size'] = [224, 224]
        
        # Save config
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2, allow_unicode=True)
        
        print(f"✅ Configuration updated: {config_path}")
        print(f"   species_model_path: {config['ai']['species_model_path']}")
        print(f"   species_input_size: {config['ai']['species_input_size']}")
        
    except Exception as e:
        print(f"⚠️  Failed to update config: {e}")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Train bird species classification model"
    )
    parser.add_argument(
        "--data-dir",
        default=str(PROJECT_ROOT / "data" / "bird_species"),
        help="Directory containing the bird species dataset",
    )
    parser.add_argument(
        "--model-size",
        default="n",
        choices=['n', 's', 'm', 'l', 'x'],
        help="YOLO model size (n=nano, s=small, m=medium, l=large, x=xlarge)",
    )
    parser.add_argument(
        "--epochs",
        type=int,
        default=100,
        help="Number of training epochs",
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=224,
        help="Image size for training (224 is standard for classification)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=16,
        help="Batch size for training",
    )
    parser.add_argument(
        "--device",
        default=None,
        help="Device to use (auto, cpu, cuda, 0, etc.). If not specified, will auto-detect (cuda if available, else cpu)",
    )
    parser.add_argument(
        "--output-dir",
        help="Output directory for trained model (default: models/training/bird_species_classifier)",
    )
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Run non-interactively",
    )
    
    args = parser.parse_args()
    
    data_dir = Path(args.data_dir)
    output_dir = Path(args.output_dir) if args.output_dir else None
    
    print("=" * 60)
    print("Bird Species Classification Model Training")
    print("=" * 60)
    print(f"Dataset: {data_dir}")
    print(f"Model: YOLO11{args.model_size}-cls")
    print(f"Epochs: {args.epochs}")
    print(f"Image size: {args.imgsz}")
    print(f"Batch size: {args.batch_size}")
    print()
    
    if not args.yes:
        try:
            response = input("Do you want to proceed? (y/N): ").strip().lower()
        except EOFError:
            response = "n"
        if response not in ["y", "yes"]:
            print("Cancelled.")
            return 0
    
    # Train model
    success = train_classifier(
        data_dir=data_dir,
        model_size=args.model_size,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch_size=args.batch_size,
        device=args.device,
        output_dir=output_dir,
    )
    
    if success:
        print("\n" + "=" * 60)
        print("🎉 Training complete!")
        print("=" * 60)
        print("\nThe species classifier is now configured in config/skyguard.yaml")
        print("SkyGuard will automatically use it for species identification!")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

