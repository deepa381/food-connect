"""
Django settings for FoodSaver project.
Optimized for Render deployment with Gemini API integration.
"""

from pathlib import Path
import os
from decouple import config, Csv

# ---------------------------------------------------------------
# BASE DIRECTORY CONFIGURATION
# ---------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------
# SECURITY SETTINGS
# ---------------------------------------------------------------
SECRET_KEY = config(
    'SECRET_KEY',
    default='django-insecure-fallback-key-for-dev'
)

DEBUG = config('DEBUG', default=False, cast=bool)

# Render gives you a .onrender.com domain
ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='.onrender.com,127.0.0.1,localhost',
    cast=Csv()
)

# ---------------------------------------------------------------
# API KEYS (Gemini + optional IPStack)
# ---------------------------------------------------------------
GEMINI_API_KEY = config('GEMINI_API_KEY', default='')
IPSTACK_API_KEY = config('IPSTACK_API_KEY', default='')

if not GEMINI_API_KEY:
    print("⚠️ WARNING: GEMINI_API_KEY not found in environment variables")
if not IPSTACK_API_KEY:
    print("ℹ️ IPSTACK_API_KEY not provided (optional)")

# ---------------------------------------------------------------
# INSTALLED APPS
# ---------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "HungerFree",
]

# ---------------------------------------------------------------
# MIDDLEWARE
# ---------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Custom middleware for role handling
    "HungerFree.middleware.RoleBasedRedirectMiddleware",
]

ROOT_URLCONF = "FoodSaver.urls"

# ---------------------------------------------------------------
# TEMPLATES
# ---------------------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "FoodSaver.wsgi.application"

# ---------------------------------------------------------------
# DATABASE CONFIGURATION
# ---------------------------------------------------------------
# Use SQLite locally and PostgreSQL on Render (via DATABASE_URL)
if config("DATABASE_URL", default="").startswith("postgres"):
    import dj_database_url
    DATABASES = {
        "default": dj_database_url.parse(config("DATABASE_URL"))
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ---------------------------------------------------------------
# PASSWORD VALIDATION
# ---------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------
# INTERNATIONALIZATION
# ---------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------
# STATIC FILES CONFIGURATION
# ---------------------------------------------------------------
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'HungerFree', 'static'),
]

# ---------------------------------------------------------------
# MEDIA FILES
# ---------------------------------------------------------------
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# ---------------------------------------------------------------
# DEFAULT PRIMARY KEY FIELD TYPE
# ---------------------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------
# LOGGING (Useful for Render logs)
# ---------------------------------------------------------------
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
