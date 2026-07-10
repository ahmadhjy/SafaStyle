"""
Seed 10 launch-ready products with real structure (colors, sizes, variations,
images). Used when the live WooCommerce import is unavailable.

Usage:
  python manage.py seed_launch_catalog
"""

from __future__ import annotations

import io
import urllib.request
from decimal import Decimal

from django.core.files.base import ContentFile
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from catalog.models import Category, Color, MediaAsset, Product, ProductImage, ProductVariation, Size

# Modest-fashion reference photos (Unsplash — high quality, free to use).
IMAGE_URLS = [
    "https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=1400&q=88",
    "https://images.unsplash.com/photo-1539008835657-9e8e9680c956?w=1400&q=88",
    "https://images.unsplash.com/photo-1515372039744-b8f02a3ae446?w=1400&q=88",
    "https://images.unsplash.com/photo-1469334031218-e382a71b716b?w=1400&q=88",
    "https://images.unsplash.com/photo-1496747611176-843222e1e57c?w=1400&q=88",
    "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=1400&q=88",
    "https://images.unsplash.com/photo-1509631179647-0177331693ae?w=1400&q=88",
    "https://images.unsplash.com/photo-1521577352947-9bb58764b69a?w=1400&q=88",
    "https://images.unsplash.com/photo-1585487000160-6ebcfceb0d6d?w=1400&q=88",
    "https://images.unsplash.com/photo-1617137968427-85924c800a43?w=1400&q=88",
    "https://images.unsplash.com/photo-1571513722275-a132d769a282?w=1400&q=88",
    "https://images.unsplash.com/photo-1581044777550-4cfa60707c03?w=1400&q=88",
    "https://images.unsplash.com/photo-1594633312681-425a7b956cc9?w=1400&q=88",
    "https://images.unsplash.com/photo-1618354691373-d851c5c3a990?w=1400&q=88",
    "https://images.unsplash.com/photo-1594938298605-cd64d68329e3?w=1400&q=88",
    "https://images.unsplash.com/photo-1591047139829-d91aecb6caea?w=1400&q=88",
    "https://images.unsplash.com/photo-1583497013659-9d0935a2a2f6?w=1400&q=88",
    "https://images.unsplash.com/photo-1550614000-0b1a4a4a4a4a?w=1400&q=88",
    "https://images.unsplash.com/photo-1566174053879-31528523f8ae?w=1400&q=88",
    "https://images.unsplash.com/photo-1572804013309-59a881b3e962?w=1400&q=88",
]

CATALOG = [
    {
        "name": "New Linen Set",
        "category": "Sets",
        "price": "45.00",
        "sale": "35.00",
        "colors": ["Black", "Beige", "Camel"],
        "sizes": ["1", "2", "3"],
        "short": "Relaxed linen co-ord with wide-leg pants.",
        "desc": "A breathable linen set designed for everyday modest dressing. Soft hand-feel, easy movement, and a clean silhouette.",
    },
    {
        "name": "Classic Linen Set",
        "category": "Sets",
        "price": "48.00",
        "sale": None,
        "colors": ["Black", "Brown", "offwhite"],
        "sizes": ["1", "2", "3"],
        "short": "Timeless linen co-ord in a tailored cut.",
        "desc": "Our classic linen set pairs a structured top with flowing pants — polished enough for outings, comfortable enough for all day.",
    },
    {
        "name": "Long Linen Set",
        "category": "Sets",
        "price": "52.00",
        "sale": "42.00",
        "colors": ["Beige", "Olive Green", "Black"],
        "sizes": ["1", "2", "3"],
        "short": "Extended-length linen set with elegant drape.",
        "desc": "Extra length through the top and pant for a refined modest look. Lightweight linen that keeps its shape.",
    },
    {
        "name": "Embroidered Abaya",
        "category": "Dresses",
        "price": "65.00",
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
        "sale": "68.00",
        "colors": ["Black", "Camel"],
        "sizes": ["1", "2", "3"],
        "short": "Gold-thread embroidery on flowing crepe.",
        "desc": "Elevated evening abaya with gold embroidery accents. Designed to drape beautifully with every step.",
    },
    {
        "name": "Front Zip Abaya",
        "category": "Dresses",
        "price": "55.00",
        "sale": None,
        "colors": ["Black", "Navy Blue", "Gray"],
        "sizes": ["1", "2", "3"],
        "short": "Practical front-zip abaya in soft crepe.",
        "desc": "Easy to wear with a discreet front zip closure. A wardrobe essential in a modest, modern cut.",
    },
    {
        "name": "Belted Wide-Leg Pants",
        "category": "Pants",
        "price": "38.00",
        "sale": "32.00",
        "colors": ["Black", "Beige", "Brown"],
        "sizes": ["1", "2", "3"],
        "short": "High-waist wide-leg pant with matching belt.",
        "desc": "Flowing wide-leg pants with a removable belt. Pairs perfectly with our tops and blazers.",
    },
    {
        "name": "Sculpted Silhouette Blazer",
        "category": "Jackets",
        "price": "42.00",
        "sale": None,
        "colors": ["Black", "Camel", "Navy Blue"],
        "sizes": ["1", "2", "3"],
        "short": "Structured blazer with a modest longline cut.",
        "desc": "Clean lines and a flattering longline shape. Layer over sets and dresses for a polished finish.",
    },
    {
        "name": "Classy Linen Set",
        "category": "Sets",
        "price": "50.00",
        "sale": None,
        "colors": ["offwhite", "Beige", "Mint Green"],
        "sizes": ["1", "2", "3"],
        "short": "Refined linen set with subtle detailing.",
        "desc": "A elevated take on our linen co-ord — minimal, fresh, and easy to style for day or evening.",
    },
    {
        "name": "Eye Box Clutch",
        "category": "Bags",
        "price": "28.00",
        "sale": "22.00",
        "colors": ["Black", "Camel"],
        "sizes": [],
        "short": "Compact box clutch with gold hardware.",
        "desc": "A chic evening clutch with structured shape and eye-catching hardware. Fits essentials with ease.",
    },
]


class Command(BaseCommand):
    help = "Seed 10 launch products with images, variations and categories"

    def handle(self, *args, **options):
        call_command("seed_store")
        ProductVariation.objects.all().delete()
        ProductImage.objects.all().delete()
        Product.objects.all().delete()
        MediaAsset.objects.all().delete()

        img_idx = 0
        for spec in CATALOG:
            product = Product.objects.create(
                name=spec["name"],
                slug=slugify(spec["name"]),
                short_description=spec["short"],
                description=spec["desc"],
                base_price=Decimal(spec["price"]),
                base_sale_price=Decimal(spec["sale"]) if spec.get("sale") else None,
                is_active=True,
                is_featured=True,
                is_on_sale=bool(spec.get("sale")),
            )
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

            # Default gallery (2 images) + one image per color for the card slider.
            for n in range(2):
                url = IMAGE_URLS[img_idx % len(IMAGE_URLS)]
                img_idx += 1
                self._attach_image(product, url, sort=n, primary=(n == 0))
            for i, color in enumerate(colors):
                url = IMAGE_URLS[img_idx % len(IMAGE_URLS)]
                img_idx += 1
                self._attach_image(product, url, sort=10 + i, primary=False, color=color)

            self.stdout.write(f"  + {product.name}")

        # Reactivate categories that have products.
        Category.objects.filter(products__isnull=False).update(is_active=True)
        self.stdout.write(self.style.SUCCESS("Seeded 10 launch products."))

    def _attach_image(self, product, url, sort=0, primary=False, color=None):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "SafaStyleSeeder/1.0"})
            data = urllib.request.urlopen(req, timeout=60).read()
        except Exception as exc:
            self.stderr.write(f"    image download failed: {exc}")
            return
        name = f"{slugify(product.name)}-{sort + 1}.jpg"
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
