from django import forms
from django.contrib import admin
from django.utils.html import format_html

from .models import DeliveryLocality, Governorate, Order, OrderItem


class OrderAdminForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = "__all__"
        widgets = {
            "street_address": forms.Textarea(
                attrs={
                    "rows": 2,
                    "class": "vLargeTextField order-address-field",
                    "style": "width:100%;max-width:100%;min-height:3.2em;resize:vertical;",
                }
            ),
            "apartment": forms.Textarea(
                attrs={
                    "rows": 2,
                    "class": "vLargeTextField order-address-field",
                    "style": "width:100%;max-width:100%;min-height:3.2em;resize:vertical;",
                }
            ),
            "city": forms.TextInput(
                attrs={
                    "class": "vTextField order-address-field",
                    "style": "width:100%;max-width:100%;",
                }
            ),
            "order_notes": forms.Textarea(
                attrs={
                    "rows": 4,
                    "style": "width:100%;max-width:100%;resize:vertical;",
                }
            ),
        }


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = (
        "product_image",
        "product_name",
        "variation_label",
        "sku",
        "unit_price",
        "quantity",
        "line_total",
    )
    readonly_fields = (
        "product_image",
        "product_name",
        "variation_label",
        "sku",
        "unit_price",
        "quantity",
        "line_total",
    )
    can_delete = False

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("variation__product", "variation__color", "variation__size")
            .prefetch_related("variation__product__images")
        )

    @admin.display(description="Image")
    def product_image(self, obj):
        url = self._image_url(obj)
        if not url:
            return format_html(
                '<span style="display:inline-block;width:56px;height:72px;'
                'background:#f0ebe3;border-radius:6px;"></span>'
            )
        return format_html(
            '<img src="{}" alt="" style="width:56px;height:72px;object-fit:cover;'
            'border-radius:6px;display:block;background:#f0ebe3;" />',
            url,
        )

    def _image_url(self, obj):
        variation = obj.variation
        if not variation or not variation.product_id:
            return ""
        return variation.product.image_url_for_color(variation.color)


@admin.register(Governorate)
class GovernorateAdmin(admin.ModelAdmin):
    list_display = ("name", "delivery_fee", "sort_order", "is_active")
    list_editable = ("delivery_fee", "sort_order", "is_active")
    search_fields = ("name",)
    ordering = ("sort_order", "name")


@admin.register(DeliveryLocality)
class DeliveryLocalityAdmin(admin.ModelAdmin):
    list_display = ("name", "governorate", "sort_order", "is_active")
    list_filter = ("governorate", "is_active")
    list_editable = ("sort_order", "is_active")
    search_fields = ("name", "governorate__name")
    autocomplete_fields = ("governorate",)
    ordering = ("name",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    form = OrderAdminForm
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
        "city",
        "street_address",
        "apartment",
    )
    list_editable = ("status",)
    readonly_fields = (
        "order_number",
        "created_at",
        "updated_at",
        "subtotal",
        "delivery_fee",
        "total",
        "full_address_display",
    )
    raw_id_fields = ("user",)
    autocomplete_fields = ("locality", "governorate")
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
                    "full_address_display",
                    "country",
                    "governorate",
                    "locality",
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
    class Media:
        css = {"all": ("admin/css/order_admin.css",)}
        js = ("admin/js/order_address.js",)

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("governorate", "locality", "user")
        )

    @admin.display(description="Full address")
    def full_address_display(self, obj):
        lines = [
            obj.street_address,
            obj.apartment,
            obj.city,
            obj.governorate.name if obj.governorate_id else "",
            obj.country,
            obj.postcode,
        ]
        lines = [line for line in lines if line]
        if not lines:
            return "—"
        return format_html(
            '<div class="order-full-address">{}</div>',
            format_html("<br>".join("{}" for _ in lines), *lines),
        )
