"""
Base Django settings shared by every environment.

Environment-specific settings (development.py, production.py) import
everything from here with `from .base import *` and only override what
actually differs between environments.
"""

from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY")
DEBUG = env.bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])
CSRF_TRUSTED_ORIGINS = env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=[])

FRONTEND_URL = env("FRONTEND_URL", default="http://localhost:3000")

# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
    "channels",
    "storages",
]

LOCAL_APPS = [
    "apps.core",
    "apps.users",
    "apps.workspaces",
    "apps.meetings",
    "apps.chat",
    "apps.notifications",
    "apps.recordings",
    "apps.analytics",
    "apps.payments",
    "apps.ai",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.core.middleware.RequestLoggingMiddleware",
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
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB"),
        "USER": env("POSTGRES_USER"),
        "PASSWORD": env("POSTGRES_PASSWORD"),
        "HOST": env("POSTGRES_HOST", default="localhost"),
        "PORT": env("POSTGRES_PORT", default="5432"),
        "CONN_MAX_AGE": 60,
        "OPTIONS": {},
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

AUTH_USER_MODEL = "users.User"

# No password validators - accounts have no usable password at all (see
# UserManager._create_user); identity is proven by WhatsApp OTP every login.

# ---------------------------------------------------------------------------
# I18N / TZ
# ---------------------------------------------------------------------------

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static / media
# ---------------------------------------------------------------------------

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "mediafiles"

AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME", default="")
if AWS_STORAGE_BUCKET_NAME:
    AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")
    # The endpoint the backend container itself talks to for every S3 API
    # call (upload, HeadObject, etc.) - must be reachable *from inside the
    # container*. On a cloud box (EC2) the instance's own public IP is often
    # NOT reachable from inside itself (hairpin NAT isn't guaranteed), so
    # this needs to be the docker-internal address (http://minio:9000) in
    # that case, not the public IP - using the public IP here produced a
    # ConnectTimeoutError for every file upload (chat attachments, avatars)
    # in production until this was split from AWS_S3_CUSTOM_DOMAIN below.
    AWS_S3_ENDPOINT_URL = env("AWS_S3_ENDPOINT_URL", default=None)
    # The endpoint LiveKit's egress process uploads recordings to - a
    # *third* distinct address, because egress runs with network_mode: host
    # (see docker-compose.yml) and so isn't on the bridge network where
    # AWS_S3_ENDPOINT_URL's docker-internal hostname resolves. Same
    # situation as redis's address there: a host-networked process reaches
    # another container via its published port on 127.0.0.1, not by Docker
    # DNS name and not by the box's public IP (also unreachable from a
    # process on the box itself). Falls back to AWS_S3_ENDPOINT_URL, correct
    # when nothing is host-networked (egress doesn't need to be, just is
    # here for the same reason coturn/livekit-server are - see their
    # comments in docker-compose.yml).
    AWS_S3_EGRESS_ENDPOINT_URL = env("AWS_S3_EGRESS_ENDPOINT_URL", default=None) or AWS_S3_ENDPOINT_URL
    # The host (no scheme - "1.2.3.4:9000", not "http://1.2.3.4:9000") put
    # into URLs handed to browsers - needs to be externally reachable,
    # unlike AWS_S3_ENDPOINT_URL above. Unset by default, which makes
    # django-storages fall back to deriving the host from
    # AWS_S3_ENDPOINT_URL - correct whenever the two coincide (local dev:
    # the LAN IP is reachable both from the host's browser and from its own
    # containers).
    AWS_S3_CUSTOM_DOMAIN = env("AWS_S3_CUSTOM_DOMAIN", default=None)
    AWS_S3_URL_PROTOCOL = env("AWS_S3_URL_PROTOCOL", default="http:")
    AWS_S3_REGION_NAME = env("AWS_S3_REGION_NAME", default="us-east-1")
    AWS_DEFAULT_ACL = None
    AWS_S3_FILE_OVERWRITE = False
    # The bucket is already anonymous-read (see docker-compose.yml's
    # minio-init `mc anonymous set download`), so presigned auth query
    # strings are redundant - and would be actively wrong whenever
    # AWS_S3_CUSTOM_DOMAIN differs from AWS_S3_ENDPOINT_URL's host, since
    # the signature is computed against the latter.
    AWS_QUERYSTRING_AUTH = env.bool("AWS_QUERYSTRING_AUTH", default=False)
    AWS_QUERYSTRING_EXPIRE = 3600
    STORAGES = {
        "default": {"BACKEND": "storages.backends.s3.S3Storage"},
        "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
    }
    # Recordings build their own public URL by hand (see
    # apps/recordings/services.py) rather than going through this storage
    # backend's .url(), since LiveKit egress - not Django - writes that
    # file. This is the same "externally-reachable base URL" the storage
    # backend itself uses, computed once here instead of duplicating the
    # custom-domain-vs-endpoint fallback logic at the call site.
    PUBLIC_S3_BASE_URL = (
        f"{AWS_S3_URL_PROTOCOL}//{AWS_S3_CUSTOM_DOMAIN}" if AWS_S3_CUSTOM_DOMAIN else AWS_S3_ENDPOINT_URL
    )
else:
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
    }

FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

# ---------------------------------------------------------------------------
# REST framework
# ---------------------------------------------------------------------------

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
    ),
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.StandardResultsPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend",),
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.ScopedRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "auth": "20/min",
        "auth-sensitive": "5/min",
        "meetings": "60/min",
        "chat": "120/min",
    },
    "EXCEPTION_HANDLER": "apps.core.exceptions.custom_exception_handler",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
    "DATETIME_FORMAT": "iso-8601",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "FizX API",
    "DESCRIPTION": "REST API for the FizX video conferencing platform.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SCHEMA_PATH_PREFIX": r"/api/v1/",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env.int("JWT_ACCESS_TOKEN_LIFETIME_MINUTES", default=15)),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env.int("JWT_REFRESH_TOKEN_LIFETIME_DAYS", default=14)),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
}

# ---------------------------------------------------------------------------
# CORS / CSRF
# ---------------------------------------------------------------------------

CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=["http://localhost:3000"])
CORS_ALLOW_CREDENTIALS = True

# ---------------------------------------------------------------------------
# Cache / Channels / Celery (all backed by Redis)
# ---------------------------------------------------------------------------

REDIS_URL = env("REDIS_URL", default="redis://localhost:6379/0")

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
    }
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [REDIS_URL]},
    }
}

CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://localhost:6379/1")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="redis://localhost:6379/2")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_BEAT_SCHEDULE = {
    "send-meeting-reminders": {
        "task": "apps.meetings.tasks.send_meeting_reminders",
        "schedule": 300.0,
    },
    "auto-start-scheduled-meetings": {
        "task": "apps.meetings.tasks.auto_start_scheduled_meetings",
        "schedule": 60.0,
    },
    "auto-end-overdue-meetings": {
        "task": "apps.meetings.tasks.auto_end_overdue_meetings",
        "schedule": 60.0,
    },
    "sync-whatsapp-groups": {
        "task": "apps.workspaces.tasks.sync_whatsapp_groups",
        "schedule": 300.0,
    },
}

# ---------------------------------------------------------------------------
# WhatsApp OTP (separate local service - see /whatsapp-otp at the repo root)
# ---------------------------------------------------------------------------

# host.docker.internal because the service runs standalone on the host, not
# as a container on this compose network - same pattern as LIVEKIT_HTTP_URL.
WHATSAPP_OTP_URL = env("WHATSAPP_OTP_URL", default="http://host.docker.internal:3210")
WHATSAPP_OTP_API_KEY = env("WHATSAPP_OTP_API_KEY", default="")

# ---------------------------------------------------------------------------
# LiveKit
# ---------------------------------------------------------------------------

LIVEKIT_API_KEY = env("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = env("LIVEKIT_API_SECRET")
LIVEKIT_URL = env("LIVEKIT_URL", default="ws://localhost:7880")
LIVEKIT_HTTP_URL = env("LIVEKIT_HTTP_URL", default="http://localhost:7880")

# ---------------------------------------------------------------------------
# coturn (TURN relay) - REST API long-term credential mechanism.
# https://datatracker.ietf.org/doc/html/draft-uberti-behave-turn-rest-00
# ---------------------------------------------------------------------------

TURN_SHARED_SECRET = env("TURN_SHARED_SECRET", default="")
TURN_REALM = env("TURN_REALM", default="fizx.local")

# ---------------------------------------------------------------------------
# Stripe
# ---------------------------------------------------------------------------

STRIPE_PUBLIC_KEY = env("STRIPE_PUBLIC_KEY", default="")
STRIPE_SECRET_KEY = env("STRIPE_SECRET_KEY", default="")
STRIPE_WEBHOOK_SECRET = env("STRIPE_WEBHOOK_SECRET", default="")
STRIPE_PRICE_ID_PRO = env("STRIPE_PRICE_ID_PRO", default="")

# ---------------------------------------------------------------------------
# OpenAI (AI assistant)
# ---------------------------------------------------------------------------

OPENAI_API_KEY = env("OPENAI_API_KEY", default="")
OPENAI_MODEL = env("OPENAI_MODEL", default="gpt-4o-mini")

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(asctime)s [%(levelname)s] %(name)s %(module)s.%(funcName)s:%(lineno)d - %(message)s",
        },
        "json": {
            "()": "apps.core.logging.JSONFormatter",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "django.request": {"handlers": ["console"], "level": "ERROR", "propagate": False},
        "apps": {"handlers": ["console"], "level": "DEBUG", "propagate": False},
        "celery": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "daphne": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}

SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
