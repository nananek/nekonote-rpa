from __future__ import annotations

import asyncio
from typing import Any

from nekonote.engine.context import ExecutionContext
from nekonote.engine.nodes.registry import register


@register("control.wait")
async def wait_node(params: dict[str, Any], ctx: ExecutionContext) -> Any:
    seconds = float(params.get("seconds", 1))
    await asyncio.sleep(seconds)
    return seconds


@register("control.if")
async def if_node(params: dict[str, Any], ctx: ExecutionContext) -> Any:
    """Evaluate condition and return True/False. Executor uses this to pick edge."""
    condition = params.get("condition", "")
    if isinstance(condition, bool):
        return condition
    if isinstance(condition, str):
        condition = condition.strip()
        if not condition:
            return False
        # Simple evaluations
        if condition.lower() == "true":
            return True
        if condition.lower() == "false":
            return False
        # Try numeric comparison
        try:
            return bool(eval(condition, {"__builtins__": {}}, ctx.variables))
        except Exception:
            return bool(condition)
    return bool(condition)


@register("control.loop")
async def loop_node(params: dict[str, Any], ctx: ExecutionContext) -> Any:
    """Return loop config. The executor handles the actual iteration."""
    # Just a marker - execution logic is in executor._execute_node
    return {
        "count": int(params.get("count", 0)),
        "condition": params.get("condition", "")
    }


@register("control.forEach")
async def for_each_node(params: dict[str, Any], ctx: ExecutionContext) -> Any:
    """Return forEach config. The executor handles iteration."""
    list_variable = params.get("list_variable", "")
    item_variable = params.get("item_variable", "item")
    items = ctx.get(list_variable, [])
    return {
        "items": items if isinstance(items, list) else [],
        "item_variable": item_variable
    }


@register("control.tryCatch")
async def try_catch_node(params: dict[str, Any], ctx: ExecutionContext) -> Any:
    """Marker node. Executor handles try/catch branching."""
    return True
