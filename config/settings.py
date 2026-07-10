"""
Django settings for Safa Style.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _load_env(path):
    """Minimal .env loader (no external dependency)."""
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


_load_env(BASE_DIR / ".env")

SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "django-insecure-sybwh@kbh5y0qz5hkb9lg2_c0n)qt%&q94k7!un#j70y^a94pd",
)

DEBUG = os.environ.get("DEBUG", "true").lower() == "true"

ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if h.strip()
]

INSTALLED_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",
    "catalog",
    "orders",
    "pages",
    "accounts",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "pages.context_processors.site_globals",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql"
        if os.environ.get("DB_ENGINE") == "postgresql"
        else "django.db.backends.sqlite3",
        "NAME": os.environ.get("DB_NAME", BASE_DIR / "db.sqlite3"),
        "USER": os.environ.get("DB_USER", ""),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", ""),
        "PORT": os.environ.get("DB_PORT", ""),
    }
}
if DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3":
    DATABASES["default"]["NAME"] = BASE_DIR / "db.sqlite3"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Beirut"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
# Bump when CSS/JS changes so browsers fetch fresh files (nginx caches /static/ 30 days).
STATIC_CACHE_VERSION = "15"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

SESSION_ENGINE = "django.contrib.sessions.backends.db"
CART_SESSION_KEY = "cart"

# Customer accounts
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "accounts:dashboard"
LOGOUT_REDIRECT_URL = "catalog:home"

JAZZMIN_SETTINGS = {
    "site_title": "Safa Style Admin",
    "site_header": "Safa Style",
    "site_brand": "Safa Style",
    "welcome_sign": "Welcome to Safa Style admin",
    "copyright": "Safa Style Boutique",
    "search_model": ["catalog.Product", "orders.Order"],
    "topmenu_links": [
        {"name": "Storefront", "url": "/", "new_window": True},
        {"model": "catalog.Product"},
        {"model": "orders.Order"},
    ],
    "icons": {
        "catalog.Product": "fas fa-tshirt",
        "catalog.Category": "fas fa-tags",
        "catalog.Color": "fas fa-palette",
        "catalog.Size": "fas fa-ruler",
        "orders.Order": "fas fa-shopping-bag",
        "pages.SitePage": "fas fa-file-alt",
        "pages.SiteSetting": "fas fa-cog",
    },
    "order_with_respect_to": [
        "catalog",
        "orders",
        "pages",
    ],
}

JAZZMIN_UI_TWEAKS = {
    "theme": "flatly",
    "navbar": "navbar-white navbar-light",
    "sidebar": "sidebar-dark-warning",
    "accent": "accent-warning",
}

# ---------------------------------------------------------------------------
# Email (IONOS SMTP). Credentials live in the gitignored .env file.
# If no SMTP user is configured, fall back to the console backend so local
# development never fails and never sends real mail.
# ---------------------------------------------------------------------------
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.ionos.com")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "true").lower() == "true"
EMAIL_USE_SSL = os.environ.get("EMAIL_USE_SSL", "false").lower() == "true"
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_TIMEOUT = int(os.environ.get("EMAIL_TIMEOUT", "20"))

_default_backend = (
    "django.core.mail.backends.smtp.EmailBackend"
    if EMAIL_HOST_USER
    else "django.core.mail.backends.console.EmailBackend"
)
EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND", _default_backend)

DEFAULT_FROM_EMAIL = os.environ.get(
    "DEFAULT_FROM_EMAIL", "Safa Style <info@safastyle.com>"
)
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Where new-order notifications and contact-form messages are delivered.
ORDER_NOTIFICATION_EMAILS = [
    e.strip()
    for e in os.environ.get(
        "ORDER_NOTIFICATION_EMAILS", "info@safastyle.com,sales@safastyle.com"
    ).split(",")
    if e.strip()
]
CONTACT_EMAIL = os.environ.get("CONTACT_EMAIL", "info@safastyle.com")

# SEO / production (override via .env on the droplet)
SITE_URL = os.environ.get("SITE_URL", "https://safastyle.com")

# WooCommerce import (Bluehost temp URL while DNS points at Django)
WOO_BASE_URL = os.environ.get("WOO_BASE_URL", "https://safastyle.com").rstrip("/")
WOO_CONSUMER_KEY = os.environ.get("WOO_CONSUMER_KEY", "")
WOO_CONSUMER_SECRET = os.environ.get("WOO_CONSUMER_SECRET", "")

if not DEBUG:
    CSRF_TRUSTED_ORIGINS = [
        o.strip()
        for o in os.environ.get(
            "CSRF_TRUSTED_ORIGINS", "https://safastyle.com,https://www.safastyle.com"
        ).split(",")
        if o.strip()
    ]
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
