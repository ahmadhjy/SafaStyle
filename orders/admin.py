from django.contrib import admin

from .models import Governorate, Order, OrderItem


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


@admin.register(Governorate)
class GovernorateAdmin(admin.ModelAdmin):
    list_display = ("name", "delivery_fee", "sort_order", "is_active")
    list_editable = ("delivery_fee", "sort_order", "is_active")
    search_fields = ("name",)
    ordering = ("sort_order", "name")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number",
        "full_name",
        "phone",
        "city",
        "governorate",
        "status",
        "total",
        "created_at",
    )
    list_filter = ("status", "payment_method", "created_at", "governorate")
    search_fields = (
        "order_number",
        "first_name",
        "last_name",
        "phone",
        "email",
    )
    list_editable = ("status",)
    readonly_fields = (
        "order_number",
        "created_at",
        "updated_at",
        "subtotal",
        "delivery_fee",
        "total",
    )
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
                    "governorate",
                    "street_address",
                    "apartment",
                    "city",
                    "postcode",
                )
            },
        ),
        (
            "Notes & totals",
            {"fields": ("order_notes", "subtotal", "delivery_fee", "total")},
        ),
    )
