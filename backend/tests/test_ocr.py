"""Tests for nekonote.ocr (mocked pytesseract)."""

from unittest.mock import patch, MagicMock

import pytest


class TestOcrRead:
    @pytest.fixture(autouse=True)
    def _check_deps(self):
        pytest.importorskip("pytesseract")

    @patch("pytesseract.image_to_string", return_value="Hello World")
    @patch("PIL.Image.open")
    def test_read_basic(self, mock_open, mock_ocr, tmp_path):
        f = tmp_path / "test.png"
        f.write_bytes(b"PNG")
        mock_open.return_value = MagicMock()

        from nekonote import ocr
        result = ocr.read(str(f))
        assert result == "Hello World"
        mock_ocr.assert_called_once()

    @patch("pytesseract.image_to_string", return_value="Cropped")
    @patch("PIL.Image.open")
    def test_read_with_region(self, mock_open, mock_ocr, tmp_path):
        f = tmp_path / "test.png"
        f.write_bytes(b"PNG")
        mock_img = MagicMock()
        mock_img.crop.return_value = mock_img
        mock_open.return_value = mock_img

        from nekonote import ocr
        result = ocr.read(str(f), region=(10, 20, 100, 50))
        assert result == "Cropped"
        mock_img.crop.assert_called_once_with((10, 20, 110, 70))
