"""Tests for nekonote.errors."""

import json

from nekonote.errors import (
    BrowserNotOpenError,
    ElementNotFoundError,
    NekonoteError,
    ScriptError,
    TimeoutError,
    WindowNotFoundError,
    XPathNoMatchError,
)


class TestNekonoteError:
    def test_basic_fields(self):
        e = NekonoteError("something broke", action="browser.click", line=12)
        assert str(e) == "something broke"
        assert e.action == "browser.click"
        assert e.line == 12
        assert e.code == "UNKNOWN_ERROR"

    def test_to_dict(self):
        e = NekonoteError(
            "not found",
            action="browser.click",
            line=5,
            context={"selector": "#btn"},
            suggestion="Try #submit",
        )
        d = e.to_dict()
        assert d["type"] == "error"
        assert d["code"] == "UNKNOWN_ERROR"
        assert d["message"] == "not found"
        assert d["action"] == "browser.click"
        assert d["line"] == 5
        assert d["context"]["selector"] == "#btn"
        assert d["suggestion"] == "Try #submit"

    def test_to_json_roundtrip(self):
        e = NekonoteError("test", action="x", context={"key": "val"})
        j = e.to_json()
        d = json.loads(j)
        assert d["message"] == "test"
        assert d["context"]["key"] == "val"

    def test_optional_fields_omitted(self):
        e = NekonoteError("msg")
        d = e.to_dict()
        assert "line" not in d
        assert "context" not in d or d["context"] == {}
        assert "suggestion" not in d or d["suggestion"] == ""


class TestSubclasses:
    def test_element_not_found(self):
        e = ElementNotFoundError("no element", action="browser.click")
        assert e.code == "ELEMENT_NOT_FOUND"
        assert isinstance(e, NekonoteError)

    def test_browser_not_open(self):
        e = BrowserNotOpenError(action="browser.click")
        assert e.code == "BROWSER_NOT_OPEN"
        assert "browser.open()" in str(e)
        assert "browser.open()" in e.suggestion

    def test_timeout(self):
        e = TimeoutError("timed out", action="browser.wait")
        assert e.code == "TIMEOUT"

    def test_window_not_found(self):
        e = WindowNotFoundError("no window", action="window.find")
        assert e.code == "WINDOW_NOT_FOUND"

    def test_xpath_no_match(self):
        e = XPathNoMatchError("xpath miss", action="desktop.click_element")
        assert e.code == "XPATH_NO_MATCH"

    def test_script_error(self):
        e = ScriptError("script failed")
        assert e.code == "SCRIPT_ERROR"

    def test_all_are_exceptions(self):
        for cls in [
            ElementNotFoundError,
            BrowserNotOpenError,
            TimeoutError,
            WindowNotFoundError,
            XPathNoMatchError,
            ScriptError,
        ]:
            assert issubclass(cls, NekonoteError)
            assert issubclass(cls, Exception)
