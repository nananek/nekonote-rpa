"""Tests for nekonote.pdf (mocked pdfplumber)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from nekonote.errors import FileNotFoundError


class TestPdfReadText:
    @patch("pdfplumber.open")
    def test_read_all_pages(self, mock_open, tmp_path):
        # Create a dummy file so existence check passes
        f = tmp_path / "doc.pdf"
        f.write_bytes(b"%PDF-1.4")

        page1, page2 = MagicMock(), MagicMock()
        page1.extract_text.return_value = "Page 1 text"
        page2.extract_text.return_value = "Page 2 text"

        mock_pdf = MagicMock()
        mock_pdf.pages = [page1, page2]
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        mock_open.return_value = mock_pdf

        from nekonote import pdf
        result = pdf.read_text(str(f))
        assert "Page 1 text" in result
        assert "Page 2 text" in result

    @patch("pdfplumber.open")
    def test_read_specific_pages(self, mock_open, tmp_path):
        f = tmp_path / "doc.pdf"
        f.write_bytes(b"%PDF-1.4")

        page0, page1 = MagicMock(), MagicMock()
        page0.extract_text.return_value = "First"
        page1.extract_text.return_value = "Second"

        mock_pdf = MagicMock()
        mock_pdf.pages = [page0, page1]
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        mock_open.return_value = mock_pdf

        from nekonote import pdf
        result = pdf.read_text(str(f), pages=[1])
        assert "Second" in result
        assert "First" not in result

    def test_read_not_found(self, tmp_path):
        from nekonote import pdf
        with pytest.raises(FileNotFoundError):
            pdf.read_text(str(tmp_path / "missing.pdf"))


class TestPdfReadTables:
    @patch("pdfplumber.open")
    def test_extract_table(self, mock_open, tmp_path):
        f = tmp_path / "table.pdf"
        f.write_bytes(b"%PDF-1.4")

        page = MagicMock()
        page.extract_tables.return_value = [
            [["Name", "Age"], ["Alice", "30"], ["Bob", "25"]]
        ]

        mock_pdf = MagicMock()
        mock_pdf.pages = [page]
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        mock_open.return_value = mock_pdf

        from nekonote import pdf
        tables = pdf.read_tables(str(f))
        assert len(tables) == 1
        assert tables[0][0]["Name"] == "Alice"
        assert tables[0][1]["Age"] == "25"


class TestPdfGetInfo:
    @patch("pdfplumber.open")
    def test_get_info(self, mock_open, tmp_path):
        f = tmp_path / "info.pdf"
        f.write_bytes(b"%PDF-1.4")

        mock_pdf = MagicMock()
        mock_pdf.pages = [MagicMock(), MagicMock(), MagicMock()]
        mock_pdf.metadata = {"Author": "Test"}
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=False)
        mock_open.return_value = mock_pdf

        from nekonote import pdf
        info = pdf.get_info(str(f))
        assert info["pages"] == 3
        assert info["metadata"]["Author"] == "Test"
