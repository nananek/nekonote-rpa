"""Synchronous desktop automation API for nekonote scripts.

Usage::

    from nekonote import desktop

    desktop.click(x=100, y=200)
    desktop.type("Hello World")
    desktop.hotkey("ctrl", "s")
"""

from __future__ import annotations

import asyncio
import base64
import io
from typing import Any

from nekonote._runtime import run_async


def _to_thread(func, *args, **kwargs):
    """Run a blocking function on the background event loop's thread pool."""

    async def _run():
        return await asyncio.to_thread(func, *args, **kwargs)

    return run_async(_run())


# ---------------------------------------------------------------------------
# Mouse
# ---------------------------------------------------------------------------


def click(
    x: int | None = None,
    y: int | None = None,
    *,
    image: str = "",
    confidence: float = 0.8,
    button: str = "left",
    clicks: int = 1,
) -> dict[str, int]:
    """Click at coordinates or on an image match.

    Returns ``{"x": int, "y": int}`` of the click location.
    """
    import pyautogui

    if image:
        from nekonote.errors import ElementNotFoundError

        loc = _to_thread(pyautogui.locateCenterOnScreen, image, confidence=confidence)
        if loc is None:
            raise ElementNotFoundError(
                f"Image '{image}' not found on screen",
                action="desktop.click",
                context={"image": image, "confidence": confidence},
                suggestion="Verify the image file exists and matches the current screen.",
            )
        _to_thread(pyautogui.click, loc.x, loc.y, button=button, clicks=clicks)
        return {"x": loc.x, "y": loc.y}

    if x is None or y is None:
        raise ValueError("Provide (x, y) coordinates or image= parameter")
    _to_thread(pyautogui.click, x, y, button=button, clicks=clicks)
    return {"x": x, "y": y}


def double_click(x: int, y: int) -> None:
    import pyautogui

    _to_thread(pyautogui.doubleClick, x, y)


def right_click(x: int, y: int) -> None:
    import pyautogui

    _to_thread(pyautogui.rightClick, x, y)


def drag(from_x: int, from_y: int, to_x: int, to_y: int, *, duration: float = 0.5) -> None:
    import pyautogui

    _to_thread(pyautogui.moveTo, from_x, from_y)
    _to_thread(pyautogui.drag, to_x - from_x, to_y - from_y, duration=duration)


def mouse_move(x: int, y: int) -> None:
    import pyautogui

    _to_thread(pyautogui.moveTo, x, y)


def scroll(direction: str = "down", clicks: int = 3) -> None:
    """Scroll the mouse wheel.  *direction*: up/down/left/right."""
    import pyautogui

    if direction == "down":
        _to_thread(pyautogui.scroll, -clicks)
    elif direction == "up":
        _to_thread(pyautogui.scroll, clicks)
    elif direction == "right":
        _to_thread(pyautogui.hscroll, clicks)
    elif direction == "left":
        _to_thread(pyautogui.hscroll, -clicks)


# ---------------------------------------------------------------------------
# Keyboard
# ---------------------------------------------------------------------------


def type(text: str, *, interval: float = 0.02) -> None:
    """Type text.  Handles Japanese / non-ASCII via clipboard."""
    import pyautogui

    if any(ord(c) > 127 for c in text):
        # Clipboard approach for non-ASCII
        async def _clip():
            import subprocess as _sp

            proc = await asyncio.create_subprocess_exec(
                "clip.exe", stdin=asyncio.subprocess.PIPE
            )
            await proc.communicate(input=text.encode("utf-16-le"))
            await asyncio.to_thread(pyautogui.hotkey, "ctrl", "v")

        run_async(_clip())
    else:
        _to_thread(pyautogui.write, text, interval=interval)


def hotkey(*keys: str) -> None:
    """Press a key combination, e.g. ``hotkey("ctrl", "s")``."""
    import pyautogui

    _to_thread(pyautogui.hotkey, *keys)


def press(key: str) -> None:
    """Press a single key."""
    import pyautogui

    _to_thread(pyautogui.press, key)


# ---------------------------------------------------------------------------
# Screen / Image
# ---------------------------------------------------------------------------


def screenshot(path: str = "", *, region: tuple[int, int, int, int] | None = None) -> str:
    """Take a screenshot.  Returns base64 if *path* is empty."""
    import pyautogui

    img = _to_thread(pyautogui.screenshot, region=region)
    if path:
        img.save(path)
        return path
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def find_image(
    template: str, *, confidence: float = 0.8
) -> dict[str, Any]:
    """Find an image on screen.  Returns ``{"x", "y", "found"}``."""
    import pyautogui

    try:
        loc = _to_thread(pyautogui.locateCenterOnScreen, template, confidence=confidence)
    except Exception:
        return {"x": 0, "y": 0, "found": False}
    if loc:
        return {"x": loc.x, "y": loc.y, "found": True}
    return {"x": 0, "y": 0, "found": False}


def wait_image(template: str, *, timeout: float = 10, confidence: float = 0.8) -> dict[str, Any]:
    """Wait until *template* appears on screen."""
    import time
    import pyautogui

    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            loc = _to_thread(pyautogui.locateCenterOnScreen, template, confidence=confidence)
            if loc:
                return {"x": loc.x, "y": loc.y, "found": True}
        except Exception:
            pass
        _to_thread(time.sleep, 0.5)

    from nekonote.errors import TimeoutError

    raise TimeoutError(
        f"Image '{template}' not found within {timeout}s",
        action="desktop.wait_image",
        context={"template": template, "timeout": timeout},
    )


def get_screen_size() -> tuple[int, int]:
    import pyautogui

    size = pyautogui.size()
    return (size.width, size.height)


def get_pixel_color(x: int, y: int) -> tuple[int, int, int]:
    import pyautogui

    img = _to_thread(pyautogui.screenshot, region=(x, y, 1, 1))
    return img.getpixel((0, 0))[:3]


# ---------------------------------------------------------------------------
# Clipboard
# ---------------------------------------------------------------------------


def get_clipboard() -> str:
    import subprocess

    result = subprocess.run(
        ["powershell", "-command", "Get-Clipboard"],
        capture_output=True,
        text=True,
    )
    return result.stdout.rstrip("\r\n")


def set_clipboard(text: str) -> None:
    import subprocess

    subprocess.run(
        ["clip.exe"],
        input=text.encode("utf-16-le"),
        check=True,
    )
