from catalog.models import Category

from .models import SiteSetting


def site_globals(request):
    settings = SiteSetting.load()
    cart = request.session.get("cart", {})
    cart_count = sum(int(i.get("qty", 0)) for i in cart.values())
    cart_total = sum(
        float(i.get("price", 0)) * int(i.get("qty", 0)) for i in cart.values()
    )
    return {
        "site": settings,
        "nav_categories": Category.objects.filter(
            is_active=True, parent__isnull=True, products__is_active=True
        )
        .distinct()
        .order_by("sort_order", "name")[:16],
        "cart_count": cart_count,
        "cart_total": cart_total,
    }
