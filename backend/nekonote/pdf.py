"""PDF text and table extraction for nekonote scripts.

Usage::

    from nekonote import pdf

    text = pdf.read_text("document.pdf")
    tables = pdf.read_tables("invoice.pdf")
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from nekonote.errors import FileNotFoundError as NkFileNotFoundError


def _require_file(path: str, action: str) -> Path:
    p = Path(path)
    if not p.is_file():
        nearby = [f.name for f in p.parent.iterdir()][:20] if p.parent.is_dir() else []
        raise NkFileNotFoundError(
            f"File not found: {path}",
            action=action,
            context={"path": str(p.resolve()), "nearby_files": nearby},
        )
    return p


def read_text(path: str, *, pages: list[int] | None = None) -> str:
    """Extract text from a PDF file.

    *pages* is 0-indexed. If None, extract all pages.
    """
    import pdfplumber

    _require_file(path, "pdf.read_text")
    texts: list[str] = []
    with pdfplumber.open(path) as pdf_doc:
        target_pages = pdf_doc.pages
        if pages is not None:
            target_pages = [pdf_doc.pages[i] for i in pages if i < len(pdf_doc.pages)]
        for page in target_pages:
            text = page.extract_text()
            if text:
                texts.append(text)
    return "\n".join(texts)


def read_tables(path: str, *, pages: list[int] | None = None) -> list[list[dict[str, str]]]:
    """Extract tables from a PDF file.

    Returns a list of tables, each table is a list of dicts (first row = headers).
    """
    import pdfplumber

    _require_file(path, "pdf.read_tables")
    all_tables: list[list[dict[str, str]]] = []
    with pdfplumber.open(path) as pdf_doc:
        target_pages = pdf_doc.pages
        if pages is not None:
            target_pages = [pdf_doc.pages[i] for i in pages if i < len(pdf_doc.pages)]
        for page in target_pages:
            tables = page.extract_tables()
            for table in tables:
                if not table or len(table) < 2:
                    continue
                headers = [str(c or f"col_{i}") for i, c in enumerate(table[0])]
                rows = []
                for row in table[1:]:
                    rows.append(dict(zip(headers, [str(c or "") for c in row])))
                all_tables.append(rows)
    return all_tables


def get_info(path: str) -> dict[str, Any]:
    """Get PDF metadata (page count, etc.)."""
    import pdfplumber

    _require_file(path, "pdf.get_info")
    with pdfplumber.open(path) as pdf_doc:
        return {
            "pages": len(pdf_doc.pages),
            "metadata": pdf_doc.metadata or {},
        }
