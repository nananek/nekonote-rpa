"""Tests for nekonote.dialog (mocked PowerShell)."""

from unittest.mock import patch, MagicMock

from nekonote import dialog


class TestDialog:
    @patch("nekonote.dialog.subprocess.run")
    def test_show_message(self, mock_run):
        mock_run.return_value = MagicMock(stdout="OK", returncode=0)
        dialog.show_message("Hello")
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert "powershell" in cmd[0].lower()

    @patch("nekonote.dialog.subprocess.run")
    def test_confirm_yes(self, mock_run):
        mock_run.return_value = MagicMock(stdout="Yes", returncode=0)
        assert dialog.confirm("Continue?") is True

    @patch("nekonote.dialog.subprocess.run")
    def test_confirm_no(self, mock_run):
        mock_run.return_value = MagicMock(stdout="No", returncode=0)
        assert dialog.confirm("Continue?") is False

    @patch("nekonote.dialog.subprocess.run")
    def test_input(self, mock_run):
        mock_run.return_value = MagicMock(stdout="Taro", returncode=0)
        assert dialog.input("Name:") == "Taro"

    @patch("nekonote.dialog.subprocess.run")
    def test_input_cancel(self, mock_run):
        mock_run.return_value = MagicMock(stdout="::CANCEL::", returncode=0)
        assert dialog.input("Name:") is None

    @patch("nekonote.dialog.subprocess.run")
    def test_open_file(self, mock_run):
        mock_run.return_value = MagicMock(stdout="C:\\test.xlsx", returncode=0)
        assert dialog.open_file() == "C:\\test.xlsx"

    @patch("nekonote.dialog.subprocess.run")
    def test_open_file_cancel(self, mock_run):
        mock_run.return_value = MagicMock(stdout="::CANCEL::", returncode=0)
        assert dialog.open_file() is None

    @patch("nekonote.dialog.subprocess.run")
    def test_select_folder(self, mock_run):
        mock_run.return_value = MagicMock(stdout="C:\\Users\\test", returncode=0)
        assert dialog.select_folder() == "C:\\Users\\test"
