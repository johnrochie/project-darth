"""
Django Settings for GAA Stats App

Multi-tenant platform with subdomain-based club access
Real-time updates via Django Channels WebSockets
"""

from pathlib import Path
import os
from decouple import config

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-this-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

# Allowed hosts - support wildcard subdomains
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,.gaastats.ie').split(',')

# CORS settings for API access
CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOWED_ORIGINS = config('CORS_ORIGINS', default='http://localhost:3000').split(',')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    # 'social_django',  # X/Twitter OAuth - Removed, using social-core auth backend only

    # Channels
    'channels',

    # Local apps
    'gaastats',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Static files in production
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # Custom middleware for multi-tenant subdomain support
    'gaastats.middleware.SubdomainMiddleware',
    'gaastats.middleware.ClubFilterMiddleware',
]

ROOT_URLCONF = 'gaastats.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'gaastats' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'gaastats.context_processors.club_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'gaastats.wsgi.application'
ASGI_APPLICATION = 'gaastats.asgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='gaastats'),
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default='postgres'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
        'TEST': {
            'NAME': 'test_gaastats',
            'MIRROR': None,
        }
    }
}

# Redis for Channels
REDIS_URL = config('REDIS_URL', default='redis://localhost:6379/0')

# Channels configuration
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [REDIS_URL],
        },
    },
}

# Authentication (JWT for iPad app, sessions for web)
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 100,
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-ie'
TIME_ZONE = 'Europe/Dublin'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files (user uploads, logos)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model - using default Django User
# AUTH_USER_MODEL = 'auth.User'  # Default Django User model (no custom user model yet)

# Social Auth (X/Twitter)
AUTHENTICATION_BACKENDS = [
    'social_core.backends.twitter.TwitterOAuth',  # X/Twitter
    'django.contrib.auth.backends.ModelBackend',
]

SOCIAL_AUTH_TWITTER_KEY = config('TWITTER_API_KEY', default='')
SOCIAL_AUTH_TWITTER_SECRET = config('TWITTER_API_SECRET', default='')
SOCIAL_AUTH_TWITTER_ACCESS_TOKEN = config('TWITTER_ACCESS_TOKEN', default='')
SOCIAL_AUTH_TWITTER_ACCESS_TOKEN_SECRET = config('TWITTER_ACCESS_TOKEN_SECRET', default='')

# Django Admin customization
ADMIN_SITE_TITLE = 'GAA Stats Admin'
ADMIN_SITE_HEADER = 'GAA Stats Administration'
ADMIN_INDEX_TITLE = 'Club Management Dashboard'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'gaastats': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
    },
}

# Multi-tenant settings
DEFAULT_CLUB_SUBDOMAIN = config('DEFAULT_CLUB_SUBDOMAIN', default='demo')

# Report settings
REPORTS_PDF_TEMPLATE_DIR = BASE_DIR / 'gaastats' / 'templates' / 'reports'
REPORTS_OUTPUT_DIR = BASE_DIR / 'media' / 'reports'
REPORTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# X/Twitter posting
X_AUTO_TWEET_ENABLED = config('X_AUTO_TWEET_ENABLED', default=True, cast=bool)
X_TWEET_TEMPLATE = "@{club_handle} {team} Score Update: {score}-{opposition_score} | {minute}'"
