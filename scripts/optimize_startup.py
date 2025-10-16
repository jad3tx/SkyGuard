#!/usr/bin/env python3
"""
SkyGuard Startup Optimization Script

This script optimizes the SkyGuard startup process to reduce detection delays
by implementing warmup detection and resource optimization.
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


class SkyGuardStartupOptimizer:
    """Optimizes SkyGuard startup for faster detection."""
    
    def __init__(self, config_path: str = "config/skyguard.yaml"):
        """Initialize the startup optimizer."""
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.get_config()
        
        # Setup logging
        setup_logging(self.config.get('logging', {}))
        self.logger = logging.getLogger(__name__)
        
        self.camera_manager = None
        self.detector = None
        self.alert_system = None
        self.event_logger = None
        
    def optimize_startup(self) -> bool:
        """Optimize startup process for faster detection."""
        try:
            self.logger.info("🚀 Starting SkyGuard startup optimization...")
            
            # Step 1: Initialize components with optimizations
            self._initialize_components_optimized()
            
            # Step 2: Perform warmup detections
            self._perform_warmup_detections()
            
            # Step 3: Verify system is ready
            self._verify_system_ready()
            
            self.logger.info("✅ SkyGuard startup optimization complete!")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Startup optimization failed: {e}")
            return False
    
    def _initialize_components_optimized(self):
        """Initialize components with startup optimizations."""
        self.logger.info("🔧 Initializing components with optimizations...")
        
        # Initialize camera with lower resolution for faster startup
        camera_config = self.config['camera'].copy()
        camera_config['width'] = 320  # Lower resolution for warmup
        camera_config['height'] = 240
        camera_config['fps'] = 10  # Lower FPS for warmup
        
        self.camera_manager = CameraManager(camera_config)
        if not self.camera_manager.initialize():
            self.logger.warning("⚠️ Camera initialization failed, using dummy mode")
            self.camera_manager = None
        
        # Initialize detector with optimizations
        ai_config = self.config['ai'].copy()
        ai_config['input_size'] = 320  # Lower input size for faster processing
        
        self.detector = RaptorDetector(ai_config)
        if not self.detector.load_model():
            self.logger.warning("⚠️ Model loading failed, using dummy mode")
        
        # Initialize other components
        self.alert_system = AlertSystem(self.config['notifications'])
        self.alert_system.initialize()
        
        self.event_logger = EventLogger(self.config['storage'])
        self.event_logger.initialize()
        
        self.logger.info("✅ Components initialized with optimizations")
    
    def _perform_warmup_detections(self):
        """Perform warmup detections to optimize system performance."""
        warmup_count = self.config.get('system', {}).get('warmup_detections', 5)
        self.logger.info(f"🔥 Performing {warmup_count} warmup detections...")
        
        for i in range(warmup_count):
            try:
                # Capture frame
                if self.camera_manager:
                    frame = self.camera_manager.capture_frame()
                    if frame is None:
                        # Create dummy frame for warmup
                        frame = np.zeros((240, 320, 3), dtype=np.uint8)
                else:
                    # Create dummy frame for warmup
                    frame = np.zeros((240, 320, 3), dtype=np.uint8)
                
                # Run detection (this optimizes the model)
                if self.detector:
                    detections = self.detector.detect(frame)
                    self.logger.debug(f"Warmup detection {i+1}: {len(detections)} objects found")
                
                # Small delay between warmup detections
                time.sleep(0.5)
                
            except Exception as e:
                self.logger.warning(f"Warmup detection {i+1} failed: {e}")
        
        self.logger.info("✅ Warmup detections completed")
    
    def _verify_system_ready(self):
        """Verify that the system is ready for normal operation."""
        self.logger.info("🔍 Verifying system readiness...")
        
        # Test camera
        if self.camera_manager:
            frame = self.camera_manager.capture_frame()
            if frame is not None:
                self.logger.info("✅ Camera ready")
            else:
                self.logger.warning("⚠️ Camera not ready")
        
        # Test detector
        if self.detector and self.detector.model is not None:
            test_frame = np.zeros((240, 320, 3), dtype=np.uint8)
            detections = self.detector.detect(test_frame)
            self.logger.info("✅ Detector ready")
        else:
            self.logger.warning("⚠️ Detector not ready")
        
        # Test alert system
        if self.alert_system:
            self.logger.info("✅ Alert system ready")
        else:
            self.logger.warning("⚠️ Alert system not ready")
        
        # Test event logger
        if self.event_logger:
            self.logger.info("✅ Event logger ready")
        else:
            self.logger.warning("⚠️ Event logger not ready")
    
    def cleanup(self):
        """Cleanup resources."""
        if self.camera_manager:
            self.camera_manager.cleanup()
        if self.event_logger:
            self.event_logger.cleanup()


def main():
    """Main function for startup optimization."""
    import argparse
    
    parser = argparse.ArgumentParser(description="SkyGuard Startup Optimizer")
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
    optimizer = SkyGuardStartupOptimizer(args.config)
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Run optimization
    success = optimizer.optimize_startup()
    
    # Cleanup
    optimizer.cleanup()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

