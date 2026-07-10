import json

from django import forms
from django.contrib import admin, messages
from django.http import JsonResponse
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import (
    Category,
    Color,
    MediaAsset,
    Product,
    ProductImage,
    ProductVariation,
    Size,
)


# ---------------------------------------------------------------------------
# WordPress-style media gallery widget
# ---------------------------------------------------------------------------
class GalleryWidget(forms.Widget):
    """Renders the gallery editor: a grid of chosen images + an "Add media"
    button that opens the media-library modal. The selection is stored as JSON
    in a hidden textarea so it round-trips even if JavaScript is disabled."""

    def __init__(self, attrs=None, colors=None, library_url="", upload_url=""):
        super().__init__(attrs)
        self.colors = colors or []
        self.library_url = library_url
        self.upload_url = upload_url

    def render(self, name, value, attrs=None, renderer=None):
        value = value or "[]"
        widget_id = (attrs or {}).get("id", f"id_{name}")
        colors_json = json.dumps(self.colors)
        return mark_safe(
            f"""
<div class="ss-gallery" data-library-url="{self.library_url}"
     data-upload-url="{self.upload_url}" data-input="{widget_id}">
  <script type="application/json" class="ss-gallery-colors">{colors_json}</script>
  <div class="ss-gallery-grid" data-role="grid"></div>
  <div class="ss-gallery-empty" data-role="empty">
    No images yet. Click <strong>Add media</strong> to choose from the library
    or upload new photos.
  </div>
  <button type="button" class="button ss-gallery-add">
    <span aria-hidden="true">&#43;</span> Add media
  </button>
  <textarea id="{widget_id}" name="{name}" class="ss-gallery-input" hidden>{value}</textarea>
</div>
"""
        )


class ProductAdminForm(forms.ModelForm):
    gallery_data = forms.CharField(required=False, widget=forms.HiddenInput)

    class Meta:
        model = Product
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        colors = [
            {"id": c.id, "name": c.name, "hex": c.hex_code or "#cccccc"}
            for c in Color.objects.all()
        ]
        self.fields["gallery_data"].widget = GalleryWidget(
            colors=colors,
            library_url=reverse("admin:catalog_gallery_library"),
            upload_url=reverse("admin:catalog_gallery_upload"),
        )
        self.fields["gallery_data"].label = "Media"
        if self.instance and self.instance.pk:
            gallery = [
                {
                    "image_id": img.id,
                    "asset_id": None,
                    "url": img.image.url if img.image else "",
                    "color_id": img.color_id,
                    "is_primary": img.is_primary,
                }
                for img in self.instance.images.all().order_by("sort_order", "id")
            ]
            self.fields["gallery_data"].initial = json.dumps(gallery)


@admin.register(MediaAsset)
class MediaAssetAdmin(admin.ModelAdmin):
    list_display = ("thumb", "title", "created_at")
    list_display_links = ("thumb", "title")
    search_fields = ("title",)
    ordering = ("-created_at",)

    @admin.display(description="")
    def thumb(self, obj):
        if obj.file:
            return format_html(
                '<img src="{}" style="height:54px;width:54px;object-fit:cover;'
                'border-radius:6px;" />',
                obj.file.url,
            )
        return "—"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "is_featured", "is_active", "sort_order")
    list_editable = ("is_featured", "is_active", "sort_order")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ("swatch", "name", "hex_code", "sort_order")
    list_editable = ("hex_code", "sort_order")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "hex_code")

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == "hex_code":
            kwargs["widget"] = forms.TextInput(
                attrs={
                    "type": "color",
                    "style": "width:52px;height:34px;padding:2px;cursor:pointer;",
                }
            )
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    @admin.display(description="")
    def swatch(self, obj):
        color = obj.hex_code or "#ccc"
        return format_html(
            '<span style="display:inline-block;width:18px;height:18px;'
            'border-radius:50%;background:{};border:1px solid #ddd;"></span>',
            color,
        )


@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ("name", "sort_order")
    list_editable = ("sort_order",)
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


class ProductVariationInline(admin.TabularInline):
    model = ProductVariation
    extra = 0
    fields = ("color", "size", "sku", "price", "sale_price", "stock", "is_active")
    autocomplete_fields = ("color", "size")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    list_display = (
        "thumb",
        "name",
        "product_kind",
        "base_price",
        "base_sale_price",
        "is_active",
        "is_featured",
        "is_on_sale",
        "variation_count",
    )
    list_display_links = ("thumb", "name")
    list_filter = ("is_active", "is_featured", "is_on_sale", "categories")
    list_editable = ("is_active", "is_featured", "is_on_sale")
    search_fields = ("name", "sku", "short_description")
    readonly_fields = ("slug", "sku")
    filter_horizontal = ("categories", "available_colors", "available_sizes")
    inlines = [ProductVariationInline]
    actions = ["generate_variations_action", "generate_variations_overwrite_prices"]
    save_on_top = True
    fieldsets = (
        (
            "Product",
            {
                "fields": (
                    "name",
                    ("slug", "sku"),
                    "short_description",
                    "description",
                    "measurements",
                    "categories",
                ),
                "description": "Slug and SKU are generated automatically from the title.",
            },
        ),
        (
            "Media",
            {
                "fields": ("gallery_data",),
                "description": (
                    "Simple product? Just add photos. Variable product? Add photos and "
                    "assign a color to each — the storefront swaps the gallery when a "
                    "shopper picks that color."
                ),
            },
        ),
        (
            "Pricing",
            {
                "fields": ("base_price", "base_sale_price"),
                "description": (
                    "For simple products this is the selling price. For variable "
                    "products it's the default used when generating variations."
                ),
            },
        ),
        (
            "Colors & sizes",
            {
                "fields": ("available_colors", "available_sizes"),
                "description": (
                    "Pick the colors and sizes and Save. Then open the Variations tab "
                    "and click “Generate variations” to build every combination."
                ),
            },
        ),
        (
            "Visibility",
            {"fields": ("is_active", "is_featured", "is_on_sale")},
        ),
    )

    class Media:
        css = {"all": ("admin/css/gallery.css",)}
        js = ("admin/js/gallery.js", "admin/js/variations.js")

    # -- custom media-library endpoints -------------------------------------
    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "gallery/library/",
                self.admin_site.admin_view(self.gallery_library),
                name="catalog_gallery_library",
            ),
            path(
                "gallery/upload/",
                self.admin_site.admin_view(self.gallery_upload),
                name="catalog_gallery_upload",
            ),
            path(
                "<int:pk>/generate-variations/",
                self.admin_site.admin_view(self.generate_variations_view),
                name="catalog_generate_variations",
            ),
        ]
        return custom + urls

    def generate_variations_view(self, request, pk):
        """AJAX: build the color×size matrix on the spot from saved attributes."""
        if request.method != "POST":
            return JsonResponse({"error": "POST required"}, status=405)
        product = Product.objects.filter(pk=pk).first()
        if not product:
            return JsonResponse({"error": "Product not found"}, status=404)
        created = product.generate_variations(overwrite_prices=False)
        return JsonResponse(
            {
                "ok": True,
                "created": created,
                "total": product.variations.count(),
            }
        )

    def gallery_library(self, request):
        q = request.GET.get("q", "").strip()
        assets = MediaAsset.objects.all()
        if q:
            assets = assets.filter(title__icontains=q)
        assets = assets[:600]
        return JsonResponse(
            {
                "assets": [
                    {"id": a.id, "url": a.file.url, "title": a.title}
                    for a in assets
                    if a.file
                ]
            }
        )

    def gallery_upload(self, request):
        if request.method != "POST":
            return JsonResponse({"error": "POST required"}, status=405)
        files = request.FILES.getlist("files")
        out = []
        for f in files:
            asset = MediaAsset.objects.create(file=f)
            out.append({"id": asset.id, "url": asset.file.url, "title": asset.title})
        return JsonResponse({"assets": out})

    # -- save: sync gallery --------------------------------------------------
    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        product = form.instance
        self._sync_gallery(product, form.cleaned_data.get("gallery_data"))

    def _sync_gallery(self, product, raw):
        if raw is None:
            return
        try:
            entries = json.loads(raw or "[]")
        except (ValueError, TypeError):
            return

        keep_ids = []
        for order, entry in enumerate(entries):
            color_id = entry.get("color_id") or None
            is_primary = bool(entry.get("is_primary"))
            image_id = entry.get("image_id")
            if image_id:
                ProductImage.objects.filter(pk=image_id, product=product).update(
                    color_id=color_id, is_primary=is_primary, sort_order=order
                )
                keep_ids.append(image_id)
                continue
            asset = MediaAsset.objects.filter(pk=entry.get("asset_id")).first()
            if not asset or not asset.file:
                continue
            image = ProductImage(
                product=product,
                color_id=color_id,
                is_primary=is_primary,
                sort_order=order,
            )
            image.image.name = asset.file.name  # reference the library file
            image.save()
            keep_ids.append(image.id)

        product.images.exclude(pk__in=keep_ids).delete()

        if product.images.exists() and not product.images.filter(is_primary=True).exists():
            first = product.images.order_by("sort_order", "id").first()
            first.is_primary = True
            first.save(update_fields=["is_primary"])

    # -- list display helpers ----------------------------------------------
    @admin.display(description="")
    def thumb(self, obj):
        img = obj.primary_image
        if img and img.image:
            return format_html(
                '<img src="{}" style="height:42px;width:42px;object-fit:cover;'
                'border-radius:6px;" />',
                img.image.url,
            )
        return "—"

    @admin.display(description="Type")
    def product_kind(self, obj):
        return "Variable" if obj.is_variable else "Simple"

    @admin.display(description="Vars")
    def variation_count(self, obj):
        return obj.variations.count()

    @admin.action(description="Generate missing variations from colors × sizes")
    def generate_variations_action(self, request, queryset):
        total = 0
        for product in queryset:
            total += product.generate_variations(overwrite_prices=False)
        self.message_user(
            request,
            f"Created {total} variation(s). Edit price/stock per row.",
            messages.SUCCESS,
        )

    @admin.action(description="Generate variations & overwrite prices from base")
    def generate_variations_overwrite_prices(self, request, queryset):
        total = 0
        for product in queryset:
            total += product.generate_variations(overwrite_prices=True)
        self.message_user(
            request,
            f"Synced variations ({total} new). Prices updated from base.",
            messages.SUCCESS,
        )


@admin.register(ProductVariation)
class ProductVariationAdmin(admin.ModelAdmin):
    list_display = (
        "product",
        "color",
        "size",
        "price",
        "sale_price",
        "stock",
        "is_active",
    )
    list_filter = ("is_active", "color", "size")
    list_editable = ("price", "sale_price", "stock", "is_active")
    search_fields = ("product__name", "sku")
    autocomplete_fields = ("product", "color", "size")


# ---------------------------------------------------------------------------
# Shop manager role
# ---------------------------------------------------------------------------
from django.contrib.auth import get_user_model  # noqa: E402
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin  # noqa: E402
from django.contrib.auth.forms import UserChangeForm  # noqa: E402
from django.contrib.auth.models import Group, Permission  # noqa: E402

User = get_user_model()

SHOP_MANAGER_GROUP = "Shop Manager"
# Apps a shop manager may administer. Everything else (Pages, Users/Groups)
# stays hidden because they hold no permissions there.
SHOP_MANAGER_APPS = ("catalog", "orders")


def ensure_shop_manager_group():
    """Create/refresh the Shop Manager group with catalog + orders permissions."""
    group, _ = Group.objects.get_or_create(name=SHOP_MANAGER_GROUP)
    perms = Permission.objects.filter(content_type__app_label__in=SHOP_MANAGER_APPS)
    group.permissions.set(perms)
    return group


class ShopUserChangeForm(UserChangeForm):
    shop_manager = forms.BooleanField(
        required=False,
        label="Shop manager",
        help_text=(
            "Gives this user staff access to Products, Orders and media only — "
            "no access to Pages or Users/Groups. Leave superuser unchecked."
        ),
    )

    class Meta(UserChangeForm.Meta):
        model = User

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["shop_manager"].initial = self.instance.groups.filter(
                name=SHOP_MANAGER_GROUP
            ).exists()


class SafaUserAdmin(BaseUserAdmin):
    form = ShopUserChangeForm
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Store role", {"fields": ("shop_manager",)}),
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if "shop_manager" not in form.cleaned_data:
            return
        group = ensure_shop_manager_group()
        if form.cleaned_data["shop_manager"]:
            if not obj.is_staff:
                obj.is_staff = True
                obj.save(update_fields=["is_staff"])
            obj.groups.add(group)
        else:
            obj.groups.remove(group)


try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass
admin.site.register(User, SafaUserAdmin)
