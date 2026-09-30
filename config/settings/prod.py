import sentry_sdk
from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403
from .base import ADMIN_URL, env

DEBUG = False

# Required in production: the app refuses to start without them.
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = env.list("DJANGO_CSRF_TRUSTED_ORIGINS")
if not ALLOWED_HOSTS or "*" in ALLOWED_HOSTS:
    raise ImproperlyConfigured("DJANGO_ALLOWED_HOSTS must list real domain names, not '*'.")
if ADMIN_URL == "admin/":
    raise ImproperlyConfigured("Set DJANGO_ADMIN_URL to a non-default path in production.")

# The app sits behind a TLS-terminating load balancer that sets X-Forwarded-Proto.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = env.int("DJANGO_HSTS_SECONDS", default=60 * 60 * 24 * 365)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Login lockout must see the visitor's real IP, not the load balancer's.
# Set AXES_PROXY_COUNT to the number of proxies in front of the app (e.g. 2 with Cloudflare + LB).
AXES_IPWARE_PROXY_COUNT = env.int("AXES_PROXY_COUNT", default=1)
AXES_IPWARE_META_PRECEDENCE_ORDER = ["HTTP_X_FORWARDED_FOR", "REMOTE_ADDR"]

if dsn := env("SENTRY_DSN", default=""):
    sentry_sdk.init(
        dsn=dsn,
        environment=env("SENTRY_ENVIRONMENT", default="production"),
        send_default_pii=False,
        traces_sample_rate=env.float("SENTRY_TRACES_SAMPLE_RATE", default=0.0),
    )
