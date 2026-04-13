"""Stdio JSON-lines server: reads commands from stdin, writes events to stdout.
No TCP socket is opened. Communication is entirely via process pipes."""

from __future__ import annotations

import asyncio
import json
import logging
import sys
import threading
from typing import Any

from nekonote.engine.executor import FlowExecutor
from nekonote.engine.picker import start_picker
from nekonote.models.flow import Flow

logger = logging.getLogger(__name__)

# Shared browser page for picker
_shared_page = None


def set_shared_page(page):
    global _shared_page
    _shared_page = page


def get_shared_page():
    return _shared_page


class StdioServer:
    """Reads JSON lines from stdin, dispatches commands, writes events to stdout."""

    def __init__(self):
        self._executions: dict[str, FlowExecutor] = {}
        self._write_lock = threading.Lock()
        self._loop: asyncio.AbstractEventLoop | None = None

    def send_sync(self, event: dict[str, Any]) -> None:
        """Write a JSON line to stdout (thread-safe, synchronous)."""
        line = json.dumps(event, ensure_ascii=False, default=str)
        with self._write_lock:
            sys.stdout.write(line + "\n")
            sys.stdout.flush()

    async def send(self, event: dict[str, Any]) -> None:
        """Write a JSON line to stdout (async wrapper)."""
        await asyncio.to_thread(self.send_sync, event)

    async def handle_message(self, msg: dict[str, Any]) -> None:
        msg_type = msg.get("type")

        if msg_type == "ping":
            await self.send({"type": "pong"})

        elif msg_type == "execute":
            flow_data = msg.get("flow")
            if not flow_data:
                await self.send({"type": "error", "error": "Missing flow data"})
                return
            flow = Flow(**flow_data)
            executor = FlowExecutor(flow, on_event=self.send)
            self._executions[executor.execution_id] = executor
            asyncio.create_task(self._run_execution(executor))

        elif msg_type == "stop":
            exec_id = msg.get("execution_id")
            if exec_id and exec_id in self._executions:
                self._executions[exec_id].cancel()

        elif msg_type == "record.start":
            mode = msg.get("mode", "auto")  # auto | element | coordinate | image
            target = msg.get("target", "desktop")  # desktop | browser
            url = msg.get("url", "")
            asyncio.create_task(self._run_record(mode, target=target, url=url))

        elif msg_type == "record.stop":
            self._record_stop = True

        elif msg_type == "record.pause":
            self._record_paused = True
            await self.send({"type": "record.paused"})

        elif msg_type == "record.resume":
            self._record_paused = False
            await self.send({"type": "record.resumed"})

        elif msg_type == "record.setMode":
            self._record_mode = msg.get("mode", "auto")
            await self.send({"type": "record.modeChanged", "mode": self._record_mode})

        elif msg_type == "picker.openBrowser":
            asyncio.create_task(self._open_picker_browser(msg))

        elif msg_type == "picker.start":
            asyncio.create_task(self._run_picker())

    _record_stop = False
    _record_paused = False
    _record_mode = "auto"  # auto | element | coordinate | image

    async def _run_record(self, mode: str = "auto", *, target: str = "desktop", url: str = "") -> None:
        """Record operations in real-time, sending each block immediately.

        Args:
            mode: Recognition mode (auto/element/coordinate/image). Desktop only.
            target: 'desktop' (pynput) or 'browser' (Playwright CDP).
            url: Initial URL for browser recording.
        """
        self._record_stop = False
        self._record_paused = False
        self._record_mode = mode

        if target == "browser":
            await self._run_record_browser(url=url)
            return

        await self.send({"type": "record.started", "mode": mode, "target": target})

        try:
            import pynput.mouse
            import pynput.keyboard
            import time
            import uuid

            loop = asyncio.get_running_loop()
            last_event_time = [time.time()]
            typed_buf: list[str] = []
            typed_start = [0.0]

            def mkid() -> str:
                return f"block_{uuid.uuid4().hex[:8]}"

            def emit_block(block: dict) -> None:
                """Schedule sending a block from the event-loop thread."""
                asyncio.run_coroutine_threadsafe(
                    self.send({"type": "record.block", "block": block}),
                    loop
                )

            def maybe_wait_block() -> None:
                """Emit a control.wait block if the gap is large enough."""
                now = time.time()
                gap = now - last_event_time[0]
                if gap > 0.5:
                    emit_block({
                        "id": mkid(),
                        "type": "control.wait",
                        "label": f"Wait {gap:.1f}s",
                        "params": {"seconds": round(gap, 1)},
                    })
                last_event_time[0] = now

            def flush_typed() -> None:
                """Flush buffered text input as a desktop.type block."""
                if typed_buf:
                    text = "".join(typed_buf)
                    emit_block({
                        "id": mkid(),
                        "type": "desktop.type",
                        "label": f"Type: {text[:20]}",
                        "params": {"text": text},
                    })
                    typed_buf.clear()

            def try_element_capture(x: int, y: int) -> dict | None:
                """Try to identify the UI element at (x, y) via uitree.

                Returns a block dict with XPath, or None if element can't be detected.
                """
                try:
                    import uiautomation as auto
                    ctrl = auto.ControlFromPoint(x, y)
                    if ctrl is None:
                        return None

                    # Walk up to find the owning window
                    win_ctrl = ctrl
                    while win_ctrl and not isinstance(win_ctrl, auto.WindowControl):
                        win_ctrl = win_ctrl.GetParentControl()
                    if win_ctrl is None:
                        return None

                    win_title = win_ctrl.Name or ""
                    if not win_title:
                        return None

                    # Build a simple XPath by tag + name or automation_id
                    tag = type(ctrl).__name__
                    name = ctrl.Name
                    aid = ctrl.AutomationId
                    if aid:
                        xpath = f'.//{tag}[@automation_id="{aid}"]'
                    elif name:
                        xpath = f'.//{tag}[@name="{name}"]'
                    else:
                        return None

                    return {
                        "id": mkid(),
                        "type": "desktop.clickElement",
                        "label": f"Click: {name or aid or tag}",
                        "params": {"title": win_title, "xpath": xpath},
                    }
                except Exception:
                    return None

            def try_image_capture(x: int, y: int) -> dict | None:
                """Capture a small region around the click for image matching."""
                try:
                    import pyautogui
                    import os
                    import tempfile
                    # 60x60 region centered on click
                    rx, ry = max(0, x - 30), max(0, y - 30)
                    img = pyautogui.screenshot(region=(rx, ry, 60, 60))
                    path = os.path.join(tempfile.gettempdir(), f"nk_rec_{mkid()}.png")
                    img.save(path)
                    return {
                        "id": mkid(),
                        "type": "desktop.click",
                        "label": f"Click (image)",
                        "params": {"image": path, "confidence": 0.8},
                    }
                except Exception:
                    return None

            def on_click(x, y, button, pressed):
                if self._record_stop:
                    flush_typed()
                    return False
                if self._record_paused or not pressed:
                    return
                flush_typed()
                maybe_wait_block()
                btn = str(button).replace("Button.", "")
                mode = self._record_mode

                block: dict | None = None

                if btn != "right" and mode in ("auto", "element"):
                    block = try_element_capture(int(x), int(y))

                if block is None and mode == "image" and btn != "right":
                    block = try_image_capture(int(x), int(y))

                if block is None:
                    # Fall back to coordinates
                    block_type = "desktop.rightClick" if btn == "right" else "desktop.click"
                    label = f"{'Right-click' if btn == 'right' else 'Click'} ({int(x)}, {int(y)})"
                    block = {
                        "id": mkid(),
                        "type": block_type,
                        "label": label,
                        "params": {"x": int(x), "y": int(y)},
                    }

                emit_block(block)

            def on_key(key):
                if self._record_stop:
                    flush_typed()
                    return False
                if self._record_paused:
                    return
                try:
                    c = key.char
                    if c:
                        if not typed_buf:
                            typed_start[0] = time.time()
                        typed_buf.append(c)
                        last_event_time[0] = time.time()
                        return
                except AttributeError:
                    pass
                # Special key — flush buffered text first
                flush_typed()
                maybe_wait_block()
                kn = key.name if hasattr(key, "name") else str(key)
                emit_block({
                    "id": mkid(),
                    "type": "desktop.press",
                    "label": f"Press: {kn}",
                    "params": {"key": kn},
                })

            ml = pynput.mouse.Listener(on_click=on_click)
            kl = pynput.keyboard.Listener(on_press=on_key)
            ml.start()
            kl.start()

            # Wait until stop is requested, polling in a thread
            def wait_for_stop():
                while not self._record_stop:
                    time.sleep(0.1)

            await asyncio.to_thread(wait_for_stop)
            ml.stop()
            kl.stop()
            flush_typed()

            await self.send({"type": "record.completed"})
        except Exception as e:
            await self.send({"type": "record.failed", "error": str(e)})

    async def _run_record_browser(self, *, url: str = "") -> None:
        """Record browser operations via Playwright JS injection."""
        import uuid as _uuid
        import time as _time

        await self.send({"type": "record.started", "target": "browser"})

        try:
            from playwright.async_api import async_playwright

            pw = await async_playwright().start()
            browser_inst = await pw.chromium.launch(headless=False)
            ctx = await browser_inst.new_context()
            page = await ctx.new_page()

            # Emit browser.open + navigate blocks
            await self.send({"type": "record.block", "block": {
                "id": f"block_{_uuid.uuid4().hex[:8]}",
                "type": "browser.open",
                "label": "Open Browser",
                "params": {"browser_type": "chromium", "headless": False},
            }})

            if url:
                await self.send({"type": "record.block", "block": {
                    "id": f"block_{_uuid.uuid4().hex[:8]}",
                    "type": "browser.navigate",
                    "label": f"Navigate: {url}",
                    "params": {"url": url},
                }})
                await page.goto(url)

            # Expose a binding so page JS can call back to Python
            last_event_time = [_time.time()]

            def maybe_wait_block() -> None:
                now = _time.time()
                gap = now - last_event_time[0]
                if gap > 0.5:
                    asyncio.run_coroutine_threadsafe(
                        self.send({"type": "record.block", "block": {
                            "id": f"block_{_uuid.uuid4().hex[:8]}",
                            "type": "control.wait",
                            "label": f"Wait {gap:.1f}s",
                            "params": {"seconds": round(gap, 1)},
                        }}),
                        asyncio.get_running_loop()
                    )
                last_event_time[0] = now

            async def handle_browser_event(_src, payload: dict):
                if self._record_paused:
                    return
                maybe_wait_block()
                etype = payload.get("type")
                selector = payload.get("selector", "")
                if etype == "click":
                    await self.send({"type": "record.block", "block": {
                        "id": f"block_{_uuid.uuid4().hex[:8]}",
                        "type": "browser.click",
                        "label": f"Click: {payload.get('text', selector)[:40]}",
                        "params": {"selector": selector},
                    }})
                elif etype == "input":
                    await self.send({"type": "record.block", "block": {
                        "id": f"block_{_uuid.uuid4().hex[:8]}",
                        "type": "browser.type",
                        "label": f"Type: {payload.get('value', '')[:20]}",
                        "params": {"selector": selector, "text": payload.get("value", "")},
                    }})
                elif etype == "navigate":
                    await self.send({"type": "record.block", "block": {
                        "id": f"block_{_uuid.uuid4().hex[:8]}",
                        "type": "browser.navigate",
                        "label": f"Navigate: {payload.get('url', '')}",
                        "params": {"url": payload.get("url", "")},
                    }})

            await ctx.expose_binding("_nekonote_record", handle_browser_event)

            # Inject recorder script into every page
            recorder_js = r"""
            () => {
                function selectorFor(el) {
                    if (el.id) return '#' + el.id;
                    if (el.name) return el.tagName.toLowerCase() + '[name="' + el.name + '"]';
                    if (el.getAttribute('data-testid')) return '[data-testid="' + el.getAttribute('data-testid') + '"]';
                    // Path-based fallback
                    const parts = [];
                    let cur = el;
                    while (cur && cur.nodeType === 1 && parts.length < 5) {
                        let part = cur.tagName.toLowerCase();
                        if (cur.className && typeof cur.className === 'string') {
                            part += '.' + cur.className.split(/\s+/).filter(Boolean)[0];
                        }
                        parts.unshift(part);
                        cur = cur.parentElement;
                    }
                    return parts.join(' > ');
                }
                document.addEventListener('click', (e) => {
                    if (window._nekonote_record) {
                        window._nekonote_record({
                            type: 'click',
                            selector: selectorFor(e.target),
                            text: (e.target.textContent || '').trim().substring(0, 50),
                        });
                    }
                }, true);
                document.addEventListener('change', (e) => {
                    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') {
                        if (window._nekonote_record) {
                            window._nekonote_record({
                                type: 'input',
                                selector: selectorFor(e.target),
                                value: e.target.value || '',
                            });
                        }
                    }
                }, true);
            }
            """
            await ctx.add_init_script(recorder_js)

            # Also inject into the current page
            await page.evaluate(recorder_js)

            # Capture navigations
            def on_frame_nav(frame):
                if frame == page.main_frame and frame.url and frame.url != "about:blank":
                    asyncio.run_coroutine_threadsafe(
                        handle_browser_event(None, {"type": "navigate", "url": frame.url}),
                        asyncio.get_running_loop()
                    )

            page.on("framenavigated", on_frame_nav)

            # Wait for stop
            while not self._record_stop:
                await asyncio.sleep(0.1)

            await ctx.close()
            await browser_inst.close()
            await pw.stop()

            await self.send({"type": "record.completed"})
        except Exception as e:
            await self.send({"type": "record.failed", "error": str(e)})

    async def _run_execution(self, executor: FlowExecutor) -> None:
        try:
            await executor.execute()
        finally:
            self._executions.pop(executor.execution_id, None)

    async def _open_picker_browser(self, msg: dict) -> None:
        url = msg.get("url", "about:blank")
        try:
            from playwright.async_api import async_playwright

            page = get_shared_page()
            if not page:
                pw = await async_playwright().start()
                browser = await pw.chromium.launch(headless=False)
                ctx = await browser.new_context()
                page = await ctx.new_page()
                set_shared_page(page)

            if url and url != "about:blank":
                await page.goto(url, wait_until="domcontentloaded")

            await self.send({
                "type": "picker.browserReady",
                "url": page.url,
                "title": await page.title()
            })
        except Exception as e:
            await self.send({"type": "picker.error", "error": str(e)})

    async def _run_picker(self) -> None:
        try:
            page = get_shared_page()
            if not page:
                await self.send({"type": "picker.error", "error": "No browser open."})
                return
            await self.send({"type": "picker.started"})
            result = await start_picker(page)
            await self.send({
                "type": "picker.result",
                "selector": result.get("selector", ""),
                "tagName": result.get("tagName", ""),
                "text": result.get("text", ""),
                "cancelled": result.get("cancelled", False)
            })
        except Exception as e:
            await self.send({"type": "picker.error", "error": str(e)})

    def _stdin_reader(self) -> None:
        """Read stdin in a background thread (works on Windows ProactorEventLoop)."""
        try:
            for line in sys.stdin:
                line = line.strip()
                if not line:
                    continue
                try:
                    msg = json.loads(line)
                    if self._loop:
                        asyncio.run_coroutine_threadsafe(
                            self.handle_message(msg), self._loop
                        )
                except json.JSONDecodeError:
                    self.send_sync({"type": "error", "error": "Invalid JSON"})
        except Exception:
            pass  # stdin closed

    async def run(self) -> None:
        """Main loop."""
        self._loop = asyncio.get_event_loop()
        self.send_sync({"type": "ready"})

        # Read stdin in a thread (avoids Windows ProactorEventLoop pipe issues)
        reader_thread = threading.Thread(target=self._stdin_reader, daemon=True)
        reader_thread.start()

        # Keep the event loop alive until stdin reader exits
        await asyncio.to_thread(reader_thread.join)


def run_stdio():
    """Entry point for stdio mode."""
    # Redirect logging to stderr so it doesn't pollute the JSON stdout stream
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stderr,
    )

    server = StdioServer()
    asyncio.run(server.run())
