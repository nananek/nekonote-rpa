"""OCR (optical character recognition) for nekonote scripts.

Usage::

    from nekonote import ocr

    text = ocr.read("screenshot.png")
    text = ocr.read_screen(region=(100, 200, 300, 50))
"""

from __future__ import annotations

import base64
import io
from typing import Any


def read(path: str, *, lang: str = "jpn+eng", region: tuple[int, int, int, int] | None = None) -> str:
    """Extract text from an image file using Tesseract OCR.

    Args:
        path: Path to the image file.
        lang: Tesseract language code (default: "jpn+eng").
        region: Optional (x, y, width, height) to crop before OCR.
    """
    import pytesseract
    from PIL import Image

    img = Image.open(path)
    if region:
        x, y, w, h = region
        img = img.crop((x, y, x + w, y + h))
    return pytesseract.image_to_string(img, lang=lang).strip()


def read_screen(*, region: tuple[int, int, int, int] | None = None, lang: str = "jpn+eng") -> str:
    """Take a screenshot and extract text via OCR.

    Args:
        region: Optional (x, y, width, height) to capture.
        lang: Tesseract language code.
    """
    import pyautogui
    import pytesseract

    img = pyautogui.screenshot(region=region)
    return pytesseract.image_to_string(img, lang=lang).strip()


def read_blocks(path: str, *, lang: str = "jpn+eng") -> list[dict[str, Any]]:
    """Extract text blocks with position and confidence.

    Returns list of dicts: text, confidence, bbox (x, y, w, h).
    """
    import pytesseract
    from PIL import Image

    img = Image.open(path)
    data = pytesseract.image_to_data(img, lang=lang, output_type=pytesseract.Output.DICT)

    blocks = []
    for i in range(len(data["text"])):
        text = data["text"][i].strip()
        conf = int(data["conf"][i])
        if text and conf > 0:
            blocks.append({
                "text": text,
                "confidence": conf / 100.0,
                "bbox": (data["left"][i], data["top"][i], data["width"][i], data["height"][i]),
            })
    return blocks
