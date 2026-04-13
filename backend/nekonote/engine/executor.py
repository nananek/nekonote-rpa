from __future__ import annotations

import asyncio
import logging
import time
import uuid
from typing import Any, Callable, Awaitable

from nekonote.engine.context import ExecutionContext
from nekonote.engine.nodes.registry import get_handler

# Ensure node handlers are registered by importing the modules
import nekonote.engine.nodes.data  # noqa: F401
import nekonote.engine.nodes.control  # noqa: F401
import nekonote.engine.nodes.browser  # noqa: F401
import nekonote.engine.nodes.desktop  # noqa: F401

from nekonote.models.flow import Flow, FlowNode

logger = logging.getLogger(__name__)

EventCallback = Callable[[dict[str, Any]], Awaitable[None]]


class FlowExecutor:
    """Interprets a Flow by walking its graph and dispatching to node handlers."""

    def __init__(self, flow: Flow, on_event: EventCallback | None = None, step_delay: float = 0.0):
        self.flow = flow
        self.on_event = on_event or self._noop
        self.ctx = ExecutionContext()
        self.execution_id = str(uuid.uuid4())
        self._cancelled = False
        self.step_delay = step_delay  # seconds between steps (0 = fast)

        # Build lookup structures
        self._nodes: dict[str, FlowNode] = {n.id: n for n in flow.nodes}
        # adjacency: source_id -> list of (target_id, sourceHandle)
        self._adj: dict[str, list[tuple[str, str]]] = {}
        for edge in flow.edges:
            self._adj.setdefault(edge.source, []).append(
                (edge.target, edge.sourceHandle)
            )
        # nodes with incoming edges
        self._has_incoming: set[str] = {e.target for e in flow.edges}

    @staticmethod
    async def _noop(event: dict[str, Any]) -> None:
        pass

    def cancel(self) -> None:
        self._cancelled = True
        self.ctx.cancelled = True

    async def _cleanup(self) -> None:
        """Clean up resources like browser instances."""
        try:
            browser = self.ctx.variables.get("_browser")
            pw = self.ctx.variables.get("_playwright")
            if browser:
                await browser.close()
            if pw:
                await pw.stop()
        except Exception as e:
            logger.warning("Cleanup error: %s", e)

    async def _emit(self, event: dict[str, Any]) -> None:
        try:
            await self.on_event(event)
        except Exception as e:
            logger.warning("Event emission error: %s", e)

    async def _emit_log(self, message: str, level: str = "info") -> None:
        await self._emit({
            "type": "log",
            "execution_id": self.execution_id,
            "level": level,
            "message": message,
        })

    async def _emit_variable_changed(self, name: str, value: Any) -> None:
        await self._emit({
            "type": "variable.changed",
            "execution_id": self.execution_id,
            "name": name,
            "value": _safe_serialize(value),
        })

    async def execute(self) -> None:
        # Initialize variables from flow definition
        for var in self.flow.variables:
            self.ctx.set(var.name, var.default)

        await self._emit(
            {"type": "execution.started", "execution_id": self.execution_id}
        )

        try:
            # Countdown before execution starts (give user time to switch windows)
            has_desktop = any(n.type.startswith("desktop.") for n in self.flow.nodes)
            if has_desktop:
                for i in range(3, 0, -1):
                    if self._cancelled:
                        raise asyncio.CancelledError()
                    await self._emit_log(f"Starting in {i}...")
                    await asyncio.sleep(1)

            # Find start nodes (no incoming edges)
            start_nodes = [
                n.id for n in self.flow.nodes if n.id not in self._has_incoming
            ]
            if not start_nodes:
                raise RuntimeError("No start node found (all nodes have incoming edges)")

            # Execute from first start node
            await self._execute_node(start_nodes[0])

            await self._emit(
                {
                    "type": "execution.completed",
                    "execution_id": self.execution_id,
                    "status": "success",
                }
            )
        except asyncio.CancelledError:
            await self._emit(
                {
                    "type": "execution.completed",
                    "execution_id": self.execution_id,
                    "status": "cancelled",
                }
            )
        except Exception as e:
            await self._emit(
                {
                    "type": "execution.failed",
                    "execution_id": self.execution_id,
                    "error": str(e),
                }
            )
        finally:
            await self._cleanup()

    async def _execute_node(self, node_id: str) -> Any:
        if self._cancelled:
            raise asyncio.CancelledError()

        # Step delay for slow/normal execution modes
        if self.step_delay > 0:
            await asyncio.sleep(self.step_delay)

        node = self._nodes.get(node_id)
        if not node:
            raise RuntimeError(f"Node not found: {node_id}")

        handler = get_handler(node.type)
        if not handler:
            raise RuntimeError(f"Unknown node type: {node.type}")

        # Evaluate params
        params = self.ctx.evaluate(node.params)

        await self._emit(
            {
                "type": "node.enter",
                "execution_id": self.execution_id,
                "node_id": node_id,
            }
        )

        start = time.perf_counter()
        try:
            result = await handler(params, self.ctx)
            duration_ms = (time.perf_counter() - start) * 1000

            # Emit log for data.log nodes
            if node.type == "data.log":
                await self._emit_log(str(result))

            # Emit variable.changed for data.setVariable nodes
            if node.type == "data.setVariable":
                name = params.get("name", "")
                if name:
                    await self._emit_variable_changed(name, self.ctx.get(name))

            await self._emit(
                {
                    "type": "node.exit",
                    "execution_id": self.execution_id,
                    "node_id": node_id,
                    "status": "success",
                    "duration_ms": round(duration_ms, 1),
                }
            )
        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000
            await self._emit(
                {
                    "type": "node.error",
                    "execution_id": self.execution_id,
                    "node_id": node_id,
                    "error": str(e),
                    "duration_ms": round(duration_ms, 1),
                }
            )
            raise

        # Route to next node based on node type
        return await self._route_next(node, result, params)

    async def _route_next(self, node: FlowNode, result: Any, params: dict) -> Any:
        next_edges = self._adj.get(node.id, [])
        if not next_edges:
            return result

        # control.if: follow true/false branch
        if node.type == "control.if":
            branch = "true" if result else "false"
            for target_id, handle in next_edges:
                if handle == branch:
                    return await self._execute_node(target_id)
            return result

        # control.loop: iterate
        if node.type == "control.loop":
            return await self._handle_loop(next_edges, params, result)

        # control.forEach: iterate over list
        if node.type == "control.forEach":
            return await self._handle_for_each(next_edges, result)

        # control.tryCatch: try branch, catch on error
        if node.type == "control.tryCatch":
            return await self._handle_try_catch(next_edges)

        # Default: follow first "out" edge
        for target_id, handle in next_edges:
            if handle == "out":
                return await self._execute_node(target_id)

        # Fallback: follow first edge
        if next_edges:
            return await self._execute_node(next_edges[0][0])

        return result

    async def _handle_loop(self, edges: list, params: dict, result: Any) -> Any:
        loop_target = None
        continue_target = None
        for target_id, handle in edges:
            if handle == "loop":
                loop_target = target_id
            elif handle == "out":
                continue_target = target_id

        count = int(params.get("count", 0))
        condition = params.get("condition", "")

        i = 0
        while True:
            if self._cancelled:
                raise asyncio.CancelledError()
            if count and i >= count:
                break
            if condition and not self.ctx.evaluate(condition):
                break
            if not count and not condition:
                break  # no count and no condition = don't loop

            self.ctx.set("_loop_index", i)
            await self._emit_variable_changed("_loop_index", i)

            if loop_target:
                await self._execute_node(loop_target)
            i += 1

        if continue_target:
            return await self._execute_node(continue_target)
        return result

    async def _handle_for_each(self, edges: list, result: Any) -> Any:
        loop_target = None
        continue_target = None
        for target_id, handle in edges:
            if handle == "loop":
                loop_target = target_id
            elif handle == "out":
                continue_target = target_id

        items = result.get("items", []) if isinstance(result, dict) else []
        item_variable = result.get("item_variable", "item") if isinstance(result, dict) else "item"

        for i, item in enumerate(items):
            if self._cancelled:
                raise asyncio.CancelledError()
            self.ctx.set(item_variable, item)
            self.ctx.set("_loop_index", i)
            await self._emit_variable_changed(item_variable, item)
            await self._emit_variable_changed("_loop_index", i)

            if loop_target:
                await self._execute_node(loop_target)

        if continue_target:
            return await self._execute_node(continue_target)
        return result

    async def _handle_try_catch(self, edges: list) -> Any:
        try_target = None
        catch_target = None
        for target_id, handle in edges:
            if handle == "try":
                try_target = target_id
            elif handle == "catch":
                catch_target = target_id

        if try_target:
            try:
                return await self._execute_node(try_target)
            except Exception as e:
                self.ctx.set("_error", str(e))
                await self._emit_variable_changed("_error", str(e))
                await self._emit_log(f"Caught error: {e}", "warning")
                if catch_target:
                    return await self._execute_node(catch_target)
        return None


def _safe_serialize(value: Any) -> Any:
    """Convert value to JSON-safe form."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (list, tuple)):
        return [_safe_serialize(v) for v in value]
    if isinstance(value, dict):
        return {k: _safe_serialize(v) for k, v in value.items()}
    return str(value)
