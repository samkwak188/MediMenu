"""Detect text regions in a menu image using EasyOCR.

Returns a list of {text, x, y} where x/y are normalised [0,1] centre
coordinates of each detected text string, ready for pin placement.
"""
from __future__ import annotations

import base64
import io
from difflib import SequenceMatcher

import easyocr

# Lazily initialised singleton reader (first call downloads ~60 MB model)
_READER: easyocr.Reader | None = None


def _get_reader() -> easyocr.Reader:
    global _READER
    if _READER is None:
        _READER = easyocr.Reader(["en"], gpu=False, verbose=False)
    return _READER


def detect_text_regions(image_base64: str) -> list[dict]:
    """Run EasyOCR on the image and return detected text regions.

    Each item: {"text": str, "x": float, "y": float}
    where x and y are normalised [0..1] centres of the bounding box.
    """
    raw = base64.b64decode(image_base64)
    reader = _get_reader()
    results = reader.readtext(io.BytesIO(raw).read())

    # Discover image dimensions from raw bytes (needed for normalisation)
    from PIL import Image
    img = Image.open(io.BytesIO(raw))
    w, h = img.size

    regions: list[dict] = []
    for bbox, text, _conf in results:
        # bbox is [[x1,y1],[x2,y2],[x3,y3],[x4,y4]] – four corners
        xs = [p[0] for p in bbox]
        ys = [p[1] for p in bbox]
        cx = ((min(xs) + max(xs)) / 2) / w  # normalised centre x
        cy = ((min(ys) + max(ys)) / 2) / h  # normalised centre y
        regions.append({"text": text.strip(), "x": cx, "y": cy})

    return regions


def _similarity(a: str, b: str) -> float:
    """Case-insensitive similarity ratio between two strings."""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def match_dishes_to_ocr(
    dishes: list[dict],
    ocr_regions: list[dict],
    threshold: float = 0.45,
) -> list[dict]:
    """Assign OCR-derived x,y coordinates to each dish via fuzzy matching.

    Mutates each dish dict in-place, updating dish["location"]["x"] and
    dish["location"]["y"] when a match is found.
    """
    # Build a pool of OCR regions that haven't been claimed yet
    available = list(range(len(ocr_regions)))

    for dish in dishes:
        dish_name = dish.get("dish", "").lower().strip()
        if not dish_name:
            continue

        best_idx = -1
        best_score = -1.0

        for idx in available:
            ocr_text = ocr_regions[idx]["text"]
            # Try matching the full dish name against the OCR text
            score = _similarity(dish_name, ocr_text)

            # Also try matching first word (handles "Cheese Burger" → "Cheese")
            first_word_score = _similarity(dish_name.split()[0], ocr_text)
            score = max(score, first_word_score * 0.85)

            # Also check if OCR text is contained in dish name or vice versa
            if ocr_text.lower() in dish_name or dish_name in ocr_text.lower():
                score = max(score, 0.75)

            if score > best_score:
                best_score = score
                best_idx = idx

        if best_idx >= 0 and best_score >= threshold:
            region = ocr_regions[best_idx]
            # Update the dish location with OCR-detected coordinates
            if dish.get("location") is None:
                dish["location"] = {"x": 0, "y": 0, "width": 0.1, "height": 0.05}
            dish["location"]["x"] = region["x"]
            dish["location"]["y"] = region["y"]
            # Remove from pool so it can't be matched again
            available.remove(best_idx)

    return dishes
