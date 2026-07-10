"""
Import products from the public WooCommerce Store API on safastyle.com.

Usage:
  python manage.py import_woocommerce
  python manage.py import_woocommerce --limit 20
  python manage.py import_woocommerce --base-url https://safastyle.com
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from decimal import Decimal
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from catalog.models import (
    Category,
    Color,
    MediaAsset,
    Product,
    ProductImage,
    ProductVariation,
    Size,
)


class Command(BaseCommand):
    help = "Import catalog from WooCommerce Store API (no auth required for public products)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--base-url",
            default="https://safastyle.com",
            help="Store base URL",
        )
        parser.add_argument("--limit", type=int, default=0, help="Max products (0 = all)")
        parser.add_argument(
            "--skip-images",
            action="store_true",
            help="Skip downloading images (faster dry structure import)",
        )
        parser.add_argument(
            "--fresh",
            action="store_true",
            help="Delete existing products, images, variations and media first",
        )

    def handle(self, *args, **options):
        base = options["base_url"].rstrip("/")
        limit = options["limit"]
        skip_images = options["skip_images"]
        page = 1
        imported = 0

        if options["fresh"]:
            ProductVariation.objects.all().delete()
            ProductImage.objects.all().delete()
            Product.objects.all().delete()
            MediaAsset.objects.all().delete()
            self.stdout.write(self.style.WARNING("Cleared existing catalog + media."))

        while True:
            url = f"{base}/wp-json/wc/store/v1/products?per_page=20&page={page}"
            self.stdout.write(f"Fetching {url}")
            try:
                products = self._get_json(url)
            except Exception as exc:
                self.stderr.write(f"Failed page {page}: {exc}")
                break
            if not products:
                break

            for item in products:
                self._import_product(item, base, skip_images)
                imported += 1
                if limit and imported >= limit:
                    self.stdout.write(self.style.SUCCESS(f"Imported {imported} products"))
                    return

            page += 1
            if page > 50:
                break

        self.stdout.write(self.style.SUCCESS(f"Imported/updated {imported} products"))

    def _get_json(self, url: str):
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "SafaStyleImporter/1.0"},
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def _money(self, prices: dict, key: str) -> Decimal | None:
        raw = prices.get(key)
        if raw in (None, ""):
            return None
        # Store API returns minor units as string, e.g. "4500" with currency_minor_unit=2
        minor = int(prices.get("currency_minor_unit") or 2)
        return (Decimal(str(raw)) / (Decimal(10) ** minor)).quantize(Decimal("0.01"))

    def _get_or_create_color(self, name: str) -> Color:
        name = (name or "").strip() or "Default"
        slug = slugify(name) or "default"
        color, _ = Color.objects.get_or_create(
            slug=slug,
            defaults={"name": name},
        )
        if color.name != name:
            color.name = name
            color.save(update_fields=["name"])
        return color

    def _get_or_create_size(self, name: str) -> Size:
        name = (name or "").strip() or "OS"
        slug = slugify(name) or "os"
        size, _ = Size.objects.get_or_create(slug=slug, defaults={"name": name})
        return size

    def _import_product(self, item: dict, base: str, skip_images: bool):
        woo_id = item.get("id")
        name = item.get("name") or f"Product {woo_id}"
        slug = item.get("slug") or slugify(name)
        prices = item.get("prices") or {}
        price = self._money(prices, "price") or Decimal("0.00")
        regular = self._money(prices, "regular_price") or price
        sale = self._money(prices, "sale_price")
        on_sale = bool(item.get("on_sale")) and sale is not None and sale < regular

        product, created = Product.objects.update_or_create(
            woo_id=woo_id,
            defaults={
                "name": name,
                "slug": slug,
                "sku": item.get("sku") or "",
                "short_description": self._strip_html(item.get("short_description") or ""),
                "description": self._strip_html(item.get("description") or ""),
                "base_price": regular,
                "base_sale_price": sale if on_sale else None,
                "is_active": True,
                "is_on_sale": on_sale,
            },
        )
        # Ensure unique slug if collision with different woo_id
        if Product.objects.filter(slug=product.slug).exclude(pk=product.pk).exists():
            product.slug = f"{slug}-{woo_id}"
            product.save(update_fields=["slug"])

        for cat in item.get("categories") or []:
            category, _ = Category.objects.get_or_create(
                slug=cat.get("slug") or slugify(cat.get("name") or "cat"),
                defaults={"name": cat.get("name") or "Category", "is_active": True},
            )
            product.categories.add(category)

        colors = []
        sizes = []
        for attr in item.get("attributes") or []:
            attr_name = (attr.get("name") or "").lower()
            terms = attr.get("terms") or []
            if "color" in attr_name or "colour" in attr_name:
                for term in terms:
                    colors.append(self._get_or_create_color(term.get("name")))
            elif "size" in attr_name:
                for term in terms:
                    sizes.append(self._get_or_create_size(term.get("name")))

        if colors:
            product.available_colors.set(colors)
        if sizes:
            product.available_sizes.set(sizes)

        # Variations from store API are shallow — create matrix from attributes
        product.generate_variations(overwrite_prices=True)
        ProductVariation.objects.filter(product=product).update(
            price=regular,
            sale_price=sale if on_sale else None,
            stock=5 if item.get("is_in_stock") else 0,
            is_active=True,
        )

        if not skip_images:
            self._import_images(product, item.get("images") or [], colors)

        self.stdout.write(f"  {'+' if created else '~'} {product.name}")

    def _import_images(self, product: Product, images: list, colors: list[Color]):
        if not images:
            return
        # Every image goes into the shared media library and the product's default
        # gallery (color left empty). The data-entry team assigns colors in the admin.
        for idx, img in enumerate(images):
            src = img.get("src")
            if not src:
                continue
            filename = Path(urllib.parse.urlparse(src).path).name
            if product.images.filter(image__iendswith=filename).exists():
                continue
            try:
                data = self._download(src)
            except Exception as exc:
                self.stderr.write(f"    image fail {src}: {exc}")
                continue

            asset = MediaAsset(title=(img.get("alt") or product.name))
            asset.file.save(filename, ContentFile(data), save=True)

            obj = ProductImage(
                product=product,
                color=None,
                alt_text=img.get("alt") or product.name,
                sort_order=idx,
                is_primary=(idx == 0),
            )
            # Reference the same file stored for the library asset.
            obj.image.name = asset.file.name
            obj.save()

    def _download(self, url: str) -> bytes:
        req = urllib.request.Request(url, headers={"User-Agent": "SafaStyleImporter/1.0"})
        with urllib.request.urlopen(req, timeout=90) as resp:
            return resp.read()

    @staticmethod
    def _strip_html(value: str) -> str:
        import re

        text = re.sub(r"<[^>]+>", " ", value or "")
        text = re.sub(r"\s+", " ", text).strip()
        return text
