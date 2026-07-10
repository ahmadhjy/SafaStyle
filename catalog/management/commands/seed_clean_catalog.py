"""
Reset the catalog for a clean start: wipe products, seed categories with
generated images, and load a full color + size palette.

Usage:
  python manage.py seed_clean_catalog
  python manage.py seed_clean_catalog --keep-products
  python manage.py seed_clean_catalog --skip-images
"""

from __future__ import annotations

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.text import slugify

from catalog.category_art import render_category_image
from catalog.models import Category, Color, Product, ProductImage, ProductVariation, Size

# Categories from the original Safa Style WooCommerce store.
CATEGORY_DEFS = (
    ("Accessories", "accessories"),
    ("Bags", "bags"),
    ("Basics", "basics"),
    ("Cardigans", "cardigans"),
    ("Coats", "coats"),
    ("Dresses", "dresses"),
    ("Jackets", "jackets"),
    ("Pants", "pants"),
    ("Ramadan Specials", "ramadan-specials"),
    ("Scarfs", "scarfs"),
    ("Sets", "sets"),
    ("Shawls", "shawls"),
    ("Shoes", "shoes"),
    ("Skirts", "skirts"),
    ("Socks", "socks"),
    ("Tops", "tops"),
    ("Vests", "vests"),
)

FEATURED_SLUGS = {
    "sets",
    "bags",
    "dresses",
    "tops",
    "ramadan-specials",
    "coats",
    "pants",
    "shoes",
}

COLOR_DEFS = [
    ("Black", "#111111"),
    ("White", "#f5f5f5"),
    ("Off White", "#f3efe6"),
    ("Ivory", "#fffff0"),
    ("Cream", "#f5f0e6"),
    ("Beige", "#d7c4a8"),
    ("Sand", "#d2b48c"),
    ("Camel", "#c19a6b"),
    ("Taupe", "#8b7d72"),
    ("Nude", "#e3bc9a"),
    ("Brown", "#6b4a2e"),
    ("Mocha", "#7b5e57"),
    ("Chocolate", "#3d2314"),
    ("Burgundy", "#6e1f2b"),
    ("Wine", "#722f37"),
    ("Maroon", "#5c1a1a"),
    ("Red", "#8b0000"),
    ("Rust", "#b7410e"),
    ("Coral", "#e07a5f"),
    ("Peach", "#ffcba4"),
    ("Orange", "#e8753a"),
    ("Pink", "#e8a0b0"),
    ("Rose", "#c4868b"),
    ("Dusty Pink", "#d4a5a5"),
    ("Blush", "#f2c6c2"),
    ("Lavender", "#b8a9c9"),
    ("Lilac", "#c8a2c8"),
    ("Plum", "#5c2e5c"),
    ("Purple", "#6b3fa0"),
    ("Navy Blue", "#1b2a4a"),
    ("Royal Blue", "#1e3a8a"),
    ("Blue", "#2f4f8e"),
    ("Light Blue", "#a8c8e8"),
    ("Sky Blue", "#87ceeb"),
    ("Gray", "#8a8a8a"),
    ("Light Grey", "#c8c8c8"),
    ("Charcoal", "#36454f"),
    ("Silver", "#a8a8a8"),
    ("Olive Green", "#556b2f"),
    ("Forest Green", "#2d5016"),
    ("Emerald", "#046307"),
    ("Green", "#3d7a4a"),
    ("Mint Green", "#9fd3c0"),
    ("Sage", "#9caf88"),
    ("Teal", "#2fbfa8"),
    ("Khaki", "#c3b091"),
    ("Gold", "#c9a227"),
    ("Mustard", "#e1ad01"),
    ("Copper", "#b87333"),
    ("Yellow", "#f0d264"),
    ("Multicolor", "#cccccc"),
]

# Clothing, shoes, kids, and one-size accessories.
SIZE_DEFS = [
    "XXS",
    "XS",
    "S",
    "M",
    "L",
    "XL",
    "XXL",
    "3XL",
    "1",
    "2",
    "3",
    "4",
    "5",
    "34",
    "36",
    "37",
    "38",
    "39",
    "40",
    "41",
    "42",
    "43",
    "44",
    "46",
    "One Size",
]


class Command(BaseCommand):
    help = "Wipe products and seed categories (with images), colors, and sizes"

    def add_arguments(self, parser):
        parser.add_argument(
            "--keep-products",
            action="store_true",
            help="Do not delete existing products",
        )
        parser.add_argument(
            "--skip-images",
            action="store_true",
            help="Skip regenerating category images",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        keep_products = options["keep_products"]
        skip_images = options["skip_images"]

        if not keep_products:
            img_count = ProductImage.objects.count()
            var_count = ProductVariation.objects.count()
            prod_count = Product.objects.count()
            Product.objects.all().delete()
            self.stdout.write(
                f"Removed {prod_count} product(s), {var_count} variation(s), {img_count} image(s)"
            )
        else:
            self.stdout.write("Keeping existing products")

        color_count = self._seed_colors()
        size_count = self._seed_sizes()
        self.stdout.write(f"Seeded {color_count} colors and {size_count} sizes")

        cat_count, img_assigned = self._seed_categories(skip_images=skip_images)
        self.stdout.write(
            self.style.SUCCESS(
                f"Ready — {cat_count} categories ({img_assigned} images). Add products in admin."
            )
        )

    def _seed_colors(self) -> int:
        seen_slugs: set[str] = set()
        for i, (name, hex_code) in enumerate(COLOR_DEFS):
            slug = slugify(name)
            if slug in seen_slugs:
                slug = f"{slug}-{i}"
            seen_slugs.add(slug)
            Color.objects.update_or_create(
                slug=slug,
                defaults={"name": name, "hex_code": hex_code, "sort_order": i},
            )
        return len(COLOR_DEFS)

    def _seed_sizes(self) -> int:
        seen_slugs: set[str] = set()
        order = 0
        for name in SIZE_DEFS:
            slug = slugify(name)
            if slug in seen_slugs:
                slug = f"{slug}-{order}"
            seen_slugs.add(slug)
            Size.objects.update_or_create(
                slug=slug,
                defaults={"name": name, "sort_order": order},
            )
            order += 1
        return order

    def _seed_categories(self, *, skip_images: bool) -> tuple[int, int]:
        canonical_slugs = {slug for _, slug in CATEGORY_DEFS}
        removed = (
            Category.objects.exclude(slug__in=canonical_slugs).delete()[0]
            if not Product.objects.exists()
            else 0
        )
        if removed:
            self.stdout.write(f"Removed {removed} legacy categor{'y' if removed == 1 else 'ies'}")
        elif Category.objects.exclude(slug__in=canonical_slugs).exists():
            self.stdout.write(
                self.style.WARNING(
                    "Legacy categories remain (products still exist). "
                    "Run without --keep-products to remove them."
                )
            )

        img_assigned = 0
        for i, (name, slug) in enumerate(CATEGORY_DEFS):
            category, _ = Category.objects.update_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "is_active": True,
                    "is_featured": slug in FEATURED_SLUGS,
                    "sort_order": i,
                },
            )
            updates = {}
            if category.name != name:
                updates["name"] = name
            if category.sort_order != i:
                updates["sort_order"] = i
            if category.is_featured != (slug in FEATURED_SLUGS):
                updates["is_featured"] = slug in FEATURED_SLUGS
            if not category.is_active:
                updates["is_active"] = True
            if updates:
                for key, value in updates.items():
                    setattr(category, key, value)
                category.save(update_fields=list(updates.keys()))

            if skip_images:
                continue
            data = render_category_image(slug, name)
            filename = f"{slug}.jpg"
            category.image.save(filename, ContentFile(data), save=True)
            img_assigned += 1

        # Deactivate any leftover non-canonical categories when products were wiped.
        if not Product.objects.exists():
            Category.objects.exclude(slug__in=canonical_slugs).update(is_active=False)

        return len(CATEGORY_DEFS), img_assigned
