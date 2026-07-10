from django.db.models import Min, Prefetch, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from .models import Category, Product, ProductImage, ProductVariation
from .category_icons import accent_for_slug, icon_static_path


# Homepage hero banners (wide ~2.4:1 PNGs in static/img/banners/).
HERO_BANNER_SLIDES = (
    {
        "image": "img/banners/banner1.png",
        "width": 1942,
        "height": 809,
        "eyebrow": "New Arrivals",
        "object_position": "center center",
    },
    {
        "image": "img/banners/banner2.png",
        "width": 1973,
        "height": 797,
        "eyebrow": "Sets",
        "object_position": "62% center",
    },
    {
        "image": "img/banners/banner3.png",
        "width": 1973,
        "height": 797,
        "eyebrow": "Accessories",
        "object_position": "center center",
    },
)


def hero_slides():
    return HERO_BANNER_SLIDES


FEATURE_EDITORIAL = (
    {"slug": "sets", "name": "Sets", "image": "img/featured/featured1.png"},
    {"slug": "bags", "name": "Bags", "image": "img/featured/featured2.png"},
)


def feature_editorial_boxes():
    """Homepage editorial tiles — Sets + Bags with dedicated artwork."""
    boxes = []
    for i, item in enumerate(FEATURE_EDITORIAL):
        category, _ = Category.objects.get_or_create(
            slug=item["slug"],
            defaults={
                "name": item["name"],
                "is_active": True,
                "is_featured": True,
                "sort_order": i,
            },
        )
        updates = {}
        if category.name != item["name"]:
            updates["name"] = item["name"]
        if not category.is_active:
            updates["is_active"] = True
        if not category.is_featured:
            updates["is_featured"] = True
        if category.sort_order != i:
            updates["sort_order"] = i
        if updates:
            for key, value in updates.items():
                setattr(category, key, value)
            category.save(update_fields=list(updates.keys()))

        boxes.append(
            {
                "name": category.name,
                "url": category.get_absolute_url(),
                "image": item["image"],
            }
        )
    return boxes


def _home_categories():
    """All active categories for the homepage rail (even when empty)."""
    cats = list(
        Category.objects.filter(is_active=True, parent__isnull=True).order_by(
            "sort_order", "name"
        )
    )
    for i, cat in enumerate(cats):
        cat.icon_static = icon_static_path(cat.slug)
        cat.tile_accent = accent_for_slug(cat.slug, i)
        cat.use_icon = not bool(cat.image)
    return cats


def _category_image_map():
    """Representative image URL for each category (from its products)."""
    mapping = {}
    images = (
        ProductImage.objects.filter(color__isnull=True)
        .select_related("product")
        .prefetch_related("product__categories")
        .order_by("sort_order", "id")
    )
    for img in images:
        for cat in img.product.categories.all():
            mapping.setdefault(cat.id, img.image.url)
    return mapping


def home(request):
    products = list(
        Product.objects.filter(is_active=True)
        .prefetch_related(
            Prefetch("images", queryset=ProductImage.objects.select_related("color").order_by("sort_order")),
            "categories",
            "available_colors",
            "available_sizes",
        )
        .distinct()
    )

    slides = hero_slides()

    sale_items = [p for p in products if p.has_sale][:4]
    latest = sorted(products, key=lambda p: p.created_at, reverse=True)[:8]

    home_categories = _home_categories()

    # Editorial feature tiles (Sets + Bags) with dedicated artwork.
    feature_editorial = feature_editorial_boxes()

    return render(
        request,
        "catalog/home.html",
        {
            "slides": slides,
            "feature_editorial": feature_editorial,
            "sale_items": sale_items,
            "latest": latest,
            "home_categories": home_categories,
        },
    )


def shop(request):
    qs = (
        Product.objects.filter(is_active=True)
        .prefetch_related(
            Prefetch(
                "images",
                queryset=ProductImage.objects.select_related("color").order_by("sort_order"),
            ),
            "categories",
            "available_colors",
            "available_sizes",
        )
        .distinct()
    )
    category_slug = request.GET.get("category")
    q = request.GET.get("q", "").strip()
    color = request.GET.get("color")
    size = request.GET.get("size")
    on_sale = request.GET.get("sale")
    sort = request.GET.get("sort", "new")

    active_category = None
    if category_slug:
        active_category = get_object_or_404(Category, slug=category_slug, is_active=True)
        qs = qs.filter(categories=active_category)
    if q:
        qs = qs.filter(
            Q(name__icontains=q)
            | Q(short_description__icontains=q)
            | Q(description__icontains=q)
        )
    if color:
        qs = qs.filter(variations__color__slug=color, variations__is_active=True)
    if size:
        qs = qs.filter(variations__size__slug=size, variations__is_active=True)
    if on_sale:
        qs = qs.filter(Q(is_on_sale=True) | Q(base_sale_price__isnull=False))

    if sort == "price_asc":
        qs = qs.annotate(min_price=Min("variations__price")).order_by("min_price")
    elif sort == "price_desc":
        qs = qs.annotate(min_price=Min("variations__price")).order_by("-min_price")
    else:
        qs = qs.order_by("-created_at")

    qs = qs.distinct()
    return render(
        request,
        "catalog/shop.html",
        {
            "products": qs,
            "active_category": active_category,
            "q": q,
            "sort": sort,
        },
    )


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug, is_active=True)
    qs = (
        Product.objects.filter(is_active=True, categories=category)
        .prefetch_related(
            Prefetch(
                "images",
                queryset=ProductImage.objects.select_related("color").order_by("sort_order"),
            ),
            "categories",
            "available_colors",
            "available_sizes",
        )
        .distinct()
        .order_by("-created_at")
    )
    return render(
        request,
        "catalog/shop.html",
        {
            "products": qs,
            "active_category": category,
            "q": "",
            "sort": "new",
        },
    )


def product_detail(request, slug):
    qs = Product.objects.prefetch_related(
        "images__color",
        "variations__color",
        "variations__size",
        "categories",
        "available_colors",
        "available_sizes",
    )
    # Staff can preview inactive/draft products straight from the admin.
    if not request.user.is_staff:
        qs = qs.filter(is_active=True)
    product = get_object_or_404(qs, slug=slug)
    is_preview = product.is_active is False
    variations = list(product.variations.filter(is_active=True))
    variation_payload = [
        {
            "id": v.id,
            "color_id": v.color_id,
            "size_id": v.size_id,
            "price": str(v.price),
            "sale_price": str(v.sale_price) if v.sale_price is not None else None,
            "current_price": str(v.current_price),
            "stock": v.stock,
            "in_stock": v.in_stock,
            "label": v.label(),
        }
        for v in variations
    ]
    images_by_color = {}
    for img in product.images.all():
        key = str(img.color_id) if img.color_id else "default"
        images_by_color.setdefault(key, []).append(
            {
                "url": img.image.url,
                "alt": img.alt_text or product.name,
            }
        )

    related = (
        Product.objects.filter(is_active=True, categories__in=product.categories.all())
        .exclude(pk=product.pk)
        .prefetch_related("images", "available_colors", "available_sizes")
        .distinct()[:8]
    )
    gallery_images = []
    seen_urls: set[str] = set()
    for img in product.images.all():
        if not img.image:
            continue
        url = img.image.url
        if url in seen_urls:
            continue
        seen_urls.add(url)
        gallery_images.append(img)
    return render(
        request,
        "catalog/product_detail.html",
        {
            "product": product,
            "gallery_images": gallery_images,
            "variations_json": variation_payload,
            "images_by_color": images_by_color,
            "related": related,
            "is_preview": is_preview,
        },
    )


# json_script in template handles serialization; keep payload as Python objects.


@require_GET
def quick_view(request, slug):
    """JSON payload powering the storefront quick-view modal."""
    product = get_object_or_404(
        Product.objects.prefetch_related(
            "images__color",
            "variations__color",
            "variations__size",
            "available_colors",
            "available_sizes",
            "categories",
        ),
        slug=slug,
        is_active=True,
    )
    variations = [
        {
            "id": v.id,
            "color_id": v.color_id,
            "size_id": v.size_id,
            "price": str(v.price),
            "sale_price": str(v.sale_price) if v.sale_price is not None else None,
            "current_price": str(v.current_price),
            "stock": v.stock,
            "in_stock": v.in_stock,
            "label": v.label(),
        }
        for v in product.variations.filter(is_active=True)
    ]
    images_by_color = {}
    for img in product.images.all():
        key = str(img.color_id) if img.color_id else "default"
        images_by_color.setdefault(key, []).append(
            {"url": img.image.url, "alt": img.alt_text or product.name}
        )

    def _preview_url(color_id):
        key = str(color_id)
        if key in images_by_color and images_by_color[key]:
            return images_by_color[key][0]["url"]
        swatches = product.card_color_swatches
        for sw in swatches:
            if sw["id"] == color_id:
                return sw["image"]
        return (images_by_color.get("default") or [{}])[0].get("url", "")

    return JsonResponse(
        {
            "ok": True,
            "id": product.id,
            "name": product.name,
            "url": product.get_absolute_url(),
            "short_description": product.short_description,
            "price": str(product.display_price),
            "regular_price": str(product.display_regular_price),
            "has_sale": product.has_sale,
            "is_variable": product.is_variable,
            "colors": [
                {
                    "id": c.id,
                    "name": c.name,
                    "hex": c.hex_code or "#cccccc",
                    "preview_image": _preview_url(c.id),
                }
                for c in product.available_colors.all()
            ],
            "sizes": [
                {"id": s.id, "name": s.name} for s in product.available_sizes.all()
            ],
            "variations": variations,
            "images_by_color": images_by_color,
        }
    )


@require_GET
def variation_api(request, product_id):
    """Lightweight JSON for color/size selection."""
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    color_id = request.GET.get("color")
    size_id = request.GET.get("size")
    qs = product.variations.filter(is_active=True)
    if color_id:
        qs = qs.filter(color_id=color_id)
    if size_id:
        qs = qs.filter(size_id=size_id)
    variation = qs.first()
    if not variation:
        return JsonResponse({"ok": False, "error": "Variation not found"}, status=404)

    images = [
        {"url": img.image.url, "alt": img.alt_text or product.name}
        for img in product.images_for_color(variation.color)
    ]
    return JsonResponse(
        {
            "ok": True,
            "id": variation.id,
            "price": str(variation.price),
            "sale_price": str(variation.sale_price)
            if variation.sale_price is not None
            else None,
            "current_price": str(variation.current_price),
            "stock": variation.stock,
            "in_stock": variation.in_stock,
            "label": variation.label(),
            "images": images,
        }
    )
