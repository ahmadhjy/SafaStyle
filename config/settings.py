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
STATIC_CACHE_VERSION = "38"
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
        "orders.Governorate": "fas fa-map-marked-alt",
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
# Email. Prefer Resend (HTTPS API) when RESEND_API_KEY is set — DigitalOcean
# often blocks outbound SMTP to IONOS (ports 587/465), which causes timeouts.
# Fallback: IONOS SMTP, then console for local dev without credentials.
# ---------------------------------------------------------------------------
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.ionos.com")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "true").lower() == "true"
EMAIL_USE_SSL = os.environ.get("EMAIL_USE_SSL", "false").lower() == "true"
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_TIMEOUT = int(os.environ.get("EMAIL_TIMEOUT", "20"))
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "")

if os.environ.get("EMAIL_BACKEND"):
    EMAIL_BACKEND = os.environ["EMAIL_BACKEND"]
elif RESEND_API_KEY:
    EMAIL_BACKEND = "config.email_backends.ResendEmailBackend"
elif EMAIL_HOST_USER:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

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

# Whish Pay (credentials in .env — never commit secrets)
WHISH_PAY_ENABLED = os.environ.get("WHISH_PAY_ENABLED", "false").lower() == "true"
# During testing, only staff/admin users see and can use Whish Pay.
WHISH_PAY_ADMIN_ONLY = os.environ.get("WHISH_PAY_ADMIN_ONLY", "true").lower() == "true"
WHISH_API_BASE = os.environ.get(
    "WHISH_API_BASE",
    "https://partner.api.sbx.whish.money/itel-service/api",
).rstrip("/")
WHISH_CHANNEL = os.environ.get("WHISH_CHANNEL", "")
WHISH_SECRET = os.environ.get("WHISH_SECRET", "")
# Exact value issued by Whish (no https:// unless they say so).
WHISH_WEBSITE_URL = os.environ.get("WHISH_WEBSITE_URL", "safastyle.com")
WHISH_CURRENCY = os.environ.get("WHISH_CURRENCY", "USD")
WHISH_USER_AGENT = os.environ.get(
    "WHISH_USER_AGENT",
    "SafaStyle/1.0 (https://safastyle.com; info@safastyle.com)",
)
WHISH_TIMEOUT = int(os.environ.get("WHISH_TIMEOUT", "30"))

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
    SECURE_SSL_REDIRECT = os.environ.get("SECURE_SSL_REDIRECT", "true").lower() == "true"
    SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
    X_FRAME_OPTIONS = "DENY"
