"""Settings for the ControlFinan Django port (parity with controlfinan-rails8-hotwire)."""

import os
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-secret-key-change-me")
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "*").split(",")

INSTALLED_APPS = [
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "finance",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    # Flash messages live in a signed cookie, like Rails' flash.
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "finance.auth.AuthenticationMiddleware",
]

# WhiteNoise serves the collected files in production; the dev server serves them directly.
if DEBUG:
    MIDDLEWARE.remove("whitenoise.middleware.WhiteNoiseMiddleware")

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.messages.context_processors.messages",
                "finance.auth.context",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

_db = urlparse(os.environ.get("DATABASE_URL", "postgresql://app:app@localhost:5432/controlfinan_django"))
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": _db.path.lstrip("/"),
        "USER": _db.username,
        "PASSWORD": _db.password,
        "HOST": _db.hostname,
        "PORT": _db.port or 5432,
        "CONN_MAX_AGE": 60,
    }
}

# Rate limits (10 attempts / 3 minutes) are counted in the cache, like Rails' memory_store in development.
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"  # Rails "Brasilia"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
# Production: fingerprinted and compressed files, like Rails' assets:precompile.
if not DEBUG:
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
    }

MESSAGE_STORAGE = "django.contrib.messages.storage.cookie.CookieStorage"

EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")
DEFAULT_FROM_EMAIL = "from@example.com"

# bcrypt cost for new passwords (Rails uses 12 outside tests).
BCRYPT_COST = int(os.environ.get("BCRYPT_COST", "12"))

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
