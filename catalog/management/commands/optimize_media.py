"""
Compress product, category and library images for fast page loads while
keeping visual quality.

Usage:
  python manage.py optimize_media
"""

from __future__ import annotations

from django.core.management.base import BaseCommand

from catalog.image_utils import compress_field_file
from catalog.models import Category, MediaAsset, ProductImage


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
                if not f or not f.name:
                    continue
                obj._skip_image_optimize = True
                if compress_field_file(f):
                    update = [field]
                    if hasattr(obj, "updated_at"):
                        update.append("updated_at")
                    obj.save(update_fields=update)
                    total += 1
        self.stdout.write(self.style.SUCCESS(f"Optimized {total} image(s)."))
