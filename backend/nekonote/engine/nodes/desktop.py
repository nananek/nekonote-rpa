from __future__ import annotations

import asyncio
import base64
import io
from typing import Any

from nekonote.engine.context import ExecutionContext
from nekonote.engine.nodes.registry import register


def _run_sync(func, *args, **kwargs):
    """Run a synchronous function in a thread to avoid blocking the event loop."""
    return asyncio.to_thread(func, *args, **kwargs)


@register("desktop.click")
async def desktop_click(params: dict[str, Any], ctx: ExecutionContext) -> Any:
    import pyautogui

    image = params.get("image")

    if image:
        # Image-based click
        try:
            location = await _run_sync(pyautogui.locateCenterOnScreen, image, confidence=0.8)
            if location:
                await _run_sync(pyautogui.click, location.x, location.y)
                return {"x": location.x, "y": location.y}
            else:
                raise RuntimeError(f"Image not found on screen: {image}")
        except Exception as e:
            raise RuntimeError(f"Image click failed: {e}")
    else:
        x = int(params.get("x", 0))
        y = int(params.get("y", 0))
        await _run_sync(pyautogui.click, x, y)
        return {"x": x, "y": y}


@register("desktop.type")
async def desktop_type(params: dict[str, Any], ctx: ExecutionContext) -> Any:
    import pyautogui

    text = params.get("text", "")
    # pyautogui.write doesn't support non-ASCII, use pyperclip + hotkey for Japanese
    if any(ord(c) > 127 for c in text):
        import subprocess
        # Use clip.exe for Windows clipboard
        process = await asyncio.create_subprocess_exec(
            "clip.exe",
            stdin=asyncio.subprocess.PIPE,
        )
        await process.communicate(input=text.encode("utf-16-le"))
        await _run_sync(pyautogui.hotkey, "ctrl", "v")
    else:
        await _run_sync(pyautogui.write, text, interval=0.02)
    return True


@register("desktop.hotkey")
async def desktop_hotkey(params: dict[str, Any], ctx: ExecutionContext) -> Any:
    import pyautogui

    keys_str = params.get("keys", "")
    # Support both "ctrl,a" (comma-separated) and "ctrl+a" (plus-separated)
    if "+" in keys_str and "," not in keys_str:
        s = keys_str
        literal_plus = s == "+" or s.endswith("++")
        if literal_plus:
            s = s[:-1]  # strip the trailing literal "+"
        keys = [k.strip() for k in s.split("+") if k.strip()] if s else []
        if literal_plus:
            keys.append("+")
    else:
        keys = [k.strip() for k in keys_str.split(",") if k.strip()]
    if keys:
        await _run_sync(pyautogui.hotkey, *keys)
    return True


@register("desktop.screenshot")
async def desktop_screenshot(params: dict[str, Any], ctx: ExecutionContext) -> Any:
    import pyautogui

    region_str = params.get("region", "")
    variable = params.get("variable", "")

    region = None
    if region_str:
        parts = [int(x.strip()) for x in region_str.split(",")]
        if len(parts) == 4:
            region = tuple(parts)

    screenshot = await _run_sync(pyautogui.screenshot, region=region)

    # Convert to base64
    buf = io.BytesIO()
    screenshot.save(buf, format="PNG")
    encoded = base64.b64encode(buf.getvalue()).decode("ascii")

    if variable:
        ctx.set(variable, encoded)

    return encoded[:50] + "..."  # Truncated for logging


@register("desktop.findImage")
async def desktop_find_image(params: dict[str, Any], ctx: ExecutionContext) -> Any:
    import pyautogui

    template = params.get("template", "")
    confidence = float(params.get("confidence", 0.8))
    variable = params.get("variable", "")

    try:
        location = await _run_sync(
            pyautogui.locateCenterOnScreen, template, confidence=confidence
        )
    except Exception as e:
        raise RuntimeError(f"Image search failed: {e}")

    if location:
        result = {"x": location.x, "y": location.y, "found": True}
    else:
        result = {"x": 0, "y": 0, "found": False}

    if variable:
        ctx.set(variable, result)

    return result
