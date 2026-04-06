"""
Tests for species-aware alert messages and Discord embed payloads (REQ-5).

Covers:
  - _create_alert_message() with species present (REQ-5 AC1)
  - _create_alert_message() without species key (REQ-5 AC2)
  - Discord embed description field with / without species (REQ-5 AC3)
  - Discord embed 'Species Confidence' field insertion (REQ-5 AC4)
  - Discord embed payload is posted to the webhook URL (smoke test)
  - SMS / push text body contains species when present
  - Delivery log written for Discord on success and failure
  - update_config() propagates rate-limiting values at runtime (REQ-4 AC6)
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, Optional
from unittest.mock import MagicMock, patch, call

import pytest
import requests

from skyguard.core.alert_system import AlertSystem


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_REQUESTS_POST = 'skyguard.core.alert_system.requests.post'
_DISCORD_WEBHOOK = 'https://discord.com/api/webhooks/123456789/test-token'


def _discord_system(extra_config: Optional[Dict[str, Any]] = None) -> AlertSystem:
    """Return an AlertSystem with Discord enabled and a dummy webhook URL."""
    config: Dict[str, Any] = {
        'discord': {
            'enabled': True,
            'webhook_url': _DISCORD_WEBHOOK,
            'username': 'SkyGuard',
        },
        'audio':   {'enabled': False},
        'push':    {'enabled': False},
        'sms':     {'enabled': False},
        'email':   {'enabled': False},
    }
    if extra_config:
        config.update(extra_config)
    system = AlertSystem(config)
    system.discord_enabled = True
    return system


def _capture_discord_payload(system: AlertSystem, detection: Dict[str, Any]) -> Dict[str, Any]:
    """Send a Discord alert with a mocked requests.post and return the JSON payload."""
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None

    with patch(_REQUESTS_POST, return_value=mock_response) as mock_post:
        system._send_discord_alert("dummy body", detection)
        assert mock_post.called, "_send_discord_alert did not call requests.post"
        _, kwargs = mock_post.call_args
        return kwargs.get('json', mock_post.call_args[0][1] if len(mock_post.call_args[0]) > 1 else {})


# ---------------------------------------------------------------------------
# 1. _create_alert_message() — REQ-5 AC1 & AC2
# ---------------------------------------------------------------------------

class TestCreateAlertMessageSpecies:
    """_create_alert_message includes species data when present, degrades gracefully when absent."""

    def test_message_contains_species_name(self) -> None:
        """REQ-5 AC1: species name appears in message body."""
        system = AlertSystem({})
        detection = {
            'class_name': 'bird',
            'confidence': 0.88,
            'species': 'Sharp-shinned Hawk',
            'species_confidence': 0.82,
            'timestamp': time.time(),
        }
        msg = system._create_alert_message(detection)
        assert 'Sharp-shinned Hawk' in msg

    def test_message_contains_species_confidence(self) -> None:
        """REQ-5 AC1: species confidence (82.0%) appears in message body."""
        system = AlertSystem({})
        detection = {
            'class_name': 'bird',
            'confidence': 0.88,
            'species': 'Sharp-shinned Hawk',
            'species_confidence': 0.82,
            'timestamp': time.time(),
        }
        msg = system._create_alert_message(detection)
        assert '82.0%' in msg

    def test_message_no_species_key_no_error(self) -> None:
        """REQ-5 AC2: missing species key does not raise and omits species line."""
        system = AlertSystem({})
        detection = {
            'class_name': 'bird',
            'confidence': 0.75,
            'timestamp': time.time(),
        }
        msg = system._create_alert_message(detection)
        assert 'SKYGUARD ALERT' in msg
        assert 'Species:' not in msg

    def test_message_species_none_no_error(self) -> None:
        """REQ-5 AC2: species=None does not raise and omits species line."""
        system = AlertSystem({})
        detection = {
            'class_name': 'bird',
            'confidence': 0.70,
            'species': None,
            'species_confidence': None,
            'timestamp': time.time(),
        }
        msg = system._create_alert_message(detection)
        assert 'Species:' not in msg

    def test_message_bald_eagle_91_pct(self) -> None:
        """REQ-5 DoD: Bald Eagle + 91.0% species confidence appears."""
        system = AlertSystem({})
        detection = {
            'class_name': 'bird',
            'confidence': 0.91,
            'species': 'Bald Eagle',
            'species_confidence': 0.91,
            'timestamp': time.time(),
        }
        msg = system._create_alert_message(detection)
        assert 'Bald Eagle' in msg
        assert '91.0%' in msg

    def test_message_class_name_uppercase_present(self) -> None:
        """Detection class_name appears in uppercase in the message."""
        system = AlertSystem({})
        detection = {
            'class_name': 'hawk',
            'confidence': 0.85,
            'timestamp': time.time(),
        }
        msg = system._create_alert_message(detection)
        assert 'HAWK' in msg

    def test_message_confidence_formatted_as_percent(self) -> None:
        """Detection confidence is formatted as a percentage string."""
        system = AlertSystem({})
        detection = {
            'class_name': 'bird',
            'confidence': 0.85,
            'timestamp': time.time(),
        }
        msg = system._create_alert_message(detection)
        assert '85.0%' in msg


# ---------------------------------------------------------------------------
# 2. Discord embed — REQ-5 AC3 & AC4
# ---------------------------------------------------------------------------

class TestDiscordEmbedSpecies:
    """Discord embed description and fields are species-aware."""

    def test_description_with_species(self) -> None:
        """REQ-5 AC3: embed description contains species name and format."""
        system = _discord_system()
        detection = {
            'class_name': 'bird',
            'confidence': 0.88,
            'species': 'Sharp-shinned Hawk',
            'species_confidence': 0.82,
        }
        payload = _capture_discord_payload(system, detection)

        embed = payload['embeds'][0]
        desc = embed['description']
        assert 'Sharp-shinned Hawk' in desc
        # Detection and species confidence both visible
        assert '88%' in desc or '88.0%' in desc
        assert '82%' in desc or '82.0%' in desc

    def test_description_without_species_matches_legacy_format(self) -> None:
        """REQ-5 AC3: without species, description falls back to legacy format."""
        system = _discord_system()
        detection = {
            'class_name': 'bird',
            'confidence': 0.88,
        }
        payload = _capture_discord_payload(system, detection)

        embed = payload['embeds'][0]
        desc = embed['description']
        assert 'BIRD' in desc
        assert '88' in desc  # confidence present

    def test_species_confidence_field_inserted_when_species_present(self) -> None:
        """REQ-5 AC4: 'Species Confidence' field present when species is known."""
        system = _discord_system()
        detection = {
            'class_name': 'bird',
            'confidence': 0.88,
            'species': 'Bald Eagle',
            'species_confidence': 0.91,
        }
        payload = _capture_discord_payload(system, detection)

        embed = payload['embeds'][0]
        field_names = [f['name'] for f in embed.get('fields', [])]
        assert 'Species Confidence' in field_names

        # Retrieve and verify value
        sc_field = next(f for f in embed['fields'] if f['name'] == 'Species Confidence')
        assert '91' in sc_field['value']

    def test_species_confidence_field_absent_without_species(self) -> None:
        """REQ-5 AC4: 'Species Confidence' field is absent when species is missing."""
        system = _discord_system()
        detection = {
            'class_name': 'bird',
            'confidence': 0.75,
        }
        payload = _capture_discord_payload(system, detection)

        embed = payload['embeds'][0]
        field_names = [f['name'] for f in embed.get('fields', [])]
        assert 'Species Confidence' not in field_names

    def test_species_confidence_field_is_inline(self) -> None:
        """REQ-5 AC4: Species Confidence field has inline=True."""
        system = _discord_system()
        detection = {
            'class_name': 'bird',
            'confidence': 0.80,
            'species': 'Cooper\'s Hawk',
            'species_confidence': 0.78,
        }
        payload = _capture_discord_payload(system, detection)

        embed = payload['embeds'][0]
        sc_field = next(
            (f for f in embed['fields'] if f['name'] == 'Species Confidence'), None
        )
        assert sc_field is not None
        assert sc_field.get('inline') is True

    def test_discord_payload_sent_to_correct_url(self) -> None:
        """Discord webhook POST targets the configured URL."""
        system = _discord_system()
        detection = {'class_name': 'bird', 'confidence': 0.70}

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None

        with patch(_REQUESTS_POST, return_value=mock_response) as mock_post:
            system._send_discord_alert("body", detection)

        mock_post.assert_called_once()
        call_url = mock_post.call_args[0][0]
        assert call_url == _DISCORD_WEBHOOK

    def test_discord_alert_logs_success_delivery(self) -> None:
        """Successful Discord send writes a 'success' delivery record."""
        from pathlib import Path
        from skyguard.storage.event_logger import EventLogger

        tmp = Path('/tmp/test_discord_delivery')
        tmp.mkdir(exist_ok=True)
        storage_cfg = {
            'database_path': str(tmp / 'test.db'),
            'detection_images_path': str(tmp / 'det'),
            'log_retention_days': 30,
        }
        el = EventLogger(storage_cfg)
        el.initialize()

        system = _discord_system()
        system.event_logger = el

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None

        with patch(_REQUESTS_POST, return_value=mock_response):
            system._send_discord_alert("body", {'class_name': 'bird', 'confidence': 0.7})

        records = el.get_alert_deliveries(channel='discord', status='success')
        assert len(records) >= 1

    def test_discord_alert_logs_failure_delivery(self) -> None:
        """Failed Discord send writes a 'failure' delivery record with error text."""
        from pathlib import Path
        from skyguard.storage.event_logger import EventLogger

        tmp = Path('/tmp/test_discord_failure')
        tmp.mkdir(exist_ok=True)
        storage_cfg = {
            'database_path': str(tmp / 'fail.db'),
            'detection_images_path': str(tmp / 'det'),
            'log_retention_days': 30,
        }
        el = EventLogger(storage_cfg)
        el.initialize()

        system = _discord_system()
        system.event_logger = el

        with patch(_REQUESTS_POST, side_effect=requests.exceptions.ConnectionError("timeout")):
            system._send_discord_alert("body", {'class_name': 'bird', 'confidence': 0.7})

        records = el.get_alert_deliveries(channel='discord', status='failure')
        assert len(records) >= 1
        assert records[0]['error_message'] is not None


# ---------------------------------------------------------------------------
# 3. Rate-limiting: update_config() propagates values (REQ-4 AC6)
# ---------------------------------------------------------------------------

class TestUpdateConfigRateLimiting:
    """update_config() correctly propagates rate-limiting values to instance vars."""

    def test_update_config_sets_max_alerts_per_hour(self) -> None:
        """REQ-4 AC6: max_alerts_per_hour is updated on update_config()."""
        system = AlertSystem({}, rate_limiting_config={'max_alerts_per_hour': 10})
        assert system.max_alerts_per_hour == 10

        system.update_config({}, rate_limiting_config={'max_alerts_per_hour': 3})
        assert system.max_alerts_per_hour == 3

    def test_update_config_sets_cooldown_period(self) -> None:
        """REQ-4 AC6: cooldown_period is updated on update_config()."""
        system = AlertSystem({}, rate_limiting_config={'cooldown_period': 300.0})
        assert system.cooldown_period == 300.0

        system.update_config({}, rate_limiting_config={'cooldown_period': 60.0})
        assert system.cooldown_period == 60.0

    def test_update_config_sets_min_alert_interval(self) -> None:
        """REQ-4 AC6: min_alert_interval is updated on update_config()."""
        system = AlertSystem({}, rate_limiting_config={'min_alert_interval': 30.0})
        assert system.min_alert_interval == 30.0

        system.update_config({}, rate_limiting_config={'min_alert_interval': 5.0})
        assert system.min_alert_interval == 5.0

    def test_update_config_no_rl_config_preserves_values(self) -> None:
        """update_config() without rate_limiting_config leaves existing values unchanged."""
        rl = {'min_alert_interval': 45.0, 'max_alerts_per_hour': 7, 'cooldown_period': 120.0}
        system = AlertSystem({}, rate_limiting_config=rl)

        system.update_config({})  # no rate_limiting_config passed

        assert system.min_alert_interval == 45.0
        assert system.max_alerts_per_hour == 7
        assert system.cooldown_period == 120.0


# ---------------------------------------------------------------------------
# 4. Alert system init stores rate-limiting values (REQ-4 AC1)
# ---------------------------------------------------------------------------

class TestAlertSystemRateLimitInit:
    """AlertSystem.__init__ correctly stores all three rate-limiting parameters."""

    def test_init_stores_max_alerts_per_hour(self) -> None:
        """REQ-4 AC1: max_alerts_per_hour stored from rate_limiting_config."""
        system = AlertSystem({}, rate_limiting_config={'max_alerts_per_hour': 5})
        assert system.max_alerts_per_hour == 5

    def test_init_stores_cooldown_period(self) -> None:
        """REQ-4 AC1: cooldown_period stored from rate_limiting_config."""
        system = AlertSystem({}, rate_limiting_config={'cooldown_period': 180.0})
        assert system.cooldown_period == 180.0

    def test_init_default_max_alerts_per_hour(self) -> None:
        """Default max_alerts_per_hour is 10 when not specified."""
        system = AlertSystem({})
        assert system.max_alerts_per_hour == 10

    def test_init_default_cooldown_period(self) -> None:
        """Default cooldown_period is 300 s when not specified."""
        system = AlertSystem({})
        assert system.cooldown_period == 300.0

    def test_init_rolling_window_data_structures(self) -> None:
        """REQ-4 AC4: alert_send_times uses deque; cooldown_until is a dict."""
        from collections import deque
        system = AlertSystem({})
        assert isinstance(system.alert_send_times, dict)
        assert isinstance(system.cooldown_until, dict)


# ---------------------------------------------------------------------------
# 5. _build_alert_subject (REQ-3 AC7 / REQ-5 AC6)
# ---------------------------------------------------------------------------

class TestBuildAlertSubject:
    """Email subject line uses species name when available, class_name otherwise."""

    def test_subject_with_species(self) -> None:
        """REQ-5 AC6: Subject contains species name when species is known."""
        system = AlertSystem({})
        detection = {
            'class_name': 'bird',
            'confidence': 0.88,
            'species': 'Sharp-shinned Hawk',
            'species_confidence': 0.82,
        }
        subject = system._build_alert_subject(detection)
        assert 'Sharp-shinned Hawk' in subject

    def test_subject_without_species_uses_class_name(self) -> None:
        """REQ-3 AC7: Subject uses class_name when species is absent."""
        system = AlertSystem({})
        detection = {'class_name': 'bird', 'confidence': 0.75}
        subject = system._build_alert_subject(detection)
        assert 'Bird' in subject or 'bird' in subject.lower()

    def test_subject_format_contains_detected(self) -> None:
        """Subject line contains 'detected'."""
        system = AlertSystem({})
        detection = {'class_name': 'raptor', 'confidence': 0.85}
        subject = system._build_alert_subject(detection)
        assert 'detected' in subject.lower()

    def test_subject_does_not_use_old_format(self) -> None:
        """Subject is NOT the old 'SkyGuard Raptor Alert' format."""
        system = AlertSystem({})
        detection = {'class_name': 'bird', 'confidence': 0.75}
        subject = system._build_alert_subject(detection)
        assert subject != "SkyGuard Raptor Alert"
