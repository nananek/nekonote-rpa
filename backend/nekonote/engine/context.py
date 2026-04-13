from __future__ import annotations

import re
from typing import Any


# Safe builtins for expression evaluation
_SAFE_BUILTINS = {
    "len": len,
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "list": list,
    "dict": dict,
    "range": range,
    "enumerate": enumerate,
    "zip": zip,
    "min": min,
    "max": max,
    "sum": sum,
    "abs": abs,
    "round": round,
    "sorted": sorted,
    "reversed": reversed,
    "True": True,
    "False": False,
    "None": None,
}


class ExecutionContext:
    """Holds variable state and provides template expression evaluation."""

    def __init__(self, variables: dict[str, Any] | None = None):
        self.variables: dict[str, Any] = variables or {}
        self.cancelled = False
        self._secrets: set[str] = set()  # variable names that should be masked
        self._types: dict[str, str] = {}  # variable name -> type hint

    def set(self, name: str, value: Any, *, secret: bool = False, type_hint: str = "") -> None:
        self.variables[name] = value
        if secret:
            self._secrets.add(name)
        if type_hint:
            self._types[name] = type_hint

    def get(self, name: str, default: Any = None) -> Any:
        return self.variables.get(name, default)

    def is_secret(self, name: str) -> bool:
        return name in self._secrets

    def get_type(self, name: str) -> str:
        if name in self._types:
            return self._types[name]
        val = self.variables.get(name)
        if val is None:
            return "null"
        return type(val).__name__

    def get_visible_variables(self) -> dict[str, Any]:
        """Return variables for display, masking secrets."""
        result = {}
        for k, v in self.variables.items():
            if k.startswith("_"):
                continue
            if k in self._secrets:
                result[k] = "****"
            else:
                result[k] = v
        return result

    def evaluate(self, value: Any) -> Any:
        """Evaluate template expressions like {{ variables.x }} in a value."""
        if isinstance(value, str):
            return self._eval_string(value)
        if isinstance(value, dict):
            return {k: self.evaluate(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self.evaluate(v) for v in value]
        return value

    def _eval_string(self, text: str) -> Any:
        pattern = r"\{\{\s*(.+?)\s*\}\}"

        # If the entire string is a single expression, return its value directly
        # (preserving type, not stringifying)
        match = re.fullmatch(r"\s*\{\{\s*(.+?)\s*\}\}\s*", text)
        if match:
            return self._resolve_expr(match.group(1))

        # Otherwise, do string interpolation
        def replacer(m: re.Match) -> str:
            return str(self._resolve_expr(m.group(1)))

        return re.sub(pattern, replacer, text)

    def _resolve_expr(self, expr: str) -> Any:
        """Resolve an expression. Supports:
        - variables.name  (dotted access)
        - bare variable names
        - comparisons: variables.x == 'foo', variables.count > 5
        - arithmetic: variables.x + 1
        """
        expr = expr.strip()

        # Simple dotted variable access (fast path)
        if re.fullmatch(r"variables\.\w+", expr):
            return self.variables.get(expr[10:], "")

        # Bare variable name (fast path)
        if re.fullmatch(r"\w+", expr) and expr in self.variables:
            return self.variables[expr]

        # Expression evaluation with safe context
        try:
            # Build a namespace with variables accessible both as variables.x and bare x
            namespace = dict(self.variables)
            namespace["variables"] = _DotDict(self.variables)
            return eval(expr, {"__builtins__": _SAFE_BUILTINS}, namespace)
        except Exception:
            # If eval fails, return the raw expression string
            return expr


class _DotDict:
    """Allows dot access on a dict for use in template expressions."""

    def __init__(self, data: dict):
        self._data = data

    def __getattr__(self, name: str) -> Any:
        if name.startswith("_"):
            raise AttributeError(name)
        return self._data.get(name, "")

    def __repr__(self) -> str:
        return repr(self._data)
