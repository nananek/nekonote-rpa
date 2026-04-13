"""Tests for desktop extensions (process mgmt + uitree integration)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from nekonote import desktop
from nekonote.errors import WindowNotFoundError, XPathNoMatchError


class TestProcessManagement:
    @patch("subprocess.Popen")
    def test_start_process(self, mock_popen):
        mock_popen.return_value = MagicMock(pid=1234)
        pid = desktop.start_process("notepad.exe")
        assert pid == 1234

    @patch("subprocess.Popen")
    def test_start_process_with_args(self, mock_popen):
        mock_popen.return_value = MagicMock(pid=5678)
        desktop.start_process("app.exe", args=["--flag", "value"])
        mock_popen.assert_called_once_with(["app.exe", "--flag", "value"])

    @patch("subprocess.run")
    def test_kill_process_by_pid(self, mock_run):
        desktop.kill_process(pid=1234)
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "/PID" in args
        assert "1234" in args

    @patch("subprocess.run")
    def test_kill_process_by_name(self, mock_run):
        desktop.kill_process(name="notepad.exe")
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "/IM" in args
        assert "notepad.exe" in args


class TestUiTreeIntegration:
    """Tests for uitree-based UI element operations (mocked)."""

    def _mock_uitree(self):
        """Create a mock UITree with a window containing buttons."""
        mock_element = MagicMock()
        mock_element.tag = "ButtonControl"
        mock_element.attrib = {"name": "OK", "automation_id": "btnOK", "class": "Button"}
        mock_element.control = MagicMock()

        mock_win = MagicMock()
        mock_win.tag = "WindowControl"
        mock_win.attrib = {"name": "Test App"}
        mock_win._element = MagicMock()
        mock_win.xpath.return_value = [mock_element]

        mock_tree = MagicMock()
        mock_tree.xpath.return_value = [mock_win]
        mock_tree.dumpxml.return_value = "<root/>"
        return mock_tree, mock_win, mock_element

    @patch("uitree.UITree")
    def test_find_elements(self, MockTree):
        tree, win, btn = self._mock_uitree()
        MockTree.return_value = tree

        results = desktop.find_elements(title="Test", xpath='.//ButtonControl')
        assert len(results) == 1
        assert results[0]["tag"] == "ButtonControl"
        assert results[0]["name"] == "OK"

    @patch("uitree.UITree")
    def test_find_elements_window_not_found(self, MockTree):
        mock_tree = MagicMock()
        mock_tree.xpath.return_value = []
        MockTree.return_value = mock_tree

        with pytest.raises(WindowNotFoundError):
            desktop.find_elements(title="Missing", xpath='.//Button')

    @patch("uitree.UITree")
    def test_find_element_not_found(self, MockTree):
        mock_win = MagicMock()
        mock_win.xpath.return_value = []
        mock_tree = MagicMock()
        mock_tree.xpath.return_value = [mock_win]
        MockTree.return_value = mock_tree

        with pytest.raises(XPathNoMatchError):
            desktop.find_element(title="Test", xpath='.//Missing')

    @patch("uitree.UITree")
    def test_click_element(self, MockTree):
        tree, win, btn = self._mock_uitree()
        MockTree.return_value = tree

        desktop.click_element(title="Test", xpath='.//ButtonControl')
        btn.control.Click.assert_called_once()

    @patch("uitree.UITree")
    def test_get_element_value(self, MockTree):
        tree, win, elem = self._mock_uitree()
        elem.control.GetValuePattern.return_value.Value = "hello"
        MockTree.return_value = tree

        value = desktop.get_element_value(title="Test", xpath='.//Edit')
        assert value == "hello"

    @patch("uitree.UITree")
    def test_get_ui_tree_xml(self, MockTree):
        from lxml import etree

        xml_elem = etree.Element("WindowControl", name="Test App")
        etree.SubElement(xml_elem, "ButtonControl", name="OK")

        mock_win = MagicMock()
        mock_win._element = xml_elem
        mock_tree = MagicMock()
        mock_tree.xpath.return_value = [mock_win]
        MockTree.return_value = mock_tree

        xml = desktop.get_ui_tree(title="Test")
        assert "WindowControl" in xml
        assert "ButtonControl" in xml


class TestBrowserDialogs:
    """Tests for browser dialog extensions."""

    def test_accept_dialog(self):
        from unittest.mock import AsyncMock
        import nekonote.browser as browser

        page = AsyncMock()
        browser._pw = MagicMock()
        browser._browser = MagicMock()
        browser._context = MagicMock()
        browser._page = page

        browser.accept_dialog("yes")
        page.once.assert_called_once()
        assert page.once.call_args[0][0] == "dialog"

    def test_dismiss_dialog(self):
        from unittest.mock import AsyncMock
        import nekonote.browser as browser

        page = AsyncMock()
        browser._pw = MagicMock()
        browser._browser = MagicMock()
        browser._context = MagicMock()
        browser._page = page

        browser.dismiss_dialog()
        page.once.assert_called_once()
        assert page.once.call_args[0][0] == "dialog"
