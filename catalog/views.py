from django.db.models import Min, Prefetch, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_GET

from .models import Category, Product, ProductImage, ProductVariation


def _build_hero_slides(products, limit=3):
    """Hero slides from real product photos — featured first, then newest."""
    ranked = sorted(
        [p for p in products if p.primary_image is not None],
        key=lambda p: (not p.is_featured, -p.created_at.timestamp()),
    )
    slides = []
    for product in ranked[:limit]:
        cats = list(product.categories.all())
        eyebrow = " · ".join(c.name for c in cats[:3]) or "New arrivals"
        slides.append(
            {
                "image_url": product.primary_image.image.url,
                "eyebrow": eyebrow,
                "url": product.get_absolute_url(),
                "name": product.name,
            }
        )
    return slides


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

    slides = _build_hero_slides(products)

    sale_items = [p for p in products if p.has_sale][:4]
    latest = sorted(products, key=lambda p: p.created_at, reverse=True)[:8]

    cat_img = _category_image_map()
    featured_categories = list(
        Category.objects.filter(is_active=True, products__isnull=False)
        .distinct()
        .order_by("sort_order")[:8]
    )
    for cat in featured_categories:
        cat.rep_image = (cat.image.url if cat.image else None) or cat_img.get(cat.id)

    # Editorial banners: two generic category features with images
    feature_categories = [c for c in featured_categories if getattr(c, "rep_image", None)][:2]

    return render(
        request,
        "catalog/home.html",
        {
            "slides": slides,
            "feature_categories": feature_categories,
            "sale_items": sale_items,
            "latest": latest,
            "featured_categories": featured_categories,
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
    return render(
        request,
        "catalog/product_detail.html",
        {
            "product": product,
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
                {"id": c.id, "name": c.name, "hex": c.hex_code or "#cccccc"}
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
