from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

from nekonote.engine.executor import FlowExecutor
from nekonote.engine.picker import start_picker
from nekonote.models.flow import Flow

logger = logging.getLogger(__name__)


# Shared browser state for picker access
_shared_page = None


def set_shared_page(page):
    global _shared_page
    _shared_page = page


def get_shared_page():
    return _shared_page


class ConnectionManager:
    """Manages WebSocket connections and running executions."""

    def __init__(self):
        self._connections: list[WebSocket] = []
        self._executions: dict[str, FlowExecutor] = {}

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.append(ws)
        logger.info("WebSocket client connected")

    def disconnect(self, ws: WebSocket) -> None:
        if ws in self._connections:
            self._connections.remove(ws)
        logger.info("WebSocket client disconnected")

    async def broadcast(self, event: dict[str, Any]) -> None:
        data = json.dumps(event, ensure_ascii=False, default=str)
        for ws in list(self._connections):
            try:
                await ws.send_text(data)
            except Exception:
                pass

    async def handle_message(self, ws: WebSocket, message: str) -> None:
        try:
            msg = json.loads(message)
        except json.JSONDecodeError:
            await ws.send_text(json.dumps({"type": "error", "error": "Invalid JSON"}))
            return

        msg_type = msg.get("type")

        if msg_type == "ping":
            await ws.send_text(json.dumps({"type": "pong"}))

        elif msg_type == "execute":
            flow_data = msg.get("flow")
            if not flow_data:
                await ws.send_text(
                    json.dumps({"type": "error", "error": "Missing flow data"})
                )
                return
            flow = Flow(**flow_data)
            executor = FlowExecutor(flow, on_event=self.broadcast)
            self._executions[executor.execution_id] = executor
            asyncio.create_task(self._run_execution(executor))

        elif msg_type == "stop":
            exec_id = msg.get("execution_id")
            if exec_id and exec_id in self._executions:
                self._executions[exec_id].cancel()

        elif msg_type == "picker.start":
            asyncio.create_task(self._run_picker(ws, msg))

        elif msg_type == "picker.openBrowser":
            asyncio.create_task(self._open_picker_browser(ws, msg))

    async def _run_execution(self, executor: FlowExecutor) -> None:
        try:
            # Share the browser page for picker access
            executor.ctx.variables.get("_browser_page")
            await executor.execute()
        finally:
            self._executions.pop(executor.execution_id, None)

    async def _open_picker_browser(self, ws: WebSocket, msg: dict) -> None:
        """Open a browser for element picking (if none is open from execution)."""
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

            await ws.send_text(json.dumps({
                "type": "picker.browserReady",
                "url": page.url,
                "title": await page.title()
            }))
        except Exception as e:
            logger.error("Failed to open picker browser: %s", e)
            await ws.send_text(json.dumps({
                "type": "picker.error",
                "error": str(e)
            }))

    async def _run_picker(self, ws: WebSocket, msg: dict) -> None:
        """Start element picker on the current browser page."""
        try:
            page = get_shared_page()
            if not page:
                await ws.send_text(json.dumps({
                    "type": "picker.error",
                    "error": "No browser open. Open a browser first."
                }))
                return

            await ws.send_text(json.dumps({"type": "picker.started"}))

            result = await start_picker(page)

            await ws.send_text(json.dumps({
                "type": "picker.result",
                "selector": result.get("selector", ""),
                "tagName": result.get("tagName", ""),
                "text": result.get("text", ""),
                "cancelled": result.get("cancelled", False)
            }))
        except Exception as e:
            logger.error("Picker error: %s", e)
            await ws.send_text(json.dumps({
                "type": "picker.error",
                "error": str(e)
            }))


manager = ConnectionManager()


async def websocket_endpoint(ws: WebSocket) -> None:
    await manager.connect(ws)
    try:
        while True:
            message = await ws.receive_text()
            await manager.handle_message(ws, message)
    except WebSocketDisconnect:
        manager.disconnect(ws)
