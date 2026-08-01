from decimal import Decimal

from django.conf import settings


class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_KEY)
        if not cart:
            cart = self.session[settings.CART_SESSION_KEY] = {}
        self.cart = cart

    def add(self, variation, quantity=1, replace=False):
        key = str(variation.pk)
        qty = max(1, int(quantity))
        if key in self.cart and not replace:
            qty = self.cart[key]["qty"] + qty
        max_stock = variation.stock
        qty = min(qty, max_stock) if max_stock else 0
        if qty <= 0:
            self.remove(variation.pk)
            return False
        self.cart[key] = {
            "qty": qty,
            "price": str(variation.current_price),
            "product_id": variation.product_id,
            "name": variation.product.name,
            "label": variation.label(),
            "sku": variation.sku or "",
            "image": variation.product.image_url_for_color(variation.color),
        }
        self.save()
        return True

    def remove(self, variation_id):
        key = str(variation_id)
        if key in self.cart:
            del self.cart[key]
            self.save()

    def clear(self):
        self.session[settings.CART_SESSION_KEY] = {}
        self.session.modified = True
        self.cart = {}

    def save(self):
        self.session[settings.CART_SESSION_KEY] = self.cart
        self.session.modified = True

    def __iter__(self):
        from catalog.models import ProductVariation

        ids = self.cart.keys()
        variations = (
            ProductVariation.objects.select_related("product", "color", "size")
            .prefetch_related("product__images")
            .filter(pk__in=ids)
        )
        cart = self.cart
        for variation in variations:
            stored = cart.get(str(variation.pk)) or {}
            price = Decimal(str(stored.get("price", variation.current_price)))
            qty = int(stored.get("qty", 0) or 0)
            # Build a fresh dict so we never mutate / re-serialize session data
            # with model instances or Decimal values.
            yield {
                "qty": qty,
                "price": price,
                "total": price * qty,
                "product_id": stored.get("product_id", variation.product_id),
                "name": stored.get("name") or variation.product.name,
                "label": stored.get("label") or variation.label(),
                "sku": stored.get("sku") or variation.sku or "",
                "image": variation.product.image_url_for_color(variation.color),
                "variation": variation,
            }

    def __len__(self):
        return sum(i["qty"] for i in self.cart.values())

    @property
    def subtotal(self):
        return sum(
            (Decimal(i["price"]) * i["qty"] for i in self.cart.values()),
            Decimal("0.00"),
        )
