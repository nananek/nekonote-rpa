"""Tests for nekonote.db (SQLite — no external deps)."""

import pytest

from nekonote import db


class TestSQLiteConnect:
    def test_connect_memory(self):
        conn = db.connect("sqlite")
        assert conn is not None
        conn.close()

    def test_connect_file(self, tmp_path):
        f = str(tmp_path / "test.db")
        conn = db.connect("sqlite", database=f)
        conn.close()
        assert (tmp_path / "test.db").exists()

    def test_invalid_driver(self):
        with pytest.raises(ValueError, match="Unsupported"):
            db.connect("oracle")


class TestQuery:
    def test_create_insert_select(self):
        conn = db.connect("sqlite")
        conn.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, age INTEGER)")
        conn.execute("INSERT INTO users (name, age) VALUES (?, ?)", ["Alice", 30])
        conn.execute("INSERT INTO users (name, age) VALUES (?, ?)", ["Bob", 25])

        rows = conn.query("SELECT * FROM users ORDER BY name")
        assert len(rows) == 2
        assert rows[0]["name"] == "Alice"
        assert rows[0]["age"] == 30
        assert rows[1]["name"] == "Bob"
        conn.close()

    def test_query_empty(self):
        conn = db.connect("sqlite")
        conn.execute("CREATE TABLE empty_table (id INTEGER)")
        rows = conn.query("SELECT * FROM empty_table")
        assert rows == []
        conn.close()

    def test_query_with_params(self):
        conn = db.connect("sqlite")
        conn.execute("CREATE TABLE items (name TEXT, price INTEGER)")
        conn.execute("INSERT INTO items VALUES (?, ?)", ["A", 100])
        conn.execute("INSERT INTO items VALUES (?, ?)", ["B", 200])

        rows = conn.query("SELECT * FROM items WHERE price > ?", [150])
        assert len(rows) == 1
        assert rows[0]["name"] == "B"
        conn.close()


class TestExecuteMany:
    def test_bulk_insert(self):
        conn = db.connect("sqlite")
        conn.execute("CREATE TABLE logs (msg TEXT)")
        conn.execute_many("INSERT INTO logs (msg) VALUES (?)", [["msg1"], ["msg2"], ["msg3"]])
        rows = conn.query("SELECT * FROM logs")
        assert len(rows) == 3
        conn.close()


class TestTransaction:
    def test_commit(self):
        conn = db.connect("sqlite")
        conn.execute("CREATE TABLE t (val INTEGER)")
        with conn.transaction():
            conn._conn.execute("INSERT INTO t VALUES (1)")
            conn._conn.execute("INSERT INTO t VALUES (2)")
        rows = conn.query("SELECT * FROM t")
        assert len(rows) == 2
        conn.close()

    def test_rollback_on_error(self):
        conn = db.connect("sqlite")
        conn.execute("CREATE TABLE t2 (val INTEGER UNIQUE)")
        conn.execute("INSERT INTO t2 VALUES (?)", [1])
        try:
            with conn.transaction():
                conn._conn.execute("INSERT INTO t2 VALUES (2)")
                conn._conn.execute("INSERT INTO t2 VALUES (1)")  # duplicate -> error
        except Exception:
            pass
        rows = conn.query("SELECT * FROM t2")
        assert len(rows) == 1  # rolled back
        conn.close()


class TestContextManager:
    def test_with_statement(self):
        with db.connect("sqlite") as conn:
            conn.execute("CREATE TABLE cm (x INTEGER)")
            conn.execute("INSERT INTO cm VALUES (?)", [42])
            rows = conn.query("SELECT * FROM cm")
            assert rows[0]["x"] == 42
