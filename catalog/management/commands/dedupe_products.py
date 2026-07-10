"""Remove empty duplicate products that share a slugified name with a real listing."""

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from catalog.models import Product


class Command(BaseCommand):
    help = "Delete empty duplicate products (0 variations, same name as another product)"

    def handle(self, *args, **options):
        removed = 0
        for product in Product.objects.prefetch_related("variations").order_by("id"):
            if product.variations.exists():
                continue
            norm = slugify(product.name)
            for other in Product.objects.exclude(pk=product.pk).prefetch_related(
                "variations"
            ):
                if slugify(other.name) == norm and other.variations.exists():
                    self.stdout.write(
                        f"Removing #{product.pk} {product.name!r} "
                        f"(keeping #{other.pk} {other.name!r})"
                    )
                    product.delete()
                    removed += 1
                    break
        self.stdout.write(self.style.SUCCESS(f"Removed {removed} duplicate(s)."))
