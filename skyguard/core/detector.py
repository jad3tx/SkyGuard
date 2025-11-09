"""
Raptor Detector for SkyGuard System

Handles AI-based detection and classification of raptors using
YOLO computer vision models.
"""

import cv2
import numpy as np
import logging
import time
import sys
import importlib
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


class BirdSegmentationDetector:
    """AI-powered bird segmentation detection system."""
    
    def __init__(self, config: dict):
        """Initialize the bird detector.
        
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
        self.classes = config.get('classes', ['bird'])
        # Prefer a segmentation model by default if not provided
        self.default_seg_model_path = self.config.get(
            'model_path', '../../models/yolo11n-seg.pt'
        )
        # Optional species classifier
        self.species_model = None
        self.species_model_path = self.config.get('species_model_path')
        self.species_input_size = tuple(
            self.config.get('species_input_size', (224, 224))
        )
        self.species_confidence_threshold = self.config.get('species_confidence_threshold', 0.3)
        # External repo backend (optional)
        self.species_backend = self.config.get('species_backend', 'ultralytics')
        self.species_repo_path = self.config.get('species_repo_path')
        self.species_module = self.config.get('species_module')
        self.species_function = self.config.get('species_function')
        self._species_predict_fn = None  # callable(image_rgb_np) -> (label, conf)
        
    def load_model(self) -> bool:
        """Load the AI model for detection.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Prefer a segmentation model by default
            model_path_str = self.config.get(
                'model_path', self.default_seg_model_path
            )
            model_path = self._resolve_model_path(model_path_str)
            
            if not Path(model_path).exists():
                self.logger.error(
                    f"Model file not found: {model_path}"
                )
                return False
            
            # Only YOLO models are supported
            if not PYTORCH_AVAILABLE:
                self.logger.error(
                    "PyTorch/YOLO not available; cannot load YOLO model"
                )
                return False
            
            self.model = YOLO(str(model_path))
            self.logger.info(f"YOLO model loaded: {model_path}")
            # Load optional species classifier (ultralytics or external)
            self._init_species_backend()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load model: {e}")
            return False

    def _init_species_backend(self) -> None:
        """Initialize optional species classification backend based on config."""
        try:
            if not self.species_model_path and self.species_backend != 'external':
                return
            if self.species_backend == 'ultralytics':
                if not self.species_model_path:
                    return
                sp_path = self._resolve_model_path(self.species_model_path)
                if not sp_path.exists():
                    self.logger.error(f"Species model not found: {sp_path}")
                    return
                self.species_model = YOLO(str(sp_path))
                # Note: _classify_species uses self.species_model directly
                self.logger.info(f"Species model loaded (ultralytics): {sp_path}")
            elif self.species_backend == 'external':
                # Expect: species_repo_path, species_module, species_function
                if not (self.species_repo_path and self.species_module and self.species_function):
                    self.logger.error(
                        "External species backend requires species_repo_path, "
                        "species_module, species_function"
                    )
                    return
                repo = Path(self.species_repo_path).resolve()
                if not repo.exists():
                    self.logger.error(f"Species repo path not found: {repo}")
                    return
                if str(repo) not in sys.path:
                    sys.path.insert(0, str(repo))
                mod = importlib.import_module(self.species_module)
                predict_fn = getattr(mod, self.species_function, None)
                if not callable(predict_fn):
                    self.logger.error(
                        f"Species function not callable: {self.species_module}.{self.species_function}"
                    )
                    return
                # Wrap into standardized callable
                def _wrapped_predict(img_rgb_np: np.ndarray):
                    return predict_fn(img_rgb_np)
                self._species_predict_fn = _wrapped_predict
                self.logger.info(
                    f"Species backend loaded (external): {self.species_module}.{self.species_function}"
                )
            else:
                self.logger.warning(
                    f"Unknown species_backend: {self.species_backend}; skipping"
                )
        except Exception as e:
            self.logger.error(f"Failed to init species backend: {e}")

    def _resolve_model_path(self, path_str: str) -> Path:
        """Resolve a possibly relative model path against project root.

        We try, in order:
        - As given (absolute or relative to CWD)
        - Relative to the project root (SkyGuard/)
        - Relative to the package root (skyguard/)
        """
        p = Path(path_str)
        if p.exists():
            return p
        base = Path(__file__).resolve()
        # Project root is three levels up: SkyGuard/skyguard/core -> SkyGuard/
        project_root = base.parents[3]
        candidates = [
            project_root / path_str,
            base.parents[2] / path_str,  # skyguard/
        ]
        for c in candidates:
            if c.exists():
                return c
        # Log attempted locations for troubleshooting
        try:
            self.logger.debug(
                "Model path resolution failed. Tried: %s",
                ", ".join(str(x) for x in [p] + candidates),
            )
        except Exception:
            pass
        return p
    
    def detect(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """Detect birds in the given frame and return instance segmentations.
        
        Args:
            frame: Input frame as numpy array
            
        Returns:
            List of detection dictionaries
        """
        try:
            if self.model is None:
                self.logger.warning("Model not loaded")
                return []
            
            # Run YOLO detection/segmentation
            results = self.model(
                frame,
                conf=self.confidence_threshold,
                iou=self.nms_threshold,
            )
            
            detections = []
            for result in results:
                boxes = result.boxes
                masks = getattr(result, 'masks', None)
                names = getattr(result, 'names', None)
                num_instances = (
                    int(boxes.shape[0])
                    if (boxes is not None and hasattr(boxes, 'shape'))
                    else 0
                )
                
                if boxes is None or num_instances == 0:
                    continue
                
                # Prepare mask polygons if available
                polygons_list = []
                if (
                    masks is not None
                    and getattr(masks, 'xy', None) is not None
                ):
                    # list of per-instance arrays of polygon points
                    polygons_list = masks.xy
                else:
                    polygons_list = [None] * num_instances
                
                for idx in range(num_instances):
                    box = boxes[idx]
                    # Extract detection information
                    x1, y1, x2, y2 = box.xyxy[0].detach().cpu().numpy()
                    has_conf = getattr(box, 'conf', None) is not None
                    confidence = (
                        float(box.conf[0].detach().cpu().numpy())
                        if has_conf else 0.0
                    )
                    has_cls = getattr(box, 'cls', None) is not None
                    class_id = (
                        int(box.cls[0].detach().cpu().numpy())
                        if has_cls else -1
                    )
                    class_name = None
                    if names is not None and class_id in names:
                        class_name = names[class_id]
                    
                    # Filter for bird class; prefer class name check, fallback to COCO id 14
                    is_bird = False
                    if class_name is not None:
                        is_bird = 'bird' in str(class_name).lower()
                    elif class_id == 14:
                        is_bird = True
                    
                    if not is_bird:
                        continue
                    
                    polygon = polygons_list[idx]
                    polygon_points = None
                    if polygon is not None and len(polygon) > 0:
                        # Use the largest polygon path
                        pts = (
                            max(polygon, key=lambda arr: arr.shape[0])
                            if isinstance(polygon, list)
                            else polygon
                        )
                        polygon_points = pts.astype(np.int32).tolist()
                    
                    # Optional species classification
                    species_name = None
                    species_conf = None
                    if self._species_predict_fn is not None or self.species_model is not None:
                        try:
                            crop = self._extract_crop(
                                frame, polygon_points, x1, y1, x2, y2
                            )
                            if crop is not None:
                                species_name, species_conf = self._classify_species(crop)
                        except Exception as ce:
                            self.logger.debug(
                                f"Species classify error: {ce}"
                            )
                    detection = {
                        'bbox': [int(x1), int(y1), int(x2), int(y2)],
                        'confidence': float(confidence),
                        'class_id': class_id,
                        'class_name': class_name or 'bird',
                        'timestamp': time.time(),
                        'center': [int((x1 + x2) / 2), int((y1 + y2) / 2)],
                        'area': int(max(0, (x2 - x1)) * max(0, (y2 - y1))),
                        'polygon': polygon_points,  # list of [x,y]
                        'species': species_name,
                        'species_confidence': (
                            float(species_conf) if species_conf is not None
                            else None
                        ),
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

    def _extract_crop(
        self,
        frame: np.ndarray,
        polygon_points: Any,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
    ) -> Optional[np.ndarray]:
        """Extract an RGB crop of the detected bird for classification.

        Uses polygon mask if available to reduce background; otherwise uses
        the bounding box.
        """
        h, w = frame.shape[:2]
        x1i = max(0, int(x1))
        y1i = max(0, int(y1))
        x2i = min(w, int(x2))
        y2i = min(h, int(y2))
        if x2i <= x1i or y2i <= y1i:
            return None
        crop = frame[y1i:y2i, x1i:x2i]
        if crop.size == 0:
            return None
        if polygon_points is not None:
            pts = np.array(polygon_points, dtype=np.int32)
            pts[:, 0] -= x1i
            pts[:, 1] -= y1i
            mask = np.zeros(crop.shape[:2], dtype=np.uint8)
            cv2.fillPoly(mask, [pts], 255)
            crop = cv2.bitwise_and(crop, crop, mask=mask)
        # BGR to RGB and resize to classifier input size
        rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
        resized = cv2.resize(rgb, self.species_input_size)
        return resized

    def _classify_species(
        self, crop_rgb_resized: np.ndarray
    ) -> Tuple[Optional[str], Optional[float]]:
        """Run species classifier (Ultralytics or external backend).

        Returns (label, confidence) or (None, None) if not available.
        """
        # External backend callable takes precedence if provided
        if self._species_predict_fn is not None:
            return self._species_predict_fn(crop_rgb_resized)
        if self.species_model is None:
            return None, None
        results = self.species_model(crop_rgb_resized)
        if not results:
            return None, None
        res = results[0]
        names = getattr(res, 'names', None)
        probs = getattr(res, 'probs', None)
        if probs is None or names is None:
            return None, None
        arr = probs.data.detach().cpu().numpy()
        top_i = int(np.argmax(arr))
        conf = float(arr[top_i])
        
        # Filter by confidence threshold - only return if above threshold
        if conf < self.species_confidence_threshold:
            return None, None
        
        label = names.get(top_i) if isinstance(names, dict) else None
        return label, conf
    
    def draw_detections(
        self, frame: np.ndarray, detections: List[Dict[str, Any]]
    ) -> np.ndarray:
        """Draw detection segmentations and bounding boxes on the frame.
        
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
                polygon = detection.get('polygon')
                
                # Draw segmentation mask if available
                if polygon is not None:
                    overlay = annotated_frame.copy()
                    pts = np.array(polygon, dtype=np.int32)
                    cv2.fillPoly(overlay, [pts], color=(0, 255, 0))
                    # Alpha blend mask
                    alpha = 0.3
                    annotated_frame = cv2.addWeighted(
                        overlay,
                        alpha,
                        annotated_frame,
                        1 - alpha,
                        0,
                    )
                
                # Draw bounding box (optional for context)
                cv2.rectangle(
                    annotated_frame,
                    (bbox[0], bbox[1]),
                    (bbox[2], bbox[3]),
                    (0, 255, 0),
                    1,
                )
                
                # Draw label
                sp = detection.get('species')
                spc = detection.get('species_confidence')
                if sp and spc is not None:
                    label = (
                        f"{class_name}: {confidence:.2f} | {sp} {spc:.2f}"
                    )
                else:
                    label = f"{class_name}: {confidence:.2f}"
                label_size = cv2.getTextSize(
                    label,
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    2,
                )[0]
                
                # Draw label background
                cv2.rectangle(
                    annotated_frame,
                    (bbox[0], bbox[1] - label_size[1] - 10),
                    (bbox[0] + label_size[0], bbox[1]),
                    (0, 255, 0),
                    -1,
                )
                
                # Draw label text
                cv2.putText(
                    annotated_frame,
                    label,
                    (bbox[0], bbox[1] - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 0, 0),
                    2,
                )
            
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
        self.confidence_threshold = self.config.get(
            'confidence_threshold', 0.5
        )
        self.nms_threshold = self.config.get(
            'nms_threshold', 0.4
        )
        self.input_size = self.config.get(
            'input_size', [640, 640]
        )
        self.classes = self.config.get('classes', ['bird'])
        
        self.logger.info("Detector configuration updated")


class RaptorDetector(BirdSegmentationDetector):
    """Backward-compatible alias for legacy imports.

    This class preserves the previous public API name while leveraging the
    new bird-only segmentation detector implementation.
    """
    pass
