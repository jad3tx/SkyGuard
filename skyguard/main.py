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
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from skyguard.core.config_manager import ConfigManager
from skyguard.core.detector import RaptorDetector
from skyguard.core.camera import CameraManager
from skyguard.core.camera_snapshot import CameraSnapshotService
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
        self.snapshot_service = CameraSnapshotService()
        
        self.running = False
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def initialize(self):
        """Initialize all system components."""
        try:
            self.logger.info("=" * 60)
            self.logger.info("🚀 SKYGUARD SYSTEM STARTING")
            self.logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            self.logger.info("=" * 60)
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
            
            self.logger.info("✅ SkyGuard system initialized successfully")
            self.logger.info("=" * 60)
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
        
        # Perform warmup detections for faster startup
        self._perform_warmup_detections()
        
        # Start snapshot service for web portal
        if self.camera_manager:
            self.snapshot_service.start(self.camera_manager)
        
        # Track last cleanup to run retention periodically (e.g., every 10 minutes)
        last_cleanup_ts = time.time()

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
                
                # Debug: Log detection results
                if detections:
                    self.logger.info(f"Found {len(detections)} detections, max confidence: {max(d['confidence'] for d in detections):.3f}")
                
                # Process detections
                for detection in detections:
                    if detection['confidence'] > self.config['ai']['confidence_threshold']:
                        self._handle_raptor_detection(detection, frame)
                
                # Sleep between detection cycles
                time.sleep(self.config['system']['detection_interval'])

                # Periodic cleanup of old detections/events
                now_ts = time.time()
                if now_ts - last_cleanup_ts > 600:  # 10 minutes
                    try:
                        if self.event_logger:
                            self.event_logger.cleanup_old_data()
                    except Exception as cleanup_err:
                        self.logger.debug(f"Retention cleanup skipped: {cleanup_err}")
                    finally:
                        last_cleanup_ts = now_ts
                
        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt")
        except Exception as e:
            self.logger.error(f"Error in main loop: {e}")
        finally:
            # Stop snapshot service
            self.snapshot_service.stop()
            self.shutdown()
            
        return True
    
    def _handle_raptor_detection(self, detection: dict, frame):
        """Handle a detected raptor threat."""
        self.logger.warning(f"Raptor detected! Confidence: {detection['confidence']:.2f}")
        
        # Log the event (includes saving annotated detection image)
        self.event_logger.log_detection(detection, frame)
        
        # Send alerts
        self.alert_system.send_raptor_alert(detection)
    
    
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
    
    def _perform_warmup_detections(self):
        """Perform warmup detections to optimize system performance."""
        warmup_count = self.config.get('system', {}).get('warmup_detections', 5)
        if warmup_count <= 0:
            return
            
        self.logger.info(f"🔥 Performing {warmup_count} warmup detections for faster startup...")
        
        for i in range(warmup_count):
            try:
                # Capture frame
                frame = self.camera_manager.capture_frame()
                if frame is None:
                    self.logger.warning(f"Warmup detection {i+1}: No frame captured")
                    continue
                
                # Run detection (this optimizes the model)
                detections = self.detector.detect(frame)
                self.logger.debug(f"Warmup detection {i+1}: {len(detections)} objects found")
                
                # Small delay between warmup detections
                time.sleep(0.5)
                
            except Exception as e:
                self.logger.warning(f"Warmup detection {i+1} failed: {e}")
        
        self.logger.info("✅ Warmup detections completed - system ready for normal operation")


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
