from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
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
            "payment_method": "cod",
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
                "payment_method": "cod",
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
                "payment_method": "cod",
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


@override_settings(
    WHISH_PAY_ENABLED=True,
    WHISH_PAY_ADMIN_ONLY=True,
    WHISH_CHANNEL="test-channel",
    WHISH_SECRET="test-secret",
    WHISH_WEBSITE_URL="safastyle.com",
    WHISH_API_BASE="https://partner.api.sbx.whish.money/itel-service/api",
    SITE_URL="https://safastyle.com",
)
class WhishPayCheckoutTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.staff = User.objects.create_user(
            username="admin_tester", password="pass", is_staff=True
        )
        self.customer = User.objects.create_user(
            username="customer", password="pass", is_staff=False
        )
        self.product = Product.objects.create(
            name="Whish Set", slug="whish-set", base_price=Decimal("20.00")
        )
        self.variation = ProductVariation.objects.create(
            product=self.product, price=Decimal("20.00"), stock=5
        )
        self.beirut, _ = Governorate.objects.get_or_create(
            name="Beirut",
            defaults={"delivery_fee": Decimal("4.00"), "is_active": True},
        )
        self.hamra, _ = DeliveryLocality.objects.get_or_create(
            name="Hamra", governorate=self.beirut, defaults={"is_active": True}
        )
        self.checkout_url = reverse("orders:checkout")

    def _payload(self, token, method="whish"):
        return {
            "checkout_token": token,
            "first_name": "Admin",
            "last_name": "Tester",
            "country": "Lebanon",
            "governorate": self.beirut.id,
            "locality": self.hamra.id,
            "street_address": "Test St",
            "city": "Hamra",
            "phone": "70111111",
            "payment_method": method,
        }

    def test_regular_customer_cannot_use_whish(self):
        self.client.login(username="customer", password="pass")
        self.client.post(reverse("orders:cart_add", args=[self.variation.id]))
        self.client.get(self.checkout_url)
        token = self.client.session["checkout_token"]
        resp = self.client.post(self.checkout_url, self._payload(token, "whish"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Order.objects.count(), 0)

    @patch("orders.views.create_payment", return_value="https://whish.money/pay/test")
    def test_staff_whish_checkout_redirects_to_collect_url(self, _mock_create):
        self.client.login(username="admin_tester", password="pass")
        self.client.post(reverse("orders:cart_add", args=[self.variation.id]))
        self.client.get(self.checkout_url)
        token = self.client.session["checkout_token"]
        resp = self.client.post(self.checkout_url, self._payload(token, "whish"))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, "https://whish.money/pay/test")
        order = Order.objects.get()
        self.assertEqual(order.payment_method, Order.PaymentMethod.WHISH)
        self.assertEqual(order.payment_status, Order.PaymentStatus.AWAITING)
        self.assertTrue(order.whish_external_id)
        self.assertEqual(order.whish_collect_url, "https://whish.money/pay/test")
        # Stock held until Whish confirms payment.
        self.variation.refresh_from_db()
        self.assertEqual(self.variation.stock, 5)

    @patch("orders.views.reconcile_whish_payment")
    def test_success_callback_reconciles(self, mock_reconcile):
        order = Order.objects.create(
            first_name="A",
            last_name="B",
            country="Lebanon",
            street_address="S",
            city="Hamra",
            phone="70111111",
            payment_method=Order.PaymentMethod.WHISH,
            payment_status=Order.PaymentStatus.AWAITING,
            whish_external_id="abc123",
            subtotal=Decimal("20"),
            delivery_fee=Decimal("4"),
            total=Decimal("24"),
        )
        mock_reconcile.return_value = (order, "success")
        url = reverse("orders:whish_callback_success")
        resp = self.client.get(url, {"externalId": "abc123", "order": order.order_number})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content, b"ok")
        mock_reconcile.assert_called_once()


class CartStockSyncTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            name="Scarce Set", slug="scarce-set", base_price=Decimal("20.00")
        )
        self.variation = ProductVariation.objects.create(
            product=self.product, price=Decimal("20.00"), stock=2
        )
        self.gov, _ = Governorate.objects.get_or_create(
            name="Beirut",
            defaults={"delivery_fee": Decimal("4.00"), "is_active": True},
        )
        self.locality, _ = DeliveryLocality.objects.get_or_create(
            name="Hamra",
            governorate=self.gov,
            defaults={"is_active": True},
        )
        self.checkout_url = reverse("orders:checkout")

    def _payload(self, token):
        return {
            "checkout_token": token,
            "first_name": "Sara",
            "last_name": "Test",
            "country": "Lebanon",
            "governorate": self.gov.id,
            "locality": self.locality.id,
            "street_address": "Street 1",
            "city": "Hamra",
            "phone": "70123456",
            "payment_method": "cod",
        }

    def test_sync_removes_out_of_stock_items_from_bag(self):
        self.client.post(reverse("orders:cart_add", args=[self.variation.id]))
        self.variation.stock = 0
        self.variation.save(update_fields=["stock", "updated_at"])
        resp = self.client.get(reverse("orders:cart"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "out of stock")
        session_cart = self.client.session.get("cart", {})
        self.assertEqual(session_cart, {})

    def test_checkout_blocked_when_item_goes_out_of_stock(self):
        self.client.post(reverse("orders:cart_add", args=[self.variation.id]))
        self.client.get(self.checkout_url)
        token = self.client.session["checkout_token"]
        self.variation.stock = 0
        self.variation.save(update_fields=["stock", "updated_at"])
        resp = self.client.post(self.checkout_url, self._payload(token))
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url, reverse("orders:cart"))
        self.assertEqual(Order.objects.count(), 0)

    def test_qty_clamped_when_stock_drops(self):
        self.client.post(
            reverse("orders:cart_add", args=[self.variation.id]),
            {"quantity": 2},
        )
        self.variation.stock = 1
        self.variation.save(update_fields=["stock", "updated_at"])
        resp = self.client.get(reverse("orders:cart"))
        self.assertEqual(resp.status_code, 200)
        session_cart = self.client.session.get("cart", {})
        self.assertEqual(session_cart[str(self.variation.id)]["qty"], 1)
