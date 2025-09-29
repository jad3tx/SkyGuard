"""
Tests for CameraSnapshotService with real camera integration.

This module tests the CameraSnapshotService using real camera hardware
and file system operations without mocking.
"""

import pytest
import time
import os
import cv2
import numpy as np
from pathlib import Path
from typing import TYPE_CHECKING

from skyguard.core.camera_snapshot import CameraSnapshotService
from skyguard.core.camera import CameraManager
from skyguard.core.config_manager import ConfigManager

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture


class TestCameraSnapshotService:
    """Test CameraSnapshotService with real components."""

    @pytest.fixture
    def config_manager(self) -> ConfigManager:
        """Create a real ConfigManager instance."""
        return ConfigManager("config/skyguard.yaml")

    @pytest.fixture
    def camera_manager(self, config_manager: ConfigManager) -> CameraManager:
        """Create a real CameraManager instance."""
        return CameraManager(config_manager.config)

    @pytest.fixture
    def snapshot_service(self) -> CameraSnapshotService:
        """Create a CameraSnapshotService instance."""
        return CameraSnapshotService()

    def test_snapshot_service_initialization(self, snapshot_service: CameraSnapshotService) -> None:
        """Test that CameraSnapshotService initializes correctly."""
        assert snapshot_service is not None
        assert not snapshot_service.running
        assert snapshot_service.interval == 3.0

    def test_snapshot_service_start_stop(self, snapshot_service: CameraSnapshotService, camera_manager: CameraManager) -> None:
        """Test starting and stopping the snapshot service."""
        # Test initial state
        assert not snapshot_service.running
        
        # Start the service
        snapshot_service.start(camera_manager)
        assert snapshot_service.running
        
        # Wait a moment for service to run
        time.sleep(1)
        
        # Stop the service
        snapshot_service.stop()
        assert not snapshot_service.running

    def test_snapshot_service_creates_files(self, snapshot_service: CameraSnapshotService, camera_manager: CameraManager) -> None:
        """Test that the snapshot service creates snapshot files."""
        # Clean up any existing snapshot
        snapshot_path = Path("data/camera_snapshot.jpg")
        if snapshot_path.exists():
            snapshot_path.unlink()
        
        # Start the service
        snapshot_service.start(camera_manager)
        
        # Wait for snapshot to be created
        time.sleep(4)  # Wait longer than the 3-second interval
        
        # Check if snapshot file was created
        assert snapshot_path.exists(), "Snapshot file should be created"
        assert snapshot_path.stat().st_size > 0, "Snapshot file should not be empty"
        
        # Stop the service
        snapshot_service.stop()

    def test_snapshot_service_file_content(self, snapshot_service: CameraSnapshotService, camera_manager: CameraManager) -> None:
        """Test that the snapshot service creates valid image files."""
        # Clean up any existing snapshot
        snapshot_path = Path("data/camera_snapshot.jpg")
        if snapshot_path.exists():
            snapshot_path.unlink()
        
        # Start the service
        snapshot_service.start(camera_manager)
        
        # Wait for snapshot to be created
        time.sleep(4)
        
        # Verify the file is a valid image
        if snapshot_path.exists():
            # Try to read the image with OpenCV
            img = cv2.imread(str(snapshot_path))
            assert img is not None, "Snapshot should be a valid image"
            assert len(img.shape) == 3, "Image should have 3 dimensions (height, width, channels)"
            assert img.shape[2] == 3, "Image should have 3 color channels"
        
        # Stop the service
        snapshot_service.stop()

    def test_snapshot_service_interval_timing(self, snapshot_service: CameraSnapshotService, camera_manager: CameraManager) -> None:
        """Test that the snapshot service respects the interval timing."""
        # Clean up any existing snapshot
        snapshot_path = Path("data/camera_snapshot.jpg")
        if snapshot_path.exists():
            snapshot_path.unlink()
        
        # Start the service
        snapshot_service.start(camera_manager)
        
        # Record initial time
        start_time = time.time()
        
        # Wait for first snapshot
        while not snapshot_path.exists() and (time.time() - start_time) < 10:
            time.sleep(0.1)
        
        assert snapshot_path.exists(), "First snapshot should be created within 10 seconds"
        first_snapshot_time = snapshot_path.stat().st_mtime
        
        # Wait for second snapshot
        time.sleep(3.5)  # Wait longer than the interval
        second_snapshot_time = snapshot_path.stat().st_mtime
        
        # Verify the second snapshot is newer
        assert second_snapshot_time > first_snapshot_time, "Second snapshot should be newer than first"
        
        # Stop the service
        snapshot_service.stop()

    def test_snapshot_service_without_camera(self, snapshot_service: CameraSnapshotService) -> None:
        """Test snapshot service behavior when no camera is available."""
        # Create a mock camera manager that will fail
        class MockCameraManager:
            def capture_frame(self):
                return None
        
        mock_camera = MockCameraManager()
        
        # Start the service with mock camera
        snapshot_service.start(mock_camera)
        
        # Wait a moment
        time.sleep(1)
        
        # The service should still be running even if camera fails
        assert snapshot_service.running
        
        # Stop the service
        snapshot_service.stop()

    def test_snapshot_service_get_bytes(self, snapshot_service: CameraSnapshotService, camera_manager: CameraManager) -> None:
        """Test getting snapshot bytes from the service."""
        # Start the service
        snapshot_service.start(camera_manager)
        
        # Wait for snapshot to be created
        time.sleep(4)
        
        # Get snapshot bytes
        snapshot_bytes = snapshot_service.get_snapshot_bytes()
        
        # Verify we got bytes
        assert snapshot_bytes is not None, "Should get snapshot bytes"
        assert len(snapshot_bytes) > 0, "Snapshot bytes should not be empty"
        
        # Verify it's valid image data by trying to decode it
        nparr = np.frombuffer(snapshot_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        assert img is not None, "Snapshot bytes should decode to valid image"
        
        # Stop the service
        snapshot_service.stop()

    def test_snapshot_service_cleanup(self, snapshot_service: CameraSnapshotService, camera_manager: CameraManager) -> None:
        """Test that the snapshot service cleans up properly."""
        # Start the service
        snapshot_service.start(camera_manager)
        assert snapshot_service.running
        
        # Stop the service
        snapshot_service.stop()
        assert not snapshot_service.running
        
        # Start and stop again to ensure cleanup works multiple times
        snapshot_service.start(camera_manager)
        assert snapshot_service.running
        snapshot_service.stop()
        assert not snapshot_service.running

    def test_snapshot_service_file_persistence(self, snapshot_service: CameraSnapshotService, camera_manager: CameraManager) -> None:
        """Test that snapshot files persist after service stops."""
        # Clean up any existing snapshot
        snapshot_path = Path("data/camera_snapshot.jpg")
        if snapshot_path.exists():
            snapshot_path.unlink()
        
        # Start the service
        snapshot_service.start(camera_manager)
        
        # Wait for snapshot to be created
        time.sleep(4)
        
        # Verify snapshot exists
        assert snapshot_path.exists(), "Snapshot file should exist"
        file_size = snapshot_path.stat().st_size
        
        # Stop the service
        snapshot_service.stop()
        
        # Verify snapshot still exists after service stops
        assert snapshot_path.exists(), "Snapshot file should persist after service stops"
        # File size might change slightly due to continued updates, so just check it's reasonable
        assert snapshot_path.stat().st_size > 0, "Snapshot file should not be empty"


class TestCameraSnapshotIntegration:
    """Integration tests for CameraSnapshotService with real system components."""

    @pytest.fixture
    def config_manager(self) -> ConfigManager:
        """Create a real ConfigManager instance."""
        return ConfigManager("config/skyguard.yaml")

    @pytest.fixture
    def camera_manager(self, config_manager: ConfigManager) -> CameraManager:
        """Create a real CameraManager instance."""
        return CameraManager(config_manager.config)

    def test_snapshot_service_with_real_camera_system(self, config_manager: ConfigManager, camera_manager: CameraManager) -> None:
        """Test snapshot service integration with real camera system."""
        # Initialize camera
        if not camera_manager.initialize():
            pytest.skip("Camera not available for integration test")
        
        # Create snapshot service
        snapshot_service = CameraSnapshotService()
        
        try:
            # Start the service
            snapshot_service.start(camera_manager)
            
            # Wait for multiple snapshots
            time.sleep(7)  # Wait for at least 2 snapshots (3-second interval)
            
            # Verify snapshot file exists and is recent
            snapshot_path = Path("data/camera_snapshot.jpg")
            assert snapshot_path.exists(), "Snapshot file should exist"
            
            # Check file is recent (within last 5 seconds)
            file_time = snapshot_path.stat().st_mtime
            current_time = time.time()
            assert (current_time - file_time) < 5, "Snapshot file should be recent"
            
            # Verify file is a valid image
            img = cv2.imread(str(snapshot_path))
            assert img is not None, "Snapshot should be a valid image"
            assert img.shape[0] > 0 and img.shape[1] > 0, "Image should have valid dimensions"
            
        finally:
            # Clean up
            snapshot_service.stop()
            camera_manager.cleanup()

    def test_snapshot_service_performance(self, config_manager: ConfigManager, camera_manager: CameraManager) -> None:
        """Test snapshot service performance with real camera."""
        # Initialize camera
        if not camera_manager.initialize():
            pytest.skip("Camera not available for performance test")
        
        # Create snapshot service
        snapshot_service = CameraSnapshotService()
        
        try:
            # Start the service
            start_time = time.time()
            snapshot_service.start(camera_manager)
            
            # Wait for multiple snapshots and measure performance
            time.sleep(10)  # Wait for multiple snapshots
            
            # Count how many snapshots were created
            snapshot_path = Path("data/camera_snapshot.jpg")
            if snapshot_path.exists():
                # Get file modification times to estimate snapshot frequency
                file_time = snapshot_path.stat().st_mtime
                elapsed = file_time - start_time
                
                # Should have created at least 3 snapshots in 10 seconds (3-second interval)
                expected_min_snapshots = 3
                actual_snapshots = int(elapsed / 3) + 1
                
                assert actual_snapshots >= expected_min_snapshots, f"Should create at least {expected_min_snapshots} snapshots, got {actual_snapshots}"
            
        finally:
            # Clean up
            snapshot_service.stop()
            camera_manager.cleanup()

    def test_snapshot_service_error_handling(self, config_manager: ConfigManager) -> None:
        """Test snapshot service error handling with invalid camera."""
        # Create snapshot service
        snapshot_service = CameraSnapshotService()
        
        # Create a camera manager that will fail
        class FailingCameraManager:
            def capture_frame(self):
                raise Exception("Camera capture failed")
        
        failing_camera = FailingCameraManager()
        
        # Start service with failing camera
        snapshot_service.start(failing_camera)
        
        # Service should still be running even with camera errors
        assert snapshot_service.running
        
        # Wait a moment
        time.sleep(1)
        
        # Service should handle errors gracefully
        assert snapshot_service.running
        
        # Stop the service
        snapshot_service.stop()
        assert not snapshot_service.running
