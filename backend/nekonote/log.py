"""Logging API for nekonote scripts.

Usage::

    from nekonote import log

    log.info("Processing started")
    log.warning("Value is empty")
    log.error("Connection failed")
"""

from __future__ import annotations

import time

from nekonote._runtime import emit_event


def _log(level: str, message: str) -> None:
    emit_event({
        "type": "log",
        "level": level,
        "message": message,
        "timestamp": time.time(),
    })


def info(message: str) -> None:
    _log("info", message)


def warning(message: str) -> None:
    _log("warning", message)


def error(message: str) -> None:
    _log("error", message)


def debug(message: str) -> None:
    _log("debug", message)
