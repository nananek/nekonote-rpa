from __future__ import annotations

from typing import Any, Callable, Awaitable

from nekonote.engine.context import ExecutionContext

NodeHandler = Callable[[dict[str, Any], ExecutionContext], Awaitable[Any]]

_registry: dict[str, NodeHandler] = {}


def register(node_type: str):
    """Decorator to register a node handler."""

    def decorator(func: NodeHandler) -> NodeHandler:
        _registry[node_type] = func
        return func

    return decorator


def get_handler(node_type: str) -> NodeHandler | None:
    return _registry.get(node_type)


def get_all_types() -> list[str]:
    return sorted(_registry.keys())
