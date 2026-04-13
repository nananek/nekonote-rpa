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
# Flow editing tools (read/write the shared flow file)
# ---------------------------------------------------------------------------


def _get_shared_flow_path() -> str:
    """Get the path to the shared flow file synced with the Electron editor."""
    import os

    if os.name == "nt":
        base = os.path.join(os.environ.get("APPDATA", ""), "nekonote", "shared")
    else:
        base = os.path.expanduser("~/.config/nekonote/shared")
    return os.path.join(base, "current_flow.json")


@mcp.tool()
def get_current_flow() -> str:
    """Get the flow currently open in the nekonote visual editor.

    Returns the full flow JSON including all blocks, variables, and metadata.
    Use this to understand what the user is working on before making changes.
    """
    path = _get_shared_flow_path()
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return json.dumps({"error": "No flow is currently open in the editor."})


@mcp.tool()
def update_flow(flow_json: str) -> str:
    """Replace the entire flow in the nekonote visual editor.

    The editor will automatically pick up the change and update the UI.
    Pass the complete flow JSON (same format as get_current_flow returns).

    IMPORTANT: Always call get_current_flow() first to get the current state,
    then modify it, then call update_flow() with the complete modified flow.
    """
    path = _get_shared_flow_path()
    try:
        # Validate JSON
        parsed = json.loads(flow_json)
        if "blocks" not in parsed:
            return json.dumps({"error": "Invalid flow: missing 'blocks' field"})
        with open(path, "w", encoding="utf-8") as f:
            json.dump(parsed, f, ensure_ascii=False, indent=2)
        return json.dumps({"status": "ok", "blocks_count": len(parsed.get("blocks", []))})
    except json.JSONDecodeError as e:
        return json.dumps({"error": f"Invalid JSON: {e}"})
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
def add_block(
    block_type: str,
    label: str = "",
    params: str = "{}",
    parent_id: str = "",
    index: int = -1,
) -> str:
    """Add a new block to the flow currently open in the editor.

    Args:
        block_type: Block type (e.g. 'browser.open', 'browser.click', 'data.log',
                    'control.if', 'desktop.click', etc.)
        label: Display label for the block.
        params: JSON string of block parameters (e.g. '{"url": "https://example.com"}')
        parent_id: If set, add as child of this block (for control blocks).
        index: Position to insert at (-1 = end).

    Use list_actions() to see available block types.
    """
    path = _get_shared_flow_path()
    try:
        with open(path, "r", encoding="utf-8") as f:
            flow = json.load(f)
    except FileNotFoundError:
        return json.dumps({"error": "No flow is currently open in the editor."})

    import uuid

    block = {
        "id": f"block_{uuid.uuid4().hex[:8]}",
        "type": block_type,
        "label": label or block_type.split(".")[-1],
        "params": json.loads(params) if isinstance(params, str) else params,
    }

    if parent_id:
        _add_to_parent(flow["blocks"], parent_id, block, index)
    else:
        if index >= 0:
            flow["blocks"].insert(index, block)
        else:
            flow["blocks"].append(block)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(flow, f, ensure_ascii=False, indent=2)

    return json.dumps({"status": "ok", "block_id": block["id"], "type": block_type})


@mcp.tool()
def remove_block(block_id: str) -> str:
    """Remove a block from the flow by its ID."""
    path = _get_shared_flow_path()
    try:
        with open(path, "r", encoding="utf-8") as f:
            flow = json.load(f)
    except FileNotFoundError:
        return json.dumps({"error": "No flow open."})

    flow["blocks"] = _remove_from_tree(flow["blocks"], block_id)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(flow, f, ensure_ascii=False, indent=2)

    return json.dumps({"status": "ok", "removed": block_id})


@mcp.tool()
def update_block_params(block_id: str, params: str) -> str:
    """Update the parameters of an existing block.

    Args:
        block_id: The ID of the block to update.
        params: JSON string of new parameters to merge into existing params.
    """
    path = _get_shared_flow_path()
    try:
        with open(path, "r", encoding="utf-8") as f:
            flow = json.load(f)
    except FileNotFoundError:
        return json.dumps({"error": "No flow open."})

    new_params = json.loads(params) if isinstance(params, str) else params
    found = _update_in_tree(flow["blocks"], block_id, new_params)
    if not found:
        return json.dumps({"error": f"Block '{block_id}' not found"})

    with open(path, "w", encoding="utf-8") as f:
        json.dump(flow, f, ensure_ascii=False, indent=2)

    return json.dumps({"status": "ok", "block_id": block_id})


def _add_to_parent(blocks: list, parent_id: str, block: dict, index: int) -> bool:
    for b in blocks:
        if b.get("id") == parent_id:
            children = b.setdefault("children", [])
            if index >= 0:
                children.insert(index, block)
            else:
                children.append(block)
            return True
        if _add_to_parent(b.get("children", []), parent_id, block, index):
            return True
        if _add_to_parent(b.get("elseChildren", []), parent_id, block, index):
            return True
    return False


def _remove_from_tree(blocks: list, block_id: str) -> list:
    result = []
    for b in blocks:
        if b.get("id") == block_id:
            continue
        if "children" in b:
            b["children"] = _remove_from_tree(b["children"], block_id)
        if "elseChildren" in b:
            b["elseChildren"] = _remove_from_tree(b["elseChildren"], block_id)
        result.append(b)
    return result


def _update_in_tree(blocks: list, block_id: str, new_params: dict) -> bool:
    for b in blocks:
        if b.get("id") == block_id:
            b["params"] = {**b.get("params", {}), **new_params}
            return True
        if _update_in_tree(b.get("children", []), block_id, new_params):
            return True
        if _update_in_tree(b.get("elseChildren", []), block_id, new_params):
            return True
    return False


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
