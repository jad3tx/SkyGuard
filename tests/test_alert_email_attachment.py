"""
Tests for email alert image attachment (REQ-3).

Covers:
  - Attachment present when valid image path provided (AC1)
  - No attachment when image path is missing/None/empty (AC2)
  - No attachment when file exceeds size cap (AC5)
  - Subject line format with and without species (REQ-3 AC7 / REQ-5 AC6)
"""

import email
import smtplib
import tempfile
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Optional
from unittest.mock import MagicMock, patch, call

import pytest

from skyguard.core.alert_system import AlertSystem


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SMTP_PATH = 'skyguard.core.alert_system.smtplib.SMTP'


def _make_alert_system(tmp_detections: Path, max_mb: float = 5.0) -> AlertSystem:
    """Create an AlertSystem configured for email with a temp detections dir."""
    config = {
        'email': {
            'enabled': True,
            'smtp_server': 'smtp.example.com',
            'smtp_port': 587,
            'username': 'user@example.com',
            'password': 'secret',
            'from_email': 'skyguard@example.com',
            'to_emails': ['farmer@example.com'],
        },
        'storage': {
            'detection_images_path': str(tmp_detections),
            'max_image_size_mb': max_mb,
        },
    }
    system = AlertSystem(config)
    system.email_enabled = True
    return system


def _sent_message(mock_smtp: MagicMock) -> MIMEMultipart:
    """Extract the MIMEMultipart message passed to server.send_message()."""
    return mock_smtp.return_value.__enter__.return_value.send_message.call_args[0][0]


# ---------------------------------------------------------------------------
# 1. Attachment is present when valid image path is given
# ---------------------------------------------------------------------------


class TestEmailAttachmentPresent:
    """When detection['image_path'] points to an existing JPEG, the email
    contains a MIMEImage part."""

    def test_attachment_included(self, tmp_path: Path) -> None:
        detections_dir = tmp_path / 'detections'
        detections_dir.mkdir()
        img_file = detections_dir / 'test_detection.jpg'
        img_file.write_bytes(b'\xff\xd8\xff' + b'\x00' * 1024)  # fake JPEG bytes

        system = _make_alert_system(detections_dir)
        detection = {
            'class_name': 'bird',
            'confidence': 0.88,
            'timestamp': 1700000000.0,
            'image_path': str(img_file),
        }

        with patch(_SMTP_PATH) as mock_smtp_cls:
            mock_server = MagicMock()
            mock_smtp_cls.return_value = mock_server
            system._send_email_alert("Test body", detection)

        # Check that send_message was called
        assert mock_server.send_message.called
        msg: MIMEMultipart = mock_server.send_message.call_args[0][0]

        # Find the image attachment part
        image_parts = [
            p for p in msg.walk()
            if p.get_content_type() == 'image/jpeg'
        ]
        assert len(image_parts) == 1

        img_part = image_parts[0]
        assert img_part.get('Content-ID') == '<detection_image>'
        assert 'inline' in img_part.get('Content-Disposition', '')
        assert 'detection.jpg' in img_part.get('Content-Disposition', '')

    def test_attachment_content_matches_file(self, tmp_path: Path) -> None:
        detections_dir = tmp_path / 'detections'
        detections_dir.mkdir()
        img_file = detections_dir / 'bird.jpg'
        img_bytes = b'\xff\xd8\xff' + b'\xAB' * 512
        img_file.write_bytes(img_bytes)

        system = _make_alert_system(detections_dir)
        detection = {
            'class_name': 'bird',
            'confidence': 0.75,
            'timestamp': 1700000000.0,
            'image_path': str(img_file),
        }

        with patch(_SMTP_PATH) as mock_smtp_cls:
            mock_server = MagicMock()
            mock_smtp_cls.return_value = mock_server
            system._send_email_alert("body", detection)

        msg = mock_server.send_message.call_args[0][0]
        image_parts = [p for p in msg.walk() if p.get_content_type() == 'image/jpeg']
        assert image_parts[0].get_payload(decode=True) == img_bytes


# ---------------------------------------------------------------------------
# 2. No attachment when image path is missing / None / empty
# ---------------------------------------------------------------------------


class TestEmailNoAttachmentMissingPath:
    """Email sends successfully as plain text when no image is available."""

    @pytest.mark.parametrize("image_path_value", [None, '', '/nonexistent/path.jpg'])
    def test_no_attachment_and_no_exception(
        self, tmp_path: Path, image_path_value: Optional[str]
    ) -> None:
        detections_dir = tmp_path / 'detections'
        detections_dir.mkdir()
        system = _make_alert_system(detections_dir)

        detection = {
            'class_name': 'bird',
            'confidence': 0.70,
            'timestamp': 1700000000.0,
            'image_path': image_path_value,
        }

        with patch(_SMTP_PATH) as mock_smtp_cls:
            mock_server = MagicMock()
            mock_smtp_cls.return_value = mock_server
            # Must not raise
            system._send_email_alert("body", detection)

        assert mock_server.send_message.called
        msg = mock_server.send_message.call_args[0][0]
        image_parts = [p for p in msg.walk() if p.get_content_type() == 'image/jpeg']
        assert len(image_parts) == 0


# ---------------------------------------------------------------------------
# 3. No attachment when file exceeds size cap
# ---------------------------------------------------------------------------


class TestEmailNoAttachmentFileTooBig:
    """When the detection image exceeds max_image_size_mb, email is plain-text."""

    def test_oversized_image_not_attached(self, tmp_path: Path) -> None:
        detections_dir = tmp_path / 'detections'
        detections_dir.mkdir()
        big_img = detections_dir / 'big.jpg'
        # Write a 2 MB file but configure cap at 1 MB
        big_img.write_bytes(b'\xff\xd8\xff' + b'\x00' * (2 * 1024 * 1024))

        system = _make_alert_system(detections_dir, max_mb=1.0)
        detection = {
            'class_name': 'bird',
            'confidence': 0.80,
            'timestamp': 1700000000.0,
            'image_path': str(big_img),
        }

        with patch(_SMTP_PATH) as mock_smtp_cls:
            mock_server = MagicMock()
            mock_smtp_cls.return_value = mock_server
            system._send_email_alert("body", detection)

        assert mock_server.send_message.called
        msg = mock_server.send_message.call_args[0][0]
        image_parts = [p for p in msg.walk() if p.get_content_type() == 'image/jpeg']
        assert len(image_parts) == 0


# ---------------------------------------------------------------------------
# 4. Subject line format
# ---------------------------------------------------------------------------


class TestEmailSubjectLine:
    """Subject line uses species name when available, class_name otherwise."""

    def test_subject_with_species(self, tmp_path: Path) -> None:
        detections_dir = tmp_path / 'detections'
        detections_dir.mkdir()
        system = _make_alert_system(detections_dir)
        detection = {
            'class_name': 'bird',
            'confidence': 0.88,
            'species': 'Sharp-shinned Hawk',
            'species_confidence': 0.82,
            'timestamp': 1700000000.0,
            'image_path': None,
        }

        with patch(_SMTP_PATH) as mock_smtp_cls:
            mock_server = MagicMock()
            mock_smtp_cls.return_value = mock_server
            system._send_email_alert("body", detection)

        msg = mock_server.send_message.call_args[0][0]
        assert 'Sharp-shinned Hawk' in msg['Subject']

    def test_subject_without_species(self, tmp_path: Path) -> None:
        detections_dir = tmp_path / 'detections'
        detections_dir.mkdir()
        system = _make_alert_system(detections_dir)
        detection = {
            'class_name': 'bird',
            'confidence': 0.75,
            'timestamp': 1700000000.0,
            'image_path': None,
        }

        with patch(_SMTP_PATH) as mock_smtp_cls:
            mock_server = MagicMock()
            mock_smtp_cls.return_value = mock_server
            system._send_email_alert("body", detection)

        msg = mock_server.send_message.call_args[0][0]
        subject = msg['Subject']
        assert 'bird' in subject.lower() or 'raptor' in subject.lower()
        # Should not contain "Raptor Alert" (old format)
        assert subject != "SkyGuard Raptor Alert"

    def test_subject_with_bald_eagle(self, tmp_path: Path) -> None:
        detections_dir = tmp_path / 'detections'
        detections_dir.mkdir()
        system = _make_alert_system(detections_dir)
        detection = {
            'class_name': 'bird',
            'confidence': 0.91,
            'species': 'Bald Eagle',
            'species_confidence': 0.91,
            'timestamp': 1700000000.0,
            'image_path': None,
        }

        with patch(_SMTP_PATH) as mock_smtp_cls:
            mock_server = MagicMock()
            mock_smtp_cls.return_value = mock_server
            system._send_email_alert("body", detection)

        msg = mock_server.send_message.call_args[0][0]
        assert 'Bald Eagle' in msg['Subject']


# ---------------------------------------------------------------------------
# 5. Path-traversal guard
# ---------------------------------------------------------------------------


class TestEmailPathTraversalGuard:
    """Images outside the detections directory are not attached."""

    def test_path_outside_detections_rejected(self, tmp_path: Path) -> None:
        detections_dir = tmp_path / 'detections'
        detections_dir.mkdir()

        # Create a "sensitive" file outside the detections directory
        outside_file = tmp_path / 'secret.jpg'
        outside_file.write_bytes(b'\xff\xd8\xff' + b'\x00' * 512)

        system = _make_alert_system(detections_dir)
        detection = {
            'class_name': 'bird',
            'confidence': 0.80,
            'timestamp': 1700000000.0,
            'image_path': str(outside_file),
        }

        with patch(_SMTP_PATH) as mock_smtp_cls:
            mock_server = MagicMock()
            mock_smtp_cls.return_value = mock_server
            system._send_email_alert("body", detection)

        # Email must still be sent (plain text), just without the attachment
        assert mock_server.send_message.called
        msg = mock_server.send_message.call_args[0][0]
        image_parts = [p for p in msg.walk() if p.get_content_type() == 'image/jpeg']
        assert len(image_parts) == 0
