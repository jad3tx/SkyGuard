#!/usr/bin/env python3
"""
SkyGuard Main Application Entry Point

This is the main entry point for the SkyGuard raptor alert system.
It initializes all components and runs the main detection loop.
"""

import sys
import logging
import signal
import time
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from skyguard.core.config_manager import ConfigManager
from skyguard.core.detector import RaptorDetector
from skyguard.core.camera import CameraManager
from skyguard.core.alert_system import AlertSystem
from skyguard.storage.event_logger import EventLogger
from skyguard.utils.logger import setup_logging


class SkyGuardSystem:
    """Main SkyGuard system coordinator."""
    
    def __init__(self, config_path: str = "config/skyguard.yaml"):
        """Initialize the SkyGuard system."""
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.get_config()
        
        # Setup logging
        setup_logging(self.config.get('logging', {}))
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.camera_manager = None
        self.detector = None
        self.alert_system = None
        self.event_logger = None
        
        self.running = False
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def initialize(self):
        """Initialize all system components."""
        try:
            self.logger.info("Initializing SkyGuard system...")
            
            # Initialize camera manager
            self.camera_manager = CameraManager(self.config['camera'])
            self.camera_manager.initialize()
            
            # Initialize AI detector
            self.detector = RaptorDetector(self.config['ai'])
            self.detector.load_model()
            
            # Initialize alert system
            self.alert_system = AlertSystem(self.config['notifications'])
            self.alert_system.initialize()
            
            # Initialize event logger
            self.event_logger = EventLogger(self.config['storage'])
            self.event_logger.initialize()
            
            self.logger.info("SkyGuard system initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize SkyGuard system: {e}")
            return False
    
    def run(self):
        """Run the main detection loop."""
        if not self.initialize():
            self.logger.error("Failed to initialize system. Exiting.")
            return False
            
        self.running = True
        self.logger.info("Starting SkyGuard detection loop...")
        
        try:
            while self.running:
                # Capture frame from camera
                frame = self.camera_manager.capture_frame()
                if frame is None:
                    self.logger.warning("Failed to capture frame")
                    time.sleep(1)
                    continue
                
                # Run detection
                detections = self.detector.detect(frame)
                
                # Process detections
                for detection in detections:
                    if detection['confidence'] > self.config['ai']['confidence_threshold']:
                        self._handle_raptor_detection(detection, frame)
                
                # Sleep between detection cycles
                time.sleep(self.config['system']['detection_interval'])
                
        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt")
        except Exception as e:
            self.logger.error(f"Error in main loop: {e}")
        finally:
            self.shutdown()
            
        return True
    
    def _handle_raptor_detection(self, detection: dict, frame):
        """Handle a detected raptor threat."""
        self.logger.warning(f"Raptor detected! Confidence: {detection['confidence']:.2f}")
        
        # Log the event
        self.event_logger.log_detection(detection, frame)
        
        # Send alerts
        self.alert_system.send_raptor_alert(detection)
        
        # Optional: Save frame with detection
        if self.config['system'].get('save_detection_frames', False):
            self._save_detection_frame(frame, detection)
    
    def _save_detection_frame(self, frame, detection):
        """Save frame with detection annotations."""
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"detection_{timestamp}_{detection['confidence']:.2f}.jpg"
            filepath = Path(self.config['storage']['detection_images_path']) / filename
            
            # Create directory if it doesn't exist
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # Save frame (you might want to add bounding box annotations here)
            import cv2
            cv2.imwrite(str(filepath), frame)
            
        except Exception as e:
            self.logger.error(f"Failed to save detection frame: {e}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    def shutdown(self):
        """Shutdown the system gracefully."""
        self.logger.info("Shutting down SkyGuard system...")
        
        if self.camera_manager:
            self.camera_manager.cleanup()
        
        if self.event_logger:
            self.event_logger.cleanup()
            
        self.logger.info("SkyGuard system shutdown complete")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="SkyGuard Raptor Alert System")
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
    
    # Create and run the system
    system = SkyGuardSystem(args.config)
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    success = system.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
