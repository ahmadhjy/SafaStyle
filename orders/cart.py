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
        if not variation.is_active or not variation.product.is_active:
            self.remove(variation.pk)
            return False
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

    def sync_stock(self):
        """Align bag lines with live stock. Returns human-readable change notes.

        Removes out-of-stock / inactive variations and clamps quantities so a
        stale session cannot check out items that sold out after they were added.
        """
        from catalog.models import ProductVariation

        notes = []
        ids = list(self.cart.keys())
        if not ids:
            return notes

        variations = {
            str(v.pk): v
            for v in ProductVariation.objects.select_related("product", "color", "size")
            .prefetch_related("product__images")
            .filter(pk__in=ids)
        }
        changed = False

        for key in list(self.cart.keys()):
            stored = self.cart.get(key) or {}
            qty = int(stored.get("qty", 0) or 0)
            name = stored.get("name") or "Item"
            label = stored.get("label") or ""
            label_bit = f" ({label})" if label else ""
            variation = variations.get(key)

            if (
                not variation
                or not variation.is_active
                or not variation.product.is_active
                or variation.stock <= 0
            ):
                notes.append(f"{name}{label_bit} is out of stock and was removed from your bag.")
                del self.cart[key]
                changed = True
                continue

            if qty > variation.stock:
                stored["qty"] = variation.stock
                notes.append(
                    f"{name}{label_bit} quantity was reduced to {variation.stock} "
                    "(only that many left)."
                )
                changed = True

            # Keep price / image / label fresh for the bag preview.
            new_price = str(variation.current_price)
            new_name = variation.product.name
            new_label = variation.label()
            new_sku = variation.sku or ""
            new_image = variation.product.image_url_for_color(variation.color)
            if (
                stored.get("price") != new_price
                or stored.get("name") != new_name
                or stored.get("label") != new_label
                or stored.get("sku") != new_sku
                or stored.get("image") != new_image
                or stored.get("product_id") != variation.product_id
            ):
                stored["price"] = new_price
                stored["name"] = new_name
                stored["label"] = new_label
                stored["sku"] = new_sku
                stored["image"] = new_image
                stored["product_id"] = variation.product_id
                changed = True

            self.cart[key] = stored

        if changed:
            self.save()
        return notes

    def unavailable_lines(self):
        """Return list of (name, reason) for lines that cannot be purchased."""
        problems = []
        for item in self:
            variation = item.get("variation")
            name = item.get("name") or "Item"
            label = item.get("label") or ""
            label_bit = f" ({label})" if label else ""
            if not variation or not variation.is_active or not variation.product.is_active:
                problems.append((f"{name}{label_bit}", "no longer available"))
            elif variation.stock <= 0:
                problems.append((f"{name}{label_bit}", "out of stock"))
            elif item["qty"] > variation.stock:
                problems.append(
                    (
                        f"{name}{label_bit}",
                        f"only {variation.stock} left (you have {item['qty']} in your bag)",
                    )
                )
        return problems

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
                "in_stock": variation.is_active
                and variation.product.is_active
                and variation.stock >= qty
                and qty > 0,
            }

    def __len__(self):
        return sum(i["qty"] for i in self.cart.values())

    @property
    def subtotal(self):
        return sum(
            (Decimal(i["price"]) * i["qty"] for i in self.cart.values()),
            Decimal("0.00"),
        )
