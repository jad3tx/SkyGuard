"""
Event Logger for SkyGuard System

Handles logging of detection events, system events, and data storage.
"""

import sqlite3
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import cv2
import numpy as np


class EventLogger:
    """Logs and stores detection events and system data.

    This class persists detection metadata and optional annotated images to a
    SQLite database and the filesystem. It also enforces data retention based
    on configuration settings.
    """
    
    def __init__(self, config: dict) -> None:
        """Initialize the event logger.
        
        Args:
            config: Storage configuration dictionary. Supported keys include
                `database_path`, `detection_images_path`, `log_retention_days`,
                and optional `detection_image_retention_days`.
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        db_path_str = config.get('database_path', 'data/skyguard.db')
        # Resolve to absolute path to ensure persistence across working directory changes
        # Try multiple resolution strategies: absolute, relative to CWD, relative to project root
        db_path_candidate = Path(db_path_str)
        if db_path_candidate.is_absolute():
            self.db_path = db_path_candidate
        elif db_path_candidate.exists():
            # Exists relative to current working directory
            self.db_path = db_path_candidate.resolve()
        else:
            # Try relative to project root (SkyGuard/)
            project_root = Path(__file__).parent.parent.parent
            self.db_path = (project_root / db_path_str).resolve()
        
        images_path_str = config.get('detection_images_path', 'data/detections')
        images_path_candidate = Path(images_path_str)
        if images_path_candidate.is_absolute():
            self.images_path = images_path_candidate
        elif images_path_candidate.exists():
            self.images_path = images_path_candidate.resolve()
        else:
            project_root = Path(__file__).parent.parent.parent
            self.images_path = (project_root / images_path_str).resolve()
        # Log/table retention for system events (defaults to 30 days)
        self.retention_days = int(config.get('log_retention_days', 30))
        # Detection image retention (defaults to log_retention_days if not set)
        self.image_retention_days = int(
            config.get('detection_image_retention_days', self.retention_days)
        )
        
        self.connection = None
        
    def initialize(self) -> bool:
        """Initialize the event logger and database.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create directories
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self.images_path.mkdir(parents=True, exist_ok=True)
            
            # Initialize database
            self._init_database()
            
            self.logger.info("Event logger initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize event logger: {e}")
            return False

    def _ensure_connection(self) -> bool:
        """Ensure an active SQLite connection exists.

        Returns:
            True if connection is valid or re-established, False otherwise
        """
        try:
            if self.connection is None:
                # Ensure database directory exists
                self.db_path.parent.mkdir(parents=True, exist_ok=True)
                self.connection = sqlite3.connect(str(self.db_path), check_same_thread=False)
                self.connection.execute('PRAGMA journal_mode=WAL')
                return True
            # Simple probe to validate connection
            try:
                cursor = self.connection.cursor()
                cursor.execute('SELECT 1')
                cursor.fetchone()
                return True
            except Exception:
                # Reconnect on failure
                self.connection.close()
                self.connection = sqlite3.connect(str(self.db_path), check_same_thread=False)
                self.connection.execute('PRAGMA journal_mode=WAL')
                return True
        except Exception as e:
            self.logger.error(f"Failed to ensure DB connection to {self.db_path}: {e}")
            return False
    
    def _init_database(self) -> None:
        """Initialize the SQLite database.

        Creates required tables and indices if they do not already exist.
        """
        try:
            # Ensure database directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Allow the same connection to be used across Flask request threads
            # Use WAL mode for better concurrency
            self.connection = sqlite3.connect(str(self.db_path), check_same_thread=False)
            # Enable WAL mode for better concurrent access
            self.connection.execute('PRAGMA journal_mode=WAL')
            cursor = self.connection.cursor()
            
            # Create detections table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS detections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    class_name TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    bbox_x1 INTEGER NOT NULL,
                    bbox_y1 INTEGER NOT NULL,
                    bbox_x2 INTEGER NOT NULL,
                    bbox_y2 INTEGER NOT NULL,
                    center_x INTEGER NOT NULL,
                    center_y INTEGER NOT NULL,
                    area INTEGER NOT NULL,
                    image_path TEXT,
                    species_name TEXT,
                    species_confidence REAL,
                    segmented_image_path TEXT,
                    metadata TEXT
                )
            ''')
            
            # Add new columns if they don't exist (for existing databases)
            try:
                cursor.execute('ALTER TABLE detections ADD COLUMN species_name TEXT')
            except sqlite3.OperationalError:
                pass  # Column already exists
            try:
                cursor.execute('ALTER TABLE detections ADD COLUMN species_confidence REAL')
            except sqlite3.OperationalError:
                pass  # Column already exists
            try:
                cursor.execute('ALTER TABLE detections ADD COLUMN segmented_image_path TEXT')
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            # Create system_events table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    event_type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    level TEXT NOT NULL,
                    metadata TEXT
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_detections_timestamp ON detections(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_detections_class ON detections(class_name)')
            try:
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_detections_species ON detections(species_name)')
            except sqlite3.OperationalError:
                pass  # Column might not exist in older databases
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_system_events_timestamp ON system_events(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_system_events_type ON system_events(event_type)')
            
            self.connection.commit()
            self.logger.info(f"Database initialized successfully at {self.db_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database at {self.db_path}: {e}")
            raise
    
    def log_detection(self, detection: Dict[str, Any], frame: Optional[np.ndarray] = None) -> bool:
        """Log a detection event.
        
        Args:
            detection: Detection information dictionary
            frame: Optional frame to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.connection is None:
                self.logger.error("Database not initialized")
                return False
            
            # Save frame if provided
            image_path = None
            segmented_image_path = None
            if frame is not None:
                image_path = self._save_detection_image(frame, detection)
                
                # Save segmented image if species is detected
                species = detection.get('species')
                species_conf = detection.get('species_confidence')
                if species and species_conf is not None and float(species_conf) >= 0.6:
                    segmented_image_path = self._save_segmented_image(frame, detection)
            
            # Insert detection record - prefer detection-provided timestamp
            cursor = self.connection.cursor()
            # Use detector's timestamp if present and valid; otherwise, fallback to now
            try:
                provided_ts = float(detection.get('timestamp')) if detection.get('timestamp') is not None else None
            except (TypeError, ValueError):
                provided_ts = None
            current_time = provided_ts if provided_ts is not None else time.time()
            
            species_name = detection.get('species')
            species_confidence = detection.get('species_confidence')
            if species_confidence is not None:
                try:
                    species_confidence = float(species_confidence)
                except (TypeError, ValueError):
                    species_confidence = None
            
            cursor.execute('''
                INSERT INTO detections (
                    timestamp, class_name, confidence, bbox_x1, bbox_y1, bbox_x2, bbox_y2,
                    center_x, center_y, area, image_path, species_name, species_confidence,
                    segmented_image_path, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                current_time,  # Store detector's timestamp when available
                detection['class_name'],
                detection['confidence'],
                detection['bbox'][0],
                detection['bbox'][1],
                detection['bbox'][2],
                detection['bbox'][3],
                detection['center'][0],
                detection['center'][1],
                detection['area'],
                image_path,
                species_name,
                species_confidence,
                segmented_image_path,
                json.dumps(detection.get('metadata', {}))
            ))
            
            self.connection.commit()
            
            self.logger.debug(f"Detection logged: {detection['class_name']} (confidence: {detection['confidence']:.2f})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to log detection: {e}")
            return False
    
    def _save_detection_image(self, frame: np.ndarray, detection: Dict[str, Any]) -> str:
        """Save detection image to disk.
        
        Args:
            frame: Frame to save
            detection: Detection information
            
        Returns:
            Path to saved image
        """
        try:
            # Prefer detection's timestamp for filename for consistency with DB/UI
            try:
                provided_ts = float(detection.get('timestamp')) if detection.get('timestamp') is not None else None
            except (TypeError, ValueError):
                provided_ts = None
            dt = datetime.fromtimestamp(provided_ts) if provided_ts is not None else datetime.now()
            filename = f"detection_{dt.strftime('%Y%m%d_%H%M%S_%f')[:-3]}_{detection['confidence']:.2f}.jpg"
            filepath = (self.images_path / filename).resolve()
            
            # Draw detection on frame
            annotated_frame = self._annotate_frame(frame, detection)
            self.logger.info(f"Saving annotated detection image: {filename}")
            
            # Save frame
            cv2.imwrite(str(filepath), annotated_frame)
            
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Failed to save detection image: {e}")
            return ""
    
    def _annotate_frame(self, frame: np.ndarray, detection: Dict[str, Any]) -> np.ndarray:
        """Annotate frame with detection information.
        
        Args:
            frame: Input frame
            detection: Detection information
            
        Returns:
            Annotated frame
        """
        try:
            annotated = frame.copy()
            bbox = detection['bbox']
            confidence = detection['confidence']
            class_name = detection['class_name']
            
            # Ensure bbox coordinates are within frame bounds
            h, w = frame.shape[:2]
            x1 = max(0, min(int(bbox[0]), w-1))
            y1 = max(0, min(int(bbox[1]), h-1))
            x2 = max(0, min(int(bbox[2]), w-1))
            y2 = max(0, min(int(bbox[3]), h-1))
            
            self.logger.info(f"Drawing bbox: frame size {w}x{h}, bbox ({x1},{y1}) to ({x2},{y2})")
            
            # Draw bounding box with very thick bright red line
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 0, 255), 5)
            
            # Draw label with larger font
            # Include species information if available
            species = detection.get('species')
            species_confidence = detection.get('species_confidence')
            if species and species_confidence is not None:
                label = f"{class_name}: {confidence:.2f} | {species}: {species_confidence:.2f}"
            else:
                label = f"{class_name}: {confidence:.2f}"
            font_scale = 0.8
            thickness = 2
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)[0]
            
            # Draw label background with bright red
            cv2.rectangle(annotated, 
                        (x1, y1 - label_size[1] - 10),
                        (x1 + label_size[0], y1),
                        (0, 0, 255), -1)
            
            # Draw label text
            cv2.putText(annotated, label,
                      (x1, y1 - 5),
                      cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 0), thickness)
            
            self.logger.info(f"Successfully annotated frame with bbox: ({x1},{y1}) to ({x2},{y2})")
            return annotated
            
        except Exception as e:
            self.logger.error(f"Failed to annotate frame: {e}")
            return frame
    
    def _save_segmented_image(self, frame: np.ndarray, detection: Dict[str, Any]) -> str:
        """Save segmented detection image with species annotations.
        
        Args:
            frame: Frame to save
            detection: Detection information
            
        Returns:
            Path to saved segmented image
        """
        try:
            # Prefer detection's timestamp for filename for consistency with DB/UI
            try:
                provided_ts = float(detection.get('timestamp')) if detection.get('timestamp') is not None else None
            except (TypeError, ValueError):
                provided_ts = None
            dt = datetime.fromtimestamp(provided_ts) if provided_ts is not None else datetime.now()
            
            species = detection.get('species', 'unknown')
            species_conf = float(detection.get('species_confidence', 0.0))
            species_safe = species.replace(" ", "_").replace("/", "_").replace("(", "").replace(")", "").replace(",", "")
            filename = f"detection_{dt.strftime('%Y%m%d_%H%M%S_%f')[:-3]}_{species_safe}_{species_conf:.2f}_segmented.jpg"
            filepath = (self.images_path / filename).resolve()
            
            # Draw segmented frame with species annotations
            segmented_frame = self._draw_segmented_frame(frame, detection)
            self.logger.info(f"Saving segmented detection image: {filename}")
            
            # Save frame
            cv2.imwrite(str(filepath), segmented_frame)
            
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Failed to save segmented detection image: {e}")
            return ""
    
    def _draw_segmented_frame(self, frame: np.ndarray, detection: Dict[str, Any]) -> np.ndarray:
        """Draw segmentation mask, bounding box, and species label on frame.
        
        Args:
            frame: Input frame
            detection: Detection information
            
        Returns:
            Annotated frame with segmentation mask and species label
        """
        try:
            annotated_frame = frame.copy()
            bbox = detection.get("bbox")
            confidence = float(detection.get("confidence", 0.0))
            class_name = detection.get("class_name", "bird")
            polygon = detection.get("polygon")
            species = detection.get("species")
            species_confidence = detection.get("species_confidence")
            
            # Draw segmentation mask if available
            if polygon is not None and len(polygon) > 0:
                overlay = annotated_frame.copy()
                pts = np.array(polygon, dtype=np.int32)
                # Use green color for segmentation mask
                cv2.fillPoly(overlay, [pts], color=(0, 255, 0))
                # Alpha blend mask for transparency
                alpha = 0.3
                annotated_frame = cv2.addWeighted(
                    overlay,
                    alpha,
                    annotated_frame,
                    1 - alpha,
                    0,
                )
            
            # Draw bounding box
            if bbox and len(bbox) == 4:
                h, w = frame.shape[:2]
                x1 = max(0, min(int(bbox[0]), w-1))
                y1 = max(0, min(int(bbox[1]), h-1))
                x2 = max(0, min(int(bbox[2]), w-1))
                y2 = max(0, min(int(bbox[3]), h-1))
                cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                
                # Build label text with species
                if species and species_confidence is not None:
                    label = f"{class_name}: {confidence:.2f} | {species}: {species_confidence:.2f}"
                else:
                    label = f"{class_name}: {confidence:.2f}"
                
                # Calculate label size for background
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.6
                thickness = 2
                (label_width, label_height), baseline = cv2.getTextSize(
                    label, font, font_scale, thickness
                )
                
                # Draw label background
                label_y = max(label_height + 5, y1)
                cv2.rectangle(
                    annotated_frame,
                    (x1, label_y - label_height - 5),
                    (x1 + label_width, label_y + baseline),
                    (0, 255, 0),
                    -1,
                )
                
                # Draw label text
                cv2.putText(
                    annotated_frame,
                    label,
                    (x1, label_y),
                    font,
                    font_scale,
                    (0, 0, 0),
                    thickness,
                    cv2.LINE_AA,
                )
            
            return annotated_frame
            
        except Exception as e:
            self.logger.error(f"Failed to draw segmented frame: {e}")
            return frame
    
    def log_system_event(self, event_type: str, message: str, level: str = "INFO", metadata: Optional[Dict] = None) -> bool:
        """Log a system event.
        
        Args:
            event_type: Type of event
            message: Event message
            level: Log level (INFO, WARNING, ERROR)
            metadata: Optional metadata dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.connection is None:
                self.logger.error("Database not initialized")
                return False
            
            cursor = self.connection.cursor()
            cursor.execute('''
                INSERT INTO system_events (timestamp, event_type, message, level, metadata)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                time.time(),
                event_type,
                message,
                level,
                json.dumps(metadata or {})
            ))
            
            self.connection.commit()
            
            self.logger.debug(f"System event logged: {event_type} - {message}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to log system event: {e}")
            return False
    
    def count_detections(self, start_time: Optional[float] = None, end_time: Optional[float] = None, 
                        class_name: Optional[str] = None, species_name: Optional[str] = None) -> int:
        """Count detection records from database.
        
        Args:
            start_time: Start timestamp filter
            end_time: End timestamp filter
            class_name: Class name filter
            species_name: Species name filter
            
        Returns:
            Total count of matching detections
        """
        try:
            if not self._ensure_connection():
                return 0
            
            cursor = self.connection.cursor()
            
            # Build query
            query = "SELECT COUNT(*) FROM detections WHERE 1=1"
            params = []
            
            if start_time is not None:
                query += " AND timestamp >= ?"
                params.append(start_time)
            
            if end_time is not None:
                query += " AND timestamp <= ?"
                params.append(end_time)
            
            if class_name is not None:
                query += " AND class_name = ?"
                params.append(class_name)
            
            if species_name is not None:
                query += " AND species_name = ?"
                params.append(species_name)
            
            cursor.execute(query, params)
            result = cursor.fetchone()
            return result[0] if result else 0
            
        except Exception as e:
            self.logger.error(f"Failed to count detections: {e}")
            return 0
    
    def get_detections(self, start_time: Optional[float] = None, end_time: Optional[float] = None, 
                     class_name: Optional[str] = None, species_name: Optional[str] = None,
                     limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """Get detection records from database.
        
        Args:
            start_time: Start timestamp filter
            end_time: End timestamp filter
            class_name: Class name filter
            species_name: Species name filter
            limit: Maximum number of records to return
            offset: Number of records to skip (for pagination)
            
        Returns:
            List of detection records
        """
        try:
            if not self._ensure_connection():
                return []
            
            cursor = self.connection.cursor()
            
            # Build query
            query = "SELECT * FROM detections WHERE 1=1"
            params = []
            
            if start_time is not None:
                query += " AND timestamp >= ?"
                params.append(start_time)
            
            if end_time is not None:
                query += " AND timestamp <= ?"
                params.append(end_time)
            
            if class_name is not None:
                query += " AND class_name = ?"
                params.append(class_name)
            
            if species_name is not None:
                query += " AND species_name = ?"
                params.append(species_name)
            
            query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
            params.append(limit)
            params.append(offset)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Convert to dictionaries
            detections = []
            for row in rows:
                # Handle both old and new schema (with/without species columns)
                detection = {
                    'id': row[0],
                    'timestamp': row[1],
                    'class_name': row[2],
                    'confidence': row[3],
                    'bbox': [row[4], row[5], row[6], row[7]],
                    'center': [row[8], row[9]],
                    'area': row[10],
                    'image_path': row[11] if len(row) > 11 else None,
                    'species_name': row[12] if len(row) > 12 else None,
                    'species_confidence': row[13] if len(row) > 13 else None,
                    'segmented_image_path': row[14] if len(row) > 14 else None,
                    'metadata': json.loads(row[15]) if len(row) > 15 and row[15] else {}
                }
                detections.append(detection)
            
            return detections
            
        except Exception as e:
            self.logger.error(f"Failed to get detections: {e}")
            return []
    
    def get_species_stats(self, days: Optional[int] = None) -> Dict[str, Any]:
        """Get species detection statistics.
        
        Args:
            days: Optional number of days to analyze (None = all time)
            
        Returns:
            Dictionary with species statistics including counts, confidence averages, and reference images
        """
        try:
            if not self._ensure_connection():
                return {}
            
            cursor = self.connection.cursor()
            
            # Build query with optional time filter
            if days is not None:
                end_time = time.time()
                start_time = end_time - (days * 24 * 60 * 60)
                time_filter = "WHERE timestamp >= ?"
                params = (start_time,)
            else:
                time_filter = ""
                params = ()
            
            # Get species breakdown with statistics
            query = f'''
                SELECT 
                    species_name,
                    COUNT(*) as count,
                    AVG(confidence) as avg_detection_confidence,
                    AVG(species_confidence) as avg_species_confidence,
                    MIN(timestamp) as first_seen,
                    MAX(timestamp) as last_seen
                FROM detections 
                {time_filter}
                AND species_name IS NOT NULL
                GROUP BY species_name
                ORDER BY count DESC
            '''
            
            cursor.execute(query, params)
            species_rows = cursor.fetchall()
            
            # Get reference images (most recent detection with segmented image for each species)
            species_stats = []
            for row in species_rows:
                species_name = row[0]
                count = row[1]
                avg_detection_conf = row[2]
                avg_species_conf = row[3]
                first_seen = row[4]
                last_seen = row[5]
                
                # Get reference image path (most recent segmented image for this species)
                ref_image_query = '''
                    SELECT segmented_image_path, image_path, timestamp
                    FROM detections
                    WHERE species_name = ? AND segmented_image_path IS NOT NULL
                    ORDER BY timestamp DESC
                    LIMIT 1
                '''
                if days is not None:
                    ref_image_query = '''
                        SELECT segmented_image_path, image_path, timestamp
                        FROM detections
                        WHERE species_name = ? AND segmented_image_path IS NOT NULL AND timestamp >= ?
                        ORDER BY timestamp DESC
                        LIMIT 1
                    '''
                    cursor.execute(ref_image_query, (species_name, start_time))
                else:
                    cursor.execute(ref_image_query, (species_name,))
                
                ref_image_row = cursor.fetchone()
                reference_image = ref_image_row[0] if ref_image_row else None
                fallback_image = ref_image_row[1] if ref_image_row and not reference_image else None
                
                species_stats.append({
                    'species': species_name,
                    'count': count,
                    'avg_detection_confidence': float(avg_detection_conf) if avg_detection_conf else None,
                    'avg_species_confidence': float(avg_species_conf) if avg_species_conf else None,
                    'first_seen': first_seen,
                    'last_seen': last_seen,
                    'reference_image': reference_image or fallback_image,
                })
            
            return {
                'period_days': days,
                'total_species': len(species_stats),
                'species_breakdown': species_stats,
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get species stats: {e}")
            return {}
    
    def get_detection_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get detection statistics for the specified period.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with statistics
        """
        try:
            if not self._ensure_connection():
                return {}
            
            end_time = time.time()
            start_time = end_time - (days * 24 * 60 * 60)
            
            cursor = self.connection.cursor()
            
            # Total detections
            cursor.execute('SELECT COUNT(*) FROM detections WHERE timestamp >= ?', (start_time,))
            total_detections = cursor.fetchone()[0]
            
            # Detections by class
            cursor.execute('''
                SELECT class_name, COUNT(*) as count, AVG(confidence) as avg_confidence
                FROM detections 
                WHERE timestamp >= ?
                GROUP BY class_name
                ORDER BY count DESC
            ''', (start_time,))
            class_stats = cursor.fetchall()
            
            # Species breakdown
            cursor.execute('''
                SELECT species_name, COUNT(*) as count, AVG(species_confidence) as avg_confidence
                FROM detections 
                WHERE timestamp >= ? AND species_name IS NOT NULL
                GROUP BY species_name
                ORDER BY count DESC
            ''', (start_time,))
            species_stats = cursor.fetchall()
            
            # Daily breakdown
            cursor.execute('''
                SELECT DATE(datetime(timestamp, 'unixepoch')) as date, COUNT(*) as count
                FROM detections 
                WHERE timestamp >= ?
                GROUP BY date
                ORDER BY date DESC
            ''', (start_time,))
            daily_stats = cursor.fetchall()
            
            return {
                'period_days': days,
                'total_detections': total_detections,
                'class_breakdown': [{'class': row[0], 'count': row[1], 'avg_confidence': row[2]} for row in class_stats],
                'species_breakdown': [{'species': row[0], 'count': row[1], 'avg_confidence': row[2]} for row in species_stats],
                'daily_breakdown': [{'date': row[0], 'count': row[1]} for row in daily_stats],
                'start_time': start_time,
                'end_time': end_time,
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get detection stats: {e}")
            return {}
    
    def cleanup_old_data(self) -> bool:
        """Clean up old data based on retention policy.
        
        Deletes detection records and associated image files older than
        `image_retention_days`, and system events older than `retention_days`.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self._ensure_connection():
                return False

            now = time.time()
            detections_cutoff_time = now - (self.image_retention_days * 24 * 60 * 60)
            events_cutoff_time = now - (self.retention_days * 24 * 60 * 60)

            cursor = self.connection.cursor()
            
            # Get old detection records
            cursor.execute('SELECT id, image_path FROM detections WHERE timestamp < ?', (detections_cutoff_time,))
            old_detections = cursor.fetchall()
            
            # Delete old image files
            for detection_id, image_path in old_detections:
                if image_path and Path(image_path).exists():
                    try:
                        Path(image_path).unlink()
                    except Exception as e:
                        self.logger.warning(f"Failed to delete old image {image_path}: {e}")
            
            # Delete old detection records
            cursor.execute('DELETE FROM detections WHERE timestamp < ?', (detections_cutoff_time,))
            deleted_detections = cursor.rowcount
            
            # Delete old system events
            cursor.execute('DELETE FROM system_events WHERE timestamp < ?', (events_cutoff_time,))
            deleted_events = cursor.rowcount
            
            self.connection.commit()
            
            self.logger.info(f"Cleaned up {deleted_detections} old detections and {deleted_events} old events")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to cleanup old data: {e}")
            return False

    def get_detection_by_id(self, detection_id: int) -> Optional[Dict[str, Any]]:
        """Get a single detection by its identifier.

        Args:
            detection_id: The database primary key of the detection.

        Returns:
            A detection record dictionary if found, otherwise None.
        """
        try:
            if not self._ensure_connection():
                return None

            cursor = self.connection.cursor()
            cursor.execute('SELECT * FROM detections WHERE id = ?', (detection_id,))
            row = cursor.fetchone()
            if row is None:
                return None

            # Handle both old and new schema (with/without species columns)
            return {
                'id': row[0],
                'timestamp': row[1],
                'class_name': row[2],
                'confidence': row[3],
                'bbox': [row[4], row[5], row[6], row[7]],
                'center': [row[8], row[9]],
                'area': row[10],
                'image_path': row[11] if len(row) > 11 else None,
                'species_name': row[12] if len(row) > 12 else None,
                'species_confidence': row[13] if len(row) > 13 else None,
                'segmented_image_path': row[14] if len(row) > 14 else None,
                'metadata': json.loads(row[15]) if len(row) > 15 and row[15] else {},
            }
        except Exception as e:
            self.logger.error(f"Failed to get detection by id {detection_id}: {e}")
            return None
    
    def cleanup(self) -> None:
        """Clean up resources."""
        try:
            if self.connection:
                self.connection.close()
                self.connection = None
            
            self.logger.info("Event logger cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during event logger cleanup: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup."""
        self.cleanup()
