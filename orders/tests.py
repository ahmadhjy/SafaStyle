from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from catalog.models import Product, ProductVariation
from orders.models import DeliveryLocality, Governorate, Order


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
        self.mount, _ = Governorate.objects.get_or_create(
            name="Mount Lebanon",
            defaults={"delivery_fee": Decimal("5.00"), "is_active": True},
        )
        self.locality, _ = DeliveryLocality.objects.get_or_create(
            name="Hamra",
            governorate=self.gov,
            defaults={"is_active": True},
        )
        self.aramol, _ = DeliveryLocality.objects.get_or_create(
            name="Aramol",
            governorate=self.mount,
            defaults={"is_active": True},
        )
        self.checkout_url = reverse("orders:checkout")

    def _add_to_cart(self):
        self.client.post(reverse("orders:cart_add", args=[self.variation.id]))

    def _valid_payload(self, token, locality=None, governorate=None):
        loc = locality or self.locality
        return {
            "checkout_token": token,
            "first_name": "Sahar",
            "last_name": "Haj Hasan",
            "country": "Lebanon",
            "governorate": (governorate or loc.governorate).id,
            "locality": loc.id,
            "street_address": "Main St",
            "city": "ignored-for-lebanon",
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


class LocalityDeliveryFeeTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name="Abaya", slug="abaya-fee", base_price=Decimal("20.00")
        )
        self.variation = ProductVariation.objects.create(
            product=self.product, price=Decimal("20.00"), stock=5
        )
        self.beirut, _ = Governorate.objects.get_or_create(
            name="Beirut",
            defaults={"delivery_fee": Decimal("4.00"), "is_active": True},
        )
        self.mount, _ = Governorate.objects.get_or_create(
            name="Mount Lebanon",
            defaults={"delivery_fee": Decimal("5.00"), "is_active": True},
        )
        self.beirut.delivery_fee = Decimal("4.00")
        self.beirut.save(update_fields=["delivery_fee"])
        self.mount.delivery_fee = Decimal("5.00")
        self.mount.save(update_fields=["delivery_fee"])

        self.hamra, _ = DeliveryLocality.objects.get_or_create(
            name="Hamra", governorate=self.beirut, defaults={"is_active": True}
        )
        self.aramol, _ = DeliveryLocality.objects.get_or_create(
            name="Aramol", governorate=self.mount, defaults={"is_active": True}
        )
        self.checkout_url = reverse("orders:checkout")

    def _token_and_cart(self):
        self.client.post(reverse("orders:cart_add", args=[self.variation.id]))
        self.client.get(self.checkout_url)
        return self.client.session["checkout_token"]

    def test_locality_locks_governorate_even_if_client_posts_beirut(self):
        """Customer picks Aramol but tries to force Beirut fee — server blocks it."""
        token = self._token_and_cart()
        resp = self.client.post(
            self.checkout_url,
            {
                "checkout_token": token,
                "first_name": "Sara",
                "last_name": "Test",
                "country": "Lebanon",
                "governorate": self.beirut.id,  # tampered
                "locality": self.aramol.id,
                "street_address": "Street 1",
                "city": "Beirut",  # tampered free text
                "phone": "70123456",
            },
        )
        self.assertEqual(resp.status_code, 302)
        order = Order.objects.get()
        self.assertEqual(order.locality_id, self.aramol.id)
        self.assertEqual(order.governorate_id, self.mount.id)
        self.assertEqual(order.city, "Aramol")
        self.assertEqual(order.delivery_fee, Decimal("5.00"))
        self.assertEqual(order.total, Decimal("25.00"))

    def test_lebanon_requires_locality(self):
        token = self._token_and_cart()
        resp = self.client.post(
            self.checkout_url,
            {
                "checkout_token": token,
                "first_name": "Sara",
                "last_name": "Test",
                "country": "Lebanon",
                "governorate": self.beirut.id,
                "street_address": "Street 1",
                "city": "Hamra",
                "phone": "70123456",
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Order.objects.count(), 0)
        self.assertIn("locality", resp.context["form"].errors)

    def test_existing_orders_keep_free_text_city_without_locality(self):
        """Old orders created before localities stay valid with locality=null."""
        order = Order.objects.create(
            first_name="Old",
            last_name="Customer",
            country="Lebanon",
            street_address="Old street",
            city="Dahye",
            phone="70999999",
            governorate=self.mount,
            delivery_fee=Decimal("5.00"),
            subtotal=Decimal("20.00"),
            total=Decimal("25.00"),
        )
        order.refresh_from_db()
        self.assertIsNone(order.locality_id)
        self.assertEqual(order.city, "Dahye")
        self.assertEqual(Order.objects.filter(pk=order.pk).count(), 1)
