from pathlib import Path

from django.core.management.base import BaseCommand
from django.utils.text import slugify

from catalog.models import Category, Color, Product, ProductVariation, Size
from pages.models import SitePage, SiteSetting


PRIVACY = """
<h2>Who we are</h2>
<p>Safa Style Boutique. Beirut – Al Asad Highway. Email: info@safastyle.com · Phone/WhatsApp: 81 820 915 / 76 902 823 / 01 820 915. This policy covers our website and in-store services.</p>

<h2>What we collect</h2>
<ul>
  <li><strong>You provide:</strong> name, contact details, delivery address, order details, returns/exchanges info, messages sent to us (email/WhatsApp/contact forms).</li>
  <li><strong>Payments:</strong> card/wallet details are processed by our payment provider(s); we receive only confirmation data (no full card numbers).</li>
  <li><strong>Automatically:</strong> device and browser data, IP, pages viewed, time on site, cookies/IDs, approximate location.</li>
  <li><strong>Media/uploads:</strong> if you upload images, avoid EXIF location data.</li>
</ul>

<h2>Why we use your data</h2>
<ul>
  <li>Process and deliver orders, handle returns, and provide customer support.</li>
  <li>Create and maintain your account and order history.</li>
  <li>Send service and marketing messages (you can opt out any time).</li>
  <li>Improve site performance, prevent fraud, and keep our services secure.</li>
  <li>Comply with law and enforce our terms.</li>
</ul>

<h2>Cookies &amp; analytics</h2>
<p>We use cookies and similar tech to keep you logged in, remember preferences, and measure performance (e.g., analytics). You can block cookies in your browser; some features may stop working.</p>

<h2>Embedded content &amp; third parties</h2>
<p>Our site may include content or widgets from third parties (e.g., Instagram). These services may collect data per their own policies. We also share limited data with payment processors, delivery partners, email/SMS providers, and analytics/security tools. We do not sell your personal data.</p>

<h2>How long we keep data</h2>
<ul>
  <li>Order and account records: kept as long as needed for accounting, legal, and customer-service purposes.</li>
  <li>Marketing consent and preferences: until you opt out or ask us to delete.</li>
  <li>Technical logs/analytics: kept for a limited time needed for security and reporting.</li>
</ul>

<h2>Your choices &amp; rights</h2>
<p>Depending on your location, you may have the right to access, correct, delete, restrict or object to processing, and receive a copy of your data. You can also opt out of marketing at any time.</p>

<h2>Security</h2>
<p>We use administrative, technical, and physical safeguards to protect your data. No method is 100% secure, but we work to keep your information safe.</p>

<h2>Children</h2>
<p>Our site is not directed to children under 13. If you believe a child provided data, contact us to remove it.</p>

<h2>Changes</h2>
<p>We may update this policy. We'll post the new date here. Continued use of our services means you accept the changes.</p>

<h2>Contact</h2>
<p>Safa Style Boutique — Beirut, Al Asad Highway<br>info@safastyle.com · 81 820 915 / 76 902 823 / 01 820 915</p>
"""

EXCHANGE = """
<h2>Overview</h2>
<p>Store: Safa Style Boutique — Beirut, Al Asad Highway. Contact: info@safastyle.com · 81 820 915 · 76 902 823 · 01 820 915.</p>
<ul>
  <li>Exchange within <strong>3 days</strong> of purchase/delivery.</li>
  <li>Items must be <strong>unused, unwashed, unaltered</strong>, with original tags/packaging.</li>
  <li>Keep your receipt or order confirmation.</li>
</ul>

<h2>Non-returnable items</h2>
<ul>
  <li>Hijab/underscarf and other intimate/sanitary items.</li>
  <li>Gift cards.</li>
  <li>Final sale/clearance items (marked sale).</li>
  <li>Digital/downloadable products (if any).</li>
  <li>Items not in original condition or missing parts not due to our error.</li>
</ul>

<h2>Exchanges</h2>
<p>Exchanges are like-for-like (size/color) when stock allows. If the item is defective or damaged on arrival, we'll replace it or refund you.</p>
"""

TERMS = """
<h2>Welcome</h2>
<p>Welcome to Safa Style Boutique. By browsing and placing orders on this website you agree to provide accurate contact and delivery details, and to pay for confirmed orders (including cash on delivery where offered).</p>

<h2>Products</h2>
<p>Colors and textures may vary slightly from photos depending on screen settings. Measurements are approximate.</p>

<h2>Orders</h2>
<p>We may contact you by phone or WhatsApp to confirm orders. We reserve the right to cancel orders if an item is unavailable — in that case we will notify you promptly.</p>

<h2>Delivery</h2>
<p>Delivery times depend on your location. For details contact +961 81 820 915.</p>

<h2>Liability</h2>
<p>To the fullest extent permitted by law, Safa Style Boutique is not liable for indirect or consequential losses arising from use of the site.</p>

<h2>Contact</h2>
<p>info@safastyle.com · Beirut – Airport Highway – Ziad Rahbani Avenue</p>
"""


class Command(BaseCommand):
    help = "Seed site settings, policy pages, colors/sizes, categories, and a demo product"

    def add_arguments(self, parser):
        parser.add_argument(
            "--with-demo",
            action="store_true",
            help="Create a sample Aura Set product when the catalog is empty",
        )

    def handle(self, *args, **options):
        SiteSetting.load()
        self.stdout.write("Site settings ready")

        pages = {
            "privacy-policy": ("Privacy Policy", PRIVACY),
            "exchange-policy": ("Exchange Policy", EXCHANGE),
            "terms": ("Terms", TERMS),
        }
        for slug, (title, content) in pages.items():
            SitePage.objects.update_or_create(
                slug=slug,
                defaults={"title": title, "content": content, "is_published": True},
            )
        self.stdout.write("Policy pages seeded")

        color_defs = [
            ("Black", "#111111"),
            ("White", "#f5f5f5"),
            ("Off White", "#f3efe6"),
            ("Ivory", "#fffff0"),
            ("Cream", "#f5f0e6"),
            ("Beige", "#d7c4a8"),
            ("Sand", "#d2b48c"),
            ("Camel", "#c19a6b"),
            ("Taupe", "#8b7d72"),
            ("Nude", "#e3bc9a"),
            ("Brown", "#6b4a2e"),
            ("Mocha", "#7b5e57"),
            ("Chocolate", "#3d2314"),
            ("Burgundy", "#6e1f2b"),
            ("Wine", "#722f37"),
            ("Red", "#8b0000"),
            ("Rust", "#b7410e"),
            ("Coral", "#e07a5f"),
            ("Peach", "#ffcba4"),
            ("Pink", "#e8a0b0"),
            ("Rose", "#c4868b"),
            ("Dusty Pink", "#d4a5a5"),
            ("Lavender", "#b8a9c9"),
            ("Plum", "#5c2e5c"),
            ("Navy Blue", "#1b2a4a"),
            ("Royal Blue", "#1e3a8a"),
            ("Light Blue", "#a8c8e8"),
            ("Sky Blue", "#87ceeb"),
            ("Gray", "#8a8a8a"),
            ("Light Grey", "#c8c8c8"),
            ("Charcoal", "#36454f"),
            ("Silver", "#a8a8a8"),
            ("Olive Green", "#556b2f"),
            ("Forest Green", "#2d5016"),
            ("Emerald", "#046307"),
            ("Mint Green", "#9fd3c0"),
            ("Teal", "#2fbfa8"),
            ("Khaki", "#c3b091"),
            ("Gold", "#c9a227"),
            ("Mustard", "#e1ad01"),
            ("Copper", "#b87333"),
        ]
        for i, (name, hex_code) in enumerate(color_defs):
            Color.objects.update_or_create(
                slug=slugify(name),
                defaults={"name": name, "hex_code": hex_code, "sort_order": i},
            )

        for i, name in enumerate(["1", "2", "3", "S", "M", "L", "XL", "36", "37", "38", "39", "40"]):
            Size.objects.update_or_create(
                slug=slugify(name),
                defaults={"name": name, "sort_order": i},
            )

        cats = [
            "Accessories",
            "Bags",
            "Basics",
            "Cardigans",
            "Coats",
            "Dresses",
            "Jackets",
            "Pants",
            "Ramadan Specials",
            "Scarfs",
            "Sets",
            "Shawls",
            "Shoes",
            "Skirts",
            "Socks",
            "Tops",
            "Vests",
        ]
        for i, name in enumerate(cats):
            Category.objects.update_or_create(
                slug=slugify(name),
                defaults={
                    "name": name,
                    "is_featured": i < 8,
                    "sort_order": i,
                    "is_active": True,
                },
            )

        # Demo product only when explicitly seeding an empty dev catalog.
        if not Product.objects.exists() and options.get("with_demo"):
            product = Product.objects.create(
                name="Aura Set",
                short_description="Sleek sport set with wide pants.",
                description=(
                    "The Aura Sport Set features a coordinated top and bottom with a clean, "
                    "modern design made for easy movement and everyday comfort."
                ),
                measurements="Length Top: 75cm\nLength Pant: 105cm",
                base_price="45.00",
                base_sale_price="35.00",
                is_active=True,
                is_featured=True,
                is_on_sale=True,
            )
            product.categories.add(Category.objects.get(slug="sets"))
            black = Color.objects.get(slug="black")
            brown = Color.objects.get(slug="brown")
            product.available_colors.add(black, brown)
            for s in Size.objects.filter(name__in=["1", "2", "3"]):
                product.available_sizes.add(s)
            product.generate_variations()
            ProductVariation.objects.filter(product=product).update(stock=10)
            self.stdout.write(self.style.SUCCESS("Demo product Aura Set created"))

        self.stdout.write(self.style.SUCCESS("Seed complete"))
