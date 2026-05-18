from __future__ import annotations

from datetime import date

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.forms_lab.forms.signup import SignupForm
from apps.forms_lab.models import ValidationLog
from apps.forms_lab.results import ValidationResult
from apps.forms_lab.services import (
    build_artifact,
    collect_errors,
    get_demo,
    log_validation_errors,
    serialize_cleaned_data,
    serialize_value,
    validate_and_clean,
    validate_single_field,
)


def test_get_demo_returns_definition():
    demo = get_demo("signup")
    assert demo.slug == "signup"
    assert demo.form_class is SignupForm


def test_serialize_value_handles_files_lists_tuples_and_dates():
    upload = SimpleUploadedFile("x.pdf", b"data", content_type="application/pdf")
    assert serialize_value(upload) == {"name": "x.pdf", "size": 4}
    assert serialize_value(["a"]) == ["a"]
    assert serialize_value(("a", "b")) == ["a", "b"]
    assert serialize_value(date(2026, 1, 2)) == "2026-01-02"
    assert serialize_value(42) == 42


def test_serialize_cleaned_data_redacts_passport_and_cvv():
    data = serialize_cleaned_data(
        {"passport_number": "X1", "cvv": "123", "name": "Prince"}
    )
    assert data["passport_number"] == "[redacted]"
    assert data["cvv"] == "[redacted]"
    assert data["name"] == "Prince"


@pytest.mark.django_db
def test_validate_and_clean_success_for_formset(valid_formset_payload):
    result = validate_and_clean("formset", valid_formset_payload)
    assert result.is_valid
    assert len(result.cleaned_data["rows"]) == 1
    assert result.errors == {}


@pytest.mark.django_db
def test_validate_and_clean_formset_collects_row_and_non_form_errors():
    payload = {
        "addresses-TOTAL_FORMS": "2",
        "addresses-INITIAL_FORMS": "0",
        "addresses-MIN_NUM_FORMS": "1",
        "addresses-MAX_NUM_FORMS": "5",
        "addresses-0-country": "US",
        "addresses-0-state_province": "CA",
        "addresses-0-street": "1 Market St",
        "addresses-0-city": "San Francisco",
        "addresses-0-postal_code": "94105",
        "addresses-1-country": "US",
        "addresses-1-state_province": "CA",
        "addresses-1-street": "1 Market St",
        "addresses-1-city": "San Francisco",
        "addresses-1-postal_code": "94105",
    }
    result = validate_and_clean("formset", payload)
    assert not result.is_valid
    assert "__all__" in result.errors
    assert "Duplicate" in " ".join(result.errors["__all__"])


@pytest.mark.django_db
def test_validate_and_clean_skips_deleted_formset_rows(valid_formset_payload):
    valid_formset_payload["addresses-TOTAL_FORMS"] = "2"
    valid_formset_payload["addresses-1-country"] = "CA"
    valid_formset_payload["addresses-1-state_province"] = "ON"
    valid_formset_payload["addresses-1-street"] = "2 Queen St"
    valid_formset_payload["addresses-1-city"] = "Toronto"
    valid_formset_payload["addresses-1-postal_code"] = "M5H 2N2"
    valid_formset_payload["addresses-1-DELETE"] = "on"
    result = validate_and_clean("formset", valid_formset_payload)
    assert result.is_valid
    assert len(result.cleaned_data["rows"]) == 1


def test_validate_single_field_raises_for_unknown_field():
    with pytest.raises(ValueError, match="not on"):
        validate_single_field("signup", "not_a_field", {})


def test_collect_errors_for_plain_form():
    form = SignupForm({"username": "!!"})
    form.is_valid()
    errors = collect_errors(form)
    assert "username" in errors


def test_collect_errors_for_formset(valid_formset_payload):
    artifact = build_artifact("formset", valid_formset_payload)
    artifact.is_valid()
    errors = collect_errors(artifact)
    assert isinstance(errors, dict)


def test_collect_errors_includes_per_row_field_errors():
    payload = {
        "addresses-TOTAL_FORMS": "1",
        "addresses-INITIAL_FORMS": "0",
        "addresses-MIN_NUM_FORMS": "1",
        "addresses-MAX_NUM_FORMS": "5",
        "addresses-0-country": "US",
        "addresses-0-state_province": "CA",
        "addresses-0-street": "",
        "addresses-0-city": "San Francisco",
        "addresses-0-postal_code": "94105",
    }
    formset = build_artifact("formset", payload)
    formset.is_valid()
    errors = collect_errors(formset)
    assert any(key.startswith("row_0.") for key in errors)


@pytest.mark.django_db
def test_log_validation_errors_records_field_and_non_field_codes():
    form = SignupForm({"username": "admin"})
    form.is_valid()
    log_validation_errors("signup", form)
    assert ValidationLog.objects.filter(form_name="signup").exists()


@pytest.mark.django_db
def test_log_validation_errors_formset_non_field_error():
    payload = {
        "addresses-TOTAL_FORMS": "2",
        "addresses-INITIAL_FORMS": "0",
        "addresses-MIN_NUM_FORMS": "1",
        "addresses-MAX_NUM_FORMS": "5",
        "addresses-0-country": "US",
        "addresses-0-state_province": "CA",
        "addresses-0-street": "Dup",
        "addresses-0-city": "City",
        "addresses-0-postal_code": "94105",
        "addresses-1-country": "US",
        "addresses-1-state_province": "CA",
        "addresses-1-street": "Dup",
        "addresses-1-city": "City",
        "addresses-1-postal_code": "94105",
    }
    formset = build_artifact("formset", payload)
    formset.is_valid()
    log_validation_errors("formset", formset)
    assert ValidationLog.objects.filter(form_name="formset").exists()


def test_validation_result_dataclass():
    result = ValidationResult(
        form_name="signup",
        is_valid=False,
        message="Validation failed.",
    )
    assert not result.is_valid
    assert result.cleaned_data == {}


def test_build_artifact_with_files_and_initial():
    upload = SimpleUploadedFile("r.pdf", b"%PDF", content_type="application/pdf")
    form = build_artifact("file-upload", {}, files={"resume": upload})
    assert form.is_bound
    form2 = build_artifact("signup", initial={"username": "seed"})
    assert form2.initial["username"] == "seed"
