#!/usr/bin/env python3
"""
Train a YOLO model on the AirBirds dataset for SkyGuard.

This script trains a custom YOLO model specifically for bird detection
using the AirBirds dataset.
"""

import sys
from pathlib import Path
import yaml
import argparse

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def train_model():
    """Train a YOLO model on the AirBirds dataset."""
    print("🤖 Training YOLO model on AirBirds dataset...")
    
    try:
        from ultralytics import YOLO
        
        # Resolve dataset path relative to repository root
        repo_root = Path(__file__).parent.parent
        dataset_yaml = (repo_root / "data" / "airbirds" / "dataset.yaml").resolve()
        if not dataset_yaml.exists():
            print("❌ Dataset not found. Please run download_airbirds_universal.py first.")
            return False
        
        # Load pre-trained YOLO model
        print("Loading pre-trained YOLOv8n model...")
        model = YOLO('yolov8n.pt')  # Use nano version for faster training
        
        # Training parameters
        training_params = {
            'data': str(dataset_yaml),
            'epochs': 50,  # Reduced for testing
            'imgsz': 640,
            'batch': 8,    # Reduced batch size for memory
            'name': 'airbirds_raptor_detector',
            'project': str((repo_root / 'models' / 'training').resolve()),
            'exist_ok': True,
            'patience': 10,  # Early stopping
            'save_period': 10,  # Save checkpoint every 10 epochs
            'device': 'cpu',  # Use CPU for compatibility
            'workers': 2,     # Number of workers
            'verbose': True
        }
        
        print("Starting training with parameters:")
        for key, value in training_params.items():
            print(f"   - {key}: {value}")
        
        # Train the model
        print("\n🚀 Starting training...")
        _ = model.train(**training_params)
        
        print("✅ Training completed!")
        
        # Get the best model path
        best_model_path = (
            repo_root
            / "models"
            / "training"
            / "airbirds_raptor_detector"
            / "weights"
            / "best.pt"
        )
        if best_model_path.exists():
            # Copy to main models directory
            import shutil
            target_path = (repo_root / "models" / "airbirds_raptor_detector.pt")
            shutil.copy2(best_model_path, target_path)
            print(f"✅ Best model saved to {target_path}")
            
            # Update SkyGuard config
            update_config(target_path)
            
        return True
        
    except Exception as e:
        print(f"❌ Training failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def update_config(model_path):
    """Update SkyGuard configuration to use the new model."""
    print("\n⚙️  Updating SkyGuard configuration...")
    
    try:
        repo_root = Path(__file__).parent.parent
        config_path = repo_root / "config" / "skyguard.yaml"
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Update AI config
            config['ai']['model_path'] = str(model_path)
            config['ai']['classes'] = ['bird']
            config['ai']['confidence_threshold'] = 0.3
            
            with open(config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, indent=2)
            
            print("✅ SkyGuard config updated!")
            print(f"   - Model path: {model_path}")
            print(f"   - Classes: {config['ai']['classes']}")
            print(
                f"   - Confidence threshold: "
                f"{config['ai']['confidence_threshold']}"
            )
        
    except Exception as e:
        print(f"❌ Failed to update config: {e}")


def test_model():
    """Test the trained model."""
    print("\n🧪 Testing the trained model...")
    
    try:
        from ultralytics import YOLO
        
        repo_root = Path(__file__).parent.parent
        model_path = repo_root / "models" / "airbirds_raptor_detector.pt"
        if not model_path.exists():
            print("❌ Trained model not found.")
            return False
        
        # Load the trained model
        model = YOLO(str(model_path))
        
        # Test on a sample image
        sample_dir = repo_root / "data" / "airbirds" / "samples"
        if sample_dir.exists():
            sample_images = list(sample_dir.glob("*.jpg"))
            if sample_images:
                test_image = sample_images[0]
                print(f"Testing on: {test_image}")
                
                # Run inference
                results = model(str(test_image))
                
                # Print results
                for result in results:
                    if result.boxes is not None:
                        print(f"✅ Detected {len(result.boxes)} objects")
                        for box in result.boxes:
                            conf = box.conf[0].item()
                            print(f"   - Confidence: {conf:.2f}")
                    else:
                        print("❌ No objects detected")
                
                return True
        
        print("❌ No sample images found for testing")
        return False
        
    except Exception as e:
        print(f"❌ Testing failed: {e}")
        return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Train YOLO on AirBirds dataset"
    )
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Run non-interactively and start training",
    )
    args = parser.parse_args()

    print("AirBirds Model Training Script")
    print("=" * 50)

    # Check if dataset exists relative to repo root
    repo_root = Path(__file__).parent.parent
    dataset_yaml = repo_root / "data" / "airbirds" / "dataset.yaml"
    if not dataset_yaml.exists():
        print("❌ Dataset not found. Please run download_airbirds_universal.py first.")
        return False

    # Confirm unless --yes
    if not args.yes:
        print("This will train a YOLO model on the AirBirds dataset.")
        print("Training may take 30-60 minutes depending on your hardware.")
        try:
            response = input("Do you want to proceed? (y/N): ").strip().lower()
        except EOFError:
            response = "n"
        if response not in ["y", "yes"]:
            print("Training cancelled.")
            return True

    # Train the model
    success = train_model()

    if success:
        # Test the model
        test_model()

        print("\nTraining complete!")
        print("\nNext steps:")
    print("1. Test SkyGuard with the new model: python -m skyguard.main")
    print("2. Adjust confidence threshold in config/skyguard.yaml if needed")
    print("3. The model is now ready for raptor detection!")

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
