"""
Import products from WooCommerce on the old WordPress host (Bluehost temp URL).

Usage:
  python manage.py import_woocommerce
  python manage.py import_woocommerce --base-url https://your-temp.mybluehost.me
  python manage.py import_woocommerce --fresh --limit 0
"""

from __future__ import annotations

import base64
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from decimal import Decimal
from pathlib import Path

from django.conf import settings
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
    help = "Import catalog from WooCommerce (Store API + optional REST v3 for color images)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--base-url",
            default="",
            help="WordPress store URL (defaults to WOO_BASE_URL / https://safastyle.com)",
        )
        parser.add_argument("--limit", type=int, default=0, help="Max products (0 = all)")
        parser.add_argument(
            "--skip-images",
            action="store_true",
            help="Skip downloading images (structure only)",
        )
        parser.add_argument(
            "--fresh",
            action="store_true",
            help="Delete existing products, images, variations and media first",
        )

    def handle(self, *args, **options):
        base = (options["base_url"] or getattr(settings, "WOO_BASE_URL", "") or "https://safastyle.com").rstrip("/")
        limit = options["limit"]
        skip_images = options["skip_images"]
        page = 1
        imported = 0

        self.stdout.write(f"Import source: {base}")
        probe = f"{base}/wp-json/wc/store/v1/products?per_page=1"
        try:
            self._get_json(probe)
        except Exception as exc:
            self.stderr.write(
                self.style.ERROR(
                    f"Cannot reach WooCommerce at {base}\n"
                    f"  {exc}\n"
                    "Set WOO_BASE_URL in .env to your Bluehost temporary WordPress URL "
                    "(Bluehost → WordPress → Manage → Settings)."
                )
            )
            return

        if options["fresh"]:
            ProductVariation.objects.all().delete()
            ProductImage.objects.all().delete()
            Product.objects.all().delete()
            MediaAsset.objects.all().delete()
            self.stdout.write(self.style.WARNING("Cleared existing catalog + media."))

        color_map: dict[str, Color] = {}
        size_map: dict[str, Size] = {}

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
                self._import_product(item, base, skip_images, color_map, size_map)
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
            headers={"User-Agent": "SafaStyleImporter/1.0", "Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=90) as resp:
            raw = resp.read().decode("utf-8")
            if raw.lstrip().startswith("<"):
                raise RuntimeError("Server returned HTML instead of JSON (not WordPress/WooCommerce?)")
            return json.loads(raw)

    def _rest_get(self, base: str, path: str):
        key = getattr(settings, "WOO_CONSUMER_KEY", "") or os.environ.get("WOO_CONSUMER_KEY", "")
        secret = getattr(settings, "WOO_CONSUMER_SECRET", "") or os.environ.get("WOO_CONSUMER_SECRET", "")
        if not key or not secret:
            return None
        url = f"{base}/wp-json/wc/v3{path}"
        token = base64.b64encode(f"{key}:{secret}".encode()).decode()
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "SafaStyleImporter/1.0",
                "Accept": "application/json",
                "Authorization": f"Basic {token}",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception:
            return None

    def _money(self, prices: dict, key: str) -> Decimal | None:
        raw = prices.get(key)
        if raw in (None, ""):
            return None
        minor = int(prices.get("currency_minor_unit") or 2)
        return (Decimal(str(raw)) / (Decimal(10) ** minor)).quantize(Decimal("0.01"))

    def _get_or_create_color(self, name: str, cache: dict[str, Color]) -> Color:
        name = (name or "").strip() or "Default"
        slug = slugify(name) or "default"
        if slug in cache:
            return cache[slug]
        color, _ = Color.objects.get_or_create(slug=slug, defaults={"name": name})
        if color.name != name:
            color.name = name
            color.save(update_fields=["name"])
        cache[slug] = color
        return color

    def _get_or_create_size(self, name: str, cache: dict[str, Size]) -> Size:
        name = (name or "").strip() or "OS"
        slug = slugify(name) or "os"
        if slug in cache:
            return cache[slug]
        size, _ = Size.objects.get_or_create(slug=slug, defaults={"name": name})
        cache[slug] = size
        return size

    def _import_product(self, item: dict, base: str, skip_images: bool, color_map, size_map):
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
        if Product.objects.filter(slug=product.slug).exclude(pk=product.pk).exists():
            product.slug = f"{slug}-{woo_id}"
            product.save(update_fields=["slug"])

        product.categories.clear()
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
                    colors.append(self._get_or_create_color(term.get("name"), color_map))
            elif "size" in attr_name:
                for term in terms:
                    sizes.append(self._get_or_create_size(term.get("name"), size_map))

        if colors:
            product.available_colors.set(colors)
        if sizes:
            product.available_sizes.set(sizes)

        product.generate_variations(overwrite_prices=True)
        ProductVariation.objects.filter(product=product).update(
            price=regular,
            sale_price=sale if on_sale else None,
            stock=5 if item.get("is_in_stock") else 0,
            is_active=True,
        )

        if not skip_images:
            color_images = self._variation_color_images(base, woo_id, colors, color_map)
            self._import_images(product, item.get("images") or [], colors, color_images)

        self.stdout.write(f"  {'+' if created else '~'} {product.name}")

    def _variation_color_images(self, base: str, woo_id: int, colors: list[Color], color_map) -> dict[int, str]:
        """Map color_id -> image URL from WooCommerce variation records."""
        mapping: dict[int, str] = {}
        if not colors or not woo_id:
            return mapping

        variations = self._rest_get(base, f"/products/{woo_id}/variations?per_page=100")
        if not variations:
            return mapping

        for var in variations:
            if not isinstance(var, dict):
                continue
            src = (var.get("image") or {}).get("src")
            if not src:
                continue
            color_name = None
            for attr in var.get("attributes") or []:
                aname = (attr.get("name") or "").lower()
                if "color" in aname or "colour" in aname:
                    color_name = attr.get("option")
                    break
            if not color_name:
                continue
            color = self._get_or_create_color(color_name, color_map)
            mapping.setdefault(color.id, src)

        return mapping

    def _import_images(
        self,
        product: Product,
        images: list,
        colors: list[Color],
        color_images: dict[int, str],
    ):
        if not images and not color_images:
            return

        product.images.all().delete()
        seen: set[str] = set()
        sort = 0

        # Default gallery (first image uncolored = featured)
        for idx, img in enumerate(images):
            src = img.get("src")
            if not src or src in seen:
                continue
            seen.add(src)
            self._save_product_image(
                product,
                src,
                alt=img.get("alt") or product.name,
                color=None,
                sort_order=sort,
                is_primary=(idx == 0),
            )
            sort += 1

        # Per-color images from Woo variations (preferred)
        for color in colors:
            src = color_images.get(color.id)
            if not src or src in seen:
                continue
            seen.add(src)
            self._save_product_image(
                product,
                src,
                alt=f"{product.name} — {color.name}",
                color=color,
                sort_order=sort,
                is_primary=False,
            )
            sort += 1

        # Extra gallery images → assign round-robin to colors still missing a photo
        missing = [c for c in colors if not product.images.filter(color=c).exists()]
        extra = [img.get("src") for img in images[1:] if img.get("src") and img.get("src") not in seen]
        for i, color in enumerate(missing):
            if i >= len(extra):
                break
            src = extra[i]
            seen.add(src)
            self._save_product_image(
                product,
                src,
                alt=f"{product.name} — {color.name}",
                color=color,
                sort_order=sort,
                is_primary=False,
            )
            sort += 1

    def _save_product_image(
        self,
        product: Product,
        src: str,
        *,
        alt: str,
        color: Color | None,
        sort_order: int,
        is_primary: bool,
    ):
        filename = Path(urllib.parse.urlparse(src).path).name
        if not filename:
            filename = f"product-{product.pk}-{sort_order}.jpg"
        try:
            data = self._download(src)
        except Exception as exc:
            self.stderr.write(f"    image fail {src}: {exc}")
            return

        asset = MediaAsset(title=alt or product.name)
        asset.file.save(filename, ContentFile(data), save=True)

        obj = ProductImage(
            product=product,
            color=color,
            alt_text=alt or product.name,
            sort_order=sort_order,
            is_primary=is_primary,
        )
        obj.image.name = asset.file.name
        obj.save()

    def _download(self, url: str) -> bytes:
        req = urllib.request.Request(url, headers={"User-Agent": "SafaStyleImporter/1.0"})
        with urllib.request.urlopen(req, timeout=90) as resp:
            return resp.read()

    @staticmethod
    def _strip_html(value: str) -> str:
        text = re.sub(r"<[^>]+>", " ", value or "")
        return re.sub(r"\s+", " ", text).strip()
