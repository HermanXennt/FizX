import environ

from .base import *  # noqa: F403

env = environ.Env()

DEBUG = False

SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
# Defaults to 0 (disabled) - HSTS makes the browser refuse to even show the
# "proceed anyway" bypass for an untrusted cert for as long as it's cached,
# which would lock out anyone hitting this server with a self-signed cert
# (the standard setup for a LAN-IP deployment with no real domain). Only
# raise this once a CA-trusted certificate is in place.
SECURE_HSTS_SECONDS = env.int("DJANGO_SECURE_HSTS_SECONDS", default=0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = SECURE_HSTS_SECONDS > 0
SECURE_HSTS_PRELOAD = SECURE_HSTS_SECONDS > 0
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# LiveKit egress webhooks hit the backend directly over plain HTTP via
# 127.0.0.1 (see docker-compose.yml's backend port publish) - they never
# touch nginx, so they have no X-Forwarded-Proto header and would otherwise
# get redirected to https on a port Django isn't listening on with TLS.
#
# `^api/` is broader: the React Native app (FizX Meet App/) deliberately
# talks to the API over plain HTTP (nginx exempts /api/ on port 80 for it -
# see infra/nginx/nginx.conf) since a native client has no browser secure-
# context/mixed-content constraint forcing it onto HTTPS. The browser-facing
# site itself is unaffected - nginx still 301s everything else on port 80.
SECURE_REDIRECT_EXEMPT = [r"^api/v1/recordings/webhook/$", r"^api/"]

SENTRY_DSN = env("SENTRY_DSN", default="")
if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.celery import CeleryIntegration
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.redis import RedisIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration(), CeleryIntegration(), RedisIntegration()],
        traces_sample_rate=0.2,
        send_default_pii=False,
    )

LOGGING["handlers"]["console"]["formatter"] = "json"  # noqa: F405
