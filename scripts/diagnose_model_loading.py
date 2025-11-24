#!/usr/bin/env python3
"""
Diagnose model loading issues in SkyGuard.
Helps identify why models can't be loaded.
"""

import sys
from pathlib import Path
from typing import Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def print_section(title: str) -> None:
    """Print a section header."""
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

def check_pytorch() -> bool:
    """Check PyTorch installation and CUDA availability."""
    print_section("🔍 PyTorch Installation")
    
    try:
        import torch
        print(f"✅ PyTorch version: {torch.__version__}")
        
        # Check where torch is loaded from
        import os
        torch_path = os.path.abspath(torch.__file__)
        venv_path = os.path.abspath(str(PROJECT_ROOT / "venv"))
        
        if venv_path in torch_path:
            print(f"⚠️  PyTorch loaded from: venv ({torch_path})")
            print(f"   This may be the wrong version (should use system CUDA version)")
        else:
            print(f"✅ PyTorch loaded from: system ({torch_path})")
        
        # Check CUDA
        if torch.cuda.is_available():
            print(f"✅ CUDA available: True")
            print(f"   CUDA device: {torch.cuda.get_device_name(0)}")
            print(f"   CUDA device count: {torch.cuda.device_count()}")
        else:
            print(f"⚠️  CUDA available: False")
            print(f"   This may cause issues on Jetson")
        
        return True
    except ImportError as e:
        print(f"❌ PyTorch not available: {e}")
        return False
    except Exception as e:
        print(f"❌ Error checking PyTorch: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_ultralytics() -> bool:
    """Check Ultralytics/YOLO installation."""
    print_section("🔍 Ultralytics/YOLO Installation")
    
    try:
        from ultralytics import YOLO
        print(f"✅ Ultralytics/YOLO is available")
        
        # Try to get version
        try:
            import ultralytics
            print(f"   Version: {getattr(ultralytics, '__version__', 'unknown')}")
        except:
            pass
        
        return True
    except ImportError as e:
        print(f"❌ Ultralytics/YOLO not available: {e}")
        print(f"   Install with: pip install ultralytics")
        return False
    except Exception as e:
        print(f"❌ Error checking Ultralytics: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_model_files() -> tuple[bool, Optional[Path], Optional[Path]]:
    """Check if model files exist."""
    print_section("🔍 Model Files")
    
    try:
        from skyguard.core.config_manager import ConfigManager
        
        config_path = PROJECT_ROOT / "config" / "skyguard.yaml"
        if not config_path.exists():
            print(f"❌ Config file not found: {config_path}")
            return False, None, None
        
        config_manager = ConfigManager(str(config_path))
        config = config_manager.get_config()
        ai_config = config.get('ai', {})
        
        # Check main model
        main_model_path_str = ai_config.get('model_path', 'models/yolo11n-seg.pt')
        print(f"\n📦 Main Detection Model:")
        print(f"   Config path: {main_model_path_str}")
        
        # Try to resolve path
        from skyguard.core.detector import BirdSegmentationDetector
        detector = BirdSegmentationDetector(ai_config)
        main_model_path = detector._resolve_model_path(main_model_path_str)
        
        if main_model_path.exists():
            size_mb = main_model_path.stat().st_size / (1024 * 1024)
            print(f"   ✅ Found at: {main_model_path}")
            print(f"   Size: {size_mb:.2f} MB")
            main_found = True
        else:
            print(f"   ❌ Not found at: {main_model_path}")
            print(f"   💡 Download with: python -c \"from ultralytics import YOLO; YOLO('yolo11n-seg.pt')\"")
            main_found = False
        
        # Check species model
        species_model_path_str = ai_config.get('species_model_path')
        species_found = False
        species_model_path = None
        
        if species_model_path_str:
            print(f"\n🐦 Species Classification Model:")
            print(f"   Config path: {species_model_path_str}")
            species_model_path = detector._resolve_model_path(species_model_path_str)
            
            if species_model_path.exists():
                size_mb = species_model_path.stat().st_size / (1024 * 1024)
                print(f"   ✅ Found at: {species_model_path}")
                print(f"   Size: {size_mb:.2f} MB")
                species_found = True
            else:
                print(f"   ⚠️  Not found at: {species_model_path}")
                print(f"   (This is optional)")
        else:
            print(f"\n🐦 Species Classification Model:")
            print(f"   ⚠️  Not configured (optional)")
        
        return main_found, main_model_path if main_found else None, species_model_path if species_found else None
        
    except Exception as e:
        print(f"❌ Error checking model files: {e}")
        import traceback
        traceback.print_exc()
        return False, None, None

def test_model_loading(model_path: Optional[Path]) -> bool:
    """Test loading a model."""
    print_section("🔬 Model Loading Test")
    
    if not model_path:
        print("⚠️  No model file to test")
        return False
    
    try:
        from ultralytics import YOLO
        import torch
        
        print(f"   Attempting to load: {model_path}")
        print(f"   PyTorch device: {'CUDA' if torch.cuda.is_available() else 'CPU'}")
        
        # Try loading the model
        model = YOLO(str(model_path))
        print(f"   ✅ Model loaded successfully!")
        
        # Try to get model info
        try:
            info = model.info()
            if info:
                print(f"   Model info available")
        except:
            print(f"   ⚠️  Could not get model info (this is okay)")
        
        # Test a simple inference
        try:
            import numpy as np
            # Create a dummy image
            dummy_img = np.zeros((640, 640, 3), dtype=np.uint8)
            results = model(dummy_img, verbose=False)
            print(f"   ✅ Model inference test passed!")
        except Exception as e:
            print(f"   ⚠️  Inference test failed: {e}")
            print(f"   (This might be okay if it's just a shape issue)")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Failed to load model: {e}")
        import traceback
        traceback.print_exc()
        
        # Provide specific guidance
        if "CUDA" in str(e) or "cuda" in str(e).lower():
            print(f"\n   💡 CUDA-related error detected")
            print(f"   Try: export CUDA_VISIBLE_DEVICES=0")
        elif "version" in str(e).lower() or "compatible" in str(e).lower():
            print(f"\n   💡 Version compatibility issue")
            print(f"   Try updating ultralytics: pip install --upgrade ultralytics")
        elif "file" in str(e).lower() or "not found" in str(e).lower():
            print(f"\n   💡 File access issue")
            print(f"   Check file permissions and path")
        
        return False

def check_device_detection() -> None:
    """Check device detection."""
    print_section("🔍 Device Detection")
    
    try:
        from skyguard.utils.platform import get_recommended_device, is_jetson
        
        device = get_recommended_device()
        jetson = is_jetson()
        
        print(f"   Platform: {'Jetson' if jetson else 'Other'}")
        print(f"   Recommended device: {device}")
        
        import torch
        if torch.cuda.is_available():
            print(f"   CUDA available: True")
            print(f"   Actual device: cuda:0")
        else:
            print(f"   CUDA available: False")
            print(f"   Actual device: cpu")
            if jetson:
                print(f"   ⚠️  WARNING: Jetson detected but CUDA not available!")
                print(f"   This suggests torch is not using the system CUDA version")
        
    except Exception as e:
        print(f"   ❌ Error checking device: {e}")
        import traceback
        traceback.print_exc()

def main() -> int:
    """Main diagnostic function."""
    print("=" * 60)
    print("SkyGuard Model Loading Diagnostic")
    print("=" * 60)
    
    # Check PyTorch
    pytorch_ok = check_pytorch()
    
    # Check Ultralytics
    ultralytics_ok = check_ultralytics()
    
    # Check device detection
    check_device_detection()
    
    # Check model files
    main_found, main_model_path, species_model_path = check_model_files()
    
    # Test model loading
    if main_found and main_model_path:
        model_ok = test_model_loading(main_model_path)
    else:
        model_ok = False
        print_section("❌ Cannot Test Model Loading")
        print("   Model file not found. Please download it first.")
        print("\n   Quick fix:")
        print("   cd ~/SkyGuard")
        print("   source venv/bin/activate")
        print("   python -c \"from ultralytics import YOLO; YOLO('yolo11n-seg.pt')\"")
        print("   mv yolo11n-seg.pt models/")
    
    # Summary
    print_section("📋 Summary")
    
    if pytorch_ok:
        print("✅ PyTorch: OK")
    else:
        print("❌ PyTorch: FAILED")
    
    if ultralytics_ok:
        print("✅ Ultralytics: OK")
    else:
        print("❌ Ultralytics: FAILED")
    
    if main_found:
        print("✅ Main model file: Found")
    else:
        print("❌ Main model file: NOT FOUND")
    
    if model_ok:
        print("✅ Model loading: OK")
        print("\n✅ All checks passed! Model should work.")
        return 0
    else:
        print("❌ Model loading: FAILED")
        print("\n❌ Issues detected. See details above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

