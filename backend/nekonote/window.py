"""Window management API for nekonote scripts.

Usage::

    from nekonote import window

    window.launch("notepad.exe")
    win = window.find(title="メモ帳")
    window.activate(win)
"""

from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass, field
from typing import Any

from nekonote.errors import WindowNotFoundError


@dataclass
class WindowInfo:
    title: str
    handle: int
    class_name: str = ""
    process_name: str = ""
    pid: int = 0
    rect: dict[str, int] = field(default_factory=dict)
    is_visible: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "handle": self.handle,
            "class_name": self.class_name,
            "process_name": self.process_name,
            "pid": self.pid,
            "rect": self.rect,
            "is_visible": self.is_visible,
        }


def _get_pywinauto_app():
    from pywinauto import Desktop

    return Desktop(backend="uia")


def list_windows(*, visible_only: bool = True) -> list[WindowInfo]:
    """List all top-level windows."""
    from pywinauto import Desktop

    desktop = Desktop(backend="uia")
    windows = desktop.windows()
    results = []
    for w in windows:
        try:
            if visible_only and not w.is_visible():
                continue
            rect = w.rectangle()
            results.append(
                WindowInfo(
                    title=w.window_text(),
                    handle=w.handle,
                    class_name=w.class_name(),
                    process_name=w.process_id(),
                    pid=w.process_id(),
                    rect={
                        "x": rect.left,
                        "y": rect.top,
                        "width": rect.width(),
                        "height": rect.height(),
                    },
                    is_visible=w.is_visible(),
                )
            )
        except Exception:
            continue
    return results


def find(*, title: str = "", class_name: str = "") -> WindowInfo:
    """Find a single window by title (partial match) or class name.

    Raises :class:`WindowNotFoundError` with the list of open windows
    if no match is found.
    """
    windows = list_windows(visible_only=True)
    for w in windows:
        if title and title.lower() in w.title.lower():
            return w
        if class_name and class_name == w.class_name:
            return w

    open_titles = [w.title for w in windows if w.title.strip()]
    raise WindowNotFoundError(
        f"No window found matching title='{title}' class='{class_name}'",
        action="window.find",
        context={
            "search_title": title,
            "search_class": class_name,
            "open_windows": open_titles[:20],
        },
        suggestion=(
            f"Open windows: {', '.join(open_titles[:10])}"
            if open_titles
            else "No visible windows found."
        ),
    )


def find_all(*, title: str = "", class_name: str = "") -> list[WindowInfo]:
    """Find all windows matching the criteria."""
    windows = list_windows(visible_only=True)
    results = []
    for w in windows:
        if title and title.lower() not in w.title.lower():
            continue
        if class_name and class_name != w.class_name:
            continue
        results.append(w)
    return results


def exists(*, title: str = "", class_name: str = "") -> bool:
    """Check if a window matching the criteria exists."""
    try:
        find(title=title, class_name=class_name)
        return True
    except WindowNotFoundError:
        return False


def launch(executable: str, *, args: list[str] | None = None) -> int:
    """Launch an application and return its PID."""
    cmd = [executable] + (args or [])
    proc = subprocess.Popen(cmd)
    return proc.pid


def activate(win: WindowInfo) -> None:
    """Bring a window to the foreground."""
    from pywinauto import Application

    app = Application(backend="uia").connect(handle=win.handle)
    app.window(handle=win.handle).set_focus()


def maximize(win: WindowInfo) -> None:
    from pywinauto import Application

    app = Application(backend="uia").connect(handle=win.handle)
    app.window(handle=win.handle).maximize()


def minimize(win: WindowInfo) -> None:
    from pywinauto import Application

    app = Application(backend="uia").connect(handle=win.handle)
    app.window(handle=win.handle).minimize()


def restore(win: WindowInfo) -> None:
    from pywinauto import Application

    app = Application(backend="uia").connect(handle=win.handle)
    app.window(handle=win.handle).restore()


def close(win: WindowInfo) -> None:
    from pywinauto import Application

    app = Application(backend="uia").connect(handle=win.handle)
    app.window(handle=win.handle).close()


def resize(win: WindowInfo, *, width: int, height: int) -> None:
    from pywinauto import Application

    app = Application(backend="uia").connect(handle=win.handle)
    w = app.window(handle=win.handle)
    rect = w.rectangle()
    w.move_window(x=rect.left, y=rect.top, width=width, height=height)


def move(win: WindowInfo, *, x: int, y: int) -> None:
    from pywinauto import Application

    app = Application(backend="uia").connect(handle=win.handle)
    w = app.window(handle=win.handle)
    rect = w.rectangle()
    w.move_window(x=x, y=y, width=rect.width(), height=rect.height())


def wait(*, title: str = "", timeout: float = 10) -> WindowInfo:
    """Wait for a window to appear."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            return find(title=title)
        except WindowNotFoundError:
            time.sleep(0.5)

    windows = list_windows(visible_only=True)
    open_titles = [w.title for w in windows if w.title.strip()]
    raise WindowNotFoundError(
        f"Window '{title}' did not appear within {timeout}s",
        action="window.wait",
        context={"search_title": title, "timeout": timeout, "open_windows": open_titles[:20]},
        suggestion=f"Currently open: {', '.join(open_titles[:10])}" if open_titles else "",
    )
