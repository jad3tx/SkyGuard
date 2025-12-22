#!/usr/bin/env python3
"""
SkyGuard Model Training Script

Trains a custom YOLO model for raptor detection.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import Optional

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def setup_logging():
    """Setup logging for training."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def train_model(
    data_path: str = "data/training/dataset.yaml",
    epochs: int = 50,
    batch_size: int = 16,
    img_size: int = 640,
    model_size: str = "n",  # n, s, m, l, x
    output_dir: str = "models/trained"
) -> bool:
    """
    Train a YOLO model for raptor detection.
    
    Args:
        data_path: Path to dataset.yaml file (relative to project root or absolute)
        epochs: Number of training epochs
        batch_size: Batch size for training
        img_size: Image size for training
        model_size: YOLO model size (n, s, m, l, x)
        output_dir: Directory to save trained model
        
    Returns:
        True if training successful, False otherwise
    """
    logger = setup_logging()
    
    try:
        from ultralytics import YOLO
        logger.info("✅ YOLO library imported successfully")
    except ImportError:
        logger.error("❌ YOLO library not available. Please install: pip install ultralytics")
        return False
    
    # Resolve dataset path relative to project root
    dataset_path = Path(data_path)
    if not dataset_path.is_absolute():
        # Try relative to project root
        dataset_path = project_root / data_path
    
    # Check if dataset exists
    if not dataset_path.exists():
        logger.error(f"❌ Dataset not found: {dataset_path}")
        logger.error(f"   Resolved from: {data_path}")
        logger.error(f"   Project root: {project_root}")
        
        # Try to find common dataset locations
        logger.info("\n🔍 Searching for datasets in common locations...")
        common_locations = [
            project_root / "data" / "training" / "dataset.yaml",
            project_root / "data" / "custom" / "dataset.yaml",
            project_root / "data" / "dataset.yaml",
        ]
        
        found_datasets = []
        for loc in common_locations:
            if loc.exists():
                found_datasets.append(str(loc.relative_to(project_root)))
        
        if found_datasets:
            logger.info("   Found potential datasets:")
            for ds in found_datasets:
                logger.info(f"     - {ds}")
            logger.info(f"\n   Try using: --data-path {found_datasets[0]}")
        else:
            logger.info("   No datasets found in common locations")
            logger.info("\n   To create a YOLO detection dataset:")
            logger.info("   1. Organize images in YOLO format:")
            logger.info("      data/training/")
            logger.info("      ├── images/")
            logger.info("      │   ├── train/")
            logger.info("      │   └── val/")
            logger.info("      └── labels/")
            logger.info("          ├── train/")
            logger.info("          └── val/")
            logger.info("   2. Create dataset.yaml automatically:")
            logger.info(f"      python scripts/create_dataset_yaml.py --dataset-dir data/training")
            logger.info("   3. Or create dataset.yaml manually:")
            logger.info("      path: data/training")
            logger.info("      train: images/train")
            logger.info("      val: images/val")
            logger.info("      nc: 1")
            logger.info("      names: ['bird']")
        
        return False
    
    # Use resolved path
    data_path = str(dataset_path.resolve())
    
    # Create output directory (resolve relative to project root)
    output_path = Path(output_dir)
    if not output_path.is_absolute():
        output_path = project_root / output_dir
    output_path.mkdir(parents=True, exist_ok=True)
    
    logger.info("🦅 Starting SkyGuard model training")
    logger.info("=" * 60)
    logger.info(f"📁 Dataset: {data_path}")
    logger.info(f"🔄 Epochs: {epochs}")
    logger.info(f"📦 Batch size: {batch_size}")
    logger.info(f"🖼️  Image size: {img_size}")
    logger.info(f"🏗️  Model size: YOLO11{model_size} (or YOLOv8{model_size} if YOLO11 not available)")
    logger.info(f"💾 Output: {output_path}")
    logger.info("=" * 60)
    
    try:
        # Load pre-trained YOLO model (try YOLO11 first, fallback to YOLOv8)
        model_name = f"yolo11{model_size}.pt"
        try:
            logger.info(f"📥 Loading pre-trained model: {model_name}")
            model = YOLO(model_name)
        except Exception:
            # Fallback to YOLOv8 if YOLO11 not available
            model_name = f"yolov8{model_size}.pt"
            logger.info(f"📥 Loading pre-trained model (fallback): {model_name}")
            model = YOLO(model_name)
        
        # Train the model
        logger.info("🚀 Starting training...")
        results = model.train(
            data=data_path,
            epochs=epochs,
            batch=batch_size,
            imgsz=img_size,
            project=output_path,
            name="skyguard_raptor_detector",
            exist_ok=True,
            save=True,
            save_period=5,  # Save checkpoint every 5 epochs
            device='cpu',  # Use CPU for compatibility, change to 'cuda' if GPU available
            workers=4,
            patience=10,  # Early stopping patience (stops if no improvement for 10 epochs)
            verbose=True
        )
        
        # Save the best model
        best_model_path = output_path / "skyguard_raptor_detector" / "weights" / "best.pt"
        final_model_path = output_path / "skyguard_raptor_detector.pt"
        
        if best_model_path.exists():
            import shutil
            shutil.copy2(best_model_path, final_model_path)
            logger.info(f"✅ Best model saved to: {final_model_path}")
        else:
            logger.warning("⚠️  Best model not found, using last model")
            last_model_path = output_path / "skyguard_raptor_detector" / "weights" / "last.pt"
            if last_model_path.exists():
                shutil.copy2(last_model_path, final_model_path)
                logger.info(f"✅ Last model saved to: {final_model_path}")
        
        # Update SkyGuard configuration
        update_skyguard_config(final_model_path)
        
        logger.info("🎉 Training completed successfully!")
        logger.info(f"📊 Model saved to: {final_model_path}")
        logger.info("🔧 SkyGuard configuration updated")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Training failed: {e}")
        return False

def update_skyguard_config(model_path: Path):
    """Update SkyGuard configuration to use the new model."""
    logger = setup_logging()
    
    try:
        import yaml
        
        config_path = project_root / "config" / "skyguard.yaml"
        if not config_path.exists():
            logger.warning("⚠️  SkyGuard config not found, creating default")
            return
        
        # Load current config
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Update model path
        config['ai']['model_path'] = str(model_path)
        config['ai']['model_type'] = 'yolo'
        
        # Save updated config
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, indent=2)
        
        logger.info("✅ SkyGuard configuration updated")
        
    except Exception as e:
        logger.error(f"❌ Failed to update configuration: {e}")

def validate_model(model_path: str) -> bool:
    """Validate the trained model."""
    logger = setup_logging()
    
    try:
        from ultralytics import YOLO
        
        logger.info("🔍 Validating trained model...")
        model = YOLO(model_path)
        
        # Test with a sample image
        test_image = "data/training/images/val"
        if Path(test_image).exists():
            test_images = list(Path(test_image).glob("*.jpg"))[:5]  # Test with 5 images
            
            for img_path in test_images:
                results = model(str(img_path))
                logger.info(f"✅ Model validation successful on {img_path.name}")
        
        logger.info("✅ Model validation completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Model validation failed: {e}")
        return False

def main():
    """Main training function."""
    parser = argparse.ArgumentParser(description="Train SkyGuard raptor detection model")
    parser.add_argument("--data-path", default="data/training/dataset.yaml",
                       help="Path to dataset.yaml file")
    parser.add_argument("--epochs", type=int, default=50,
                       help="Number of training epochs (default: 50, based on experience that improvements plateau around 40)")
    parser.add_argument("--batch-size", type=int, default=16,
                       help="Batch size for training")
    parser.add_argument("--img-size", type=int, default=640,
                       help="Image size for training")
    parser.add_argument("--model-size", default="n", choices=['n', 's', 'm', 'l', 'x'],
                       help="YOLO model size")
    parser.add_argument("--output-dir", default="models/trained",
                       help="Output directory for trained model")
    parser.add_argument("--validate", action="store_true",
                       help="Validate the trained model")
    
    args = parser.parse_args()
    
    # Train the model
    success = train_model(
        data_path=args.data_path,
        epochs=args.epochs,
        batch_size=args.batch_size,
        img_size=args.img_size,
        model_size=args.model_size,
        output_dir=args.output_dir
    )
    
    if success and args.validate:
        model_path = Path(args.output_dir) / "skyguard_raptor_detector.pt"
        validate_model(str(model_path))
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
