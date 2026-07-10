"""
Import curated Safa demo products + images from the Bluehost WordPress store.

Usage:
  python manage.py seed_demo_catalog
  python manage.py seed_demo_catalog --base-url https://website-881c8e5a.cvn.pkr.mybluehost.me
"""

from __future__ import annotations

from django.core.files.base import ContentFile
from django.core.management import call_command
from django.core.management.base import BaseCommand

from catalog.management.commands.import_woocommerce import Command as ImportCommand
from catalog.models import Category, MediaAsset, Product, ProductImage, ProductVariation

DEFAULT_BASE = "https://website-881c8e5a.cvn.pkr.mybluehost.me"

DEMO_SLUGS = (
    "classy-linen-set",
    "long-crepe-set",
    "embroidered-abaya",
    "royal-gold-embroidered-abaya",
    "belted-wide-leg-pants",
)


class Command(BaseCommand):
    help = "Seed demo products and images from the Bluehost Safa WordPress store"

    def add_arguments(self, parser):
        parser.add_argument(
            "--base-url",
            default=DEFAULT_BASE,
            help="Bluehost / WordPress store URL",
        )

    def handle(self, *args, **options):
        base = options["base_url"].rstrip("/")
        self.stdout.write(f"Demo source: {base}")

        call_command("seed_store")

        ProductVariation.objects.all().delete()
        ProductImage.objects.all().delete()
        Product.objects.all().delete()
        MediaAsset.objects.all().delete()
        self.stdout.write("Cleared catalog for fresh demo seed.")

        importer = ImportCommand()
        importer.stdout = self.stdout
        importer.stderr = self.stderr

        probe = f"{base}/wp-json/wc/store/v1/products?per_page=1"
        try:
            importer._get_json(probe)
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"Cannot reach WooCommerce at {base}: {exc}"))
            return

        wanted = set(DEMO_SLUGS)
        found: dict[str, dict] = {}
        page = 1
        while wanted - found.keys() and page <= 10:
            url = f"{base}/wp-json/wc/store/v1/products?per_page=100&page={page}"
            self.stdout.write(f"Fetching {url}")
            try:
                batch = importer._get_json(url)
            except Exception as exc:
                self.stderr.write(f"Fetch failed page {page}: {exc}")
                break
            if not batch:
                break
            for item in batch:
                slug = item.get("slug") or ""
                if slug in wanted:
                    found[slug] = item
            page += 1

        missing = wanted - found.keys()
        if missing:
            self.stderr.write(self.style.WARNING(f"Not found on source: {', '.join(sorted(missing))}"))

        color_map: dict = {}
        size_map: dict = {}
        imported = 0
        for slug in DEMO_SLUGS:
            item = found.get(slug)
            if not item:
                continue
            importer._import_product(item, base, skip_images=False, color_map=color_map, size_map=size_map)
            product = Product.objects.filter(slug=slug).first()
            if product:
                product.is_featured = True
                product.save(update_fields=["is_featured"])
            imported += 1

        self._assign_category_covers()
        Category.objects.filter(products__isnull=False).update(is_active=True)

        self.stdout.write(self.style.SUCCESS(f"Seeded {imported} demo products from Bluehost."))

    def _assign_category_covers(self):
        covers = {
            "sets": "classy-linen-set",
            "dresses": "embroidered-abaya",
            "pants": "belted-wide-leg-pants",
        }
        for cat_slug, product_slug in covers.items():
            cat = Category.objects.filter(slug=cat_slug).first()
            product = Product.objects.filter(slug=product_slug).first()
            if not cat or not product:
                continue
            img = product.images.filter(is_primary=True).first() or product.images.first()
            if not img or not img.image:
                continue
            try:
                with img.image.open("rb") as fh:
                    data = fh.read()
                name = img.image.name.rsplit("/", 1)[-1]
                cat.image.save(name, ContentFile(data), save=True)
            except Exception as exc:
                self.stderr.write(f"  category cover {cat.name}: {exc}")
