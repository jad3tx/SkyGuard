#!/usr/bin/env python3
"""
SkyGuard Installation Test Script

Tests the SkyGuard installation to ensure all components are working correctly.
"""

import sys
import os
import importlib
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_python_version():
    """Test Python version compatibility."""
    print("🐍 Testing Python version...")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python {version.major}.{version.minor} is not supported. Python 3.8+ required.")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True


def test_imports():
    """Test importing required packages."""
    print("\n📦 Testing package imports...")
    
    required_packages = [
        'numpy',
        'opencv-python',  # imported as cv2
        'pyyaml',
        'requests',
        'pygame',
    ]
    
    optional_packages = [
        'torch',
        'ultralytics',
        'twilio',
    ]
    
    failed_imports = []
    
    # Test required packages
    for package in required_packages:
        try:
            if package == 'opencv-python':
                import cv2
                print(f"✅ {package} (cv2) imported successfully")
            elif package == 'pyyaml':
                import yaml
                print(f"✅ {package} (yaml) imported successfully")
            else:
                importlib.import_module(package)
                print(f"✅ {package} imported successfully")
        except ImportError as e:
            print(f"❌ {package} import failed: {e}")
            failed_imports.append(package)
    
    # Test optional packages
    for package in optional_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {package} (optional) imported successfully")
        except ImportError:
            print(f"⚠️  {package} (optional) not available")
    
    if failed_imports:
        print(f"\n❌ Failed to import required packages: {', '.join(failed_imports)}")
        return False
    
    print("\n✅ All required packages imported successfully")
    return True


def test_skyguard_imports():
    """Test importing SkyGuard modules."""
    print("\n🦅 Testing SkyGuard imports...")
    
    try:
        import skyguard
        print("✅ skyguard package imported")
        
        from skyguard.core.config_manager import ConfigManager
        print("✅ ConfigManager imported")
        
        from skyguard.core.camera import CameraManager
        print("✅ CameraManager imported")
        
        from skyguard.core.detector import RaptorDetector
        print("✅ RaptorDetector imported")
        
        from skyguard.core.alert_system import AlertSystem
        print("✅ AlertSystem imported")
        
        from skyguard.storage.event_logger import EventLogger
        print("✅ EventLogger imported")
        
        print("\n✅ All SkyGuard modules imported successfully")
        return True
        
    except ImportError as e:
        print(f"❌ SkyGuard import failed: {e}")
        return False


def test_camera():
    """Test camera functionality."""
    print("\n📷 Testing camera...")
    
    try:
        import cv2
        
        # Try to open default camera
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                height, width = frame.shape[:2]
                print(f"✅ Camera working: {width}x{height} resolution")
                cap.release()
                return True
            else:
                print("❌ Camera opened but failed to capture frame")
                cap.release()
                return False
        else:
            print("⚠️  No camera detected (this is normal if no camera is connected)")
            return True  # Not a failure, just no camera
            
    except Exception as e:
        print(f"❌ Camera test failed: {e}")
        return False


def test_audio():
    """Test audio functionality."""
    print("\n🔊 Testing audio...")
    
    try:
        import pygame
        pygame.mixer.init()
        print("✅ Audio system initialized successfully")
        return True
        
    except Exception as e:
        print(f"❌ Audio test failed: {e}")
        return False


def test_configuration():
    """Test configuration system."""
    print("\n⚙️  Testing configuration...")
    
    try:
        from skyguard.core.config_manager import ConfigManager
        
        # Test with temporary config
        config_manager = ConfigManager("test_config.yaml")
        config = config_manager.load_config()
        
        # Check required sections
        required_sections = ['system', 'camera', 'ai', 'notifications', 'storage']
        for section in required_sections:
            if section in config:
                print(f"✅ Configuration section '{section}' present")
            else:
                print(f"❌ Configuration section '{section}' missing")
                return False
        
        print("✅ Configuration system working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


def test_directories():
    """Test directory structure."""
    print("\n📁 Testing directory structure...")
    
    required_dirs = [
        'skyguard',
        'skyguard/core',
        'skyguard/storage',
        'skyguard/utils',
        'config',
        'docs',
        'tests',
    ]
    
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"✅ Directory '{dir_path}' exists")
        else:
            print(f"❌ Directory '{dir_path}' missing")
            return False
    
    print("✅ Directory structure is correct")
    return True


def test_file_permissions():
    """Test file permissions."""
    print("\n🔐 Testing file permissions...")
    
    # Test if we can create files in the project directory
    try:
        test_file = Path("test_permissions.tmp")
        test_file.write_text("test")
        test_file.unlink()
        print("✅ File permissions are correct")
        return True
        
    except Exception as e:
        print(f"❌ File permission test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🧪 SkyGuard Installation Test")
    print("=" * 50)
    
    tests = [
        test_python_version,
        test_imports,
        test_skyguard_imports,
        test_directories,
        test_file_permissions,
        test_configuration,
        test_camera,
        test_audio,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! SkyGuard is ready to use.")
        print("\nNext steps:")
        print("1. Run: skyguard-setup")
        print("2. Run: skyguard --test-system")
        print("3. Run: skyguard")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        print("\nTroubleshooting:")
        print("1. Make sure all dependencies are installed: pip install -r requirements.txt")
        print("2. Check that you're in the SkyGuard root directory")
        print("3. Verify Python version is 3.8 or higher")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
