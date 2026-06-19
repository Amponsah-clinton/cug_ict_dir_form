"""
Django settings for cug_project.

Database strategy:
  Django ORM  → SQLite (db.sqlite3) for sessions and admin only
  Supabase    → corrections state and director confirmation via REST API
"""

from pathlib import Path
import os
import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-cug-archival-system-change-in-production')

DEBUG = True

ALLOWED_HOSTS = ['*', '127.0.0.1', 'localhost']

CSRF_TRUSTED_ORIGINS = [
    'http://127.0.0.1:8000',
    'http://localhost:8000',
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'report',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

if not DEBUG:
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

ROOT_URLCONF = 'cug_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'cug_project.wsgi.application'

_database_url = os.getenv('DATABASE_URL', '')
if _database_url:
    DATABASES = {
        'default': dj_database_url.config(
            default=_database_url,
            conn_max_age=60,
            ssl_require=True,
        )
    }
    DATABASES['default']['CONN_HEALTH_CHECKS'] = True
    DATABASES['default'].setdefault('OPTIONS', {})
    DATABASES['default']['OPTIONS'].setdefault('connect_timeout', 10)
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ── Supabase Configuration ──────────────────────────────────────────────────
# Same project as applab: xdouuloczyuaqplfmrve
# Data stored: corrections (is_done state) + director_confirmation
SUPABASE_URL = 'https://xdouuloczyuaqplfmrve.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inhkb3V1bG9jenl1YXFwbGZtcnZlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjYxMTI4NDksImV4cCI6MjA4MTY4ODg0OX0.ZNCn-4Kv8yhqafNz6o1YV8g8wrxy5E0-Ki15mrYDZiw'
SUPABASE_SERVICE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inhkb3V1bG9jenl1YXFwbGZtcnZlIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NjExMjg0OSwiZXhwIjoyMDgxNjg4ODQ5fQ.GqBmsygTS23PyIiofEIs3BT88tsgiQ3qRt-7mF38DXM'

if not SUPABASE_URL or not SUPABASE_KEY or not SUPABASE_SERVICE_KEY:
    print("\n" + "=" * 80)
    print("WARNING: Supabase configuration is incomplete!")
    print("=" * 80)
    print(f"SUPABASE_URL: {'OK' if SUPABASE_URL else 'MISSING'}")
    print(f"SUPABASE_KEY: {'OK' if SUPABASE_KEY and len(SUPABASE_KEY) > 100 else f'MISSING or INVALID (length: {len(SUPABASE_KEY) if SUPABASE_KEY else 0})'}")
    print(f"SUPABASE_SERVICE_KEY: {'OK' if SUPABASE_SERVICE_KEY and len(SUPABASE_SERVICE_KEY) > 100 else f'MISSING or INVALID (length: {len(SUPABASE_SERVICE_KEY) if SUPABASE_SERVICE_KEY else 0})'}")
    print("=" * 80 + "\n")
elif len(SUPABASE_KEY) > 100 and len(SUPABASE_SERVICE_KEY) > 100:
    print(f"[Supabase Config] OK - Keys loaded (anon: {len(SUPABASE_KEY)} chars, service: {len(SUPABASE_SERVICE_KEY)} chars)")

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

if not DEBUG:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── Email (Resend SMTP) ─────────────────────────────────────────────────────
RESEND_API_KEY    = 're_8oKMDXqA_83UBMsJcVZXRqJKuwjyn3XbV'
RESEND_FROM_EMAIL = 'support@academicdigital.space'

EMAIL_BACKEND       = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST          = 'smtp.resend.com'
EMAIL_PORT          = 465
EMAIL_HOST_USER     = 'resend'
EMAIL_HOST_PASSWORD = RESEND_API_KEY
EMAIL_USE_SSL       = True
EMAIL_USE_TLS       = False
EMAIL_TIMEOUT       = 30
DEFAULT_FROM_EMAIL  = f'CUG Archival System <{RESEND_FROM_EMAIL}>'

# Addresses that receive form-submitted notifications
FORM_NOTIFICATION_EMAILS = [
    'metascholarlimited@gmail.com',
    'miracle.atianashie@cug.edu.gh',
    'ceo@academicdigital.space',
]

# Edit window (seconds) — form locks after this many seconds since first save
FORM_EDIT_WINDOW = 600  # 10 minutes
