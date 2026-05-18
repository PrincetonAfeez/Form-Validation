from __future__ import annotations

import pytest
from django.core.exceptions import ObjectDoesNotExist

from apps.forms_lab.models import ValidationLog
from apps.forms_lab.services import (
    build_artifact,
    get_demo,
    serialize_cleaned_data,
    validate_and_clean,
    validate_single_field,
)


@pytest.mark.django_db
def test_validate_and_clean_returns_structured_result_and_redacts(valid_signup_payload):
    result = validate_and_clean("signup", valid_signup_payload)
    assert result.is_valid
    assert result.cleaned_data["password"] == "[redacted]"
    assert result.cleaned_data["phone"] == "+14155552671"


@pytest.mark.django_db
def test_validate_and_clean_logs_errors():
    result = validate_and_clean(
        "signup",
        {
            "username": "admin",
            "email": "bot@mailinator.com",
            "password": "short",
            "confirm_password": "different",
            "phone": "nope",
        },
    )
    assert not result.is_valid
    assert ValidationLog.objects.count() >= 1


def test_build_artifact_creates_formset():
    formset = build_artifact("formset")
    assert formset.prefix == "addresses"


def test_build_artifact_creates_wizard_step_and_unknown_demo_raises():
    form = build_artifact("wizard", step=2, initial={"preferred_contact": "email"})
    assert "preferred_contact" in form.fields
    with pytest.raises(ObjectDoesNotExist):
        get_demo("missing")


def test_serialize_cleaned_data_handles_lists_dates_and_redaction():
    from datetime import date

    data = serialize_cleaned_data(
        {"password": "secret", "items": ["a", "b"], "day": date(2026, 6, 1)}
    )
    assert data["password"] == "[redacted]"
    assert data["items"] == ["a", "b"]
    assert data["day"] == "2026-06-01"


def test_validate_single_field_reports_invalid_state():
    form, field, state, message = validate_single_field(
        "signup",
        "username",
        {"username": "admin"},
    )
    assert form.is_bound
    assert field.name == "username"
    assert state == "invalid"
    assert "unavailable" in message


def test_validate_single_field_does_not_require_unrelated_fields():
    _, _, state, message = validate_single_field(
        "signup",
        "username",
        {"username": "princeton"},
    )
    assert state == "valid"
    assert message == "Looks good."


@pytest.mark.django_db
def test_index_and_demo_pages_render(client):
    assert client.get("/").status_code == 200
    response = client.get("/forms/signup/")
    assert response.status_code == 200
    assert b"Signup Form" in response.content
    assert client.get("/forms/missing/").status_code == 404


@pytest.mark.django_db
def test_full_signup_post_renders_success(client, valid_signup_payload):
    response = client.post("/forms/signup/", valid_signup_payload)
    assert response.status_code == 200
    assert b"Validation passed" in response.content


@pytest.mark.django_db
def test_htmx_field_validation_returns_shared_field_partial(client):
    response = client.post(
        "/forms/signup/field/username/",
        {"username": "admin"},
        HTTP_HX_REQUEST="true",
    )
    assert response.status_code == 200
    assert b"id_username-wrap" in response.content
    assert b"unavailable" in response.content


@pytest.mark.django_db
def test_payment_brand_detect_endpoint(client):
    response = client.post(
        "/forms/payment/brand-detect/",
        {"card_number": "378282246310005"},
        HTTP_HX_REQUEST="true",
    )
    assert response.status_code == 200
    assert b"amex" in response.content
    assert b"4" in response.content


@pytest.mark.django_db
def test_dependent_htmx_endpoints_render(client):
    country = client.post(
        "/forms/address/country-change/",
        {"country": "CA"},
        HTTP_HX_REQUEST="true",
    )
    assert country.status_code == 200
    assert b"Ontario" in country.content

    passport = client.post(
        "/forms/survey/toggle-passport/",
        {"has_passport": "on"},
        HTTP_HX_REQUEST="true",
    )
    assert passport.status_code == 200
    assert b"Passport number" in passport.content


@pytest.mark.django_db
def test_reference_and_stats_pages_render(client):
    ValidationLog.objects.create(
        form_name="signup",
        field_name="email",
        error_code="disposable_email",
    )
    assert client.get("/reference/").status_code == 200
    response = client.get("/stats/")
    assert response.status_code == 200
    assert b"disposable_email" in response.content


@pytest.mark.django_db
def test_wizard_step_endpoint_advances_on_valid_step(client):
    response = client.post(
        "/forms/wizard/step/1/",
        {
            "first_name": "Prince",
            "last_name": "Afeez",
            "phone": "4155552671",
            "step": "1",
        },
        HTTP_HX_REQUEST="true",
    )
    assert response.status_code == 200
    assert b"Step 2 of 3" in response.content


@pytest.mark.django_db
def test_wizard_completion_revalidates_session_state(client):
    session = client.session
    session["wizard_state"] = {
        "1": {"first_name": "Prince", "last_name": "Afeez", "phone": "+14155552671"},
        "2": {
            "preferred_contact": "email",
            "topics": ["forms"],
            "notes": "Plain note",
        },
    }
    session.save()
    response = client.post(
        "/forms/wizard/step/3/",
        {"confirm": "on", "step": "3"},
        HTTP_HX_REQUEST="true",
    )
    assert response.status_code == 200
    assert b"Wizard completed" in response.content


@pytest.mark.django_db
def test_file_scan_and_formset_endpoints_render(client):
    from django.core.files.uploadedfile import SimpleUploadedFile

    scan = client.post(
        "/forms/file-upload/scan/",
        {
            "resume": SimpleUploadedFile(
                "resume.pdf", b"%PDF-1.4\nbody", content_type="application/pdf"
            )
        },
        HTTP_HX_REQUEST="true",
    )
    assert scan.status_code == 200
    assert b"Validation passed" in scan.content

    add = client.post(
        "/forms/formset/add-row/",
        {"addresses-TOTAL_FORMS": "1"},
        HTTP_HX_REQUEST="true",
    )
    assert add.status_code == 200
    assert b"formset-row-1" in add.content
