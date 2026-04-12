from __future__ import annotations

import logging
from typing import Any

from nekonote.engine.context import ExecutionContext
from nekonote.engine.nodes.registry import register

logger = logging.getLogger(__name__)


@register("data.setVariable")
async def set_variable(params: dict[str, Any], ctx: ExecutionContext) -> Any:
    name = params["name"]
    value = ctx.evaluate(params.get("value", ""))
    ctx.set(name, value)
    return value


@register("data.log")
async def log_message(params: dict[str, Any], ctx: ExecutionContext) -> Any:
    message = ctx.evaluate(params.get("message", ""))
    level = params.get("level", "info")
    logger.log(getattr(logging, level.upper(), logging.INFO), message)
    return message


@register("data.comment")
async def comment(params: dict[str, Any], ctx: ExecutionContext) -> Any:
    # No-op node for documentation
    return None
