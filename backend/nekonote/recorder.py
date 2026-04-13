"""Desktop operation recorder for nekonote.

Records mouse clicks and keyboard input, converts to flow blocks.

Usage::

    from nekonote import recorder

    blocks = recorder.record(duration=10)  # record for 10 seconds
    # Returns list of FlowBlock-compatible dicts
"""

from __future__ import annotations

import json
import time
import uuid
from typing import Any


def record(*, duration: float = 30, include_mouse: bool = True, include_keyboard: bool = True) -> list[dict[str, Any]]:
    """Record desktop operations and return as flow blocks.

    Args:
        duration: Recording duration in seconds.
        include_mouse: Record mouse clicks.
        include_keyboard: Record keyboard input.

    Returns:
        List of block dicts compatible with nekonote flow format.
    """
    import pynput.mouse
    import pynput.keyboard

    events: list[dict[str, Any]] = []
    start_time = time.time()

    # Mouse listener
    def on_click(x, y, button, pressed):
        if not pressed or not include_mouse:
            return
        if time.time() - start_time > duration:
            return False
        events.append({
            "time": time.time() - start_time,
            "type": "click",
            "x": int(x),
            "y": int(y),
            "button": str(button),
        })

    # Keyboard listener
    typed_buffer: list[str] = []
    last_key_time = [start_time]

    def flush_typed():
        if typed_buffer:
            text = "".join(typed_buffer)
            events.append({
                "time": last_key_time[0] - start_time,
                "type": "type",
                "text": text,
            })
            typed_buffer.clear()

    def on_key_press(key):
        if not include_keyboard:
            return
        if time.time() - start_time > duration:
            return False
        try:
            char = key.char
            if char:
                typed_buffer.append(char)
                last_key_time[0] = time.time()
                return
        except AttributeError:
            pass

        # Special key — flush text buffer first
        flush_typed()
        key_name = key.name if hasattr(key, "name") else str(key)
        events.append({
            "time": time.time() - start_time,
            "type": "hotkey",
            "key": key_name,
        })

    mouse_listener = pynput.mouse.Listener(on_click=on_click)
    key_listener = pynput.keyboard.Listener(on_press=on_key_press)

    mouse_listener.start()
    key_listener.start()

    # Wait for duration
    time.sleep(duration)

    mouse_listener.stop()
    key_listener.stop()
    flush_typed()

    return _events_to_blocks(events)


def _events_to_blocks(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert raw events to nekonote flow blocks."""
    blocks: list[dict[str, Any]] = []
    prev_time = 0.0

    for evt in events:
        # Add wait block if gap > 0.5s
        gap = evt["time"] - prev_time
        if gap > 0.5 and blocks:
            blocks.append({
                "id": f"block_{uuid.uuid4().hex[:8]}",
                "type": "control.wait",
                "label": f"Wait {gap:.1f}s",
                "params": {"seconds": round(gap, 1)},
            })

        if evt["type"] == "click":
            blocks.append({
                "id": f"block_{uuid.uuid4().hex[:8]}",
                "type": "desktop.click",
                "label": f"Click ({evt['x']}, {evt['y']})",
                "params": {"x": evt["x"], "y": evt["y"]},
            })
        elif evt["type"] == "type":
            blocks.append({
                "id": f"block_{uuid.uuid4().hex[:8]}",
                "type": "desktop.type",
                "label": f"Type: {evt['text'][:20]}",
                "params": {"text": evt["text"]},
            })
        elif evt["type"] == "hotkey":
            blocks.append({
                "id": f"block_{uuid.uuid4().hex[:8]}",
                "type": "desktop.hotkey",
                "label": f"Key: {evt['key']}",
                "params": {"keys": evt["key"]},
            })

        prev_time = evt["time"]

    return blocks
