"""Tests for nekonote.window (mocked pywinauto)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from nekonote.errors import WindowNotFoundError
from nekonote.window import WindowInfo, find, find_all, exists, list_windows


def _mock_window(title="Test", handle=123, class_name="TestClass", visible=True):
    w = MagicMock()
    w.window_text.return_value = title
    w.handle = handle
    w.class_name.return_value = class_name
    w.process_id.return_value = 1000
    w.is_visible.return_value = visible
    rect = MagicMock()
    rect.left = 0
    rect.top = 0
    rect.width.return_value = 800
    rect.height.return_value = 600
    w.rectangle.return_value = rect
    return w


class TestWindowInfo:
    def test_to_dict(self):
        info = WindowInfo(title="Test", handle=123, class_name="Cls", pid=100)
        d = info.to_dict()
        assert d["title"] == "Test"
        assert d["handle"] == 123
        assert d["class_name"] == "Cls"
        assert d["pid"] == 100


class TestListWindows:
    @patch("pywinauto.Desktop")
    def test_list_visible(self, mock_desktop_cls):
        mock_desktop = MagicMock()
        mock_desktop.windows.return_value = [
            _mock_window("App1", 1, visible=True),
            _mock_window("App2", 2, visible=False),
            _mock_window("App3", 3, visible=True),
        ]
        mock_desktop_cls.return_value = mock_desktop

        result = list_windows(visible_only=True)
        assert len(result) == 2
        assert result[0].title == "App1"
        assert result[1].title == "App3"

    @patch("pywinauto.Desktop")
    def test_list_all(self, mock_desktop_cls):
        mock_desktop = MagicMock()
        mock_desktop.windows.return_value = [
            _mock_window("A", 1, visible=True),
            _mock_window("B", 2, visible=False),
        ]
        mock_desktop_cls.return_value = mock_desktop

        result = list_windows(visible_only=False)
        assert len(result) == 2


class TestFind:
    @patch("nekonote.window.list_windows")
    def test_find_by_title(self, mock_list):
        mock_list.return_value = [
            WindowInfo(title="メモ帳", handle=1),
            WindowInfo(title="Firefox", handle=2),
        ]
        result = find(title="メモ帳")
        assert result.handle == 1

    @patch("nekonote.window.list_windows")
    def test_find_partial_match(self, mock_list):
        mock_list.return_value = [
            WindowInfo(title="無題 - メモ帳", handle=1),
        ]
        result = find(title="メモ帳")
        assert result.handle == 1

    @patch("nekonote.window.list_windows")
    def test_find_not_found_with_context(self, mock_list):
        mock_list.return_value = [
            WindowInfo(title="Firefox", handle=1),
            WindowInfo(title="Chrome", handle=2),
        ]
        with pytest.raises(WindowNotFoundError) as exc_info:
            find(title="メモ帳")
        err = exc_info.value
        assert err.code == "WINDOW_NOT_FOUND"
        assert "Firefox" in err.suggestion or "Firefox" in str(err.context.get("open_windows", []))

    @patch("nekonote.window.list_windows")
    def test_find_by_class_name(self, mock_list):
        mock_list.return_value = [
            WindowInfo(title="A", handle=1, class_name="Notepad"),
        ]
        result = find(class_name="Notepad")
        assert result.handle == 1


class TestFindAll:
    @patch("nekonote.window.list_windows")
    def test_find_all_multiple(self, mock_list):
        mock_list.return_value = [
            WindowInfo(title="Doc1 - メモ帳", handle=1),
            WindowInfo(title="Doc2 - メモ帳", handle=2),
            WindowInfo(title="Firefox", handle=3),
        ]
        result = find_all(title="メモ帳")
        assert len(result) == 2


class TestExists:
    @patch("nekonote.window.list_windows")
    def test_exists_true(self, mock_list):
        mock_list.return_value = [WindowInfo(title="App", handle=1)]
        assert exists(title="App") is True

    @patch("nekonote.window.list_windows")
    def test_exists_false(self, mock_list):
        mock_list.return_value = []
        assert exists(title="Missing") is False
