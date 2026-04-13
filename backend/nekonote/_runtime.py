"""Core runtime for nekonote scripting API.

Manages a background asyncio event loop so that user scripts can call
async operations (Playwright, etc.) via synchronous function calls.
"""

from __future__ import annotations

import asyncio
import atexit
import json
import sys
import threading
import time
import traceback
from typing import Any, TypeVar

T = TypeVar("T")

# ---------------------------------------------------------------------------
# Background event loop
# ---------------------------------------------------------------------------

_loop: asyncio.AbstractEventLoop | None = None
_thread: threading.Thread | None = None
_lock = threading.Lock()


def _ensure_loop() -> asyncio.AbstractEventLoop:
    global _loop, _thread
    if _loop is not None and _loop.is_running():
        return _loop
    with _lock:
        if _loop is not None and _loop.is_running():
            return _loop
        _loop = asyncio.new_event_loop()
        _thread = threading.Thread(target=_loop.run_forever, daemon=True, name="nekonote-loop")
        _thread.start()
        atexit.register(_shutdown)
    return _loop


def run_async(coro) -> Any:
    """Submit *coro* to the background loop and block until it completes."""
    loop = _ensure_loop()
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    return future.result()


def _shutdown() -> None:
    """Cleanup: close browsers, stop loop."""
    global _loop, _thread
    if _loop is None:
        return

    # Run cleanup callbacks
    for cb in list(_cleanup_callbacks):
        try:
            if asyncio.iscoroutinefunction(cb):
                asyncio.run_coroutine_threadsafe(cb(), _loop).result(timeout=5)
            else:
                cb()
        except Exception:
            pass

    _loop.call_soon_threadsafe(_loop.stop)
    if _thread is not None:
        _thread.join(timeout=5)
    _loop = None
    _thread = None


_cleanup_callbacks: list[Any] = []


def register_cleanup(cb) -> None:
    _cleanup_callbacks.append(cb)


# ---------------------------------------------------------------------------
# JSON Lines emitter (for CLI output)
# ---------------------------------------------------------------------------

_output_format: str = "human"  # "json" or "human"
_verbose: bool = False
_start_time: float = 0.0


def configure_output(*, format: str = "human", verbose: bool = False) -> None:
    global _output_format, _verbose, _start_time
    _output_format = format
    _verbose = verbose
    _start_time = time.time()


def emit_event(event: dict[str, Any]) -> None:
    """Write a structured event to stdout (JSON mode) or formatted (human mode)."""
    if _output_format == "json":
        print(json.dumps(event, ensure_ascii=False, default=str), flush=True)
    elif _verbose:
        _print_human(event)


def _print_human(event: dict[str, Any]) -> None:
    etype = event.get("type", "")
    if etype == "step":
        status = event.get("status", "")
        action = event.get("action", "")
        line = event.get("line", "?")
        dur = event.get("duration_ms", 0)
        mark = "OK" if status == "ok" else "ERR"
        print(f"  [{mark}] L{line} {action} ({dur:.0f}ms)", flush=True)
    elif etype == "log":
        level = event.get("level", "info").upper()
        msg = event.get("message", "")
        print(f"  [{level}] {msg}", flush=True)
    elif etype == "error":
        msg = event.get("message", "")
        suggestion = event.get("suggestion", "")
        print(f"  [ERROR] {msg}", file=sys.stderr, flush=True)
        if suggestion:
            print(f"  [HINT]  {suggestion}", file=sys.stderr, flush=True)
    elif etype == "start":
        script = event.get("script", "")
        print(f"nekonote: running {script}", flush=True)
    elif etype == "end":
        status = event.get("status", "")
        dur = event.get("total_duration_ms", 0)
        print(f"nekonote: {status} ({dur:.0f}ms)", flush=True)
