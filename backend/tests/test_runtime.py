"""Tests for nekonote._runtime."""

import asyncio
import json

from nekonote._runtime import (
    _ensure_loop,
    configure_output,
    emit_event,
    register_cleanup,
    run_async,
)


class TestEventLoop:
    def test_ensure_loop_creates_running_loop(self):
        loop = _ensure_loop()
        assert loop is not None
        assert loop.is_running()

    def test_ensure_loop_idempotent(self):
        loop1 = _ensure_loop()
        loop2 = _ensure_loop()
        assert loop1 is loop2

    def test_run_async_simple_coroutine(self):
        async def add(a, b):
            return a + b

        result = run_async(add(2, 3))
        assert result == 5

    def test_run_async_with_await(self):
        async def delayed():
            await asyncio.sleep(0.01)
            return "done"

        assert run_async(delayed()) == "done"

    def test_run_async_propagates_exception(self):
        async def fail():
            raise ValueError("boom")

        try:
            run_async(fail())
            assert False, "Should have raised"
        except ValueError as e:
            assert "boom" in str(e)


class TestEmitEvent:
    def test_json_format(self, capsys):
        configure_output(format="json", verbose=False)
        emit_event({"type": "log", "message": "hello"})
        out = capsys.readouterr().out.strip()
        d = json.loads(out)
        assert d["type"] == "log"
        assert d["message"] == "hello"

    def test_human_verbose_log(self, capsys):
        configure_output(format="human", verbose=True)
        emit_event({"type": "log", "level": "info", "message": "test msg"})
        out = capsys.readouterr().out.strip()
        assert "INFO" in out
        assert "test msg" in out

    def test_human_not_verbose_silent(self, capsys):
        configure_output(format="human", verbose=False)
        emit_event({"type": "log", "level": "info", "message": "hidden"})
        out = capsys.readouterr().out.strip()
        assert out == ""

    def test_json_ensure_ascii_false(self, capsys):
        configure_output(format="json")
        emit_event({"type": "log", "message": "日本語テスト"})
        out = capsys.readouterr().out.strip()
        assert "日本語テスト" in out


class TestCleanup:
    def test_register_cleanup(self):
        from nekonote._runtime import _cleanup_callbacks

        called = []
        register_cleanup(lambda: called.append(True))
        # Just verify registration works; actual cleanup happens at shutdown
        assert len(_cleanup_callbacks) > 0
