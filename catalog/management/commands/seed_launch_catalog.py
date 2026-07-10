"""
Seed 5 Safa demo products with distinct real photos (no duplicate ChatGPT shots).

Usage:
  python manage.py seed_launch_catalog
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from catalog.models import Category, Color, MediaAsset, Product, ProductImage, ProductVariation, Size

# Each product gets unique files — matches the Safa storefront screenshots.
PRODUCT_MEDIA: dict[str, list[str]] = {
    "new-linen-set": [
        "ChatGPT-Image-Feb-14-2026-03_06_52-PM_bnqgroA.png",
        "IMG_7441.png",
        "IMG_7442.png",
    ],
    "classy-linen-set": [
        "ChatGPT-Image-Feb-14-2026-03_06_52-PM_u23FbVX.png",
        "IMG_7521.png",
        "IMG_7504.png",
    ],
    "belted-wide-leg-pants": [
        "IMG_7358-2.png",
        "IMG_7360-1.png",
        "IMG_7361-1.png",
    ],
    "embroidered-abaya": [
        "IMG_1013-scaled.jpeg",
        "IMG_1015-scaled.jpeg",
        "IMG_0871-scaled.jpeg",
    ],
    "royal-gold-embroidered-abaya": [
        "IMG_1017-scaled.jpeg",
        "IMG_1023-scaled.jpeg",
        "IMG_1025-scaled.jpeg",
    ],
}

CATEGORY_COVER = {
    "sets": "new-linen-set",
    "dresses": "embroidered-abaya",
    "pants": "belted-wide-leg-pants",
}

CATALOG = [
    {
        "name": "Classy Linen Set",
        "category": "Sets",
        "price": "50.00",
        "sale": "25.00",
        "colors": ["Camel", "Beige", "Off White"],
        "sizes": ["1", "2", "3"],
        "short": "Refined linen co-ord with subtle detailing.",
        "desc": "An elevated take on our linen set — minimal, fresh, and easy to style for day or evening.",
    },
    {
        "name": "Belted Wide-Leg Pants",
        "category": "Pants",
        "price": "38.00",
        "sale": "29.00",
        "colors": ["Black", "Beige", "Brown"],
        "sizes": ["1", "2", "3"],
        "short": "High-waist wide-leg pant with matching belt.",
        "desc": "Flowing wide-leg pants with a removable belt. Pairs perfectly with our tops and blazers.",
    },
    {
        "name": "Embroidered Abaya",
        "category": "Dresses",
        "price": "50.00",
        "sale": None,
        "colors": ["Black", "Burgundy"],
        "sizes": ["1", "2", "3"],
        "short": "Delicate embroidery on premium crepe.",
        "desc": "A statement abaya with fine embroidery detailing. Fully lined for coverage and comfort.",
    },
    {
        "name": "Royal Gold Embroidered Abaya",
        "category": "Dresses",
        "price": "78.00",
        "sale": "70.00",
        "colors": ["Black", "Camel"],
        "sizes": ["1", "2", "3"],
        "short": "Gold-thread embroidery on flowing crepe.",
        "desc": "Elevated evening abaya with gold embroidery accents. Designed to drape beautifully with every step.",
    },
    {
        "name": "New Linen Set",
        "category": "Sets",
        "price": "45.00",
        "sale": "35.00",
        "colors": ["Black", "Beige", "Camel"],
        "sizes": ["1", "2", "3"],
        "short": "Relaxed linen co-ord with wide-leg pants.",
        "desc": "A breathable linen set designed for everyday modest dressing. Soft hand-feel and a clean silhouette.",
    },
]


class Command(BaseCommand):
    help = "Seed 5 demo products with distinct Safa photos"

    def handle(self, *args, **options):
        call_command("seed_store")
        ProductVariation.objects.all().delete()
        ProductImage.objects.all().delete()
        Product.objects.all().delete()
        MediaAsset.objects.all().delete()

        media_root = Path(settings.MEDIA_ROOT) / "library"
        file_index = self._build_file_index(media_root)

        products_by_slug: dict[str, Product] = {}

        for spec in CATALOG:
            slug = slugify(spec["name"])
            product = Product.objects.create(
                name=spec["name"],
                slug=slug,
                short_description=spec["short"],
                description=spec["desc"],
                base_price=Decimal(spec["price"]),
                base_sale_price=Decimal(spec["sale"]) if spec.get("sale") else None,
                is_active=True,
                is_featured=True,
                is_on_sale=bool(spec.get("sale")),
            )
            products_by_slug[slug] = product

            cat = Category.objects.filter(slug=slugify(spec["category"])).first()
            if cat:
                product.categories.add(cat)

            colors = [Color.objects.get(name=c) for c in spec["colors"]]
            sizes = [Size.objects.get(name=s) for s in spec["sizes"]]
            product.available_colors.set(colors)
            product.available_sizes.set(sizes)
            product.generate_variations(overwrite_prices=True)

            if spec.get("sale"):
                ProductVariation.objects.filter(product=product).update(
                    sale_price=Decimal(spec["sale"])
                )
            ProductVariation.objects.filter(product=product).update(stock=12)

            files = self._resolve_files(slug, file_index)
            for n, path in enumerate(files):
                self._attach_image(product, path, sort=n, primary=(n == 0))
            for i, color in enumerate(colors):
                if i >= len(files):
                    break
                self._attach_image(
                    product, files[i], sort=10 + i, primary=False, color=color
                )

            self.stdout.write(f"  + {product.name}")

        self._assign_category_images(products_by_slug, file_index)
        Category.objects.filter(products__isnull=False).update(is_active=True)
        Category.objects.filter(products__isnull=True).update(is_active=False)
        self.stdout.write(self.style.SUCCESS(f"Seeded {len(CATALOG)} demo products with unique images."))

    def _build_file_index(self, root: Path) -> dict[str, Path]:
        index: dict[str, Path] = {}
        if not root.exists():
            return index
        for path in root.rglob("*.*"):
            if path.is_file():
                index[path.name] = path
        return index

    def _resolve_files(self, slug: str, index: dict[str, Path]) -> list[Path]:
        names = PRODUCT_MEDIA.get(slug, [])
        files = []
        for name in names:
            path = index.get(name)
            if path:
                files.append(path)
        return files

    def _assign_category_images(self, products: dict[str, Product], index: dict[str, Path]):
        for cat_slug, product_slug in CATEGORY_COVER.items():
            cat = Category.objects.filter(slug=cat_slug).first()
            product = products.get(product_slug)
            if not cat or not product:
                continue
            img = product.images.filter(color__isnull=True).order_by("sort_order").first()
            if not img or not img.image:
                continue
            try:
                with img.image.open("rb") as fh:
                    data = fh.read()
                name = img.image.name.rsplit("/", 1)[-1]
                cat.image.save(name, ContentFile(data), save=True)
            except Exception as exc:
                self.stderr.write(f"  category image {cat.name}: {exc}")

    def _attach_image(self, product, source: Path, sort=0, primary=False, color=None):
        try:
            data = source.read_bytes()
            name = source.name
        except Exception as exc:
            self.stderr.write(f"    image read failed: {exc}")
            return
        asset = MediaAsset(title=f"{product.name} {sort + 1}")
        asset.file.save(name, ContentFile(data), save=True)
        img = ProductImage(
            product=product,
            color=color,
            alt_text=product.name,
            sort_order=sort,
            is_primary=primary,
        )
        img.image.name = asset.file.name
        img.save()
