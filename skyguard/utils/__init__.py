"""
SkyGuard Utilities Module

Contains utility functions and helper classes for the SkyGuard system.
"""

from .logger import setup_logging

# Platform detection (optional import to avoid circular dependencies)
try:
    from .platform import (
        PlatformDetector,
        get_platform_detector,
        detect_platform,
        is_jetson,
        is_raspberry_pi,
        get_recommended_device,
    )
    __all__ = [
        "setup_logging",
        "PlatformDetector",
        "get_platform_detector",
        "detect_platform",
        "is_jetson",
        "is_raspberry_pi",
        "get_recommended_device",
    ]
except ImportError:
    # Platform detection not available (shouldn't happen in normal operation)
    __all__ = [
        "setup_logging",
    ]
