"""Tests for nekonote.log."""

import json

from nekonote._runtime import configure_output
from nekonote.log import debug, error, info, warning


class TestLog:
    def test_info(self, capsys):
        configure_output(format="json")
        info("hello")
        d = json.loads(capsys.readouterr().out.strip())
        assert d["type"] == "log"
        assert d["level"] == "info"
        assert d["message"] == "hello"
        assert "timestamp" in d

    def test_warning(self, capsys):
        configure_output(format="json")
        warning("careful")
        d = json.loads(capsys.readouterr().out.strip())
        assert d["level"] == "warning"

    def test_error(self, capsys):
        configure_output(format="json")
        error("bad")
        d = json.loads(capsys.readouterr().out.strip())
        assert d["level"] == "error"

    def test_debug(self, capsys):
        configure_output(format="json")
        debug("detail")
        d = json.loads(capsys.readouterr().out.strip())
        assert d["level"] == "debug"

    def test_japanese_message(self, capsys):
        configure_output(format="json")
        info("処理完了しました")
        d = json.loads(capsys.readouterr().out.strip())
        assert d["message"] == "処理完了しました"
