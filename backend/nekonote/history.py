"""Execution log history for nekonote.

Persists execution logs to SQLite for later review.

Usage::

    from nekonote import history

    runs = history.list_runs(limit=10)
    logs = history.get_run_logs(run_id)
"""

from __future__ import annotations

import json
import os
import sqlite3
import time
from pathlib import Path
from typing import Any


def _db_path() -> str:
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home()))
    else:
        base = Path.home() / ".config"
    d = base / "nekonote" / "logs"
    d.mkdir(parents=True, exist_ok=True)
    return str(d / "history.db")


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_db_path())
    conn.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            id TEXT PRIMARY KEY,
            flow_name TEXT,
            status TEXT,
            started_at REAL,
            finished_at REAL,
            duration_ms REAL,
            error TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT,
            type TEXT,
            node_id TEXT,
            message TEXT,
            level TEXT,
            timestamp REAL,
            data TEXT,
            FOREIGN KEY (run_id) REFERENCES runs(id)
        )
    """)
    conn.commit()
    return conn


def record_event(run_id: str, event: dict[str, Any]) -> None:
    """Record an execution event to the history database."""
    conn = _get_conn()
    etype = event.get("type", "")

    if etype == "execution.started":
        conn.execute(
            "INSERT OR REPLACE INTO runs (id, flow_name, status, started_at) VALUES (?, ?, ?, ?)",
            [run_id, event.get("flow_name", ""), "running", time.time()],
        )
    elif etype in ("execution.completed", "execution.failed"):
        status = event.get("status", etype.split(".")[-1])
        conn.execute(
            "UPDATE runs SET status=?, finished_at=?, duration_ms=?, error=? WHERE id=?",
            [status, time.time(), event.get("duration_ms"), event.get("error"), run_id],
        )

    conn.execute(
        "INSERT INTO events (run_id, type, node_id, message, level, timestamp, data) VALUES (?, ?, ?, ?, ?, ?, ?)",
        [
            run_id,
            etype,
            event.get("node_id", ""),
            event.get("message", ""),
            event.get("level", ""),
            time.time(),
            json.dumps(event, ensure_ascii=False, default=str),
        ],
    )
    conn.commit()
    conn.close()


def list_runs(*, limit: int = 20) -> list[dict[str, Any]]:
    """List recent execution runs."""
    conn = _get_conn()
    cursor = conn.execute(
        "SELECT id, flow_name, status, started_at, finished_at, duration_ms, error "
        "FROM runs ORDER BY started_at DESC LIMIT ?",
        [limit],
    )
    cols = [d[0] for d in cursor.description]
    runs = [dict(zip(cols, row)) for row in cursor.fetchall()]
    conn.close()
    return runs


def get_run_logs(run_id: str) -> list[dict[str, Any]]:
    """Get all events for a specific run."""
    conn = _get_conn()
    cursor = conn.execute(
        "SELECT type, node_id, message, level, timestamp FROM events WHERE run_id=? ORDER BY id",
        [run_id],
    )
    cols = [d[0] for d in cursor.description]
    events = [dict(zip(cols, row)) for row in cursor.fetchall()]
    conn.close()
    return events


def clear(*, older_than_days: int = 0) -> int:
    """Clear history. If older_than_days > 0, only delete old entries."""
    conn = _get_conn()
    if older_than_days > 0:
        cutoff = time.time() - (older_than_days * 86400)
        conn.execute("DELETE FROM events WHERE run_id IN (SELECT id FROM runs WHERE started_at < ?)", [cutoff])
        cursor = conn.execute("DELETE FROM runs WHERE started_at < ?", [cutoff])
    else:
        conn.execute("DELETE FROM events")
        cursor = conn.execute("DELETE FROM runs")
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted
