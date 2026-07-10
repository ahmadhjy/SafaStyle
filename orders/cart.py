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
            "image": (
                variation.product.images_for_color(variation.color)
                .first()
                .image.url
                if variation.product.images_for_color(variation.color).exists()
                else ""
            ),
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
        variations = ProductVariation.objects.select_related(
            "product", "color", "size"
        ).filter(pk__in=ids)
        cart = self.cart.copy()
        for variation in variations:
            item = cart[str(variation.pk)]
            item["variation"] = variation
            item["price"] = Decimal(item["price"])
            item["total"] = item["price"] * item["qty"]
            yield item

    def __len__(self):
        return sum(i["qty"] for i in self.cart.values())

    @property
    def subtotal(self):
        return sum(
            (Decimal(i["price"]) * i["qty"] for i in self.cart.values()),
            Decimal("0.00"),
        )
