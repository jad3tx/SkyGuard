"""Security helpers for the SkyGuard web portal.

Centralises authentication, session-secret management, CSRF protection and
model-path validation so the Flask app in :mod:`skyguard.web.app` stays
focused on request handling.

Configuration is driven by environment variables so that no secret ever has
to live in the git-tracked ``config/skyguard.yaml``:

- ``SKYGUARD_SECRET_KEY``        Flask session signing key (optional; a
                                 persistent random key is generated if unset).
- ``SKYGUARD_WEB_USERNAME``      Portal login username (default ``admin``).
- ``SKYGUARD_WEB_PASSWORD``      Portal login password (hashed at startup).
- ``SKYGUARD_WEB_PASSWORD_HASH`` Pre-computed werkzeug password hash
                                 (takes precedence over the plaintext var).
"""

from __future__ import annotations

import os
import secrets
import logging
from pathlib import Path
from typing import Optional, Tuple

from werkzeug.security import generate_password_hash, check_password_hash

logger = logging.getLogger(__name__)

# Session key names
SESSION_AUTH = "authenticated"
SESSION_USER = "username"
SESSION_CSRF = "csrf_token"

# HTTP methods that mutate state and therefore require a CSRF token.
_MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def load_or_create_secret_key(data_dir: str = "data") -> str:
    """Return a stable Flask secret key.

    Order of preference:
      1. ``SKYGUARD_SECRET_KEY`` environment variable.
      2. A persisted random key at ``<data_dir>/.flask_secret`` (created with
         ``0600`` permissions on first run).

    Persisting the key means sessions survive a restart (previously the key
    was regenerated on every boot via ``os.urandom``).
    """
    env_key = os.environ.get("SKYGUARD_SECRET_KEY")
    if env_key:
        return env_key

    key_path = Path(data_dir) / ".flask_secret"
    try:
        if key_path.exists():
            existing = key_path.read_text(encoding="utf-8").strip()
            if existing:
                return existing
    except Exception as exc:  # pragma: no cover - best effort
        logger.warning("Could not read persisted secret key: %s", exc)

    key = secrets.token_hex(32)
    try:
        key_path.parent.mkdir(parents=True, exist_ok=True)
        key_path.write_text(key, encoding="utf-8")
        try:
            os.chmod(key_path, 0o600)
        except OSError:
            pass  # e.g. Windows without POSIX perms
    except Exception as exc:  # pragma: no cover - best effort
        logger.warning("Could not persist secret key (%s); using ephemeral key", exc)

    return key


def resolve_credentials() -> Tuple[str, str]:
    """Resolve the portal (username, password_hash).

    If no password is configured a random one-time password is generated and
    logged so the portal is *never* left open without a credential.
    """
    username = os.environ.get("SKYGUARD_WEB_USERNAME", "admin")

    pw_hash = os.environ.get("SKYGUARD_WEB_PASSWORD_HASH")
    if pw_hash:
        return username, pw_hash

    plaintext = os.environ.get("SKYGUARD_WEB_PASSWORD")
    if plaintext:
        return username, generate_password_hash(plaintext)

    # Nothing configured: generate an ephemeral password and surface it once.
    generated = secrets.token_urlsafe(12)
    banner = (
        "\n"
        "============================================================\n"
        " SkyGuard web portal: no SKYGUARD_WEB_PASSWORD configured.\n"
        " A temporary login has been generated for this session:\n"
        f"     username: {username}\n"
        f"     password: {generated}\n"
        " Set SKYGUARD_WEB_PASSWORD (or SKYGUARD_WEB_PASSWORD_HASH) to\n"
        " make this permanent and silence this message.\n"
        "============================================================\n"
    )
    logger.warning(banner)
    try:
        print(banner, flush=True)
    except Exception:
        pass
    return username, generate_password_hash(generated)


def verify_password(stored_hash: str, candidate: str) -> bool:
    """Constant-time-ish password check via werkzeug."""
    try:
        return check_password_hash(stored_hash, candidate)
    except Exception:
        return False


def get_or_create_csrf_token(session) -> str:
    """Return the per-session CSRF token, creating it if needed."""
    token = session.get(SESSION_CSRF)
    if not token:
        token = secrets.token_urlsafe(32)
        session[SESSION_CSRF] = token
    return token


def csrf_token_valid(session, request) -> bool:
    """Validate the CSRF token supplied by a mutating request.

    The token may arrive via the ``X-CSRF-Token`` header (used by the fetch
    calls in the UI) or a ``csrf_token`` form field.
    """
    expected = session.get(SESSION_CSRF)
    if not expected:
        return False
    supplied = request.headers.get("X-CSRF-Token") or request.form.get("csrf_token")
    if not supplied:
        return False
    return secrets.compare_digest(str(expected), str(supplied))


def is_mutating(method: str) -> bool:
    return method.upper() in _MUTATING_METHODS


def is_allowed_model_path(path_str: Optional[str]) -> bool:
    """Return True if a configured model path is safe to load.

    Model weights are deserialized via pickle (``torch.load`` under YOLO), so
    an attacker who can set an arbitrary path could achieve code execution.
    We therefore confine model paths to the project-relative ``models/``
    directory and reject absolute paths, Windows drive/UNC paths and
    ``..`` traversal.
    """
    if not path_str:
        return True  # empty / unset is fine

    norm = str(path_str).replace("\\", "/").strip()
    if not norm:
        return True

    # Absolute POSIX path, Windows drive (C:) or UNC (//host)
    if norm.startswith("/") or norm.startswith("//"):
        return False
    if len(norm) >= 2 and norm[1] == ":":
        return False

    parts = [p for p in norm.split("/") if p not in ("", ".")]
    if ".." in parts:
        return False

    return norm.startswith("models/")
