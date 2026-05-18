"""Settings for CI: Postgres via DATABASE_URL, debug on, non-production secret."""

from django.core.exceptions import ImproperlyConfigured

from .dev import *  # noqa: F403

SECRET_KEY = "ci-only-not-for-production"

if not os.environ.get("DATABASE_URL"):  # noqa: F405
    raise ImproperlyConfigured("DATABASE_URL must be set for CI test runs.")
