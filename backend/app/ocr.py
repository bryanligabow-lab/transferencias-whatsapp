"""OCR local con Tesseract. No consume tokens de ninguna API externa."""

from __future__ import annotations

import io

import pytesseract
from PIL import Image, ImageFilter, ImageOps

from .config import settings

pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd


def _preprocess(img: Image.Image) -> Image.Image:
    """Mejora básica para OCR: escala de grises, autocontraste y nitidez."""
    img = img.convert("L")
    img = ImageOps.autocontrast(img)
    # Escalar imágenes pequeñas para mejorar reconocimiento
    if img.width < 1000:
        ratio = 1000 / img.width
        img = img.resize((int(img.width * ratio), int(img.height * ratio)))
    img = img.filter(ImageFilter.SHARPEN)
    return img


def image_to_text(image_bytes: bytes) -> str:
    img = Image.open(io.BytesIO(image_bytes))
    img = _preprocess(img)
    text = pytesseract.image_to_string(img, lang=settings.tesseract_lang)
    return text


def ocr_confidence(image_bytes: bytes) -> float:
    """Confianza media (0-100) de las palabras reconocidas por Tesseract."""
    img = Image.open(io.BytesIO(image_bytes))
    img = _preprocess(img)
    data = pytesseract.image_to_data(
        img, lang=settings.tesseract_lang, output_type=pytesseract.Output.DICT
    )
    confs = [int(c) for c in data.get("conf", []) if str(c).lstrip("-").isdigit() and int(c) >= 0]
    if not confs:
        return 0.0
    return sum(confs) / len(confs)
