"""Configuration management for nekonote scripts.

Usage::

    from nekonote import config

    config.set("browser", "chromium")
    browser_type = config.get("browser", "chromium")
    creds = config.get_credential("gmail")
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def _config_dir() -> Path:
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home()))
    else:
        base = Path.home() / ".config"
    d = base / "nekonote"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _load() -> dict[str, Any]:
    path = _config_dir() / "config.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def _save(data: dict[str, Any]) -> None:
    path = _config_dir() / "config.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------


def get(key: str, default: Any = None) -> Any:
    """Get a configuration value."""
    data = _load()
    return data.get("settings", {}).get(key, default)


def set(key: str, value: Any) -> None:
    """Set a configuration value."""
    data = _load()
    data.setdefault("settings", {})[key] = value
    _save(data)


def get_all() -> dict[str, Any]:
    """Get all settings."""
    return _load().get("settings", {})


# ---------------------------------------------------------------------------
# Credentials
# ---------------------------------------------------------------------------


def get_credential(name: str) -> dict[str, str]:
    """Get a stored credential by name."""
    data = _load()
    return data.get("credentials", {}).get(name, {})


def set_credential(name: str, **kwargs: str) -> None:
    """Store a credential."""
    data = _load()
    data.setdefault("credentials", {})[name] = kwargs
    _save(data)


def list_credentials() -> list[str]:
    """List stored credential names."""
    return list(_load().get("credentials", {}).keys())


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------


def env(name: str, default: str = "") -> str:
    """Get an environment variable."""
    return os.environ.get(name, default)
