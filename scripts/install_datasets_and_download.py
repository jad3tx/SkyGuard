#!/usr/bin/env python3
"""
Install datasets library and download AirBirds dataset.
This script ensures the datasets library is available before downloading.
"""

import os
import sys
import subprocess
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def install_datasets_library() -> bool:
    """Install the datasets library."""
    print("📦 Installing datasets library...")
    
    try:
        # Try to import first
        import datasets
        print("✅ datasets library already available")
        return True
    except ImportError:
        print("Installing datasets library...")
        
        try:
            # Install using pip
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "datasets>=3.1.0"
            ], capture_output=True, text=True, check=True)
            
            print("✅ datasets library installed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install datasets library: {e}")
            print(f"   stdout: {e.stdout}")
            print(f"   stderr: {e.stderr}")
            return False
        except Exception as e:
            print(f"❌ Error installing datasets library: {e}")
            return False


def run_original_download_script() -> bool:
    """Run the original AirBirds download script."""
    print("🦅 Running original AirBirds download script...")
    
    # Try different download scripts in order of preference
    scripts_to_try = [
        "scripts/download_airbirds_alternative.py"
    ]
    
    for script_path in scripts_to_try:
        if os.path.exists(script_path):
            print(f"Trying {script_path}...")
            try:
                result = subprocess.run([
                    sys.executable, script_path
                ], check=True, capture_output=True, text=True)
                
                print("✅ Download script completed successfully")
                print(f"   Output: {result.stdout}")
                return True
                
            except subprocess.CalledProcessError as e:
                print(f"❌ Script {script_path} failed: {e}")
                print(f"   stdout: {e.stdout}")
                print(f"   stderr: {e.stderr}")
                continue
            except Exception as e:
                print(f"❌ Error running {script_path}: {e}")
                continue
    
    print("❌ All download scripts failed")
    return False


def main():
    """Main function."""
    print("🛠️ AirBirds Dataset Setup with Auto-Install")
    print("=" * 45)
    
    # Step 1: Install datasets library
    if not install_datasets_library():
        print("❌ Failed to install datasets library")
        return False
    
    # Step 2: Run download script
    if not run_original_download_script():
        print("❌ Failed to download dataset")
        return False
    
    print("\n✅ AirBirds dataset setup completed successfully!")
    print("\n📁 Dataset location: data/airbirds/")
    print("📊 Check dataset_info.yaml for details")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
