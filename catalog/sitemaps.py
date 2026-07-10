from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from catalog.models import Category, Product
from pages.models import SitePage


class ProductSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return Product.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at


class CategorySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return Category.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at


class StaticViewSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.6

    def items(self):
        return ["home", "shop", "contact", "find_us"]

    def location(self, item):
        if item == "home":
            return reverse("catalog:home")
        if item == "shop":
            return reverse("catalog:shop")
        if item == "contact":
            return reverse("pages:contact")
        if item == "find_us":
            return reverse("pages:find_us")
        return "/"


class PageSitemap(Sitemap):
    changefreq = "yearly"
    priority = 0.4

    def items(self):
        return SitePage.objects.filter(is_published=True)

    def location(self, obj):
        return reverse("pages:page", kwargs={"slug": obj.slug})

    def lastmod(self, obj):
        return obj.updated_at
