"""
Camera Manager for SkyGuard System

Handles video capture from various camera sources including USB webcams,
Raspberry Pi camera modules, and IP cameras.
"""

import cv2
import logging
import time
import numpy as np
from typing import Optional, Tuple
from pathlib import Path


class CameraManager:
    """Manages camera operations for the SkyGuard system."""
    
    def __init__(self, config: dict):
        """Initialize the camera manager.
        
        Args:
            config: Camera configuration dictionary
        """
        self.config = config
        self.cap = None
        self.logger = logging.getLogger(__name__)
        self.last_frame_time = 0
        self.frame_count = 0
        
    def initialize(self) -> bool:
        """Initialize the camera.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Determine camera source
            source = self.config.get('source', 0)
            
            # Initialize camera
            self.cap = cv2.VideoCapture(source)
            
            if not self.cap.isOpened():
                self.logger.error(f"Failed to open camera source: {source}")
                return False
            
            # Set camera properties
            self._configure_camera()
            
            # Test capture
            ret, frame = self.cap.read()
            if not ret:
                self.logger.error("Failed to capture test frame")
                return False
                
            self.logger.info(f"Camera initialized successfully: {source}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize camera: {e}")
            return False
    
    def _configure_camera(self):
        """Configure camera properties."""
        try:
            # Set resolution
            width = self.config.get('width', 640)
            height = self.config.get('height', 480)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            
            # Set FPS
            fps = self.config.get('fps', 30)
            self.cap.set(cv2.CAP_PROP_FPS, fps)
            
            # Set buffer size to reduce latency
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # Get actual properties
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
            
            self.logger.info(f"Camera configured: {actual_width}x{actual_height} @ {actual_fps:.1f}fps")
            
        except Exception as e:
            self.logger.warning(f"Failed to configure camera properties: {e}")
    
    def capture_frame(self) -> Optional[np.ndarray]:
        """Capture a frame from the camera.
        
        Returns:
            Captured frame as numpy array, or None if failed
        """
        try:
            if self.cap is None or not self.cap.isOpened():
                self.logger.error("Camera not initialized")
                return None
            
            ret, frame = self.cap.read()
            if not ret:
                self.logger.warning("Failed to capture frame")
                return None
            
            # Apply transformations
            frame = self._apply_transformations(frame)
            
            # Update statistics
            self.frame_count += 1
            self.last_frame_time = time.time()
            
            return frame
            
        except Exception as e:
            self.logger.error(f"Error capturing frame: {e}")
            return None
    
    def _apply_transformations(self, frame: np.ndarray) -> np.ndarray:
        """Apply configured transformations to the frame.
        
        Args:
            frame: Input frame
            
        Returns:
            Transformed frame
        """
        try:
            # Apply rotation
            rotation = self.config.get('rotation', 0)
            if rotation != 0:
                frame = self._rotate_frame(frame, rotation)
            
            # Apply flips
            if self.config.get('flip_horizontal', False):
                frame = cv2.flip(frame, 1)
                
            if self.config.get('flip_vertical', False):
                frame = cv2.flip(frame, 0)
            
            return frame
            
        except Exception as e:
            self.logger.warning(f"Failed to apply transformations: {e}")
            return frame
    
    def _rotate_frame(self, frame: np.ndarray, angle: int) -> np.ndarray:
        """Rotate frame by specified angle.
        
        Args:
            frame: Input frame
            angle: Rotation angle in degrees (90, 180, 270)
            
        Returns:
            Rotated frame
        """
        if angle == 90:
            return cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        elif angle == 180:
            return cv2.rotate(frame, cv2.ROTATE_180)
        elif angle == 270:
            return cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
        else:
            return frame
    
    def get_frame_info(self) -> dict:
        """Get information about the current frame.
        
        Returns:
            Dictionary with frame information
        """
        return {
            'frame_count': self.frame_count,
            'last_frame_time': self.last_frame_time,
            'fps': self.cap.get(cv2.CAP_PROP_FPS) if self.cap else 0,
            'width': int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)) if self.cap else 0,
            'height': int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) if self.cap else 0,
        }
    
    def save_frame(self, frame: np.ndarray, filename: str) -> bool:
        """Save a frame to disk.
        
        Args:
            frame: Frame to save
            filename: Filename to save as
            
        Returns:
            True if successful, False otherwise
        """
        try:
            filepath = Path(filename)
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            success = cv2.imwrite(str(filepath), frame)
            if success:
                self.logger.debug(f"Frame saved: {filepath}")
            else:
                self.logger.error(f"Failed to save frame: {filepath}")
                
            return success
            
        except Exception as e:
            self.logger.error(f"Error saving frame: {e}")
            return False
    
    def cleanup(self):
        """Clean up camera resources."""
        try:
            if self.cap is not None:
                self.cap.release()
                self.cap = None
                
            self.logger.info("Camera cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during camera cleanup: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup()
