"""Tests for nekonote.browser (mocked Playwright)."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import nekonote.browser as browser
from nekonote.errors import BrowserNotOpenError, ElementNotFoundError, TimeoutError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _setup_mock_page():
    """Set up browser module with a mock page."""
    page = AsyncMock()
    page.url = "https://example.com"
    page.title = AsyncMock(return_value="Example")
    page.is_visible = AsyncMock(return_value=True)

    browser._pw = MagicMock()
    browser._browser = MagicMock()
    browser._context = MagicMock()
    browser._page = page
    return page


# ---------------------------------------------------------------------------
# Tests: no browser open
# ---------------------------------------------------------------------------


class TestBrowserNotOpen:
    def test_navigate_raises(self):
        with pytest.raises(BrowserNotOpenError):
            browser.navigate("https://example.com")

    def test_click_raises(self):
        with pytest.raises(BrowserNotOpenError):
            browser.click("#btn")

    def test_type_raises(self):
        with pytest.raises(BrowserNotOpenError):
            browser.type("#input", "text")

    def test_get_text_raises(self):
        with pytest.raises(BrowserNotOpenError):
            browser.get_text("h1")

    def test_wait_raises(self):
        with pytest.raises(BrowserNotOpenError):
            browser.wait("#el")

    def test_screenshot_raises(self):
        with pytest.raises(BrowserNotOpenError):
            browser.screenshot()

    def test_execute_js_raises(self):
        with pytest.raises(BrowserNotOpenError):
            browser.execute_js("1+1")


# ---------------------------------------------------------------------------
# Tests: with mocked page
# ---------------------------------------------------------------------------


class TestNavigate:
    def test_navigate_returns_url(self):
        page = _setup_mock_page()
        page.goto = AsyncMock()
        page.url = "https://example.com/page"

        result = browser.navigate("https://example.com/page")
        assert result == "https://example.com/page"
        page.goto.assert_called_once()


class TestClick:
    def test_click_success(self):
        page = _setup_mock_page()
        page.click = AsyncMock()

        browser.click("#btn")
        page.click.assert_called_once_with("#btn", timeout=5000)

    def test_click_element_not_found(self):
        page = _setup_mock_page()
        page.click = AsyncMock(side_effect=Exception("Timeout waiting for locator"))
        page.evaluate = AsyncMock(return_value=["#submit", "#cancel"])

        with pytest.raises(ElementNotFoundError) as exc_info:
            browser.click("#nonexistent")
        assert exc_info.value.code == "ELEMENT_NOT_FOUND"
        assert "nonexistent" in str(exc_info.value)


class TestType:
    def test_type_fill(self):
        page = _setup_mock_page()
        page.fill = AsyncMock()

        browser.type("#input", "hello")
        page.fill.assert_called_once_with("#input", "hello", timeout=5000)

    def test_type_element_not_found(self):
        page = _setup_mock_page()
        page.fill = AsyncMock(side_effect=Exception("Timeout waiting for locator"))
        page.evaluate = AsyncMock(return_value=[])

        with pytest.raises(ElementNotFoundError):
            browser.type("#missing", "text")


class TestGetText:
    def test_get_text_success(self):
        page = _setup_mock_page()
        el = AsyncMock()
        el.text_content = AsyncMock(return_value="Hello World")
        page.query_selector = AsyncMock(return_value=el)

        result = browser.get_text("h1")
        assert result == "Hello World"

    def test_get_text_not_found(self):
        page = _setup_mock_page()
        page.query_selector = AsyncMock(return_value=None)
        page.evaluate = AsyncMock(return_value=[])

        with pytest.raises(ElementNotFoundError):
            browser.get_text("#missing")


class TestWait:
    def test_wait_success(self):
        page = _setup_mock_page()
        page.wait_for_selector = AsyncMock()

        browser.wait("#el")
        page.wait_for_selector.assert_called_once_with("#el", timeout=30000)

    def test_wait_timeout(self):
        page = _setup_mock_page()
        page.wait_for_selector = AsyncMock(side_effect=Exception("Timeout"))

        with pytest.raises(TimeoutError) as exc_info:
            browser.wait("#el", timeout=1000)
        assert exc_info.value.code == "TIMEOUT"


class TestScreenshot:
    def test_screenshot_to_file(self):
        page = _setup_mock_page()
        page.screenshot = AsyncMock()

        result = browser.screenshot(path="/tmp/test.png")
        assert result == "/tmp/test.png"
        page.screenshot.assert_called_once_with(path="/tmp/test.png")

    def test_screenshot_base64(self):
        page = _setup_mock_page()
        page.screenshot = AsyncMock(return_value=b"\x89PNG\r\n")

        result = browser.screenshot()
        assert isinstance(result, str)
        assert len(result) > 0


class TestMiscBrowser:
    def test_is_visible(self):
        page = _setup_mock_page()
        assert browser.is_visible("#el") is True

    def test_execute_js(self):
        page = _setup_mock_page()
        page.evaluate = AsyncMock(return_value=42)
        assert browser.execute_js("21 * 2") == 42

    def test_count(self):
        page = _setup_mock_page()
        page.eval_on_selector_all = AsyncMock(return_value=3)
        assert browser.count(".item") == 3

    def test_back(self):
        page = _setup_mock_page()
        page.go_back = AsyncMock()
        browser.back()
        page.go_back.assert_called_once()

    def test_forward(self):
        page = _setup_mock_page()
        page.go_forward = AsyncMock()
        browser.forward()
        page.go_forward.assert_called_once()

    def test_reload(self):
        page = _setup_mock_page()
        page.reload = AsyncMock()
        browser.reload()
        page.reload.assert_called_once()

    def test_check_checkbox(self):
        page = _setup_mock_page()
        page.check = AsyncMock()
        browser.check("#cb")
        page.check.assert_called_once_with("#cb")

    def test_uncheck_checkbox(self):
        page = _setup_mock_page()
        page.uncheck = AsyncMock()
        browser.uncheck("#cb")
        page.uncheck.assert_called_once_with("#cb")

    def test_upload(self):
        page = _setup_mock_page()
        page.set_input_files = AsyncMock()
        browser.upload("#file", "/path/to/file.pdf")
        page.set_input_files.assert_called_once_with("#file", "/path/to/file.pdf")


class TestGetTable:
    def test_get_table_success(self):
        page = _setup_mock_page()
        page.evaluate = AsyncMock(return_value=[
            {"Name": "Alice", "Age": "30"},
            {"Name": "Bob", "Age": "25"},
        ])

        result = browser.get_table("table#data")
        assert len(result) == 2
        assert result[0]["Name"] == "Alice"

    def test_get_table_not_found(self):
        page = _setup_mock_page()
        page.evaluate = AsyncMock(return_value=None)

        with pytest.raises(ElementNotFoundError):
            browser.get_table("table#missing")


class TestClose:
    def test_close_resets_state(self):
        page = _setup_mock_page()
        browser._browser.close = AsyncMock()
        browser._pw.stop = AsyncMock()

        browser.close()
        assert browser._page is None
        assert browser._browser is None
        assert browser._pw is None
