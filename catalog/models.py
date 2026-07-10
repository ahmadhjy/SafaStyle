from decimal import Decimal

from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class MediaAsset(TimeStampedModel):
    """A globally reusable image, like the WordPress media library."""

    file = models.ImageField(upload_to="library/%Y/%m/")
    title = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title or (self.file.name.rsplit("/", 1)[-1] if self.file else "asset")

    def save(self, *args, **kwargs):
        if not self.title and self.file:
            base = self.file.name.rsplit("/", 1)[-1]
            self.title = base.rsplit(".", 1)[0].replace("-", " ").replace("_", " ").strip()
        super().save(*args, **kwargs)


class Category(TimeStampedModel):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="categories/", blank=True)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="children",
        on_delete=models.CASCADE,
    )
    is_featured = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "categories"
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("catalog:category", kwargs={"slug": self.slug})


class Color(TimeStampedModel):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    hex_code = models.CharField(
        max_length=7,
        blank=True,
        help_text="Optional swatch color, e.g. #1a1a1a",
    )
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Size(TimeStampedModel):
    name = models.CharField(max_length=40, unique=True)
    slug = models.SlugField(max_length=60, unique=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Product(TimeStampedModel):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    sku = models.CharField(max_length=80, blank=True)
    short_description = models.CharField(max_length=300, blank=True)
    description = models.TextField(blank=True)
    measurements = models.TextField(
        blank=True,
        help_text="e.g. Length Top: 75cm / Length Pant: 105cm",
    )
    categories = models.ManyToManyField(Category, related_name="products", blank=True)
    base_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Default price used when generating variations",
    )
    base_sale_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Optional default sale price for new variations",
    )
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_on_sale = models.BooleanField(default=False)
    available_colors = models.ManyToManyField(
        Color,
        blank=True,
        related_name="products",
        help_text="Pick colors, then generate variations",
    )
    available_sizes = models.ManyToManyField(
        Size,
        blank=True,
        related_name="products",
        help_text="Pick sizes, then generate variations",
    )
    woo_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        unique=True,
        help_text="Original WooCommerce product ID",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name) or "product"
            slug = base
            n = 2
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base}-{n}"
                n += 1
            self.slug = slug
        super().save(*args, **kwargs)
        # Auto-generate a stable SKU from the record id once we have a pk.
        if not self.sku:
            sku = f"SS-{self.pk:05d}"
            Product.objects.filter(pk=self.pk).update(sku=sku)
            self.sku = sku

    def get_absolute_url(self):
        return reverse("catalog:product", kwargs={"slug": self.slug})

    @property
    def is_variable(self):
        """Variable products have colors and/or sizes; otherwise they're simple.

        Uses ``.all()`` so prefetched querysets don't trigger extra queries on
        listing pages.
        """
        return bool(self.available_colors.all()) or bool(self.available_sizes.all())

    @property
    def primary_image(self):
        img = self.images.filter(color__isnull=True).order_by("sort_order").first()
        if img:
            return img
        return self.images.order_by("sort_order").first()

    @property
    def display_price(self):
        variation = (
            self.variations.filter(is_active=True)
            .order_by("sale_price", "price")
            .first()
        )
        if variation:
            return variation.current_price
        if self.base_sale_price:
            return self.base_sale_price
        return self.base_price

    @property
    def display_regular_price(self):
        variation = self.variations.filter(is_active=True).order_by("price").first()
        if variation:
            return variation.price
        return self.base_price

    @property
    def has_sale(self):
        if self.variations.filter(is_active=True, sale_price__isnull=False).exists():
            return True
        return bool(self.base_sale_price)

    @property
    def card_color_swatches(self):
        """Color swatches with image URLs for product gallery cards."""
        by_color = {}
        defaults = []
        for img in self.images.all():
            if img.color_id and img.color_id not in by_color and img.image:
                by_color[img.color_id] = img.image.url
            elif not img.color_id and img.image:
                defaults.append(img.image.url)
        primary = (
            self.primary_image.image.url
            if self.primary_image and self.primary_image.image
            else (defaults[0] if defaults else "")
        )
        seen_images: set[str] = set()
        swatches = []
        for color in self.available_colors.all():
            image = by_color.get(color.id) or ""
            if not image:
                for url in defaults:
                    if url and url not in seen_images:
                        image = url
                        break
            if not image:
                image = primary
            if image:
                seen_images.add(image)
            swatches.append(
                {
                    "id": color.id,
                    "hex": color.hex_code or "#cccccc",
                    "name": color.name,
                    "image": image or "",
                }
            )
        return swatches

    def images_for_color(self, color):
        qs = self.images.filter(color=color).order_by("sort_order")
        if qs.exists():
            return qs
        return self.images.filter(color__isnull=True).order_by("sort_order")

    def _variation_sku(self, color, size):
        base = self.sku or (f"SS-{self.pk:05d}" if self.pk else "SS")
        parts = [base]
        if color:
            parts.append(slugify(color.name).upper()[:6] or "C")
        if size:
            parts.append(slugify(size.name).upper()[:4] or "S")
        return "-".join(parts)

    def generate_variations(self, overwrite_prices=False):
        """Create the full color×size matrix. Images stay on ProductImage by color."""
        colors = list(self.available_colors.all())
        sizes = list(self.available_sizes.all())
        created = 0

        if not colors and not sizes:
            _, was_created = ProductVariation.objects.get_or_create(
                product=self,
                color=None,
                size=None,
                defaults={
                    "sku": self._variation_sku(None, None),
                    "price": self.base_price,
                    "sale_price": self.base_sale_price,
                    "stock": 0,
                    "is_active": True,
                },
            )
            return 1 if was_created else 0

        color_list = colors or [None]
        size_list = sizes or [None]

        for color in color_list:
            for size in size_list:
                defaults = {
                    "sku": self._variation_sku(color, size),
                    "price": self.base_price,
                    "sale_price": self.base_sale_price,
                    "stock": 0,
                    "is_active": True,
                }
                variation, was_created = ProductVariation.objects.get_or_create(
                    product=self,
                    color=color,
                    size=size,
                    defaults=defaults,
                )
                if was_created:
                    created += 1
                elif overwrite_prices:
                    variation.price = self.base_price
                    variation.sale_price = self.base_sale_price
                    if not variation.sku:
                        variation.sku = self._variation_sku(color, size)
                    variation.save(
                        update_fields=["price", "sale_price", "sku", "updated_at"]
                    )
        return created


class ProductImage(TimeStampedModel):
    product = models.ForeignKey(
        Product, related_name="images", on_delete=models.CASCADE
    )
    color = models.ForeignKey(
        Color,
        null=True,
        blank=True,
        related_name="images",
        on_delete=models.SET_NULL,
        help_text="Leave empty for default gallery. Set color so gallery swaps on color select.",
    )
    image = models.ImageField(upload_to="products/%Y/%m/")
    alt_text = models.CharField(max_length=200, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_primary = models.BooleanField(default=False)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        color = self.color.name if self.color else "default"
        return f"{self.product.name} — {color}"


class ProductVariation(TimeStampedModel):
    product = models.ForeignKey(
        Product, related_name="variations", on_delete=models.CASCADE
    )
    color = models.ForeignKey(
        Color, null=True, blank=True, on_delete=models.PROTECT, related_name="variations"
    )
    size = models.ForeignKey(
        Size, null=True, blank=True, on_delete=models.PROTECT, related_name="variations"
    )
    sku = models.CharField(max_length=100, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    woo_variation_id = models.PositiveIntegerField(null=True, blank=True, unique=True)

    class Meta:
        ordering = ["color__sort_order", "size__sort_order", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["product", "color", "size"],
                name="unique_product_color_size",
            )
        ]

    def __str__(self):
        parts = [self.product.name]
        if self.color:
            parts.append(self.color.name)
        if self.size:
            parts.append(self.size.name)
        return " / ".join(parts)

    @property
    def current_price(self):
        if self.sale_price is not None:
            return self.sale_price
        return self.price

    @property
    def on_sale(self):
        return self.sale_price is not None and self.sale_price < self.price

    @property
    def in_stock(self):
        return self.is_active and self.stock > 0

    def label(self):
        bits = []
        if self.color:
            bits.append(self.color.name)
        if self.size:
            bits.append(self.size.name)
        return ", ".join(bits) if bits else "Default"
