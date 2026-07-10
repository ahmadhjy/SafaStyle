"""
Prepare the storefront for launch:
  1. Merge duplicate categories
  2. Import 10 products from safastyle.com (fresh)
  3. Assign a representative image to every active category
  4. Deactivate empty / legacy categories
  5. Optimize uploaded media

Usage:
  python manage.py prepare_launch
  python manage.py prepare_launch --skip-import
"""

from __future__ import annotations

import io
from collections import defaultdict

from django.core.files.base import ContentFile
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db.models import Count
from django.utils.text import slugify

from catalog.models import Category, Product, ProductImage


class Command(BaseCommand):
    help = "Clean categories, import 10 products, set category images, optimize media"

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-import",
            action="store_true",
            help="Skip WooCommerce import (only clean categories + images)",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=10,
            help="Number of products to import (default 10)",
        )

    def handle(self, *args, **options):
        merged = self._merge_duplicate_categories()
        self.stdout.write(f"Merged {merged} duplicate categor{'y' if merged == 1 else 'ies'}")

        if not options["skip_import"]:
            from django.conf import settings as dj_settings

            base_url = dj_settings.WOO_BASE_URL
            call_command(
                "import_woocommerce",
                fresh=True,
                limit=options["limit"],
                base_url=base_url,
            )

        if Product.objects.count() == 0:
            self.stdout.write(self.style.WARNING("No products from import — seeding 5 demo products."))
            call_command("seed_launch_catalog")

        assigned = self._assign_category_images()
        self.stdout.write(f"Set images on {assigned} categor{'y' if assigned == 1 else 'ies'}")

        deactivated = self._deactivate_empty_categories()
        self.stdout.write(f"Deactivated {deactivated} empty categor{'y' if deactivated == 1 else 'ies'}")

        call_command("optimize_media")
        self.stdout.write(self.style.SUCCESS("Launch catalog is ready."))

    def _merge_duplicate_categories(self) -> int:
        """Keep the oldest row per slugified name; move products then delete dupes."""
        buckets: dict[str, list[Category]] = defaultdict(list)
        for cat in Category.objects.all().order_by("id"):
            key = slugify(cat.name) or cat.slug
            buckets[key].append(cat)

        merged = 0
        for cats in buckets.values():
            if len(cats) < 2:
                continue
            canonical = cats[0]
            for dup in cats[1:]:
                for product in Product.objects.filter(categories=dup):
                    product.categories.add(canonical)
                    product.categories.remove(dup)
                dup.delete()
                merged += 1
        return merged

    def _assign_category_images(self) -> int:
        assigned = 0
        for cat in Category.objects.filter(is_active=True):
            if cat.image:
                continue
            img = (
                ProductImage.objects.filter(
                    product__categories=cat,
                    product__is_active=True,
                    color__isnull=True,
                )
                .select_related("product")
                .order_by("sort_order", "id")
                .first()
            )
            if not img:
                img = (
                    ProductImage.objects.filter(
                        product__categories=cat, product__is_active=True
                    )
                    .order_by("sort_order", "id")
                    .first()
                )
            if not img or not img.image:
                continue
            try:
                with img.image.open("rb") as fh:
                    data = fh.read()
                name = img.image.name.rsplit("/", 1)[-1]
                cat.image.save(name, ContentFile(data), save=True)
                assigned += 1
            except Exception as exc:
                self.stderr.write(f"  category image fail {cat.name}: {exc}")
        return assigned

    def _deactivate_empty_categories(self) -> int:
        if Product.objects.filter(is_active=True).count() == 0:
            return 0
        qs = (
            Category.objects.annotate(product_count=Count("products", distinct=True))
            .filter(product_count=0, is_active=True)
        )
        count = qs.count()
        qs.update(is_active=False)
        return count
