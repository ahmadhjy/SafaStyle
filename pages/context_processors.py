from django.conf import settings

from catalog.models import Category

from .models import SiteSetting


def site_globals(request):
    settings_obj = SiteSetting.load()
    cart = request.session.get("cart", {})
    cart_count = sum(int(i.get("qty", 0)) for i in cart.values())
    cart_total = sum(
        float(i.get("price", 0)) * int(i.get("qty", 0)) for i in cart.values()
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
        # Quick-view / bag / qty steppers only needed on shop + cart flows.
        "needs_store_js": namespace in ("catalog", "orders"),
    }
