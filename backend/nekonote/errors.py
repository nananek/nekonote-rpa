"""Structured error types for nekonote.

Every error carries machine-readable fields so that AI coding agents
can autonomously diagnose and fix scripts.
"""

from __future__ import annotations

import json
from typing import Any


class NekonoteError(Exception):
    """Base error with structured context for AI-agent consumption."""

    code: str = "UNKNOWN_ERROR"

    def __init__(
        self,
        message: str,
        *,
        action: str = "",
        line: int | None = None,
        context: dict[str, Any] | None = None,
        suggestion: str = "",
    ):
        super().__init__(message)
        self.action = action
        self.line = line
        self.context = context or {}
        self.suggestion = suggestion

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {
            "type": "error",
            "code": self.code,
            "message": str(self),
            "action": self.action,
        }
        if self.line is not None:
            d["line"] = self.line
        if self.context:
            d["context"] = self.context
        if self.suggestion:
            d["suggestion"] = self.suggestion
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)


class ElementNotFoundError(NekonoteError):
    code = "ELEMENT_NOT_FOUND"


class BrowserNotOpenError(NekonoteError):
    code = "BROWSER_NOT_OPEN"

    def __init__(self, action: str = ""):
        super().__init__(
            "No browser is open. Call browser.open() first.",
            action=action,
            suggestion="Add `browser.open()` before this line.",
        )


class TimeoutError(NekonoteError):
    code = "TIMEOUT"


class WindowNotFoundError(NekonoteError):
    code = "WINDOW_NOT_FOUND"


class FileNotFoundError(NekonoteError):
    code = "FILE_NOT_FOUND"


class XPathNoMatchError(NekonoteError):
    code = "XPATH_NO_MATCH"


class TypeError(NekonoteError):
    code = "TYPE_ERROR"


class ProcessError(NekonoteError):
    code = "PROCESS_ERROR"


class ScriptError(NekonoteError):
    """Wraps an error that occurred during user script execution."""

    code = "SCRIPT_ERROR"
