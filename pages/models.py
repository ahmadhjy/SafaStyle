from django.db import models
from django.utils.text import slugify


class SitePage(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    content = models.TextField()
    is_published = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class SiteSetting(models.Model):
    """Singleton-ish store settings."""

    store_name = models.CharField(max_length=120, default="Safa Style")
    tagline = models.CharField(
        max_length=255,
        default="Modest. Modern. Made for you.",
    )
    about = models.TextField(
        blank=True,
        default=(
            "Your new Beirut-based fashion go-to. We're famous for redefining "
            "modest minimalism with a trend-forward approach, all while maintaining "
            "top notch quality, comfort, and most importantly, aesthetic."
        ),
    )
    address = models.CharField(
        max_length=255,
        default="Beirut - Airport Highway - Ziad Rahbani Avenue",
    )
    phone_boutique = models.CharField(max_length=80, default="81 820 915 / 01 820 915")
    phone_shoes = models.CharField(max_length=80, default="76 902 823")
    email = models.EmailField(default="info@safastyle.com")
    instagram_url = models.URLField(
        blank=True, default="https://www.instagram.com/safastyleboutique/"
    )
    instagram_handle = models.CharField(max_length=80, default="@safastyleboutique")
    currency_symbol = models.CharField(max_length=8, default="$")
    default_country = models.CharField(max_length=80, default="Lebanon")

    class Meta:
        verbose_name = "Site settings"
        verbose_name_plural = "Site settings"

    def __str__(self):
        return self.store_name

    @classmethod
    def load(cls):
        obj = cls.objects.first()
        if obj is None:
            obj = cls.objects.create()
        return obj
