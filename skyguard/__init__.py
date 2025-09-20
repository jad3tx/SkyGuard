"""
SkyGuard - Open-Source Raptor Alert System

A low-cost, AI-powered system to protect small poultry farms from raptor attacks.
Uses computer vision and machine learning to detect and alert on airborne predators.

Author: John Daughtridge
Institution: Texas A&M University
Project: Capstone - Master of Engineering Technical Management
"""

__version__ = "0.1.0"
__author__ = "John Daughtridge"
__email__ = "johnd@tamu.edu"
__description__ = "Open-source AI-powered raptor alert system for small poultry farms"

# Core imports
from .core.detector import RaptorDetector
from .core.camera import CameraManager
from .core.alert_system import AlertSystem
from .core.config_manager import ConfigManager

__all__ = [
    "RaptorDetector",
    "CameraManager", 
    "AlertSystem",
    "ConfigManager",
    "__version__",
    "__author__",
    "__email__",
    "__description__",
]
