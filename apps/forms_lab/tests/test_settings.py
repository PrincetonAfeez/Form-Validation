from __future__ import annotations

import os

import pytest
from django.core.exceptions import ImproperlyConfigured


def test_prod_settings_rejects_default_secret_key():
    module = "config.settings.prod"
    original = os.environ.get("SECRET_KEY")
    os.environ.pop("SECRET_KEY", None)
    try:
        with pytest.raises(ImproperlyConfigured, match="SECRET_KEY"):
            __import__(module)
    finally:
        if original is not None:
            os.environ["SECRET_KEY"] = original
        # Allow subsequent Django setup in this process to use dev settings.
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
