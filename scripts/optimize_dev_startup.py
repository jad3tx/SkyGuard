#!/usr/bin/env python3
"""
SkyGuard Development Workstation Startup Optimization

This script optimizes SkyGuard startup for development workstations
while maintaining high resolution for better detection quality.
"""

import sys
import time
import logging
import cv2
import numpy as np
from pathlib import Path
from typing import Optional

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from skyguard.core.config_manager import ConfigManager
from skyguard.core.detector import RaptorDetector
from skyguard.core.camera import CameraManager
from skyguard.core.alert_system import AlertSystem
from skyguard.storage.event_logger import EventLogger
from skyguard.utils.logger import setup_logging


class DevStartupOptimizer:
    """Optimizes SkyGuard startup for development workstations."""
    
    def __init__(self, config_path: str = "config/skyguard.yaml"):
        """Initialize the development startup optimizer."""
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.get_config()
        
        # Setup logging
        setup_logging(self.config.get('logging', {}))
        self.logger = logging.getLogger(__name__)
        
        self.camera_manager = None
        self.detector = None
        self.alert_system = None
        self.event_logger = None
        
    def optimize_dev_startup(self) -> bool:
        """Optimize startup process for development workstation."""
        try:
            self.logger.info("Starting SkyGuard development workstation optimization...")
            
            # Step 1: Initialize components with dev optimizations
            self._initialize_components_dev_optimized()
            
            # Step 2: Perform warmup detections
            self._perform_warmup_detections()
            
            # Step 3: Verify system is ready
            self._verify_system_ready()
            
            self.logger.info("SkyGuard development optimization complete!")
            return True
            
        except Exception as e:
            self.logger.error(f"Development optimization failed: {e}")
            return False
    
    def _initialize_components_dev_optimized(self):
        """Initialize components with development workstation optimizations."""
        self.logger.info("Initializing components for development workstation...")
        
        # Initialize camera with full resolution (development workstation can handle it)
        self.camera_manager = CameraManager(self.config['camera'])
        if not self.camera_manager.initialize():
            self.logger.warning("⚠️ Camera initialization failed, using dummy mode")
            self.camera_manager = None
        
        # Initialize detector with full resolution
        self.detector = RaptorDetector(self.config['ai'])
        if not self.detector.load_model():
            self.logger.warning("⚠️ Model loading failed, using dummy mode")
        
        # Initialize other components
        self.alert_system = AlertSystem(self.config['notifications'])
        self.alert_system.initialize()
        
        self.event_logger = EventLogger(self.config['storage'])
        self.event_logger.initialize()
        
        self.logger.info("Components initialized for development workstation")
    
    def _perform_warmup_detections(self):
        """Perform warmup detections to optimize system performance."""
        warmup_count = self.config.get('system', {}).get('warmup_detections', 3)
        self.logger.info(f"Performing {warmup_count} warmup detections...")
        
        for i in range(warmup_count):
            try:
                # Capture frame
                if self.camera_manager:
                    frame = self.camera_manager.capture_frame()
                    if frame is None:
                        # Create dummy frame for warmup
                        frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
                else:
                    # Create dummy frame for warmup
                    frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
                
                # Run detection (this optimizes the model)
                if self.detector:
                    detections = self.detector.detect(frame)
                    self.logger.debug(f"Warmup detection {i+1}: {len(detections)} objects found")
                
                # Small delay between warmup detections
                time.sleep(0.3)
                
            except Exception as e:
                self.logger.warning(f"Warmup detection {i+1} failed: {e}")
        
        self.logger.info("Warmup detections completed")
    
    def _verify_system_ready(self):
        """Verify that the system is ready for normal operation."""
        self.logger.info("Verifying system readiness...")
        
        # Test camera
        if self.camera_manager:
            frame = self.camera_manager.capture_frame()
            if frame is not None:
                self.logger.info(f"Camera ready - Resolution: {frame.shape[1]}x{frame.shape[0]}")
            else:
                self.logger.warning("⚠️ Camera not ready")
        
        # Test detector
        if self.detector and self.detector.model is not None:
            test_frame = np.zeros((1080, 1920, 3), dtype=np.uint8)
            detections = self.detector.detect(test_frame)
            self.logger.info("Detector ready")
        else:
            self.logger.warning("⚠️ Detector not ready")
        
        # Test alert system
        if self.alert_system:
            self.logger.info("Alert system ready")
        else:
            self.logger.warning("⚠️ Alert system not ready")
        
        # Test event logger
        if self.event_logger:
            self.logger.info("Event logger ready")
        else:
            self.logger.warning("⚠️ Event logger not ready")
    
    def cleanup(self):
        """Cleanup resources."""
        if self.camera_manager:
            self.camera_manager.cleanup()
        if self.event_logger:
            self.event_logger.cleanup()


def main():
    """Main function for development startup optimization."""
    import argparse
    
    parser = argparse.ArgumentParser(description="SkyGuard Development Workstation Startup Optimizer")
    parser.add_argument(
        "--config", 
        default="config/skyguard.yaml",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Create optimizer
    optimizer = DevStartupOptimizer(args.config)
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Run optimization
    success = optimizer.optimize_dev_startup()
    
    # Cleanup
    optimizer.cleanup()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
