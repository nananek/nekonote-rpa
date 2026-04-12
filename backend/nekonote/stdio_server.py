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

        elif msg_type == "picker.openBrowser":
            asyncio.create_task(self._open_picker_browser(msg))

        elif msg_type == "picker.start":
            asyncio.create_task(self._run_picker())

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
