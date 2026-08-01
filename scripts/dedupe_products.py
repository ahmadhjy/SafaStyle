"""Remove empty duplicate products (same slugified name, 0 variations)."""
import os
import sys

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.utils.text import slugify  # noqa: E402

from catalog.models import Product  # noqa: E402

removed = 0
for product in Product.objects.prefetch_related("variations").order_by("id"):
    if product.variations.exists():
        continue
    norm = slugify(product.name)
    for other in Product.objects.exclude(pk=product.pk).prefetch_related("variations"):
        if slugify(other.name) == norm and other.variations.exists():
            print(f"Removing duplicate #{product.pk} {product.name!r} (keeping #{other.pk})")
            product.delete()
            removed += 1
            break

print(f"Done — removed {removed} duplicate(s).")
