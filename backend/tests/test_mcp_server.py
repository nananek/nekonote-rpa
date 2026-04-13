"""Tests for nekonote.mcp_server."""

from unittest.mock import patch, MagicMock

from nekonote.mcp_server import mcp


class TestMcpTools:
    def test_tools_registered(self):
        tools = mcp._tool_manager.list_tools()
        names = {t.name for t in tools}
        assert "inspect_windows" in names
        assert "inspect_ui_tree" in names
        assert "inspect_browser" in names
        assert "inspect_screenshot" in names
        assert "inspect_processes" in names
        assert "run_script" in names
        assert "check_script" in names
        assert "list_actions" in names

    def test_tool_count(self):
        tools = mcp._tool_manager.list_tools()
        assert len(tools) == 8


class TestRunCli:
    @patch("nekonote.mcp_server.subprocess.run")
    def test_run_cli_success(self, mock_run):
        mock_run.return_value = MagicMock(stdout="output", stderr="", returncode=0)
        from nekonote.mcp_server import _run_cli

        result = _run_cli(["list-actions"])
        assert result == "output"

    @patch("nekonote.mcp_server.subprocess.run")
    def test_run_cli_error(self, mock_run):
        mock_run.return_value = MagicMock(stdout="", stderr="error msg", returncode=1)
        from nekonote.mcp_server import _run_cli

        result = _run_cli(["run", "bad.py"])
        assert "error msg" in result

    @patch("nekonote.mcp_server.subprocess.run")
    def test_run_cli_timeout(self, mock_run):
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired(cmd="x", timeout=120)
        from nekonote.mcp_server import _run_cli

        result = _run_cli(["run", "slow.py"])
        assert "timed out" in result.lower()
