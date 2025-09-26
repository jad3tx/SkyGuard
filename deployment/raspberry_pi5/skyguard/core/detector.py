"""
Raptor Detector for SkyGuard System

Handles AI-based detection and classification of raptors using computer vision models.
Supports both YOLO and TensorFlow model formats.
"""

import cv2
import numpy as np
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Try to import PyTorch and YOLO, but don't fail if not available
try:
    import torch
    from ultralytics import YOLO
    PYTORCH_AVAILABLE = True
except ImportError:
    PYTORCH_AVAILABLE = False
    torch = None
    YOLO = None

# Try to import TensorFlow, but don't fail if not available
try:
    import tensorflow as tf
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    tf = None


class RaptorDetector:
    """AI-powered raptor detection system."""
    
    def __init__(self, config: dict):
        """Initialize the raptor detector.
        
        Args:
            config: AI configuration dictionary
        """
        self.config = config
        self.model = None
        self.logger = logging.getLogger(__name__)
        self.detection_count = 0
        self.last_detection_time = 0
        
        # Detection parameters
        self.confidence_threshold = config.get('confidence_threshold', 0.5)
        self.nms_threshold = config.get('nms_threshold', 0.4)
        self.input_size = config.get('input_size', [640, 640])
        self.classes = config.get('classes', ['raptor', 'hawk', 'eagle', 'owl'])
        
    def load_model(self) -> bool:
        """Load the AI model for detection.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            model_path = self.config.get('model_path', 'models/raptor_detector.pt')
            model_type = self.config.get('model_type', 'yolo')
            
            if not Path(model_path).exists():
                self.logger.warning(f"Model file not found: {model_path}")
                self._create_dummy_model()
                return True
            
            if model_type.lower() == 'yolo':
                if not PYTORCH_AVAILABLE:
                    self.logger.warning("PyTorch/YOLO not available, using dummy model")
                    self._create_dummy_model()
                    return True
                self.model = YOLO(model_path)
                self.logger.info(f"YOLO model loaded: {model_path}")
            elif model_type.lower() == 'tensorflow':
                if not TENSORFLOW_AVAILABLE:
                    self.logger.warning("TensorFlow not available, using dummy model")
                    self._create_dummy_model()
                    return True
                # TODO: Implement TensorFlow model loading
                self.logger.warning("TensorFlow model loading not yet implemented, using dummy model")
                self._create_dummy_model()
                return True
            else:
                self.logger.error(f"Unsupported model type: {model_type}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load model: {e}")
            self._create_dummy_model()
            return True  # Always return True to allow dummy mode
    
    def _create_dummy_model(self):
        """Create a dummy model for testing when no real model is available."""
        self.logger.info("Creating dummy model for testing")
        # This would create a simple model that randomly detects objects
        # For now, we'll use a placeholder
        self.model = "dummy"
    
    def detect(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """Detect raptors in the given frame.
        
        Args:
            frame: Input frame as numpy array
            
        Returns:
            List of detection dictionaries
        """
        try:
            if self.model is None:
                self.logger.warning("Model not loaded")
                return []
            
            if self.model == "dummy":
                return self._dummy_detection(frame)
            
            # Run YOLO detection
            results = self.model(frame, conf=self.confidence_threshold, iou=self.nms_threshold)
            
            detections = []
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Extract detection information
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        confidence = box.conf[0].cpu().numpy()
                        class_id = int(box.cls[0].cpu().numpy())
                        
                        # Filter for raptor classes
                        if class_id < len(self.classes):
                            detection = {
                                'bbox': [int(x1), int(y1), int(x2), int(y2)],
                                'confidence': float(confidence),
                                'class_id': class_id,
                                'class_name': self.classes[class_id],
                                'timestamp': time.time(),
                                'center': [int((x1 + x2) / 2), int((y1 + y2) / 2)],
                                'area': int((x2 - x1) * (y2 - y1)),
                            }
                            detections.append(detection)
            
            # Update statistics
            if detections:
                self.detection_count += len(detections)
                self.last_detection_time = time.time()
            
            return detections
            
        except Exception as e:
            self.logger.error(f"Error during detection: {e}")
            return []
    
    def _dummy_detection(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """Generate dummy detections for testing.
        
        Args:
            frame: Input frame
            
        Returns:
            List of dummy detections
        """
        # Randomly generate a detection 5% of the time
        if np.random.random() < 0.05:
            h, w = frame.shape[:2]
            x1 = np.random.randint(0, w//2)
            y1 = np.random.randint(0, h//2)
            x2 = x1 + np.random.randint(50, w//2)
            y2 = y1 + np.random.randint(50, h//2)
            
            return [{
                'bbox': [x1, y1, x2, y2],
                'confidence': np.random.uniform(0.6, 0.9),
                'class_id': 0,
                'class_name': 'raptor',
                'timestamp': time.time(),
                'center': [int((x1 + x2) / 2), int((y1 + y2) / 2)],
                'area': (x2 - x1) * (y2 - y1),
            }]
        
        return []
    
    def draw_detections(self, frame: np.ndarray, detections: List[Dict[str, Any]]) -> np.ndarray:
        """Draw detection bounding boxes on the frame.
        
        Args:
            frame: Input frame
            detections: List of detections
            
        Returns:
            Frame with drawn detections
        """
        try:
            annotated_frame = frame.copy()
            
            for detection in detections:
                bbox = detection['bbox']
                confidence = detection['confidence']
                class_name = detection['class_name']
                
                # Draw bounding box
                cv2.rectangle(annotated_frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 255, 0), 2)
                
                # Draw label
                label = f"{class_name}: {confidence:.2f}"
                label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
                
                # Draw label background
                cv2.rectangle(annotated_frame, 
                            (bbox[0], bbox[1] - label_size[1] - 10),
                            (bbox[0] + label_size[0], bbox[1]),
                            (0, 255, 0), -1)
                
                # Draw label text
                cv2.putText(annotated_frame, label,
                          (bbox[0], bbox[1] - 5),
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
            
            return annotated_frame
            
        except Exception as e:
            self.logger.error(f"Error drawing detections: {e}")
            return frame
    
    def get_detection_stats(self) -> Dict[str, Any]:
        """Get detection statistics.
        
        Returns:
            Dictionary with detection statistics
        """
        return {
            'total_detections': self.detection_count,
            'last_detection_time': self.last_detection_time,
            'confidence_threshold': self.confidence_threshold,
            'nms_threshold': self.nms_threshold,
            'model_loaded': self.model is not None,
            'classes': self.classes,
        }
    
    def update_config(self, new_config: dict):
        """Update detector configuration.
        
        Args:
            new_config: New configuration dictionary
        """
        self.config.update(new_config)
        self.confidence_threshold = self.config.get('confidence_threshold', 0.5)
        self.nms_threshold = self.config.get('nms_threshold', 0.4)
        self.input_size = self.config.get('input_size', [640, 640])
        self.classes = self.config.get('classes', ['raptor', 'hawk', 'eagle', 'owl'])
        
        self.logger.info("Detector configuration updated")
