from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class CustomerProfile(models.Model):
    """Saved shipping / contact details so returning shoppers can check out fast.

    First name, last name and email live on the User; everything else that the
    checkout needs is mirrored here and pre-filled on the checkout page.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    phone = models.CharField(max_length=40, blank=True)
    company = models.CharField(max_length=150, blank=True)
    country = models.CharField(max_length=100, default="Lebanon", blank=True)
    street_address = models.CharField(max_length=255, blank=True)
    apartment = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=120, blank=True)
    postcode = models.CharField(max_length=40, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile for {self.user}"

    def checkout_initial(self):
        """Values used to pre-fill the checkout form for a logged-in shopper."""
        user = self.user
        return {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "phone": self.phone,
            "company": self.company,
            "country": self.country or "Lebanon",
            "street_address": self.street_address,
            "apartment": self.apartment,
            "city": self.city,
            "postcode": self.postcode,
        }

    def update_from_order(self, order):
        """Remember the address a shopper just used, for next time."""
        self.phone = order.phone or self.phone
        self.company = order.company or self.company
        self.country = order.country or self.country
        self.street_address = order.street_address or self.street_address
        self.apartment = order.apartment or self.apartment
        self.city = order.city or self.city
        self.postcode = order.postcode or self.postcode
        self.save()


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def ensure_profile(sender, instance, created, **kwargs):
    if created:
        CustomerProfile.objects.get_or_create(user=instance)
