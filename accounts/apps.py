from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"
    verbose_name = "Customer accounts"

    def ready(self):
        # Register the signal that keeps a CustomerProfile alongside every user.
        from . import models  # noqa: F401
