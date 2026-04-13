"""Tests for iframe auto-search in browser API."""

from unittest.mock import AsyncMock, MagicMock

import pytest

import nekonote.browser as browser


def _setup_page_with_frames(main_found=False, iframe_found=True):
    """Set up a mocked page with main frame + iframe."""
    # Top-level locator — not found
    top_loc = AsyncMock()
    top_loc.wait_for = AsyncMock(side_effect=Exception("timeout") if not main_found else None)
    top_loc.count = AsyncMock(return_value=0 if not main_found else 1)
    top_loc.first = AsyncMock()
    top_loc.first.click = AsyncMock()

    # Iframe locator — found
    iframe_loc = AsyncMock()
    iframe_loc.count = AsyncMock(return_value=1 if iframe_found else 0)
    iframe_loc.first = AsyncMock()
    iframe_loc.first.click = AsyncMock()

    iframe = MagicMock()
    iframe.locator = MagicMock(return_value=iframe_loc)
    iframe.child_frames = []

    page = AsyncMock()
    page.locator = MagicMock(return_value=top_loc)
    page.url = "https://example.com"
    page.title = AsyncMock(return_value="Test")
    page.main_frame = MagicMock()
    page.frames = [page.main_frame, iframe]

    browser._pw = MagicMock()
    browser._browser = MagicMock()
    browser._context = MagicMock()
    browser._page = page

    return page, top_loc, iframe_loc


class TestIframeAutoSearch:
    def test_click_finds_in_iframe(self):
        page, top_loc, iframe_loc = _setup_page_with_frames()
        browser.click("#btn")
        # Should have clicked via iframe locator, not top
        iframe_loc.first.click.assert_called_once()

    def test_type_finds_in_iframe(self):
        page, top_loc, iframe_loc = _setup_page_with_frames()
        iframe_loc.first.fill = AsyncMock()
        browser.type("#input", "hello")
        iframe_loc.first.fill.assert_called_once()

    def test_click_not_found_anywhere(self):
        from nekonote.errors import ElementNotFoundError

        page, top_loc, iframe_loc = _setup_page_with_frames(main_found=False, iframe_found=False)
        page.evaluate = AsyncMock(return_value=[])
        # After exhaustive search, wait_for on top with full timeout will also fail
        top_loc.wait_for = AsyncMock(side_effect=Exception("timeout waiting for locator"))

        with pytest.raises(ElementNotFoundError) as exc_info:
            browser.click("#missing", timeout=100)
        err = exc_info.value
        assert err.context.get("iframe_count") == 1


class TestPageInfoFrames:
    def test_get_page_info_includes_frames(self):
        page = AsyncMock()
        page.evaluate = AsyncMock(return_value={
            "url": "https://example.com",
            "title": "Test",
            "clickable": [],
            "inputs": [],
            "tables": [],
        })
        iframe = MagicMock()
        iframe.url = "https://example.com/frame"
        iframe.name = "payment"
        iframe.parent_frame = MagicMock(url="https://example.com")

        page.main_frame = MagicMock()
        page.frames = [page.main_frame, iframe]

        browser._page = page
        browser._pw = MagicMock()
        browser._browser = MagicMock()
        browser._context = MagicMock()

        info = browser.get_page_info()
        assert "frames" in info
        assert len(info["frames"]) == 1
        assert info["frames"][0]["name"] == "payment"
