"""Database connection and SQL query execution for nekonote scripts.

Usage::

    from nekonote import db

    conn = db.connect(driver="sqlite", database="app.db")
    rows = conn.query("SELECT * FROM users WHERE active = ?", [True])
    conn.execute("INSERT INTO logs (msg) VALUES (?)", ["hello"])
    conn.close()
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Any


class Connection:
    """Database connection wrapper."""

    def __init__(self, raw_conn: Any, driver: str):
        self._conn = raw_conn
        self._driver = driver

    def query(self, sql: str, params: list[Any] | None = None) -> list[dict[str, Any]]:
        """Execute a SELECT query and return rows as list of dicts."""
        cursor = self._conn.cursor()
        cursor.execute(sql, params or [])
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = cursor.fetchall()
        return [dict(zip(columns, row)) for row in rows]

    def execute(self, sql: str, params: list[Any] | None = None) -> int:
        """Execute an INSERT/UPDATE/DELETE and return affected row count."""
        cursor = self._conn.cursor()
        cursor.execute(sql, params or [])
        self._conn.commit()
        return cursor.rowcount

    def execute_many(self, sql: str, params_list: list[list[Any]]) -> int:
        """Execute a statement for each set of params."""
        cursor = self._conn.cursor()
        cursor.executemany(sql, params_list)
        self._conn.commit()
        return cursor.rowcount

    @contextmanager
    def transaction(self):
        """Context manager for transactions. Commits on success, rolls back on error."""
        try:
            yield self
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise

    def close(self) -> None:
        """Close the connection."""
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def connect(
    driver: str = "sqlite",
    *,
    database: str = "",
    host: str = "localhost",
    port: int = 0,
    username: str = "",
    password: str = "",
) -> Connection:
    """Open a database connection.

    Supported drivers:
    - ``"sqlite"`` — stdlib sqlite3, no extra dependency
    - ``"postgresql"`` — requires ``psycopg2``
    - ``"mysql"`` — requires ``pymysql``
    """
    if driver == "sqlite":
        raw = sqlite3.connect(database or ":memory:")
        raw.row_factory = None  # we handle row→dict ourselves
        return Connection(raw, driver)

    if driver == "postgresql":
        import psycopg2

        raw = psycopg2.connect(
            host=host, port=port or 5432,
            dbname=database, user=username, password=password,
        )
        return Connection(raw, driver)

    if driver == "mysql":
        import pymysql

        raw = pymysql.connect(
            host=host, port=port or 3306,
            database=database, user=username, password=password,
        )
        return Connection(raw, driver)

    raise ValueError(f"Unsupported driver: {driver!r}. Use 'sqlite', 'postgresql', or 'mysql'.")
