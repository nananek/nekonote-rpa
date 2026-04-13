"""nekonote MCP server — exposes RPA capabilities as Claude Code tools.

Run with:
    python -m nekonote.mcp_server
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("nekonote")


# ---------------------------------------------------------------------------
# Inspect tools
# ---------------------------------------------------------------------------


@mcp.tool()
def inspect_windows(filter: str = "") -> str:
    """List all visible windows on the desktop.

    Returns JSON array of windows with title, handle, class_name, pid, rect.
    Use the 'filter' parameter to search by title substring.
    """
    args = ["inspect", "windows"]
    if filter:
        args += ["--filter", filter]
    return _run_cli(args)


@mcp.tool()
def inspect_ui_tree(title: str, depth: int = 4, xpath: str = "") -> str:
    """Dump the UI element tree for a window as XML.

    Use XPath expressions to search for specific elements within the window.
    Example xpath: './/ButtonControl[@name="OK"]'
    """
    args = ["inspect", "ui-tree", title, "--depth", str(depth)]
    if xpath:
        args += ["--xpath", xpath]
    return _run_cli(args)


@mcp.tool()
def inspect_browser() -> str:
    """Get information about the current browser page.

    Returns JSON with url, title, clickable elements, input fields, and tables.
    Requires a browser to be open (via a running script).
    """
    return _run_cli(["inspect", "browser"])


@mcp.tool()
def inspect_screenshot(output: str = "screenshot.png", region: str = "") -> str:
    """Take a screenshot of the desktop.

    Args:
        output: File path to save the screenshot.
        region: Optional region as 'X,Y,W,H'.
    """
    args = ["inspect", "screenshot", "--output", output]
    if region:
        args += ["--region", region]
    return _run_cli(args)


@mcp.tool()
def inspect_processes(filter: str = "") -> str:
    """List running processes. Optionally filter by name."""
    result = _run_cli(["inspect", "processes"])
    if filter:
        try:
            data = json.loads(result)
            filtered = [p for p in data if filter.lower() in str(p).lower()]
            return json.dumps(filtered, ensure_ascii=False, indent=2)
        except Exception:
            pass
    return result


# ---------------------------------------------------------------------------
# Execution tools
# ---------------------------------------------------------------------------


@mcp.tool()
def run_script(script_path: str, variables: dict[str, str] | None = None) -> str:
    """Execute a nekonote Python RPA script.

    Returns structured JSON output with execution events, including
    any errors with line numbers and fix suggestions.

    Args:
        script_path: Path to the .py script file.
        variables: Optional dict of variables to pass to the script.
    """
    args = ["run", script_path, "--format", "json"]
    if variables:
        for k, v in variables.items():
            args += ["--var", f"{k}={v}"]
    return _run_cli(args)


@mcp.tool()
def check_script(script_path: str) -> str:
    """Validate a Python script without executing it.

    Returns whether the script is syntactically valid, and if not,
    the exact error location and message.
    """
    return _run_cli(["check", script_path])


@mcp.tool()
def list_actions() -> str:
    """List all available nekonote API functions with signatures and descriptions.

    Use this to discover what nekonote can do before writing a script.
    """
    return _run_cli(["list-actions"])


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _run_cli(args: list[str]) -> str:
    """Run a nekonote CLI command and return its output."""
    cmd = [sys.executable, "-m", "nekonote.cli"] + args
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            encoding="utf-8",
            errors="replace",
        )
        output = result.stdout
        if result.returncode != 0 and result.stderr:
            output += "\n" + result.stderr
        return output.strip() or "(no output)"
    except subprocess.TimeoutExpired:
        return json.dumps({"error": "Command timed out after 120s"})
    except Exception as e:
        return json.dumps({"error": str(e)})


if __name__ == "__main__":
    mcp.run()
