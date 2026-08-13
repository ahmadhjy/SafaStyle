from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONFIRMED = "confirmed", "Confirmed"
        PROCESSING = "processing", "Processing"
        SHIPPED = "shipped", "Shipped"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    class PaymentMethod(models.TextChoices):
        COD = "cod", "Cash on delivery"
        WHISH = "whish", "Whish Pay"

    class PaymentStatus(models.TextChoices):
        NOT_REQUIRED = "not_required", "Not required"  # COD
        AWAITING = "awaiting", "Awaiting payment"
        PAID = "paid", "Paid"
        FAILED = "failed", "Failed / expired"
        REFUNDED = "refunded", "Refunded"

    order_number = models.CharField(max_length=20, unique=True, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="orders",
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )

    # Billing details (matches current WooCommerce checkout)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    company = models.CharField(max_length=150, blank=True)
    country = models.CharField(max_length=100, default="Lebanon")
    street_address = models.CharField(max_length=255)
    apartment = models.CharField(max_length=255, blank=True)
    city = models.CharField(
        max_length=120,
        help_text="Town / city name (copied from locality for Lebanon checkouts).",
    )
    postcode = models.CharField(max_length=40, blank=True)
    phone = models.CharField(max_length=40)
    email = models.EmailField(blank=True)
    order_notes = models.TextField(blank=True)

    governorate = models.ForeignKey(
        "Governorate",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="orders",
    )
    # Optional structured locality for new Lebanon orders. Older orders keep
    # free-text city only (locality stays null) so existing data is untouched.
    locality = models.ForeignKey(
        "DeliveryLocality",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="orders",
    )
    delivery_fee = models.DecimalField(
        max_digits=8, decimal_places=2, default=Decimal("0")
    )

    payment_method = models.CharField(
        max_length=40,
        choices=PaymentMethod.choices,
        default=PaymentMethod.COD,
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.NOT_REQUIRED,
    )
    whish_external_id = models.CharField(
        max_length=64,
        blank=True,
        db_index=True,
        help_text="Idempotent reference sent to Whish Pay.",
    )
    whish_collect_url = models.URLField(blank=True)
    whish_payer_phone = models.CharField(max_length=40, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0"))

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order {self.order_number}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self._generate_order_number()
        super().save(*args, **kwargs)

    @staticmethod
    def _generate_order_number():
        from django.utils.crypto import get_random_string

        while True:
            number = f"SS{timezone.now():%y%m%d}{get_random_string(5, '0123456789').upper()}"
            if not Order.objects.filter(order_number=number).exists():
                return number

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product_name = models.CharField(max_length=200)
    variation_label = models.CharField(max_length=200, blank=True)
    sku = models.CharField(max_length=100, blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    line_total = models.DecimalField(max_digits=10, decimal_places=2)
    variation = models.ForeignKey(
        "catalog.ProductVariation",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="order_items",
    )

    def __str__(self):
        return f"{self.product_name} × {self.quantity}"


class Governorate(models.Model):
    """Lebanon delivery zones — fee applied at checkout when country is Lebanon."""

    name = models.CharField(max_length=120, unique=True)
    delivery_fee = models.DecimalField(
        max_digits=8, decimal_places=2, default=Decimal("5.00")
    )
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name = "Governorate"
        verbose_name_plural = "Governorates"

    def __str__(self):
        return self.name


class DeliveryLocality(models.Model):
    """City / town / neighborhood used to lock delivery governorate at checkout."""

    name = models.CharField(max_length=120)
    governorate = models.ForeignKey(
        Governorate,
        on_delete=models.CASCADE,
        related_name="localities",
    )
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["name"]
        verbose_name = "Delivery locality"
        verbose_name_plural = "Delivery localities"
        constraints = [
            models.UniqueConstraint(
                fields=["name", "governorate"],
                name="unique_locality_name_per_governorate",
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.governorate.name})"
