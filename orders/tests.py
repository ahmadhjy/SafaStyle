from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from catalog.models import Product, ProductVariation
from orders.models import Governorate, Order


class DuplicateOrderTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name="Test Set", slug="test-set", base_price=Decimal("20.00")
        )
        self.variation = ProductVariation.objects.create(
            product=self.product, price=Decimal("20.00"), stock=10
        )
        self.gov, _ = Governorate.objects.get_or_create(
            name="Beirut",
            defaults={"delivery_fee": Decimal("4.00"), "is_active": True},
        )
        self.checkout_url = reverse("orders:checkout")

    def _add_to_cart(self):
        self.client.post(reverse("orders:cart_add", args=[self.variation.id]))

    def _valid_payload(self, token):
        return {
            "checkout_token": token,
            "first_name": "Sahar",
            "last_name": "Haj Hasan",
            "country": "Lebanon",
            "governorate": self.gov.id,
            "street_address": "Main St",
            "city": "Dahye",
            "phone": "71599118",
        }

    def _get_token(self):
        self.client.get(self.checkout_url)
        return self.client.session["checkout_token"]

    def test_single_order_created_on_valid_submit(self):
        self._add_to_cart()
        token = self._get_token()
        resp = self.client.post(self.checkout_url, self._valid_payload(token))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Order.objects.count(), 1)

    def test_duplicate_submit_with_same_token_does_not_create_second_order(self):
        """The classic 'client thought it failed and resubmitted' scenario."""
        self._add_to_cart()
        token = self._get_token()
        payload = self._valid_payload(token)

        first = self.client.post(self.checkout_url, payload)
        self.assertEqual(first.status_code, 302)

        # Client hits back / resubmits the same page (same token). Cart may even
        # still look full on their side. Re-add + resubmit with the stale token.
        self._add_to_cart()
        second = self.client.post(self.checkout_url, payload)

        self.assertEqual(second.status_code, 302)
        self.assertEqual(Order.objects.count(), 1)

    def test_missing_token_is_rejected(self):
        self._add_to_cart()
        self._get_token()
        payload = self._valid_payload("")
        resp = self.client.post(self.checkout_url, payload)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Order.objects.count(), 0)
