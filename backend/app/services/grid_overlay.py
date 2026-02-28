"""Draw a semi-transparent labelled grid over a menu image.

The grid gives GPT-4o Vision a visible coordinate reference frame so it can
return accurate x/y positions for each dish title.

Grid layout:
  - COLS columns numbered 0 .. COLS-1 along the top
  - ROWS rows   numbered 0 .. ROWS-1 along the left
  - Each cell centre maps to normalised coordinates:
      x_norm = (col + 0.5) / COLS
      y_norm = (row + 0.5) / ROWS
"""
from __future__ import annotations

import base64
import io

from PIL import Image, ImageDraw, ImageFont

GRID_COLS = 8
GRID_ROWS = 6


def overlay_grid(image_base64: str, mime_type: str) -> str:
    """Return a new base64-encoded image with a labelled grid overlay.

    The overlay is drawn with semi-transparent lines and small labels at
    each column/row so GPT can see the coordinate reference.
    """
    raw = base64.b64decode(image_base64)
    img = Image.open(io.BytesIO(raw)).convert("RGBA")
    w, h = img.size

    # Create a transparent overlay for the grid lines + labels
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    col_w = w / GRID_COLS
    row_h = h / GRID_ROWS

    # Semi-transparent white/grey for grid lines
    line_colour = (255, 255, 255, 90)
    label_fill = (255, 255, 255, 180)
    text_colour = (30, 30, 30, 220)

    # Try to get a reasonable font size (proportional to image)
    font_size = max(12, min(28, int(min(w, h) / 40)))
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except OSError:
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
        except OSError:
            font = ImageFont.load_default()

    # Draw vertical lines + column labels
    for col in range(GRID_COLS + 1):
        x = int(col * col_w)
        draw.line([(x, 0), (x, h)], fill=line_colour, width=1)

    # Draw horizontal lines + row labels
    for row in range(GRID_ROWS + 1):
        y = int(row * row_h)
        draw.line([(0, y), (w, y)], fill=line_colour, width=1)

    # Draw cell labels at centre of each cell
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            cx = int((col + 0.5) * col_w)
            cy = int((row + 0.5) * row_h)
            label = f"{col},{row}"
            bbox = font.getbbox(label)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            pad = 3
            # Draw a small rounded background for readability
            draw.rectangle(
                [cx - tw // 2 - pad, cy - th // 2 - pad,
                 cx + tw // 2 + pad, cy + th // 2 + pad],
                fill=label_fill,
            )
            draw.text((cx - tw // 2, cy - th // 2), label, fill=text_colour, font=font)

    # Composite overlay onto original image
    result = Image.alpha_composite(img, overlay).convert("RGB")

    buf = io.BytesIO()
    fmt = "JPEG" if "jpeg" in mime_type or "jpg" in mime_type else "PNG"
    result.save(buf, format=fmt, quality=90)
    return base64.b64encode(buf.getvalue()).decode("ascii")
