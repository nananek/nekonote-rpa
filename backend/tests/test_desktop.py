"""Tests for nekonote.desktop (mocked pyautogui)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from nekonote.errors import ElementNotFoundError, TimeoutError


class TestDesktopClick:
    @patch("pyautogui.click")
    def test_click_coordinates(self, mock_click):
        from nekonote import desktop

        result = desktop.click(x=100, y=200)
        assert result == {"x": 100, "y": 200}

    def test_click_no_args_raises(self):
        from nekonote import desktop

        with pytest.raises(ValueError, match="coordinates"):
            desktop.click()

    @patch("pyautogui.locateCenterOnScreen", return_value=MagicMock(x=50, y=60))
    @patch("pyautogui.click")
    def test_click_image_found(self, mock_click, mock_locate):
        from nekonote import desktop

        result = desktop.click(image="btn.png")
        assert result == {"x": 50, "y": 60}

    @patch("pyautogui.locateCenterOnScreen", return_value=None)
    def test_click_image_not_found(self, mock_locate):
        from nekonote import desktop

        with pytest.raises(ElementNotFoundError):
            desktop.click(image="missing.png")


class TestDesktopType:
    @patch("pyautogui.write")
    def test_type_ascii(self, mock_write):
        from nekonote import desktop

        desktop.type("hello")
        mock_write.assert_called_once_with("hello", interval=0.02)


class TestDesktopHotkey:
    @patch("pyautogui.hotkey")
    def test_hotkey(self, mock_hotkey):
        from nekonote import desktop

        desktop.hotkey("ctrl", "s")
        mock_hotkey.assert_called_once_with("ctrl", "s")


class TestDesktopPress:
    @patch("pyautogui.press")
    def test_press(self, mock_press):
        from nekonote import desktop

        desktop.press("enter")
        mock_press.assert_called_once_with("enter")


class TestDesktopMouseOps:
    @patch("pyautogui.doubleClick")
    def test_double_click(self, mock_dc):
        from nekonote import desktop

        desktop.double_click(10, 20)
        mock_dc.assert_called_once_with(10, 20)

    @patch("pyautogui.rightClick")
    def test_right_click(self, mock_rc):
        from nekonote import desktop

        desktop.right_click(10, 20)
        mock_rc.assert_called_once_with(10, 20)

    @patch("pyautogui.moveTo")
    def test_mouse_move(self, mock_move):
        from nekonote import desktop

        desktop.mouse_move(100, 200)
        mock_move.assert_called_once_with(100, 200)

    @patch("pyautogui.scroll")
    def test_scroll_down(self, mock_scroll):
        from nekonote import desktop

        desktop.scroll(direction="down", clicks=5)
        mock_scroll.assert_called_once_with(-5)

    @patch("pyautogui.scroll")
    def test_scroll_up(self, mock_scroll):
        from nekonote import desktop

        desktop.scroll(direction="up", clicks=3)
        mock_scroll.assert_called_once_with(3)


class TestDesktopScreenshot:
    @patch("pyautogui.screenshot")
    def test_screenshot_base64(self, mock_ss):
        from PIL import Image
        from nekonote import desktop

        img = Image.new("RGB", (10, 10), color="red")
        mock_ss.return_value = img

        result = desktop.screenshot()
        assert isinstance(result, str)
        assert len(result) > 10  # base64 encoded

    @patch("pyautogui.screenshot")
    def test_screenshot_to_file(self, mock_ss, tmp_path):
        from PIL import Image
        from nekonote import desktop

        img = Image.new("RGB", (10, 10), color="blue")
        mock_ss.return_value = img

        out = str(tmp_path / "shot.png")
        result = desktop.screenshot(path=out)
        assert result == out


class TestDesktopFindImage:
    @patch("pyautogui.locateCenterOnScreen", return_value=MagicMock(x=100, y=200))
    def test_found(self, mock_locate):
        from nekonote import desktop

        result = desktop.find_image("target.png")
        assert result["found"] is True
        assert result["x"] == 100

    @patch("pyautogui.locateCenterOnScreen", return_value=None)
    def test_not_found(self, mock_locate):
        from nekonote import desktop

        result = desktop.find_image("target.png")
        assert result["found"] is False


class TestDesktopScreenSize:
    @patch("pyautogui.size", return_value=MagicMock(width=1920, height=1080))
    def test_get_screen_size(self, mock_size):
        from nekonote import desktop

        w, h = desktop.get_screen_size()
        assert w == 1920
        assert h == 1080
