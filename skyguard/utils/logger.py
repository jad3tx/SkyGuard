"""
Logging Configuration for SkyGuard System

Sets up structured logging for the SkyGuard application.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Dict, Any


def setup_logging(config: Dict[str, Any]) -> None:
    """Setup logging configuration for the SkyGuard system.
    
    Args:
        config: Logging configuration dictionary
    """
    # Get configuration values
    log_level = config.get('level', 'INFO').upper()
    log_file = config.get('file', 'logs/skyguard.log')
    max_size_mb = config.get('max_size_mb', 10)
    backup_count = config.get('backup_count', 5)
    
    # Create logs directory
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert log level string to logging constant
    numeric_level = getattr(logging, log_level, logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler (only if console_output is enabled, default True)
    console_output = config.get('console_output', True)
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        # Ensure immediate flushing for real-time output (important for Raspberry Pi)
        console_handler.stream = sys.stdout
        root_logger.addHandler(console_handler)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_size_mb * 1024 * 1024,  # Convert MB to bytes
        backupCount=backup_count
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # Set specific logger levels
    logging.getLogger('ultralytics').setLevel(logging.WARNING)
    logging.getLogger('torch').setLevel(logging.WARNING)
    logging.getLogger('PIL').setLevel(logging.WARNING)
    
    # Ensure detector logger uses appropriate level for inference details
    # The detector module logger should respect the root logger level
    detector_logger = logging.getLogger('skyguard.core.detector')
    detector_logger.setLevel(numeric_level)
    
    # Ensure stdout/stderr are unbuffered for real-time output (important for Raspberry Pi)
    # Python 3.7+ has reconfigure, older versions need different approach
    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(line_buffering=True)
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(line_buffering=True)
    except (AttributeError, ValueError):
        # Fallback: set PYTHONUNBUFFERED environment variable effect
        # or use flush() calls in critical sections
        pass
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info("SkyGuard logging system initialized")
    logger.info(f"Log level: {log_level}")
    logger.info(f"Log file: {log_file}")
    logger.info(f"Max file size: {max_size_mb}MB")
    logger.info(f"Backup count: {backup_count}")
    logger.info(f"Console output: {console_output}")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the given name.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
