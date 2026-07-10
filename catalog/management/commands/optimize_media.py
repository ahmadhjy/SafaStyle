"""
Compress product, category and library images for fast page loads while
keeping visual quality.

Usage:
  python manage.py optimize_media
"""

from __future__ import annotations

import io
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from PIL import Image, ImageOps

from catalog.models import Category, MediaAsset, ProductImage

MAX_WIDTH = 1800
JPEG_QUALITY = 86
WEBP_QUALITY = 82


def _optimize_file(field_file) -> tuple[bytes, str] | None:
    if not field_file or not field_file.name:
        return None
    try:
        with field_file.open("rb") as fh:
            img = Image.open(fh)
            img = ImageOps.exif_transpose(img)
    except Exception:
        return None

    if img.mode in ("RGBA", "P", "LA"):
        img = img.convert("RGBA")
        has_alpha = True
    else:
        img = img.convert("RGB")
        has_alpha = False

    w, h = img.size
    if w > MAX_WIDTH:
        ratio = MAX_WIDTH / w
        img = img.resize((MAX_WIDTH, int(h * ratio)), Image.Resampling.LANCZOS)

    buf = io.BytesIO()
    stem = Path(field_file.name).stem
    if has_alpha:
        img.save(buf, format="WEBP", quality=WEBP_QUALITY, method=4)
        return buf.getvalue(), f"{stem}.webp"
    img.save(buf, format="JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)
    return buf.getvalue(), f"{stem}.jpg"


class Command(BaseCommand):
    help = "Optimize uploaded product/category/media images"

    def handle(self, *args, **options):
        total = 0
        for model, field in (
            (ProductImage, "image"),
            (Category, "image"),
            (MediaAsset, "file"),
        ):
            for obj in model.objects.all().iterator():
                f = getattr(obj, field)
                out = _optimize_file(f)
                if not out:
                    continue
                data, name = out
                if name.endswith(f.name.rsplit(".", 1)[-1].lower()) and len(data) >= f.size:
                    continue
                getattr(obj, field).save(name, ContentFile(data), save=False)
                obj.save(update_fields=[field, "updated_at"] if hasattr(obj, "updated_at") else [field])
                total += 1
        self.stdout.write(self.style.SUCCESS(f"Optimized {total} image(s)."))
