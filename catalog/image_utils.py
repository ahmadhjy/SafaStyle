"""Compress uploaded images for faster storefront loads while keeping quality."""

from __future__ import annotations

import io
from pathlib import Path

from django.core.files.base import ContentFile
from PIL import Image, ImageOps

MAX_WIDTH = 1600
JPEG_QUALITY = 82
WEBP_QUALITY = 80


def optimize_image_file(uploaded_file):
    """Return (ContentFile, filename) or None if optimization is not needed/possible."""
    if not uploaded_file:
        return None
    try:
        uploaded_file.seek(0)
        img = Image.open(uploaded_file)
        img = ImageOps.exif_transpose(img)
    except Exception:
        try:
            uploaded_file.seek(0)
        except Exception:
            pass
        return None

    if img.mode in ("RGBA", "P", "LA"):
        img = img.convert("RGBA")
        has_alpha = True
    else:
        img = img.convert("RGB")
        has_alpha = False

    w, h = img.size
    if w > MAX_WIDTH:
        ratio = MAX_WIDTH / float(w)
        img = img.resize((MAX_WIDTH, max(1, int(h * ratio))), Image.Resampling.LANCZOS)

    buf = io.BytesIO()
    original_name = getattr(uploaded_file, "name", "image.jpg") or "image.jpg"
    stem = Path(original_name).stem[:80] or "image"
    if has_alpha:
        img.save(buf, format="WEBP", quality=WEBP_QUALITY, method=4)
        out_name = f"{stem}.webp"
    else:
        img.save(buf, format="JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)
        out_name = f"{stem}.jpg"

    data = buf.getvalue()
    try:
        original_size = uploaded_file.size
    except Exception:
        original_size = None
    # Keep original only when already smaller and within size budget.
    if original_size and len(data) >= original_size and w <= MAX_WIDTH:
        try:
            uploaded_file.seek(0)
        except Exception:
            pass
        return None

    try:
        uploaded_file.seek(0)
    except Exception:
        pass
    return ContentFile(data), out_name


def compress_field_file(field_file):
    """Optimize an already-saved ImageField in place. Returns True if rewritten."""
    if not field_file or not field_file.name:
        return False
    try:
        with field_file.open("rb") as fh:
            result = optimize_image_file(fh)
    except Exception:
        return False
    if not result:
        return False
    content, name = result
    field_file.save(name, content, save=False)
    return True
