from django.conf import settings

from catalog.models import Category

from .models import SiteSetting


def site_globals(request):
    settings_obj = SiteSetting.load()
    cart = request.session.get("cart", {})
    cart_count = 0
    cart_total = 0.0
    cart_preview = []
    for key, item in cart.items():
        qty = int(item.get("qty", 0) or 0)
        if qty <= 0:
            continue
        price = float(item.get("price", 0) or 0)
        line_total = price * qty
        cart_count += qty
        cart_total += line_total
        cart_preview.append(
            {
                "variation_id": key,
                "name": item.get("name") or "Item",
                "label": item.get("label") or "",
                "qty": qty,
                "price": price,
                "total": line_total,
                "image": item.get("image") or "",
            }
        )
    namespace = getattr(request.resolver_match, "namespace", "") or ""
    site_url = settings.SITE_URL.rstrip("/")
    canonical_url = f"{site_url}{request.path}"
    return {
        "site": settings_obj,
        "site_url": site_url,
        "canonical_url": canonical_url,
        "static_version": settings.STATIC_CACHE_VERSION,
        "nav_categories": Category.objects.filter(
            is_active=True, parent__isnull=True, products__is_active=True
        )
        .distinct()
        .order_by("sort_order", "name")[:16],
        "cart_count": cart_count,
        "cart_total": cart_total,
        "cart_preview": cart_preview,
        # Quick-view / bag / qty steppers only needed on shop + cart flows.
        "needs_store_js": namespace in ("catalog", "orders"),
    }
