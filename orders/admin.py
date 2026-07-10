from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = (
        "product_name",
        "variation_label",
        "sku",
        "unit_price",
        "quantity",
        "line_total",
    )
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number",
        "full_name",
        "phone",
        "city",
        "status",
        "total",
        "created_at",
    )
    list_filter = ("status", "payment_method", "created_at")
    search_fields = (
        "order_number",
        "first_name",
        "last_name",
        "phone",
        "email",
    )
    list_editable = ("status",)
    readonly_fields = ("order_number", "created_at", "updated_at", "subtotal", "total")
    raw_id_fields = ("user",)
    inlines = [OrderItemInline]
    fieldsets = (
        ("Order", {"fields": ("order_number", "user", "status", "payment_method", "created_at")}),
        (
            "Customer",
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "company",
                    "phone",
                    "email",
                )
            },
        ),
        (
            "Address",
            {
                "fields": (
                    "country",
                    "street_address",
                    "apartment",
                    "city",
                    "postcode",
                )
            },
        ),
        ("Notes & totals", {"fields": ("order_notes", "subtotal", "total")}),
    )
