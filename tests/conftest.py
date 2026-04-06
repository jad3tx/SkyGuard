"""
Shared pytest fixtures for the SkyGuard test suite.

This conftest.py provides:
  - A reusable ``tmp_storage_config`` fixture pointing at a fresh temp
    directory so tests never touch the production SQLite database.
  - A minimal ``base_detection`` dict used by multiple test modules.
  - A ``minimal_alert_config`` dict with all five channels disabled.
"""

import time
from pathlib import Path
from typing import Any, Dict

import pytest

from skyguard.storage.event_logger import EventLogger
from skyguard.core.alert_system import AlertSystem


# ---------------------------------------------------------------------------
# Storage / database fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_storage_config(tmp_path: Path) -> Dict[str, Any]:
    """Return a storage config dict pointing at a fresh temp directory.

    Creates the ``detections/`` sub-directory inside ``tmp_path`` so
    EventLogger can be initialised without touching the production DB.
    """
    det_dir = tmp_path / "detections"
    det_dir.mkdir(parents=True, exist_ok=True)
    return {
        "database_path": str(tmp_path / "test.db"),
        "detection_images_path": str(det_dir),
        "log_retention_days": 30,
    }


@pytest.fixture
def initialized_event_logger(tmp_storage_config: Dict[str, Any]) -> EventLogger:
    """Return an EventLogger that has been fully initialised against a temp DB."""
    el = EventLogger(tmp_storage_config)
    assert el.initialize() is True, "EventLogger failed to initialise"
    return el


# ---------------------------------------------------------------------------
# Detection fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def base_detection() -> Dict[str, Any]:
    """Minimal valid detection dict with no species data."""
    return {
        "class_name": "bird",
        "confidence": 0.85,
        "bbox": [10, 20, 110, 120],
        "center": [60, 70],
        "area": 10000,
        "timestamp": time.time(),
    }


@pytest.fixture
def species_detection() -> Dict[str, Any]:
    """Valid detection dict including species classification data."""
    return {
        "class_name": "bird",
        "confidence": 0.88,
        "species": "Sharp-shinned Hawk",
        "species_confidence": 0.82,
        "bbox": [10, 20, 110, 120],
        "center": [60, 70],
        "area": 10000,
        "timestamp": time.time(),
    }


# ---------------------------------------------------------------------------
# Alert system fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def minimal_alert_config() -> Dict[str, Any]:
    """All five notification channels disabled — safe for unit tests."""
    return {ch: {"enabled": False} for ch in ("audio", "push", "sms", "email", "discord")}


@pytest.fixture
def alert_system(minimal_alert_config: Dict[str, Any]) -> AlertSystem:
    """AlertSystem with all channels disabled and default rate limits."""
    return AlertSystem(minimal_alert_config)


@pytest.fixture
def alert_system_with_logger(
    minimal_alert_config: Dict[str, Any],
    initialized_event_logger: EventLogger,
) -> AlertSystem:
    """AlertSystem wired to a temp EventLogger for delivery-log tests."""
    return AlertSystem(minimal_alert_config, event_logger=initialized_event_logger)
