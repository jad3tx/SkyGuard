#!/usr/bin/env python3
"""
Universal AirBirds dataset download script.
Provides multiple methods to download the dataset with fallback options.
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import List, Tuple

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def check_datasets_library() -> bool:
    """Check if datasets library is available."""
    try:
        import datasets
        print("✅ datasets library available")
        return True
    except ImportError:
        print("❌ datasets library not available")
        return False


def install_datasets_library() -> bool:
    """Install the datasets library."""
    print("📦 Installing datasets library...")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "datasets>=3.1.0"
        ], capture_output=True, text=True, check=True)
        
        print("✅ datasets library installed")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install datasets library: {e}")
        return False


def run_download_method(method_name: str, script_path: str) -> bool:
    """Run a specific download method."""
    print(f"\n🔄 Trying {method_name}...")
    
    if not os.path.exists(script_path):
        print(f"❌ Script not found: {script_path}")
        return False
    
    try:
        result = subprocess.run([
            sys.executable, script_path
        ], capture_output=True, text=True, check=True)
        
        print(f"✅ {method_name} completed successfully")
        if result.stdout:
            print(f"   Output: {result.stdout}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ {method_name} failed: {e}")
        if e.stdout:
            print(f"   stdout: {e.stdout}")
        if e.stderr:
            print(f"   stderr: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Error in {method_name}: {e}")
        return False


def create_fallback_dataset() -> bool:
    """Create a fallback dataset when all download methods fail."""
    print("\n📝 Creating fallback dataset...")
    
    try:
        # Import the alternative download script
        sys.path.insert(0, str(Path(__file__).parent))
        from download_airbirds_alternative import create_sample_dataset
        
        return create_sample_dataset()
        
    except Exception as e:
        print(f"❌ Failed to create fallback dataset: {e}")
        return False


def main():
    """Main function with multiple download strategies."""
    print("🦅 Universal AirBirds Dataset Download")
    print("=" * 40)
    
    # Define download methods in order of preference
    download_methods = [
        ("Alternative method", "scripts/download_airbirds_alternative.py"),
        ("Install datasets and download", "scripts/install_datasets_and_download.py")
    ]
    
    # Check if datasets library is available
    has_datasets = check_datasets_library()
    
    if not has_datasets:
        print("\n📦 Installing datasets library...")
        if not install_datasets_library():
            print("⚠️ Could not install datasets library, will try alternative methods")
    
    # Try each download method
    for method_name, script_path in download_methods:
        if run_download_method(method_name, script_path):
            print(f"\n✅ Successfully downloaded dataset using {method_name}")
            return True
    
    # If all methods failed, create fallback dataset
    print("\n⚠️ All download methods failed, creating fallback dataset...")
    if create_fallback_dataset():
        print("✅ Fallback dataset created successfully")
        print("\n📋 Note: This is a sample dataset for testing.")
        print("   For the full AirBirds dataset, ensure the datasets library is installed:")
        print("   pip install datasets>=3.1.0")
        return True
    
    print("\n❌ All methods failed")
    return False


if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Dataset download completed!")
        print("📁 Check data/airbirds/ for the dataset")
        print("📊 See data/airbirds/dataset_info.yaml for details")
    else:
        print("\n❌ Dataset download failed")
        print("💡 Try installing the datasets library manually:")
        print("   pip install datasets>=3.1.0")
    
    sys.exit(0 if success else 1)
