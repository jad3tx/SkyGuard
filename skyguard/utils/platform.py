"""
Platform Detection Utility for SkyGuard System

Detects the hardware platform (Raspberry Pi, Jetson, etc.) and provides
platform-specific configuration recommendations.
"""

import os
import platform
import logging
from typing import Dict, Optional, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class PlatformDetector:
    """Detects and provides information about the current hardware platform."""
    
    def __init__(self) -> None:
        """Initialize the platform detector."""
        self._platform_info: Optional[Dict[str, any]] = None
        self._detect_platform()
    
    def _detect_platform(self) -> None:
        """Detect the current platform and gather information."""
        platform_type = "unknown"
        platform_name = "Unknown"
        is_gpu_available = False
        gpu_name = None
        is_arm = False
        is_64bit = False
        
        # Check for Jetson
        if self._is_jetson():
            platform_type = "jetson"
            platform_name = self._get_jetson_model()
            is_gpu_available = True  # Jetson always has GPU
            gpu_name = "NVIDIA GPU (Jetson)"
            is_arm = True
            is_64bit = True
        # Check for Raspberry Pi
        elif self._is_raspberry_pi():
            platform_type = "raspberry_pi"
            platform_name = self._get_raspberry_pi_model()
            is_arm = True
            is_64bit = platform.machine() in ('aarch64', 'arm64')
        # Check for other ARM devices
        elif platform.machine().startswith('arm') or platform.machine() == 'aarch64':
            platform_type = "arm"
            platform_name = f"ARM {platform.machine()}"
            is_arm = True
            is_64bit = platform.machine() in ('aarch64', 'arm64')
        # Check for x86/x64
        elif platform.machine() in ('x86_64', 'AMD64'):
            platform_type = "x86_64"
            platform_name = "x86_64 Desktop"
            is_64bit = True
        else:
            platform_type = "unknown"
            platform_name = platform.machine()
        
        # Check for CUDA/GPU availability
        if not is_gpu_available:
            is_gpu_available, gpu_name = self._check_cuda_availability()
        
        self._platform_info = {
            'type': platform_type,
            'name': platform_name,
            'is_gpu_available': is_gpu_available,
            'gpu_name': gpu_name,
            'is_arm': is_arm,
            'is_64bit': is_64bit,
            'machine': platform.machine(),
            'system': platform.system(),
            'processor': platform.processor(),
        }
    
    def _is_jetson(self) -> bool:
        """Check if running on NVIDIA Jetson.
        
        Returns:
            True if running on Jetson, False otherwise
        """
        # Check for Jetson-specific files
        jetson_indicators = [
            '/etc/nv_tegra_release',  # Jetson system file
            '/proc/device-tree/model',  # Device tree (may contain Jetson info)
        ]
        
        for indicator in jetson_indicators:
            if os.path.exists(indicator):
                try:
                    with open(indicator, 'r') as f:
                        content = f.read()
                        if 'jetson' in content.lower() or 'tegra' in content.lower():
                            return True
                except Exception:
                    pass
        
        # Check environment variables
        if os.environ.get('JETSON_VERSION'):
            return True
        
        # Check for nvidia-smi (though this could be any NVIDIA GPU)
        # We'll use this as a secondary indicator
        try:
            import subprocess
            result = subprocess.run(
                ['nvidia-smi', '-L'],
                capture_output=True,
                timeout=2
            )
            if result.returncode == 0 and 'jetson' in result.stdout.decode().lower():
                return True
        except Exception:
            pass
        
        return False
    
    def _get_jetson_model(self) -> str:
        """Get the Jetson model name.
        
        Returns:
            Jetson model name or "NVIDIA Jetson"
        """
        # Try to read from device tree
        if os.path.exists('/proc/device-tree/model'):
            try:
                with open('/proc/device-tree/model', 'r') as f:
                    model = f.read().strip()
                    if 'jetson' in model.lower():
                        return model
            except Exception:
                pass
        
        # Try environment variable
        jetson_version = os.environ.get('JETSON_VERSION', '')
        if jetson_version:
            return f"NVIDIA Jetson {jetson_version}"
        
        # Try to detect from nvidia-smi or other methods
        try:
            import subprocess
            result = subprocess.run(
                ['cat', '/proc/device-tree/model'],
                capture_output=True,
                timeout=2
            )
            if result.returncode == 0:
                model = result.stdout.decode().strip()
                if model:
                    return model
        except Exception:
            pass
        
        return "NVIDIA Jetson"
    
    def _is_raspberry_pi(self) -> bool:
        """Check if running on Raspberry Pi.
        
        Returns:
            True if running on Raspberry Pi, False otherwise
        """
        if os.path.exists('/proc/device-tree/model'):
            try:
                with open('/proc/device-tree/model', 'r') as f:
                    model = f.read().strip()
                    if 'raspberry pi' in model.lower():
                        return True
            except Exception:
                pass
        
        if os.path.exists('/etc/os-release'):
            try:
                with open('/etc/os-release', 'r') as f:
                    content = f.read().lower()
                    if 'raspbian' in content or 'raspberry' in content:
                        return True
            except Exception:
                pass
        
        return False
    
    def _get_raspberry_pi_model(self) -> str:
        """Get the Raspberry Pi model name.
        
        Returns:
            Raspberry Pi model name or "Raspberry Pi"
        """
        if os.path.exists('/proc/device-tree/model'):
            try:
                with open('/proc/device-tree/model', 'r') as f:
                    model = f.read().strip()
                    if 'raspberry pi' in model.lower():
                        return model
            except Exception:
                pass
        
        return "Raspberry Pi"
    
    def _check_cuda_availability(self) -> Tuple[bool, Optional[str]]:
        """Check if CUDA is available.
        
        Returns:
            Tuple of (is_available, gpu_name)
        """
        try:
            import torch
            if torch.cuda.is_available():
                gpu_name = torch.cuda.get_device_name(0) if torch.cuda.device_count() > 0 else "CUDA GPU"
                return True, gpu_name
        except ImportError:
            pass
        except Exception as e:
            logger.debug(f"Error checking CUDA: {e}")
        
        return False, None
    
    def get_platform_info(self) -> Dict[str, any]:
        """Get platform information.
        
        Returns:
            Dictionary with platform information
        """
        return self._platform_info.copy() if self._platform_info else {}
    
    def is_jetson(self) -> bool:
        """Check if running on Jetson.
        
        Returns:
            True if running on Jetson, False otherwise
        """
        return self._platform_info and self._platform_info.get('type') == 'jetson'
    
    def is_raspberry_pi(self) -> bool:
        """Check if running on Raspberry Pi.
        
        Returns:
            True if running on Raspberry Pi, False otherwise
        """
        return self._platform_info and self._platform_info.get('type') == 'raspberry_pi'
    
    def is_gpu_available(self) -> bool:
        """Check if GPU is available.
        
        Returns:
            True if GPU is available, False otherwise
        """
        return self._platform_info and self._platform_info.get('is_gpu_available', False)
    
    def get_recommended_device(self) -> str:
        """Get recommended PyTorch device for this platform.
        
        Returns:
            Device string ('cuda', 'cuda:0', or 'cpu')
        """
        if self.is_jetson() or (self.is_gpu_available() and self._platform_info.get('gpu_name')):
            # Jetson should use CUDA
            return 'cuda:0' if self.is_jetson() else 'cuda'
        return 'cpu'
    
    def get_requirements_file(self) -> str:
        """Get the recommended requirements file for this platform.
        
        Returns:
            Requirements file name
        """
        if self.is_jetson():
            return 'requirements-jetson.txt'
        elif self.is_raspberry_pi():
            return 'requirements-pi.txt'
        else:
            return 'requirements.txt'


# Global instance
_platform_detector: Optional[PlatformDetector] = None


def get_platform_detector() -> PlatformDetector:
    """Get the global platform detector instance.
    
    Returns:
        PlatformDetector instance
    """
    global _platform_detector
    if _platform_detector is None:
        _platform_detector = PlatformDetector()
    return _platform_detector


def detect_platform() -> Dict[str, any]:
    """Detect and return platform information.
    
    Returns:
        Dictionary with platform information
    """
    return get_platform_detector().get_platform_info()


def is_jetson() -> bool:
    """Check if running on Jetson.
    
    Returns:
        True if running on Jetson, False otherwise
    """
    return get_platform_detector().is_jetson()


def is_raspberry_pi() -> bool:
    """Check if running on Raspberry Pi.
    
    Returns:
        True if running on Raspberry Pi, False otherwise
    """
    return get_platform_detector().is_raspberry_pi()


def get_recommended_device() -> str:
    """Get recommended PyTorch device for this platform.
    
    Returns:
        Device string ('cuda', 'cuda:0', or 'cpu')
    """
    return get_platform_detector().get_recommended_device()

