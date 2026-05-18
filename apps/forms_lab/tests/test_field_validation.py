""" Test field validation. """

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError
from django.db import DatabaseError

from apps.forms_lab.field_validation import clean_form_field
from apps.forms_lab.fields import PhoneField
from apps.forms_lab.forms.address import AddressForm
from apps.forms_lab.forms.signup import SignupForm
from apps.forms_lab.models import ValidationLog
from apps.forms_lab.services import validate_single_field
from apps.forms_lab.validators.email_rules import validate_email_mx


def test_clean_form_field_validates_one_field_without_full_form():
    form = SignupForm({"username": "princeton"})
    value, error = clean_form_field(form, "username")
    assert error is None
    assert value == "princeton"
    assert "password" not in form.cleaned_data


def test_clean_form_field_runs_field_cleaner():
    form = SignupForm({"username": "admin"})
    _, error = clean_form_field(form, "username")
    assert error is not None
    assert "unavailable" in error


def test_clean_form_field_honors_dependencies():
    form = AddressForm({"country": "CA", "postal_code": "k1a0b1"})
    value, error = clean_form_field(form, "postal_code")
    assert error is None
    assert value == "K1A 0B1"


def test_validate_single_field_reports_valid_without_other_required_fields():
    _, _, state, message = validate_single_field(
        "signup",
        "username",
        {"username": "princeton"},
    )
    assert state == "valid"
    assert message == "Looks good."


def test_validate_single_field_rejects_bad_postal_for_country():
    _, _, state, _ = validate_single_field(
        "address",
        "postal_code",
        {"country": "US", "postal_code": "K1A 0B1"},
    )
    assert state == "invalid"


def test_field_state_is_neutral_for_empty_optional_fields():
    form = SignupForm(
        {
            "username": "",
            "email": "not-an-email",
        }
    )
    form.is_valid()
    state, message = form.field_state("website")
    assert state == "neutral"
    assert message == ""


def test_signup_form_rejects_fast_submit():
    started = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
    form = SignupForm(
        {
            "username": "princeton",
            "email": "princeton@example.com",
            "password": "CorrectHorse9!",
            "confirm_password": "CorrectHorse9!",
            "phone": "4155552671",
            "accept_terms": "on",
            "website": "",
            "started_at": started,
        }
    )
    assert not form.is_valid()
    assert form.non_field_errors()


def test_email_mx_rejects_malformed_domain():
    with pytest.raises(ValidationError):
        validate_email_mx("user@bad..example.com")


def test_phone_field_fallback_without_phonenumbers():
    field = PhoneField()
    with patch("apps.forms_lab.fields.phonenumbers", None):
        assert field.clean("(415) 555-2671") == "+14155552671"
        with pytest.raises(ValidationError):
            field.clean("12345")


@pytest.mark.django_db
def test_log_validation_errors_survives_database_errors(caplog):
    from apps.forms_lab import services

    form = SignupForm({"username": "admin"})
    form.is_valid()
    with patch.object(
        ValidationLog.objects,
        "bulk_create",
        side_effect=DatabaseError("demo db unavailable"),
    ):
        services.log_validation_errors("signup", form)
    assert "Could not persist validation log rows" in caplog.text
