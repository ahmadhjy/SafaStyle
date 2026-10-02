from django.test import TestCase
from unittest.mock import patch

from catalog.models import Product, ProductVariation

class HomepageSectionsTests(TestCase):
    @patch("catalog.views.feature_editorial_boxes", return_value=[])
    def test_new_arrivals_excludes_all_sale_products_before_limit(self, editorial):
        regular = [Product.objects.create(name=f"Regular {i}", base_price=20) for i in range(10)]
        for i in range(6):
            Product.objects.create(name=f"Sale {i}", base_price=20, base_sale_price=15)
        variable = Product.objects.create(name="Variable sale", base_price=20)
        ProductVariation.objects.create(product=variable, price=20, sale_price=15, stock=2)
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([p.pk for p in response.context["latest"]], [p.pk for p in reversed(regular[-8:])])
        self.assertEqual(len(response.context["sale_items"]), 4)
        self.assertTrue(all(p.has_sale for p in response.context["sale_items"]))
