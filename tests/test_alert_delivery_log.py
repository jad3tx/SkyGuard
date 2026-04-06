"""
Tests for the alert delivery audit log.

Covers:
  - Writing success records (REQ-1 AC1)
  - Writing failure records (REQ-1 AC2)
  - GET /api/alerts/history endpoint (REQ-1 AC3)
  - Cleanup retention (REQ-1 AC6)
  - Stats persistence across simulated restart (REQ-1 AC5)
"""

import json
import time
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest

from skyguard.storage.event_logger import EventLogger
from skyguard.core.alert_system import AlertSystem
from skyguard.web.app import SkyGuardWebPortal


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_db(tmp_path: Path) -> dict:
    """Return a storage config pointing at a temporary directory."""
    return {
        'database_path': str(tmp_path / 'test.db'),
        'detection_images_path': str(tmp_path / 'detections'),
        'log_retention_days': 30,
    }


@pytest.fixture
def logger(tmp_db: dict) -> EventLogger:
    """Return an initialised EventLogger backed by a temp database."""
    el = EventLogger(tmp_db)
    assert el.initialize() is True
    return el


@pytest.fixture
def alert_system(logger: EventLogger) -> AlertSystem:
    """Return a minimal AlertSystem wired to the temp EventLogger."""
    config: dict = {
        'audio':   {'enabled': False},
        'push':    {'enabled': False},
        'sms':     {'enabled': False},
        'email':   {'enabled': False},
        'discord': {'enabled': False},
    }
    return AlertSystem(config, event_logger=logger)


# ---------------------------------------------------------------------------
# 1. Success record is written
# ---------------------------------------------------------------------------


class TestLogAlertDeliverySuccess:
    """A success delivery is persisted with status='success'."""

    def test_success_record_saved(self, logger: EventLogger) -> None:
        result = logger.log_alert_delivery(
            channel='discord',
            status='success',
            detection_id=42,
        )
        assert result is True

        records = logger.get_alert_deliveries(limit=10)
        assert len(records) == 1
        rec = records[0]
        assert rec['channel'] == 'discord'
        assert rec['status'] == 'success'
        assert rec['detection_id'] == 42
        assert rec['error_message'] is None

    def test_record_has_recent_timestamp(self, logger: EventLogger) -> None:
        before = time.time()
        logger.log_alert_delivery(channel='sms', status='success')
        after = time.time()

        rec = logger.get_alert_deliveries(limit=1)[0]
        assert before <= rec['timestamp'] <= after

    def test_multiple_channels_logged(self, logger: EventLogger) -> None:
        for ch in ('audio', 'push', 'sms', 'email', 'discord'):
            logger.log_alert_delivery(channel=ch, status='success')

        records = logger.get_alert_deliveries(limit=10)
        channels_logged = {r['channel'] for r in records}
        assert channels_logged == {'audio', 'push', 'sms', 'email', 'discord'}


# ---------------------------------------------------------------------------
# 2. Failure record is written with error_message
# ---------------------------------------------------------------------------


class TestLogAlertDeliveryFailure:
    """A failure delivery is persisted with status='failure' and error info."""

    def test_failure_record_saved(self, logger: EventLogger) -> None:
        error = "Twilio API returned 401 Unauthorized"
        result = logger.log_alert_delivery(
            channel='sms',
            status='failure',
            detection_id=7,
            error_message=error,
        )
        assert result is True

        records = logger.get_alert_deliveries(limit=10, status='failure')
        assert len(records) == 1
        rec = records[0]
        assert rec['status'] == 'failure'
        assert rec['error_message'] == error
        assert rec['detection_id'] == 7

    def test_error_message_truncated_to_500_chars(self, logger: EventLogger) -> None:
        long_error = "X" * 1000
        logger.log_alert_delivery(channel='email', status='failure',
                                  error_message=long_error)
        rec = logger.get_alert_deliveries(limit=1)[0]
        assert len(rec['error_message']) == 500

    def test_channel_filter_isolates_failures(self, logger: EventLogger) -> None:
        logger.log_alert_delivery(channel='sms',     status='failure', error_message="err")
        logger.log_alert_delivery(channel='discord', status='success')

        sms_failures = logger.get_alert_deliveries(channel='sms', status='failure')
        assert len(sms_failures) == 1
        assert sms_failures[0]['channel'] == 'sms'

        discord_ok = logger.get_alert_deliveries(channel='discord', status='success')
        assert len(discord_ok) == 1


# ---------------------------------------------------------------------------
# 3. GET /api/alerts/history endpoint
# ---------------------------------------------------------------------------


class TestAlertsHistoryEndpoint:
    """The /api/alerts/history endpoint returns the correct JSON structure."""

    @pytest.fixture
    def portal(self) -> SkyGuardWebPortal:
        return SkyGuardWebPortal("test_config.yaml")

    def test_history_returns_json_array(
        self, portal: SkyGuardWebPortal, mocker: "MockerFixture"
    ) -> None:
        sample = [
            {
                'id': 1,
                'timestamp': 1700000000.0,
                'channel': 'discord',
                'status': 'success',
                'detection_id': 10,
                'error_message': None,
                'metadata': {},
                'image_path': None,
            }
        ]
        mocker.patch.object(portal.event_logger, 'get_alert_deliveries',
                            return_value=sample)

        with portal.app.test_client() as client:
            response = client.get('/api/alerts/history?limit=10')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]['channel'] == 'discord'
        assert data[0]['status'] == 'success'

    def test_history_passes_filters_to_event_logger(
        self, portal: SkyGuardWebPortal, mocker: "MockerFixture"
    ) -> None:
        mock_get = mocker.patch.object(
            portal.event_logger, 'get_alert_deliveries', return_value=[]
        )

        with portal.app.test_client() as client:
            client.get('/api/alerts/history?limit=25&offset=5&channel=sms&status=failure')

        mock_get.assert_called_once_with(
            limit=25, offset=5, channel='sms', status='failure'
        )

    def test_history_returns_required_fields(
        self, portal: SkyGuardWebPortal, mocker: "MockerFixture"
    ) -> None:
        record = {
            'id': 99,
            'timestamp': time.time(),
            'channel': 'email',
            'status': 'failure',
            'detection_id': None,
            'error_message': 'SMTP timeout',
            'metadata': {},
            'image_path': '/data/detections/img.jpg',
        }
        mocker.patch.object(portal.event_logger, 'get_alert_deliveries',
                            return_value=[record])

        with portal.app.test_client() as client:
            response = client.get('/api/alerts/history')
        data = json.loads(response.data)
        required_keys = {'id', 'timestamp', 'channel', 'status',
                         'detection_id', 'error_message'}
        assert required_keys.issubset(set(data[0].keys()))


# ---------------------------------------------------------------------------
# 4. Cleanup respects retention policy
# ---------------------------------------------------------------------------


class TestAlertDeliveryCleanup:
    """cleanup_old_data() removes alert_deliveries older than retention days."""

    def test_old_deliveries_deleted(self, logger: EventLogger) -> None:
        # Insert an old record (2 days ago)
        old_ts = time.time() - (2 * 24 * 60 * 60)
        logger.connection.cursor().execute(
            'INSERT INTO alert_deliveries (timestamp, channel, status) VALUES (?, ?, ?)',
            (old_ts, 'discord', 'success'),
        )
        logger.connection.commit()

        # Insert a recent record
        logger.log_alert_delivery(channel='email', status='success')

        # Override retention to 1 day
        logger.retention_days = 1
        logger.image_retention_days = 1
        logger.cleanup_old_data()

        remaining = logger.get_alert_deliveries(limit=100)
        # Only the recent record survives
        assert len(remaining) == 1
        assert remaining[0]['channel'] == 'email'

    def test_cleanup_returns_true_on_success(self, logger: EventLogger) -> None:
        assert logger.cleanup_old_data() is True


# ---------------------------------------------------------------------------
# 5. Stats survive a simulated restart (DB-backed)
# ---------------------------------------------------------------------------


class TestAlertStatsDbBacked:
    """AlertSystem.get_alert_stats() uses DB values when event_logger is set."""

    def test_total_alerts_from_db(
        self, tmp_db: dict, logger: EventLogger
    ) -> None:
        # Write 3 success records directly
        for _ in range(3):
            logger.log_alert_delivery(channel='discord', status='success')

        # "Restart" the AlertSystem with a fresh in-memory counter (count=0)
        config = {k: {'enabled': False} for k in ('audio', 'push', 'sms', 'email', 'discord')}
        system = AlertSystem(config, event_logger=logger)
        # alert_count starts at 0 in memory

        stats = system.get_alert_stats()
        assert stats['total_alerts'] == 3

    def test_failed_alerts_from_db(
        self, logger: EventLogger
    ) -> None:
        logger.log_alert_delivery(channel='sms', status='success')
        logger.log_alert_delivery(channel='email', status='failure',
                                  error_message="conn refused")
        logger.log_alert_delivery(channel='discord', status='failure',
                                  error_message="403 Forbidden")

        config = {k: {'enabled': False} for k in ('audio', 'push', 'sms', 'email', 'discord')}
        system = AlertSystem(config, event_logger=logger)
        stats = system.get_alert_stats()

        assert stats['failed_alerts'] == 2
        assert stats['total_alerts'] == 3
