import os
import sys
from pathlib import Path
import dj_database_url
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
# settings/base.py is 2 levels below config, which is 1 level below project root:
BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    SECRET_KEY=(str, "django-insecure-badshop-production-secret-key-must-change"),
    DATABASE_URL=(str, ""),
    DIRECT_DATABASE_URL=(str, ""),
    CONN_MAX_AGE=(int, 0),
    ALLOWED_HOSTS=(list, ["127.0.0.1", "localhost"]),
    MEDIA_STORAGE_BACKEND=(str, "local"),
)

# Read environment file if present
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    # Local Apps
    "core.apps.CoreConfig",
    "accounts.apps.AccountsConfig",
    "catalog.apps.CatalogConfig",
    "cart.apps.CartConfig",
    "orders.apps.OrdersConfig",
    "payments.apps.PaymentsConfig",
    "dashboard.apps.DashboardConfig",
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
                "cart.context_processors.cart_summary",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# Database configuration (Neon Serverless PostgreSQL support with local SQLite fallback)
# Neon requires sslmode=require and pooler configuration
DATABASE_URL = env("DATABASE_URL")
DIRECT_DATABASE_URL = env("DIRECT_DATABASE_URL")

# Check if running migration with direct connection
is_migrating = any(arg in sys.argv for arg in ["migrate", "makemigrations"])

if is_migrating and DIRECT_DATABASE_URL:
    db_config_url = DIRECT_DATABASE_URL
else:
    db_config_url = DATABASE_URL

if db_config_url:
    DATABASES = {
        "default": dj_database_url.parse(
            db_config_url,
            conn_max_age=env("CONN_MAX_AGE"),
            conn_health_checks=True,
            ssl_require=True,
        )
    }
    # Neon pgbouncer pooled connection support
    db_host = DATABASES["default"].get("HOST", "")
    if "-pooler" in db_host:
        DATABASES["default"]["DISABLE_SERVER_SIDE_CURSORS"] = True
else:
    # Local fallback for development / initial tests if DATABASE_URL is not set
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# Custom User Model (Email as username)
AUTH_USER_MODEL = "accounts.User"

# Secure Password Hashing (Argon2 as default, PBKDF2 as fallback)
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 8,
        },
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
LANGUAGE_CODE = "th"
TIME_ZONE = "Asia/Bangkok"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

# Media files (Product images, proof of payment)
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Authentication redirects
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "catalog:product_list"
LOGOUT_REDIRECT_URL = "catalog:product_list"

# Cart settings
CART_EXPIRY_DAYS = 7

# Currency settings
CURRENCY_SYMBOL = "฿"
