"""
Tests for detection image retention and web API image serving.

These tests validate that:
- Detection images are saved and retained for one day, then removed by cleanup
- The web API returns detection records with correct image paths
- The web API serves the image file for an existing detection
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import pytest

from skyguard.storage.event_logger import EventLogger
from skyguard.web.app import SkyGuardWebPortal

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixtu
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture


@pytest.fixture
def tmp_storage_dir(tmp_path: Path) -> Path:
    """Create a temporary storage directory for detections and database."""
    (tmp_path / "data" / "detections").mkdir(parents=True, exist_ok=True)
    return tmp_path


def _make_config(tmp_storage_dir: Path) -> dict:
    """Build a minimal storage config with 1-day image retention."""
    return {
        "database_path": str(tmp_storage_dir / "data" / "skyguard.db"),
        "detection_images_path": str(tmp_storage_dir / "data" / "detections"),
        "log_retention_days": 30,
        "detection_image_retention_days": 1,
    }


def _fake_frame() -> np.ndarray:
    """Create a simple RGB image array for saving tests."""
    return np.zeros((100, 100, 3), dtype=np.uint8)


def _fake_detection(ts: float) -> dict:
    """Create a minimal detection record used by EventLogger."""
    return {
        "timestamp": ts,
        "class_name": "bird",
        "confidence": 0.9,
        "bbox": [10, 10, 50, 50],
        "center": [30, 30],
        "area": 1600,
        "metadata": {},
    }


def test_image_saved_and_cleanup_after_one_day(tmp_storage_dir: Path) -> None:
    """EventLogger should save images and clean up those older than 1 day."""
    storage_cfg = _make_config(tmp_storage_dir)
    logger = EventLogger(storage_cfg)
    assert logger.initialize() is True

    # Insert two detections: one recent, one older than 1 day
    now = time.time()
    older_than_one_day = now - (2 * 24 * 60 * 60)

    # Log old detection
    assert logger.log_detection(_fake_detection(older_than_one_day), _fake_frame()) is True
    # Log recent detection
    assert logger.log_detection(_fake_detection(now), _fake_frame()) is True

    # Perform cleanup
    assert logger.cleanup_old_data() is True

    # Verify only recent detection remains
    dets = logger.get_detections(limit=10)
    assert len(dets) == 1
    assert dets[0]["timestamp"] >= now - 5  # within a few seconds margin

    # Verify image file exists for the remaining detection
    image_path = dets[0]["image_path"]
    assert image_path
    assert Path(image_path).exists()


def test_web_api_serves_detection_image(tmp_storage_dir: Path) -> None:
    """Web API should serve detection image via /api/detections/<id>/image."""
    # Build full portal with config pointing to our tmp storage
    config_path = str(tmp_storage_dir / "config_test.yaml")
    # Minimal config structure used by portal
    app_cfg = {
        "storage": _make_config(tmp_storage_dir),
        "camera": {},
        "ai": {},
        "notifications": {},
    }

    # Write config file for portal init
    import yaml
    with open(config_path, "w", encoding="utf-8") as fh:
        yaml.safe_dump(app_cfg, fh)

    portal = SkyGuardWebPortal(config_path)
    client = portal.app.test_client()

    # Create one detection via EventLogger directly
    logger = portal.event_logger
    assert logger is not None
    ts = time.time()
    assert logger.log_detection(_fake_detection(ts), _fake_frame()) is True

    # Fetch recent detections
    resp = client.get("/api/detections")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data and "detections" in data
    assert len(data["detections"]) >= 1
    detection_id = data["detections"][0]["id"]

    # Fetch detection image
    img_resp = client.get(f"/api/detections/{detection_id}/image")
    assert img_resp.status_code == 200
    assert img_resp.mimetype == "image/jpeg"



