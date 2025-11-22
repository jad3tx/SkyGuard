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

# Import platform detection
try:
    from skyguard.utils.platform import get_recommended_device, is_jetson
except ImportError:
    # Fallback if platform detection not available
    def get_recommended_device() -> str:
        """Fallback device recommendation."""
        try:
            import torch
            if torch and torch.cuda.is_available():
                return 'cuda:0'
        except Exception:
            pass
        return 'cpu'
    
    def is_jetson() -> bool:
        """Fallback Jetson detection."""
        return False


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
        # Detection logging detail level: 'minimal', 'standard', 'detailed'
        self.detection_log_level = self.config.get('detection_log_level', 'standard')
        self.species_repo_path = self.config.get('species_repo_path')
        self.species_module = self.config.get('species_module')
        self.species_function = self.config.get('species_function')
        self._species_predict_fn = None  # callable(image_rgb_np) -> (label, conf)
        # Class name mapping for numeric IDs to bird names
        self._species_class_name_map = None
        # Device for inference (auto-detect based on platform)
        self.device = config.get('device', None)  # None means auto-detect
        
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
            
            # Determine device for inference
            if self.device is None:
                # Auto-detect device based on platform
                self.device = get_recommended_device()
            
            # Log device information
            if is_jetson():
                self.logger.info("🚀 Jetson platform detected - using GPU acceleration")
            elif self.device.startswith('cuda'):
                self.logger.info(f"🚀 CUDA device detected: {self.device}")
            else:
                self.logger.info(f"💻 Using CPU for inference")
            
            self.model = YOLO(str(model_path))
            
            # Move model to device if CUDA is available
            if PYTORCH_AVAILABLE and torch is not None:
                if self.device.startswith('cuda') and torch.cuda.is_available():
                    # YOLO will automatically use CUDA if available
                    # But we can explicitly set it
                    try:
                        # Verify CUDA is working
                        device_name = torch.cuda.get_device_name(0) if torch.cuda.device_count() > 0 else "CUDA"
                        self.logger.info(f"✅ GPU available: {device_name}")
                    except Exception as e:
                        self.logger.warning(f"⚠️  CUDA device specified but not available: {e}")
                        self.device = 'cpu'
                elif self.device.startswith('cuda') and not torch.cuda.is_available():
                    self.logger.warning("⚠️  CUDA requested but not available, falling back to CPU")
                    self.device = 'cpu'
            
            self.logger.info(f"YOLO model loaded: {model_path} (device: {self.device})")
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
                
                self.logger.debug(f"Attempting to load species model from: {self.species_model_path}")
                sp_path = self._resolve_model_path(self.species_model_path)
                self.logger.debug(f"Resolved path: {sp_path} (exists: {sp_path.exists()})")
                
                # Check if resolved path exists (try both resolved and original)
                if not sp_path.exists():
                    # Try one more time with explicit project root resolution
                    base = Path(__file__).resolve()
                    # Project root is two levels up: SkyGuard/skyguard/core -> SkyGuard/
                    project_root = base.parents[2]
                    explicit_path = project_root / str(self.species_model_path).replace('\\', '/')
                    
                    if explicit_path.exists():
                        sp_path = explicit_path.resolve()
                        self.logger.info(f"Found species model using explicit project root path: {sp_path}")
                    else:
                        # Format paths with forward slashes for readability
                        sp_path_str = str(sp_path).replace('\\', '/')
                        explicit_path_str = str(explicit_path).replace('\\', '/')
                        project_root_str = str(project_root).replace('\\', '/')
                        
                        self.logger.error(
                            f"Species model not found: {sp_path_str} "
                            f"(resolved from: {self.species_model_path})"
                        )
                        self.logger.error(
                            f"Also tried: {explicit_path_str}"
                        )
                        self.logger.error(
                            f"Project root: {project_root_str}"
                        )
                        self.logger.error(
                            f"Current working directory: {Path.cwd()}"
                        )
                        self.logger.error(
                            f"Please ensure the model file exists at: {explicit_path_str} "
                            f"or update species_model_path in config/skyguard.yaml"
                        )
                        return
                # Use forward slashes for path string (works on both Windows and Linux)
                sp_path_str = str(sp_path).replace('\\', '/')
                self.species_model = YOLO(sp_path_str)
                # Species model will use the same device as main model
                # Note: _classify_species uses self.species_model directly
                # Get model info for logging
                try:
                    model_info = self.species_model.info()
                    if model_info:
                        layers, params, gradients, gflops = model_info
                        self.logger.info(
                            f"Species model loaded (ultralytics): {sp_path_str} | "
                            f"Layers: {layers}, Params: {params:,}, GFLOPs: {gflops:.1f}"
                        )
                    else:
                        self.logger.info(f"Species model loaded (ultralytics): {sp_path_str}")
                except Exception:
                    self.logger.info(f"Species model loaded (ultralytics): {sp_path_str}")
                # Try to load class name mapping from dataset
                self._load_species_class_name_map()
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

    def _load_species_class_name_map(self) -> None:
        """Load class name mapping from classes.txt and dataset_info.yaml if available.
        
        This attempts to map numeric class IDs to actual bird names.
        """
        try:
            import yaml
            base = Path(__file__).resolve()
            # Project root is two levels up: SkyGuard/skyguard/core -> SkyGuard/
            project_root = base.parents[2]
            
            class_name_map = {}
            
            # First, try to load classes.txt from NABirds directory (highest priority)
            classes_txt_path = project_root / "data" / "nabirds" / "classes.txt"
            if classes_txt_path.exists():
                try:
                    with open(classes_txt_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if not line:
                                continue
                            # Format: "{class_id} {class_name}"
                            parts = line.split(' ', 1)
                            if len(parts) >= 2:
                                class_id_str = parts[0].strip()
                                class_name = parts[1].strip()
                                
                                # Map both with and without leading zeros
                                # e.g., "0989" -> "Yellow-headed Blackbird (Female/Immature Male)"
                                # and "989" -> same
                                class_id_int = int(class_id_str)
                                class_name_map[class_id_str] = class_name
                                class_name_map[str(class_id_int)] = class_name
                                # Also map zero-padded versions (4 digits)
                                class_id_padded = f"{class_id_int:04d}"
                                if class_id_padded != class_id_str:
                                    class_name_map[class_id_padded] = class_name
                    
                    self.logger.info(
                        f"Loaded NABirds class mapping from {classes_txt_path} "
                        f"({len(class_name_map)} entries)"
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to load classes.txt from {classes_txt_path}: {e}")
                    import traceback
                    self.logger.debug(traceback.format_exc())
            
            # Also try to load from dataset_info.yaml (lower priority, for named species)
            dataset_paths = [
                project_root / "data" / "bird_species_merged" / "dataset_info.yaml",
                project_root / "data" / "bird_species" / "dataset_info.yaml",
                project_root / "data" / "nabirds_prepared" / "dataset_info.yaml",
            ]
            
            # Also try to find it relative to the model path
            if self.species_model_path:
                model_path = self._resolve_model_path(self.species_model_path)
                # Look for dataset_info.yaml in parent directories
                for parent in [model_path.parent, model_path.parent.parent]:
                    dataset_paths.append(parent / "dataset_info.yaml")
                    # Also check data subdirectories
                    for data_dir in parent.glob("**/data/*/dataset_info.yaml"):
                        dataset_paths.append(data_dir)
            
            for dataset_path in dataset_paths:
                if dataset_path.exists():
                    try:
                        with open(dataset_path, 'r', encoding='utf-8') as f:
                            dataset_info = yaml.safe_load(f)
                        
                        # Get class list from dataset info
                        classes = dataset_info.get('classes', [])
                        if isinstance(classes, list):
                            # Only add named species (non-numeric) from dataset_info.yaml
                            # Numeric IDs should already be mapped from classes.txt
                            for idx, class_name in enumerate(classes):
                                class_name_str = str(class_name)
                                # Check if it's a named species (not purely numeric)
                                is_numeric = class_name_str.isdigit() or (
                                    class_name_str.startswith('0') and class_name_str[1:].isdigit()
                                )
                                
                                # Only add named species, and only if not already mapped
                                if not is_numeric:
                                    # Map by index only if not already in map
                                    if str(idx) not in class_name_map:
                                        class_name_map[str(idx)] = class_name_str
                                    # Map by name
                                    if class_name_str not in class_name_map:
                                        class_name_map[class_name_str] = class_name_str
                        
                        self.logger.debug(
                            f"Loaded additional class mappings from {dataset_path}"
                        )
                    except Exception as e:
                        self.logger.debug(f"Failed to load dataset info from {dataset_path}: {e}")
                        continue
            
            if class_name_map:
                self._species_class_name_map = class_name_map
                self.logger.info(
                    f"Total class name mappings loaded: {len(class_name_map)}"
                )
            else:
                self.logger.debug("No class name mappings found")
        except Exception as e:
            self.logger.debug(f"Failed to load species class name map: {e}")
    
    def _format_species_name(self, label: str) -> str:
        """Format species name, converting numeric IDs to more readable format.
        
        Args:
            label: Raw species label from model (may be numeric ID or name)
            
        Returns:
            Formatted species name
        """
        if not label:
            return label
        
        label_str = str(label).strip()
        
        # Check if it's a numeric ID (may have leading zeros like "0395")
        # Try to determine if it's numeric by checking if it's all digits
        is_numeric = label_str.isdigit() or (label_str.startswith('0') and label_str[1:].isdigit())
        
        # If it's already a named species (not purely numeric), use it as-is
        if not is_numeric:
            # Replace underscores with spaces for readability
            return label_str.replace('_', ' ')
        
        # It's a numeric ID - try to look it up in the mapping
        if self._species_class_name_map:
            # Try both with and without leading zeros
            mapped = self._species_class_name_map.get(label_str)
            if not mapped and label_str.startswith('0'):
                # Try without leading zero
                mapped = self._species_class_name_map.get(label_str.lstrip('0'))
            if mapped and not (mapped.isdigit() or (mapped.startswith('0') and mapped[1:].isdigit())):
                # Found a named species for this ID
                return mapped.replace('_', ' ')
        
        # No mapping found - format numeric ID more readably
        # Return as "NABirds Class {ID}" 
        return f"NABirds Class {label_str}"
    
    def _resolve_model_path(self, path_str: str) -> Path:
        """Resolve a possibly relative model path against project root.

        We try, in order:
        - As given (absolute or relative to CWD)
        - Relative to the project root (SkyGuard/)
        - Relative to the package root (skyguard/)
        
        Args:
            path_str: Model path string (may contain forward or backslashes)
            
        Returns:
            Resolved Path object
        """
        # Normalize path separators (handle both Windows and Linux)
        normalized_path = str(path_str).replace('\\', '/')
        p = Path(normalized_path)
        
        # Try as absolute path first
        if p.is_absolute() and p.exists():
            return p
        
        # Try as relative to current working directory
        if p.exists():
            return p.resolve()
        
        # Try relative to project root
        base = Path(__file__).resolve()
        # Project root is two levels up: SkyGuard/skyguard/core -> SkyGuard/
        # From detector.py: parents[0]=core/, parents[1]=skyguard/, parents[2]=SkyGuard/
        project_root = base.parents[2]
        
        candidates = [
            project_root / normalized_path,
            project_root / path_str,  # Try original path too
            base.parents[1] / normalized_path,  # skyguard/ (one level up from core/)
            base.parents[1] / path_str,  # skyguard/ with original path
        ]
        
        for c in candidates:
            if c.exists():
                return c.resolve()
        
        # Log attempted locations for troubleshooting
        all_attempts = [p] + candidates
        try:
            self.logger.error(
                f"Model path resolution failed for: {path_str}"
            )
            self.logger.error(
                f"Attempted paths:\n  " + "\n  ".join(str(x) for x in all_attempts)
            )
            self.logger.error(
                f"Project root: {project_root}"
            )
            self.logger.error(
                f"Current working directory: {Path.cwd()}"
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
            
            # Log segmentation model execution
            inference_start = time.time()
            if self.detection_log_level in ['standard', 'detailed']:
                self.logger.info("🔍 [SEG] Running segmentation model")
            
            # Run YOLO detection/segmentation
            # Use verbose=False to suppress Ultralytics stdout, we'll log via Python logging
            # Specify device for inference (YOLO will use it automatically if CUDA is available)
            results = self.model(
                frame,
                conf=self.confidence_threshold,
                iou=self.nms_threshold,
                device=self.device,  # Use detected/configured device
                verbose=False,  # Suppress Ultralytics stdout, use our logging instead
            )
            
            inference_time = (time.time() - inference_start) * 1000  # Convert to ms
            if self.detection_log_level in ['standard', 'detailed']:
                self.logger.info(
                    f"⏱️  [SEG] Inference completed | "
                    f"time={inference_time:.1f}ms"
                )
                # Ensure output is flushed immediately (important for Raspberry Pi)
                sys.stdout.flush()
            
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
                    if self.detection_log_level in ['standard', 'detailed']:
                        self.logger.info("🔍 [SEG] No detections found in frame")
                    continue
                
                # Log detection count
                if self.detection_log_level in ['standard', 'detailed']:
                    self.logger.info(
                        f"📊 [SEG] Found {num_instances} detection(s) in frame"
                    )
                
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
                    
                    # Log all bird detections (any confidence level)
                    if self.detection_log_level in ['standard', 'detailed']:
                        self.logger.info(
                            f"🐦 [DETECT] Bird found | "
                            f"conf={confidence:.3f} | "
                            f"bbox=[{int(x1)},{int(y1)},{int(x2)},{int(y2)}] | "
                            f"area={int(max(0, (x2 - x1)) * max(0, (y2 - y1)))} | "
                            f"class={class_name or 'bird'}"
                        )
                        # Ensure output is flushed immediately (important for Raspberry Pi)
                        sys.stdout.flush()
                    
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
                    # Only run species classification for high-confidence detections (>= 0.20)
                    species_name = None
                    species_conf = None
                    species_candidates = []
                    
                    # Check if species classification should run
                    species_model_available = (self._species_predict_fn is not None or self.species_model is not None)
                    confidence_high_enough = confidence >= 0.20
                    
                    # Log diagnostic info if species model is available but not running
                    if species_model_available and not confidence_high_enough:
                        if self.detection_log_level in ['standard', 'detailed']:
                            self.logger.debug(
                                f"⏭️  [SPECIES] Skipped (low confidence) | "
                                f"detection_conf={confidence:.3f} | "
                                f"required>=0.20"
                            )
                    elif not species_model_available:
                        if self.detection_log_level in ['standard', 'detailed']:
                            self.logger.debug(
                                f"⏭️  [SPECIES] Skipped (model not loaded) | "
                                f"detection_conf={confidence:.3f}"
                            )
                    
                    if confidence_high_enough and species_model_available:
                        # Log that species classification is running
                        if self.detection_log_level in ['standard', 'detailed']:
                            self.logger.info(
                                f"🔬 [SPECIES] Running species classifier | "
                                f"detection_conf={confidence:.3f} | "
                                f"threshold={self.species_confidence_threshold:.3f}"
                            )
                        try:
                            crop = self._extract_crop(
                                frame, polygon_points, x1, y1, x2, y2
                            )
                            if crop is not None:
                                if self.detection_log_level in ['standard', 'detailed']:
                                    self.logger.debug(
                                        f"🔬 [SPECIES] Crop extracted | "
                                        f"size={crop.shape if hasattr(crop, 'shape') else 'unknown'}"
                                    )
                                species_name, species_conf, species_candidates = self._classify_species(crop)
                                # Log species classification results
                                if self.detection_log_level in ['standard', 'detailed']:
                                    if species_name:
                                        self.logger.info(
                                            f"✅ [SPECIES] Identified | "
                                            f"species={species_name} | "
                                            f"confidence={species_conf:.3f} | "
                                            f"detection_conf={confidence:.3f}"
                                        )
                                    else:
                                        self.logger.info(
                                            f"❌ [SPECIES] No species above threshold | "
                                            f"detection_conf={confidence:.3f} | "
                                            f"threshold={self.species_confidence_threshold:.3f}"
                                        )
                                    # Log all candidate species if detailed logging
                                    if self.detection_log_level == 'detailed' and species_candidates:
                                        candidates_str = ", ".join(
                                            f"{name}={conf:.3f}" 
                                            for name, conf in species_candidates[:5]  # Top 5
                                        )
                                        self.logger.info(
                                            f"📊 [SPECIES] Top candidates | {candidates_str}"
                                        )
                            else:
                                if self.detection_log_level in ['standard', 'detailed']:
                                    self.logger.warning(
                                        f"⚠️  [SPECIES] Crop extraction failed | "
                                        f"detection_conf={confidence:.3f}"
                                    )
                        except Exception as ce:
                            self.logger.warning(
                                f"⚠️  [SPECIES] Classification error | {ce}"
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
    ) -> Tuple[Optional[str], Optional[float], List[Tuple[str, float]]]:
        """Run species classifier (Ultralytics or external backend).

        Returns:
            Tuple of (top_label, top_confidence, all_candidates)
            - top_label: Best species name if above threshold, else None
            - top_confidence: Confidence of top species if above threshold, else None
            - all_candidates: List of (species_name, confidence) tuples for all species (any confidence)
        """
        # External backend callable takes precedence if provided
        if self._species_predict_fn is not None:
            label, conf = self._species_predict_fn(crop_rgb_resized)
            candidates = [(label, conf)] if label else []
            # Filter by threshold for return value
            if conf and conf < self.species_confidence_threshold:
                return None, None, candidates
            return label, conf, candidates
        
        if self.species_model is None:
            return None, None, []
        
        # Run species classification with verbose=False to suppress Ultralytics stdout
        species_start = time.time()
        results = self.species_model(
            crop_rgb_resized,
            device=self.device,  # Use same device as main model
            verbose=False
        )
        species_time = (time.time() - species_start) * 1000  # Convert to ms
        
        # Log species inference timing if detailed logging is enabled
        if self.detection_log_level == 'detailed':
            self.logger.info(
                f"⏱️  [SPECIES] Classification inference | "
                f"time={species_time:.1f}ms"
            )
        if not results:
            return None, None, []
        
        res = results[0]
        names = getattr(res, 'names', None)
        probs = getattr(res, 'probs', None)
        if probs is None or names is None:
            return None, None, []
        
        arr = probs.data.detach().cpu().numpy()
        
        # Get all species predictions (any confidence) for logging
        all_candidates = []
        if names and isinstance(names, dict):
            for idx, conf_val in enumerate(arr):
                if idx in names:
                    species_name = names[idx]
                    if species_name:
                        formatted_name = self._format_species_name(species_name)
                        all_candidates.append((formatted_name, float(conf_val)))
        
        # Sort by confidence (descending)
        all_candidates.sort(key=lambda x: x[1], reverse=True)
        
        # Get top prediction
        top_i = int(np.argmax(arr))
        conf = float(arr[top_i])
        
        # Filter by confidence threshold - only return if above threshold
        if conf < self.species_confidence_threshold:
            return None, None, all_candidates
        
        label = names.get(top_i) if isinstance(names, dict) else None
        if label is not None:
            # Format the label to convert numeric IDs to readable names
            label = self._format_species_name(label)
        
        return label, conf, all_candidates
    
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
        self.detection_log_level = self.config.get('detection_log_level', 'standard')
        
        self.logger.info("Detector configuration updated")


class RaptorDetector(BirdSegmentationDetector):
    """Backward-compatible alias for legacy imports.

    This class preserves the previous public API name while leveraging the
    new bird-only segmentation detector implementation.
    """
    pass
