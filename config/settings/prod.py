import os

from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403

DEBUG = False

# WhiteNoise serves static files in production (run `collectstatic` first).
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")  # noqa: F405

_DEV_SECRET = "dev-only-change-me"
if not SECRET_KEY or SECRET_KEY == _DEV_SECRET:  # noqa: F405
    raise ImproperlyConfigured(
        "Set a unique SECRET_KEY environment variable for production."
    )

CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = os.environ.get("SECURE_SSL_REDIRECT", "true").lower() in {
    "1",
    "true",
    "yes",
}
