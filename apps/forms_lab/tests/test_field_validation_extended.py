from __future__ import annotations

import pytest
from django.core.exceptions import ValidationError

from apps.forms_lab.field_validation import _first_message, clean_form_field
from apps.forms_lab.forms.address import AddressForm
from apps.forms_lab.services import validate_single_field


def test_clean_form_field_unknown_field_raises():
    form = AddressForm({})
    with pytest.raises(ValueError, match="Unknown field"):
        clean_form_field(form, "not_real")


def test_clean_form_field_dependency_failure_short_circuits():
    form = AddressForm({"country": "US", "postal_code": "K1A 0B1"})
    value, error = clean_form_field(form, "postal_code")
    assert value is None
    assert error is not None


def test_first_message_prefers_message_attribute():
    exc = ValidationError("fallback")
    exc.message = "primary"
    assert _first_message(exc) == "primary"


def test_first_message_uses_messages_list():
    exc = ValidationError(["first", "second"])
    assert _first_message(exc) == "first"


def test_validate_single_field_email_disposable():
    _, _, state, message = validate_single_field(
        "signup",
        "email",
        {"email": "bot@mailinator.com"},
    )
    assert state == "invalid"
    assert message
