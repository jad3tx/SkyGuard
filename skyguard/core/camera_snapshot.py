"""
Camera Snapshot Service for SkyGuard System

This module provides periodic camera snapshots for the web portal.
"""

import cv2
import numpy as np
import time
import os
import threading
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class CameraSnapshotService:
    """Provides periodic camera snapshots for web portal."""
    
    def __init__(self, snapshot_file: str = "data/camera_snapshot.jpg", interval: float = 3.0):
        """Initialize camera snapshot service.
        
        Args:
            snapshot_file: Path to save camera snapshots
            interval: Snapshot interval in seconds
        """
        self.snapshot_file = snapshot_file
        self.interval = interval
        self.running = False
        self.thread = None
        self.camera = None
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(snapshot_file), exist_ok=True)
    
    def start(self, camera_manager):
        """Start the snapshot service.
        
        Args:
            camera_manager: CameraManager instance to capture frames from
        """
        self.camera = camera_manager
        self.running = True
        self.thread = threading.Thread(target=self._snapshot_loop, daemon=True)
        self.thread.start()
        logger.info(f"Camera snapshot service started (interval: {self.interval}s)")
    
    def stop(self):
        """Stop the snapshot service."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        logger.info("Camera snapshot service stopped")
    
    def _snapshot_loop(self):
        """Main snapshot loop."""
        while self.running:
            try:
                if self.camera and hasattr(self.camera, 'capture_frame'):
                    # Try to capture a frame
                    frame = self.camera.capture_frame()
                    if frame is not None:
                        # Save snapshot
                        self._save_snapshot(frame)
                    else:
                        # Create a test image if no camera available
                        self._create_test_snapshot()
                else:
                    # Create a test image if no camera available
                    self._create_test_snapshot()
                
                # Wait for next interval
                time.sleep(self.interval)
                
            except Exception as e:
                logger.error(f"Error in snapshot loop: {e}")
                time.sleep(self.interval)
    
    def _save_snapshot(self, frame: np.ndarray):
        """Save camera frame as snapshot.
        
        Args:
            frame: Camera frame to save
        """
        try:
            # Encode as JPEG
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if ret:
                # Save to file
                with open(self.snapshot_file, 'wb') as f:
                    f.write(buffer.tobytes())
                logger.debug(f"Snapshot saved: {self.snapshot_file}")
            else:
                logger.warning("Failed to encode snapshot")
                
        except Exception as e:
            logger.error(f"Failed to save snapshot: {e}")
    
    def _create_test_snapshot(self):
        """Create a test snapshot when no camera is available."""
        try:
            # Create a test image
            img = np.zeros((480, 640, 3), dtype=np.uint8)
            
            # Add a gradient background
            for y in range(480):
                for x in range(640):
                    img[y, x] = [int(255 * y / 480), int(255 * x / 640), 100]
            
            # Add text
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(img, 'SkyGuard Camera Feed', (50, 100), font, 1, (255, 255, 255), 2)
            cv2.putText(img, 'Camera not available', (50, 150), font, 0.7, (200, 200, 200), 2)
            cv2.putText(img, 'Using test image', (50, 200), font, 0.7, (200, 200, 200), 2)
            
            # Add timestamp
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            cv2.putText(img, timestamp, (50, 400), font, 0.5, (150, 150, 150), 1)
            
            # Add a simple pattern
            for i in range(0, 640, 50):
                cv2.line(img, (i, 250), (i, 350), (100, 100, 100), 1)
            
            # Save the test image
            cv2.imwrite(self.snapshot_file, img)
            logger.debug(f"Test snapshot created: {self.snapshot_file}")
            
        except Exception as e:
            logger.error(f"Failed to create test snapshot: {e}")
    
    def get_snapshot_bytes(self) -> Optional[bytes]:
        """Get the latest snapshot as bytes.
        
        Returns:
            Snapshot as JPEG bytes, or None if not available
        """
        try:
            if os.path.exists(self.snapshot_file):
                with open(self.snapshot_file, 'rb') as f:
                    return f.read()
            return None
            
        except Exception as e:
            logger.error(f"Failed to get snapshot bytes: {e}")
            return None
    
    def is_snapshot_available(self) -> bool:
        """Check if snapshot is available and recent.
        
        Returns:
            True if snapshot is available and recent, False otherwise
        """
        try:
            if not os.path.exists(self.snapshot_file):
                return False
            
            # Check if file is recent (within last 10 seconds)
            file_time = os.path.getmtime(self.snapshot_file)
            return time.time() - file_time < 10
            
        except Exception:
            return False
