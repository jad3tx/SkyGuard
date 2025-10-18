#!/usr/bin/env python3
"""
Diagnose datasets library installation issues on Raspberry Pi 5.
This script helps identify why the datasets library isn't working.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def check_system_info():
    """Check system information."""
    print("🔍 System Information")
    print("=" * 20)
    print(f"Platform: {platform.platform()}")
    print(f"Python version: {sys.version}")
    print(f"Architecture: {platform.machine()}")
    print(f"Python executable: {sys.executable}")
    print()


def check_pip_info():
    """Check pip information."""
    print("📦 Pip Information")
    print("=" * 15)
    
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "--version"], 
                              capture_output=True, text=True, check=True)
        print(f"Pip version: {result.stdout.strip()}")
    except Exception as e:
        print(f"❌ Error checking pip: {e}")
    
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "list"], 
                              capture_output=True, text=True, check=True)
        print(f"Installed packages: {len(result.stdout.splitlines()) - 2}")
    except Exception as e:
        print(f"❌ Error listing packages: {e}")
    
    print()


def check_datasets_availability():
    """Check if datasets library is available and what the issue might be."""
    print("🔍 Datasets Library Check")
    print("=" * 25)
    
    # Try to import datasets
    try:
        import datasets
        print("✅ datasets library is available")
        print(f"   Version: {datasets.__version__}")
        return True
    except ImportError as e:
        print(f"❌ datasets library not available: {e}")
    
    # Try to install datasets
    print("\n📦 Attempting to install datasets...")
    try:
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "datasets"
        ], capture_output=True, text=True, check=True)
        print("✅ datasets installation successful")
        print(f"   Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ datasets installation failed")
        print(f"   Error: {e.stderr}")
        
        # Check for specific error patterns
        error_text = e.stderr.lower()
        if "no such file or directory" in error_text:
            print("   💡 Issue: Missing system dependencies")
        elif "permission denied" in error_text:
            print("   💡 Issue: Permission denied - try with --user flag")
        elif "out of memory" in error_text:
            print("   💡 Issue: Insufficient memory")
        elif "connection" in error_text:
            print("   💡 Issue: Network connection problem")
        elif "wheel" in error_text:
            print("   💡 Issue: Missing wheel package")
        
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def try_alternative_installations():
    """Try alternative installation methods."""
    print("\n🔄 Trying Alternative Installation Methods")
    print("=" * 40)
    
    alternatives = [
        ("Install with --user flag", [sys.executable, "-m", "pip", "install", "--user", "datasets"]),
        ("Install with --no-deps flag", [sys.executable, "-m", "pip", "install", "--no-deps", "datasets"]),
        ("Install specific version", [sys.executable, "-m", "pip", "install", "datasets==2.14.0"]),
        ("Install with --upgrade flag", [sys.executable, "-m", "pip", "install", "--upgrade", "datasets"]),
    ]
    
    for method_name, command in alternatives:
        print(f"\nTrying {method_name}...")
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            print(f"✅ {method_name} successful")
            
            # Test if it works
            try:
                import datasets
                print(f"✅ datasets library now available (version: {datasets.__version__})")
                return True
            except ImportError:
                print("❌ datasets library still not importable")
                
        except subprocess.CalledProcessError as e:
            print(f"❌ {method_name} failed: {e.stderr}")
        except Exception as e:
            print(f"❌ {method_name} error: {e}")
    
    return False


def check_dependencies():
    """Check for missing dependencies."""
    print("\n🔍 Checking Dependencies")
    print("=" * 25)
    
    required_packages = [
        "numpy", "pandas", "pyarrow", "requests", "tqdm", "packaging"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - missing")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n📦 Installing missing dependencies: {missing_packages}")
        try:
            result = subprocess.run([
                sys.executable, "-m", "pip", "install"
            ] + missing_packages, capture_output=True, text=True, check=True)
            print("✅ Dependencies installed")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e.stderr}")
    
    return len(missing_packages) == 0


def suggest_solutions():
    """Suggest solutions based on the diagnosis."""
    print("\n💡 Suggested Solutions")
    print("=" * 20)
    
    print("1. Install system dependencies:")
    print("   sudo apt update")
    print("   sudo apt install -y python3-dev python3-pip build-essential")
    print("   sudo apt install -y libffi-dev libssl-dev")
    
    print("\n2. Try installing with user flag:")
    print("   pip install --user datasets")
    
    print("\n3. Try installing specific version:")
    print("   pip install datasets==2.14.0")
    
    print("\n4. Use alternative download method:")
    print("   python scripts/download_airbirds_alternative.py")
    
    print("\n5. Install from conda (if available):")
    print("   conda install -c huggingface datasets")
    
    print("\n6. Use the universal download script:")
    print("   python scripts/download_airbirds_universal.py")


def main():
    """Main diagnostic function."""
    print("🔧 Pi 5 Datasets Library Diagnostic")
    print("=" * 35)
    print()
    
    # Run all checks
    check_system_info()
    check_pip_info()
    
    # Check if datasets is available
    if check_datasets_availability():
        print("✅ datasets library is working!")
        return True
    
    # Try alternative installations
    if try_alternative_installations():
        print("✅ datasets library installed successfully!")
        return True
    
    # Check dependencies
    check_dependencies()
    
    # Suggest solutions
    suggest_solutions()
    
    print("\n❌ datasets library installation failed")
    print("💡 Use alternative download methods or contact support")
    return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
