"""Tests for nekonote.cli."""

import json
import textwrap
from pathlib import Path

from nekonote.cli import main


class TestCliRun:
    def test_run_simple_script(self, tmp_path, capsys):
        script = tmp_path / "ok.py"
        script.write_text("from nekonote import log\nlog.info('hi')\n", encoding="utf-8")

        rc = main(["run", str(script), "--format", "json"])
        assert rc == 0

        lines = capsys.readouterr().out.strip().split("\n")
        events = [json.loads(l) for l in lines]
        types = [e["type"] for e in events]
        assert "start" in types
        assert "end" in types
        assert any(e.get("message") == "hi" for e in events)

    def test_run_script_error(self, tmp_path, capsys):
        script = tmp_path / "fail.py"
        script.write_text("raise RuntimeError('boom')\n", encoding="utf-8")

        rc = main(["run", str(script), "--format", "json"])
        assert rc == 1

        lines = capsys.readouterr().out.strip().split("\n")
        events = [json.loads(l) for l in lines]
        assert any(e.get("type") == "error" for e in events)
        end = [e for e in events if e["type"] == "end"][0]
        assert end["status"] == "failed"

    def test_run_nekonote_error(self, tmp_path, capsys):
        script = tmp_path / "ne.py"
        script.write_text(
            "from nekonote.errors import ElementNotFoundError\n"
            "raise ElementNotFoundError('no el', action='browser.click', suggestion='try #btn')\n",
            encoding="utf-8",
        )

        rc = main(["run", str(script), "--format", "json"])
        assert rc == 1

        lines = capsys.readouterr().out.strip().split("\n")
        events = [json.loads(l) for l in lines]
        err = [e for e in events if e.get("type") == "error"][0]
        assert err["code"] == "ELEMENT_NOT_FOUND"
        assert err["suggestion"] == "try #btn"

    def test_run_missing_script(self, capsys):
        rc = main(["run", "/nonexistent/script.py", "--format", "json"])
        assert rc == 2

    def test_run_with_variables(self, tmp_path, capsys):
        script = tmp_path / "vars.py"
        script.write_text(
            "from nekonote import log\nlog.info(f'name={variables[\"name\"]}')\n",
            encoding="utf-8",
        )

        rc = main(["run", str(script), "--var", "name=Taro", "--format", "json"])
        assert rc == 0

        lines = capsys.readouterr().out.strip().split("\n")
        events = [json.loads(l) for l in lines]
        assert any("name=Taro" in e.get("message", "") for e in events)

    def test_run_dry_run(self, tmp_path, capsys):
        script = tmp_path / "dry.py"
        script.write_text("print('should not run')\n", encoding="utf-8")

        rc = main(["run", str(script), "--dry-run"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "valid" in out.lower()


class TestCliCheck:
    def test_check_valid(self, tmp_path, capsys):
        script = tmp_path / "valid.py"
        script.write_text("x = 1\n", encoding="utf-8")

        rc = main(["check", str(script)])
        assert rc == 0

    def test_check_syntax_error(self, tmp_path, capsys):
        script = tmp_path / "bad.py"
        script.write_text("def f(\n", encoding="utf-8")

        rc = main(["check", str(script)])
        assert rc == 3

    def test_check_missing_file(self, capsys):
        rc = main(["check", "/nonexistent.py"])
        assert rc == 2


class TestCliListActions:
    def test_list_actions_json(self, capsys):
        rc = main(["list-actions"])
        assert rc == 0
        data = json.loads(capsys.readouterr().out)
        assert isinstance(data, list)
        assert len(data) > 0
        # Check known function exists
        sigs = [a["signature"] for a in data]
        assert any("browser.open" in s for s in sigs)
        assert any("log.info" in s for s in sigs)


class TestCliHelp:
    def test_no_args_shows_help(self, capsys):
        rc = main([])
        assert rc == 0
