"""
SkyGuard Storage Module

Handles data storage, event logging, and database operations.
"""

from .event_logger import EventLogger

__all__ = [
    "EventLogger",
]
