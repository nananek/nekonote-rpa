"""nekonote CLI entry point.

Usage::

    nekonote run script.py [--verbose] [--var key=value ...]
    nekonote inspect windows [--filter TITLE] [--visible-only]
    nekonote inspect ui-tree TITLE [--depth N] [--format xml|json] [--xpath EXPR]
    nekonote inspect browser [--selectors] [--forms] [--tables]
    nekonote inspect screenshot [--output FILE] [--region X,Y,W,H]
    nekonote check script.py
    nekonote list-actions
"""

from __future__ import annotations

import argparse
import ast
import io
import json
import sys
import time
import traceback
from pathlib import Path

from nekonote._runtime import configure_output, emit_event
from nekonote.errors import NekonoteError


def _ensure_utf8_stdout() -> None:
    """Force stdout/stderr to UTF-8 on Windows (avoid cp932 issues)."""
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def main(argv: list[str] | None = None) -> int:
    _ensure_utf8_stdout()
    parser = argparse.ArgumentParser(
        prog="nekonote",
        description="nekonote RPA toolkit",
    )
    sub = parser.add_subparsers(dest="command")

    # --- run ---
    p_run = sub.add_parser("run", help="Execute a Python RPA script")
    p_run.add_argument("script", help="Path to .py script")
    p_run.add_argument("--var", action="append", default=[], metavar="KEY=VALUE",
                       help="Pass variable to the script")
    p_run.add_argument("--verbose", "-v", action="store_true",
                       help="Show step-by-step output")
    p_run.add_argument("--format", choices=["json", "human"], default="human",
                       help="Output format (default: human)")
    p_run.add_argument("--dry-run", action="store_true",
                       help="Parse and validate without executing")

    # --- inspect ---
    p_inspect = sub.add_parser("inspect", help="Inspect the current desktop/browser state")
    inspect_sub = p_inspect.add_subparsers(dest="inspect_target")

    # inspect windows
    p_iw = inspect_sub.add_parser("windows", help="List open windows")
    p_iw.add_argument("--filter", "-f", default="", help="Filter by title substring")
    p_iw.add_argument("--visible-only", action="store_true", default=True)

    # inspect ui-tree
    p_ut = inspect_sub.add_parser("ui-tree", help="Dump UI element tree for a window")
    p_ut.add_argument("title", help="Window title (partial match)")
    p_ut.add_argument("--depth", type=int, default=4, help="Max tree depth")
    p_ut.add_argument("--format", choices=["xml", "json"], default="xml")
    p_ut.add_argument("--xpath", default="", help="Filter by XPath expression")

    # inspect browser
    p_ib = inspect_sub.add_parser("browser", help="Inspect the current browser page")
    p_ib.add_argument("--selectors", action="store_true", help="List clickable elements")
    p_ib.add_argument("--forms", action="store_true", help="List form fields")
    p_ib.add_argument("--tables", action="store_true", help="List tables")

    # inspect screenshot
    p_is = inspect_sub.add_parser("screenshot", help="Take a screenshot")
    p_is.add_argument("--output", "-o", default="", help="Output file path")
    p_is.add_argument("--region", default="", help="Region as X,Y,W,H")
    p_is.add_argument("--window", default="", help="Window title to capture")
    p_is.add_argument("--browser", action="store_true", dest="browser_shot",
                       help="Screenshot of browser page")

    # inspect processes
    inspect_sub.add_parser("processes", help="List running processes")

    # --- check ---
    p_check = sub.add_parser("check", help="Validate a script without running it")
    p_check.add_argument("script", help="Path to .py script")

    # --- list-actions ---
    sub.add_parser("list-actions", help="List all available nekonote API functions")

    args = parser.parse_args(argv)

    if args.command == "run":
        return _cmd_run(args)
    elif args.command == "inspect":
        return _cmd_inspect(args)
    elif args.command == "check":
        return _cmd_check(args)
    elif args.command == "list-actions":
        return _cmd_list_actions()
    else:
        parser.print_help()
        return 0


# ---------------------------------------------------------------------------
# nekonote run
# ---------------------------------------------------------------------------


def _cmd_run(args) -> int:
    script_path = Path(args.script).resolve()
    if not script_path.exists():
        _error_json({
            "code": "FILE_NOT_FOUND",
            "message": f"Script not found: {script_path}",
            "context": {"path": str(script_path)},
        })
        return 2

    # Parse user variables
    user_vars: dict[str, str] = {}
    for v in args.var:
        if "=" in v:
            k, val = v.split("=", 1)
            user_vars[k] = val

    configure_output(format=args.format, verbose=args.verbose)

    # Dry-run: parse only
    if args.dry_run:
        return _dry_run(script_path)

    # Execute
    emit_event({"type": "start", "script": str(script_path), "timestamp": time.time()})
    t0 = time.time()

    try:
        # Build execution namespace
        import nekonote.browser as _browser
        import nekonote.desktop as _desktop
        import nekonote.log as _log
        import nekonote.window as _window

        namespace = {
            "__name__": "__main__",
            "__file__": str(script_path),
            "browser": _browser,
            "desktop": _desktop,
            "window": _window,
            "log": _log,
            # user variables
            "variables": user_vars,
        }

        # Lazy-import optional modules only when script imports them
        # (they're available via `from nekonote import X` in scripts)

        code = script_path.read_text(encoding="utf-8")
        compiled = compile(code, str(script_path), "exec")
        exec(compiled, namespace)

        elapsed = (time.time() - t0) * 1000
        emit_event({"type": "end", "status": "success", "total_duration_ms": elapsed})
        return 0

    except NekonoteError as e:
        elapsed = (time.time() - t0) * 1000
        err_dict = e.to_dict()
        # Try to add line number from traceback
        if e.line is None:
            e.line = _extract_line_from_traceback(script_path)
            err_dict["line"] = e.line
        emit_event(err_dict)
        emit_event({"type": "end", "status": "failed", "total_duration_ms": elapsed, "failed_at_line": e.line})
        return 1

    except Exception as e:
        elapsed = (time.time() - t0) * 1000
        line = _extract_line_from_traceback(script_path)
        emit_event({
            "type": "error",
            "code": "SCRIPT_ERROR",
            "message": f"{type(e).__name__}: {e}",
            "line": line,
            "traceback": traceback.format_exc(),
        })
        emit_event({"type": "end", "status": "failed", "total_duration_ms": elapsed, "failed_at_line": line})
        return 1


def _dry_run(script_path: Path) -> int:
    """Parse the script and check for syntax errors without executing."""
    try:
        code = script_path.read_text(encoding="utf-8")
        ast.parse(code, filename=str(script_path))
        print(json.dumps({"status": "ok", "message": "Script is syntactically valid."}, ensure_ascii=False))
        return 0
    except SyntaxError as e:
        _error_json({
            "code": "SYNTAX_ERROR",
            "message": str(e),
            "line": e.lineno,
            "column": e.offset,
        })
        return 3


def _extract_line_from_traceback(script_path: Path) -> int | None:
    """Extract the line number in the user script from the current exception."""
    import traceback as tb

    _, _, exc_tb = sys.exc_info()
    if exc_tb is None:
        return None
    script_str = str(script_path)
    for frame in tb.extract_tb(exc_tb):
        if frame.filename == script_str:
            return frame.lineno
    return None


# ---------------------------------------------------------------------------
# nekonote inspect
# ---------------------------------------------------------------------------


def _cmd_inspect(args) -> int:
    target = args.inspect_target
    if target == "windows":
        return _inspect_windows(args)
    elif target == "ui-tree":
        return _inspect_ui_tree(args)
    elif target == "browser":
        return _inspect_browser(args)
    elif target == "screenshot":
        return _inspect_screenshot(args)
    elif target == "processes":
        return _inspect_processes()
    else:
        print("Usage: nekonote inspect {windows|ui-tree|browser|screenshot|processes}", file=sys.stderr)
        return 2


def _inspect_windows(args) -> int:
    from nekonote.window import list_windows

    windows = list_windows(visible_only=args.visible_only)
    if args.filter:
        windows = [w for w in windows if args.filter.lower() in w.title.lower()]
    data = [w.to_dict() for w in windows]
    print(json.dumps(data, ensure_ascii=False, indent=2))
    return 0


def _inspect_ui_tree(args) -> int:
    try:
        from uitree import UITree
    except ImportError:
        _error_json({
            "code": "MISSING_DEPENDENCY",
            "message": "uitree is not installed.",
            "suggestion": "pip install git+https://github.com/nananek/uitree.git",
        })
        return 1

    # Build tree from desktop, then locate the target window
    tree = UITree(depth=args.depth + 1)  # +1 because root is Desktop
    title = args.title

    # First, find the window element
    window_elements = tree.xpath(f'//*[contains(@name, "{title}")]')
    if not window_elements:
        _error_json({
            "code": "WINDOW_NOT_FOUND",
            "message": f"No UI element matching '{title}' found (depth={args.depth})",
            "suggestion": "Try increasing --depth or check the window title with: nekonote inspect windows",
        })
        return 1

    win_elem = window_elements[0]

    if args.xpath:
        # Search within the window subtree
        results = win_elem.xpath(args.xpath)
        if args.format == "json":
            data = [{"tag": e.tag, "attrib": dict(e.attrib)} for e in results]
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            for e in results:
                attrs = " ".join(f'{k}="{v}"' for k, v in e.attrib.items() if v)
                print(f"<{e.tag} {attrs}/>")
    else:
        # Dump the window's full subtree
        try:
            from lxml import etree

            xml_str = etree.tostring(win_elem._element, pretty_print=True, encoding="unicode")
            if args.format == "json":
                print(json.dumps({"xml": xml_str}, ensure_ascii=False))
            else:
                print(xml_str)
        except Exception:
            print(tree.dumpxml(pretty_print=True, encoding="unicode"))

    return 0


def _inspect_browser(args) -> int:
    from nekonote import browser

    if browser._page is None:
        _error_json({
            "code": "BROWSER_NOT_OPEN",
            "message": "No browser session. Call browser.open() or run a script first.",
            "suggestion": "Start a browser first: nekonote run script_that_opens_browser.py",
        })
        return 1

    try:
        info = browser.get_page_info()
        # Filter based on flags
        if args.selectors:
            print(json.dumps(info.get("clickable", []), ensure_ascii=False, indent=2))
        elif args.forms:
            print(json.dumps(info.get("inputs", []), ensure_ascii=False, indent=2))
        elif args.tables:
            print(json.dumps(info.get("tables", []), ensure_ascii=False, indent=2))
        else:
            print(json.dumps(info, ensure_ascii=False, indent=2))
        return 0
    except Exception as e:
        _error_json({"code": "BROWSER_ERROR", "message": str(e)})
        return 1


def _inspect_screenshot(args) -> int:
    region = None
    if args.region:
        parts = [int(x.strip()) for x in args.region.split(",")]
        if len(parts) == 4:
            region = tuple(parts)

    output = args.output or "screenshot.png"

    if hasattr(args, "browser_shot") and args.browser_shot:
        from nekonote import browser

        if browser._page is None:
            _error_json({"code": "BROWSER_NOT_OPEN", "message": "No browser session."})
            return 1
        browser.screenshot(path=output)
    else:
        from nekonote import desktop

        desktop.screenshot(path=output, region=region)

    print(json.dumps({"path": output}, ensure_ascii=False))
    return 0


def _inspect_processes() -> int:
    import subprocess

    result = subprocess.run(
        ["powershell", "-command",
         "Get-Process | Select-Object Id, ProcessName, MainWindowTitle | ConvertTo-Json"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print(result.stdout)
    else:
        print("[]")
    return 0


# ---------------------------------------------------------------------------
# nekonote check
# ---------------------------------------------------------------------------


def _cmd_check(args) -> int:
    script_path = Path(args.script).resolve()
    if not script_path.exists():
        _error_json({"code": "FILE_NOT_FOUND", "message": f"Script not found: {script_path}"})
        return 2
    return _dry_run(script_path)


# ---------------------------------------------------------------------------
# nekonote list-actions
# ---------------------------------------------------------------------------


def _cmd_list_actions() -> int:
    """List all public functions in each nekonote module."""
    import inspect

    import nekonote.browser as _browser
    import nekonote.desktop as _desktop
    import nekonote.log as _log
    import nekonote.window as _window

    modules = {
        "browser": _browser,
        "desktop": _desktop,
        "window": _window,
        "log": _log,
    }

    # Try optional modules
    optional = ["excel", "file", "pdf", "mail", "db", "http", "ocr", "ai", "dialog", "text", "datetime"]
    for name in optional:
        try:
            mod = __import__(f"nekonote.{name}", fromlist=[name])
            modules[name] = mod
        except ImportError:
            pass

    # Symbols to exclude (imports, types, internal helpers)
    _exclude = {
        "Any", "Literal", "BrowserNotOpenError", "ElementNotFoundError",
        "TimeoutError", "WindowNotFoundError", "WindowInfo",
        "register_cleanup", "run_async", "emit_event",
        "dataclass", "field", "base64", "io", "asyncio", "json",
        "subprocess", "time",
    }

    actions: list[dict[str, str]] = []
    for mod_name, mod in sorted(modules.items()):
        for func_name in sorted(dir(mod)):
            if func_name.startswith("_") or func_name in _exclude:
                continue
            obj = getattr(mod, func_name)
            if not callable(obj) or isinstance(obj, type):
                continue
            # Only include functions defined in this module
            if hasattr(obj, "__module__") and obj.__module__ != mod.__name__:
                continue
            sig = ""
            try:
                sig = str(inspect.signature(obj))
            except (ValueError, TypeError):
                pass
            doc = (inspect.getdoc(obj) or "").split("\n")[0]
            actions.append({
                "module": mod_name,
                "function": func_name,
                "signature": f"{mod_name}.{func_name}{sig}",
                "description": doc,
            })

    print(json.dumps(actions, ensure_ascii=False, indent=2))
    return 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _error_json(data: dict) -> None:
    data.setdefault("type", "error")
    print(json.dumps(data, ensure_ascii=False), file=sys.stderr)


if __name__ == "__main__":
    sys.exit(main())
