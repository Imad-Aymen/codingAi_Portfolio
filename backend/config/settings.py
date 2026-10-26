"""
CODING AI project settings — Django + PostgreSQL
================================================
All database connection values are read from environment variables:
POSTGRES_DB / POSTGRES_USER / POSTGRES_PASSWORD / POSTGRES_HOST / POSTGRES_PORT
See README.md for the startup steps.
"""

import os
from pathlib import Path
import dj_database_url

# Cloudinary is enabled only when CLOUDINARY_URL is set in the environment.
CLOUDINARY_URL = os.environ.get("CLOUDINARY_URL", "")
USE_CLOUDINARY = bool(CLOUDINARY_URL)

BASE_DIR = Path(__file__).resolve().parent.parent

# In production set DJANGO_SECRET_KEY and DJANGO_DEBUG=0
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "django-insecure-dev-only-change-this-key")
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,0.0.0.0").split(",")
    if host.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",           # allows requests from the separate frontend origin
    "registrations",         # the single registration app
    # Cloudinary: only activated when CLOUDINARY_URL env var is present
    *(["cloudinary_storage", "cloudinary"] if USE_CLOUDINARY else []),
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # must come before CommonMiddleware
    "django.middleware.security.SecurityMiddleware",
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
        "DIRS": [BASE_DIR.parent],  # serves index.html from the project root
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ------------------------------------------------------------------
# Database:
# - Production (Render): reads DATABASE_URL environment variable automatically
# - Local development:   falls back to SQLite (no installation needed)
# ------------------------------------------------------------------
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        conn_health_checks=True,
    )
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "en-us"   # API messages are written explicitly in English in views.py
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

# ------------------------------------------------------------------
# Media / uploaded files:
# - Local dev:   stored in MEDIA_ROOT, served by Django (debug only).
# - Production:  stored on Cloudinary when CLOUDINARY_URL env var is set.
#   Set CLOUDINARY_URL=cloudinary://api_key:api_secret@cloud_name on Render.
# ------------------------------------------------------------------
MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"

if USE_CLOUDINARY:
    # RawMediaCloudinaryStorage → resource_type='raw' (correct for PDFs).
    # MediaCloudinaryStorage uses 'image' which causes 401 for non-image files.
    STORAGES = {
        "default": {
            "BACKEND": "cloudinary_storage.storage.RawMediaCloudinaryStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
    DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.RawMediaCloudinaryStorage"

    # Explicit Cloudinary SDK configuration
    import cloudinary
    cloudinary.config(CLOUDINARY_URL=CLOUDINARY_URL)

    CLOUDINARY_STORAGE = {
        "CLOUDINARY_URL": CLOUDINARY_URL,
    }

# Safe upload limits (the PDF size is also checked inside the view)
DATA_UPLOAD_MAX_MEMORY_SIZE = 20 * 1024 * 1024   # 20MB for the whole request
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024    # larger files are spooled to a temp file

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ------------------------------------------------------------------
# Frontend integration:
# The single-file UI is usually served from http://localhost:5500, so only
# these origins are allowed via django-cors-headers. If the UI is served
# from the same origin as Django this setting is unnecessary (same-origin).
# Override the list with CORS_ALLOWED_ORIGINS (comma-separated).
# ------------------------------------------------------------------
_DEFAULT_ORIGINS = "http://localhost:5500,http://127.0.0.1:5500,http://localhost:8000,http://127.0.0.1:8000"
CORS_ALLOWED_ORIGINS = [o.strip() for o in os.environ.get("CORS_ALLOWED_ORIGINS", _DEFAULT_ORIGINS).split(",") if o.strip()]
CORS_ALLOW_CREDENTIALS = True
# Only needed if CSRF protection is enabled later (UI sends X-CSRFToken)
CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS

# ------------------------------------------------------------------
# API endpoint injected into index.html via Django template.
# Default: relative URL (works when Django serves the frontend).
# Override with API_ENDPOINT env var for a separate frontend deployment.
# ------------------------------------------------------------------
API_ENDPOINT = os.environ.get("API_ENDPOINT", "/api/registrations/")
