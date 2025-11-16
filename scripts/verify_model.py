#!/usr/bin/env python3
"""
Verify that the species model exists and can be loaded.
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from skyguard.core.config_manager import ConfigManager
from skyguard.core.detector import RaptorDetector

def main():
    """Verify model configuration and existence."""
    print("=" * 60)
    print("SkyGuard Model Verification")
    print("=" * 60)
    
    # Load config
    config_path = PROJECT_ROOT / "config" / "skyguard.yaml"
    if not config_path.exists():
        print(f"❌ Config file not found: {config_path}")
        return 1
    
    config_manager = ConfigManager(str(config_path))
    config = config_manager.get_config()
    ai_config = config.get('ai', {})
    
    # Check species model path
    species_model_path = ai_config.get('species_model_path')
    if not species_model_path:
        print("❌ species_model_path not configured in config/skyguard.yaml")
        return 1
    
    print(f"\n📋 Configuration:")
    print(f"   species_model_path: {species_model_path}")
    print(f"   species_backend: {ai_config.get('species_backend', 'N/A')}")
    print(f"   species_input_size: {ai_config.get('species_input_size', 'N/A')}")
    
    # Try to resolve path
    print(f"\n🔍 Checking model file...")
    
    # Normalize path (handle both Windows and Linux)
    normalized_path = str(species_model_path).replace('\\', '/')
    
    # Try multiple locations
    candidates = [
        Path(species_model_path),  # As given
        Path(normalized_path),     # Normalized
        PROJECT_ROOT / species_model_path,
        PROJECT_ROOT / normalized_path,
        Path.cwd() / species_model_path,
        Path.cwd() / normalized_path,
    ]
    
    found = False
    for candidate in candidates:
        if candidate.exists():
            print(f"   ✅ Found at: {candidate.resolve()}")
            print(f"   Size: {candidate.stat().st_size / (1024*1024):.2f} MB")
            found = True
            break
    
    if not found:
        print(f"   ❌ Model file not found!")
        print(f"\n   Searched in:")
        for candidate in candidates:
            print(f"     - {candidate}")
        print(f"\n   Project root: {PROJECT_ROOT}")
        print(f"   Current directory: {Path.cwd()}")
        print(f"\n   💡 Solutions:")
        print(f"   1. Copy the model file to: {PROJECT_ROOT / normalized_path}")
        print(f"   2. Train the model on this system")
        print(f"   3. Update species_model_path in config/skyguard.yaml")
        return 1
    
    # Try to load the model
    print(f"\n🔬 Testing model loading...")
    try:
        detector = RaptorDetector(ai_config)
        if detector.load_model():
            if detector.species_model:
                print(f"   ✅ Species model loaded successfully!")
                try:
                    info = detector.species_model.info()
                    if info:
                        layers, params, gradients, gflops = info
                        print(f"   Model info: {layers} layers, {params:,} params, {gflops:.1f} GFLOPs")
                except Exception:
                    pass
            else:
                print(f"   ⚠️  Model file exists but failed to load")
                return 1
        else:
            print(f"   ❌ Failed to load model")
            return 1
    except Exception as e:
        print(f"   ❌ Error loading model: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print(f"\n✅ All checks passed!")
    return 0

if __name__ == "__main__":
    sys.exit(main())

