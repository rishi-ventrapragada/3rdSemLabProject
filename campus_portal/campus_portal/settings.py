"""
Django settings for the Smart Campus portal (Django Lab).

All database settings come from the shared repo-root .env, the same file the Java engine reads
(see CLAUDE.md, "How Django and Java share smart_campus_db"). Domain tables belong to
database/*.sql; Django only creates its own auth/session tables in the same database.
"""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent  # campus_portal/
REPO_ROOT = BASE_DIR.parent

load_dotenv(REPO_ROOT / ".env")


def env(name, default=None, required=False):
    value = os.environ.get(name, default)
    if required and not value:
        raise ImproperlyConfigured(f"{name} is not set. Copy .env.example to .env at the repo root.")
    return value


DEBUG = env("DJANGO_DEBUG", "True").lower() in ("1", "true", "yes")

# Development fallback only. Set DJANGO_SECRET_KEY in .env for anything but local demos.
SECRET_KEY = env("DJANGO_SECRET_KEY") or (
    "dev-only-insecure-key-do-not-use-in-production" if DEBUG else None
)
if not SECRET_KEY:
    raise ImproperlyConfigured("DJANGO_SECRET_KEY must be set when DJANGO_DEBUG is false.")

ALLOWED_HOSTS = [h.strip() for h in env("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()]


# Sessions, cookies and response headers. Several of these equal Django's defaults; they are
# stated here so the security posture is visible in one place.
SESSION_COOKIE_AGE = 8 * 60 * 60          # one working day
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"

# HTTPS hardening is opt-in: the lab demo runs on plain http://127.0.0.1, where secure-only
# cookies and an HTTPS redirect would make the site unusable. Set DJANGO_HTTPS=True behind TLS.
if env("DJANGO_HTTPS", "False").lower() in ("1", "true", "yes"):
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 365
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core",
    "accounts",
    "student_portal",
    "faculty_portal",
    "admin_portal",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "campus_portal.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.campus_role",
            ],
        },
    },
]

WSGI_APPLICATION = "campus_portal.wsgi.application"


# Database: the shared smart_campus_db via PyMySQL (installed as MySQLdb in __init__.py).
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": env("DB_NAME", required=True),
        "USER": env("DB_USER", required=True),
        "PASSWORD": env("DB_PASSWORD", ""),
        "HOST": env("DB_HOST", "localhost"),
        "PORT": env("DB_PORT", "3306"),
        "OPTIONS": {
            "charset": "utf8mb4",
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        },
        "TEST": {
            # The test runner builds this database from database/*.sql (core.test_runner).
            "NAME": "test_" + env("DB_NAME", "smart_campus_db"),
            "CHARSET": "utf8mb4",
            "COLLATION": "utf8mb4_unicode_ci",
        },
    }
}

TEST_RUNNER = "core.test_runner.SmartCampusTestRunner"


AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "accounts:home"
LOGOUT_REDIRECT_URL = "accounts:login"


LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True  # DATETIME values are stored in UTC (CLAUDE.md, Gotchas)


STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Java engine bridge (CLAUDE.md, "Django -> Java bridge").
JAVA_BIN = env("DJANGO_JAVA_BIN", "java")
JAVA_ENGINE_JAR = Path(env("DJANGO_JAVA_ENGINE_JAR", str(REPO_ROOT / "java_engine" / "target" / "smart-campus-engine.jar")))
JAVA_ENGINE_TIMEOUT = int(env("DJANGO_JAVA_ENGINE_TIMEOUT", "30"))

# Demo-only password used by `manage.py seed_demo_users` (see CLAUDE.md). Never use it for real accounts.
DEMO_USER_PASSWORD = env("DJANGO_DEMO_PASSWORD", "campus-demo-2026")
