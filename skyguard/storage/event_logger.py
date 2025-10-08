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
        self.db_path = Path(config.get('database_path', 'data/skyguard.db'))
        self.images_path = Path(config.get('detection_images_path', 'data/detections'))
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
                self.connection = sqlite3.connect(str(self.db_path), check_same_thread=False)
                return True
            # Simple probe to validate connection
            try:
                cursor = self.connection.cursor()
                cursor.execute('SELECT 1')
                cursor.fetchone()
                return True
            except Exception:
                # Reconnect on failure
                self.connection = sqlite3.connect(str(self.db_path), check_same_thread=False)
                return True
        except Exception as e:
            self.logger.error(f"Failed to ensure DB connection: {e}")
            return False
    
    def _init_database(self) -> None:
        """Initialize the SQLite database.

        Creates required tables and indices if they do not already exist.
        """
        try:
            # Allow the same connection to be used across Flask request threads
            self.connection = sqlite3.connect(str(self.db_path), check_same_thread=False)
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
                    metadata TEXT
                )
            ''')
            
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
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_system_events_timestamp ON system_events(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_system_events_type ON system_events(event_type)')
            
            self.connection.commit()
            self.logger.info("Database initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
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
            if frame is not None:
                image_path = self._save_detection_image(frame, detection)
            
            # Insert detection record - prefer detection-provided timestamp
            cursor = self.connection.cursor()
            # Use detector's timestamp if present and valid; otherwise, fallback to now
            try:
                provided_ts = float(detection.get('timestamp')) if detection.get('timestamp') is not None else None
            except (TypeError, ValueError):
                provided_ts = None
            current_time = provided_ts if provided_ts is not None else time.time()
            cursor.execute('''
                INSERT INTO detections (
                    timestamp, class_name, confidence, bbox_x1, bbox_y1, bbox_x2, bbox_y2,
                    center_x, center_y, area, image_path, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
    
    def get_detections(self, start_time: Optional[float] = None, end_time: Optional[float] = None, 
                     class_name: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Get detection records from database.
        
        Args:
            start_time: Start timestamp filter
            end_time: End timestamp filter
            class_name: Class name filter
            limit: Maximum number of records to return
            
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
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Convert to dictionaries
            detections = []
            for row in rows:
                detection = {
                    'id': row[0],
                    'timestamp': row[1],
                    'class_name': row[2],
                    'confidence': row[3],
                    'bbox': [row[4], row[5], row[6], row[7]],
                    'center': [row[8], row[9]],
                    'area': row[10],
                    'image_path': row[11],
                    'metadata': json.loads(row[12]) if row[12] else {}
                }
                detections.append(detection)
            
            return detections
            
        except Exception as e:
            self.logger.error(f"Failed to get detections: {e}")
            return []
    
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

            return {
                'id': row[0],
                'timestamp': row[1],
                'class_name': row[2],
                'confidence': row[3],
                'bbox': [row[4], row[5], row[6], row[7]],
                'center': [row[8], row[9]],
                'area': row[10],
                'image_path': row[11],
                'metadata': json.loads(row[12]) if row[12] else {},
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
