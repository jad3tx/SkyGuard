#!/usr/bin/env python3
"""
SkyGuard Web Interface Demo

This script demonstrates how to use the SkyGuard web interface
and provides sample data for testing.
"""

import sys
import os
import requests
from pathlib import Path

# Add the SkyGuard directory to the path
skyguard_dir = Path(__file__).parent.parent
sys.path.insert(0, str(skyguard_dir))

def create_sample_config():
    """Create a sample configuration file for testing."""
    config_path = skyguard_dir / 'config' / 'skyguard.yaml'
    config_path.parent.mkdir(exist_ok=True)
    
    sample_config = {
        'system': {
            'detection_interval': 1.0,
            'save_detection_frames': True,
            'max_detection_history': 1000,
        },
        'camera': {
            'source': 0,
            'width': 640,
            'height': 480,
            'fps': 30,
            'rotation': 0,
            'flip_horizontal': False,
            'flip_vertical': False,
        },
        'ai': {
            'model_path': 'models/raptor_detector.pt',
            'model_type': 'yolo',
            'confidence_threshold': 0.5,
            'nms_threshold': 0.4,
            'input_size': [640, 640],
            'classes': ['raptor', 'hawk', 'eagle', 'owl'],
        },
        'notifications': {
            'audio': {
                'enabled': True,
                'sound_file': 'sounds/raptor_alert.wav',
                'volume': 0.8,
            },
            'push': {
                'enabled': False,
                'api_key': '',
                'device_id': '',
            },
            'sms': {
                'enabled': False,
                'account_sid': '',
                'auth_token': '',
                'from_number': '',
                'to_numbers': [],
            },
            'email': {
                'enabled': False,
                'smtp_server': '',
                'smtp_port': 587,
                'username': '',
                'password': '',
                'from_email': '',
                'to_emails': [],
            },
        },
        'storage': {
            'database_path': 'data/skyguard.db',
            'detection_images_path': 'data/detections',
            'log_retention_days': 30,
        },
        'logging': {
            'level': 'INFO',
            'file': 'logs/skyguard.log',
            'max_size_mb': 10,
            'backup_count': 5,
        },
        'hardware': {
            'platform': 'auto',
            'gpio_enabled': False,
            'led_pin': 18,
            'buzzer_pin': 19,
        },
    }
    
    import yaml
    with open(config_path, 'w') as f:
        yaml.dump(sample_config, f, default_flow_style=False, indent=2)
    
    print(f"Created sample configuration at {config_path}")

def test_web_interface(base_url="http://localhost:5000"):
    """Test the web interface API endpoints."""
    print(f"Testing SkyGuard web interface at {base_url}")
    
    try:
        # Test system status
        print("\n1. Testing system status...")
        response = requests.get(f"{base_url}/api/system/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ System status: {data.get('success', False)}")
            if data.get('success'):
                status = data.get('status', {})
                print(f"  - Database connected: {status.get('database_connected', False)}")
                print(f"  - Config loaded: {status.get('config_loaded', False)}")
        else:
            print(f"✗ System status failed: {response.status_code}")
    
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to web interface. Is it running?")
        return False
    except Exception as e:
        print(f"✗ Error testing system status: {e}")
        return False
    
    try:
        # Test configuration
        print("\n2. Testing configuration...")
        response = requests.get(f"{base_url}/api/config", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Configuration loaded: {data.get('success', False)}")
            if data.get('success'):
                config = data.get('config', {})
                print(f"  - Detection interval: {config.get('system', {}).get('detection_interval', 'N/A')}")
                print(f"  - Confidence threshold: {config.get('ai', {}).get('confidence_threshold', 'N/A')}")
        else:
            print(f"✗ Configuration failed: {response.status_code}")
    
    except Exception as e:
        print(f"✗ Error testing configuration: {e}")
    
    try:
        # Test detections
        print("\n3. Testing detections...")
        response = requests.get(f"{base_url}/api/detections?limit=5", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Detections loaded: {data.get('success', False)}")
            if data.get('success'):
                detections = data.get('detections', [])
                print(f"  - Found {len(detections)} detections")
                for detection in detections[:3]:  # Show first 3
                    print(f"    * {detection.get('class_name', 'Unknown')} ({detection.get('confidence', 0):.2f})")
        else:
            print(f"✗ Detections failed: {response.status_code}")
    
    except Exception as e:
        print(f"✗ Error testing detections: {e}")
    
    try:
        # Test statistics
        print("\n4. Testing statistics...")
        response = requests.get(f"{base_url}/api/stats?days=7", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Statistics loaded: {data.get('success', False)}")
            if data.get('success'):
                stats = data.get('stats', {})
                print(f"  - Total detections: {stats.get('total_detections', 0)}")
                print(f"  - Period: {stats.get('period_days', 0)} days")
        else:
            print(f"✗ Statistics failed: {response.status_code}")
    
    except Exception as e:
        print(f"✗ Error testing statistics: {e}")
    
    print("\n✓ Web interface test completed!")
    return True

def main():
    """Main demo function."""
    print("SkyGuard Web Interface Demo")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not (skyguard_dir / 'skyguard').exists():
        print(f"Error: SkyGuard directory not found at {skyguard_dir}")
        print("Please run this script from the SkyGuard project root.")
        sys.exit(1)
    
    # Create sample configuration if it doesn't exist
    config_path = skyguard_dir / 'config' / 'skyguard.yaml'
    if not config_path.exists():
        print("Creating sample configuration...")
        create_sample_config()
    else:
        print(f"Using existing configuration at {config_path}")
    
    # Test web interface
    print("\nTesting web interface...")
    success = test_web_interface()
    
    if success:
        print("\n🎉 Web interface is working correctly!")
        print("\nTo start the web interface manually:")
        print("  python skyguard/web/run_web.py")
        print("  # or")
        print("  python scripts/start_web_interface.py")
        print("\nThen open your browser to: http://localhost:5000")
    else:
        print("\n❌ Web interface test failed.")
        print("Make sure the web interface is running before testing.")

if __name__ == '__main__':
    main()
