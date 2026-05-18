from __future__ import annotations

from datetime import datetime, timezone

import pytest
from django.urls import reverse

from apps.forms_lab.forms import DEMO_BY_SLUG


@pytest.mark.parametrize("slug", list(DEMO_BY_SLUG.keys()))
@pytest.mark.django_db
def test_all_demo_pages_load(client, slug):
    response = client.get(reverse("forms_lab:form_detail", kwargs={"slug": slug}))
    assert response.status_code == 200
    demo = DEMO_BY_SLUG[slug]
    assert demo.title.encode() in response.content


@pytest.mark.django_db
def test_wizard_get_with_step_query_uses_session(client):
    session = client.session
    session["wizard_state"] = {
        "1": {"first_name": "A", "last_name": "B", "phone": "+14155552671"}
    }
    session.save()
    response = client.get("/forms/wizard/?step=2")
    assert response.status_code == 200
    assert b"Step 2" in response.content


@pytest.mark.django_db
def test_wizard_post_via_form_detail_delegates_to_step(client):
    response = client.post(
        "/forms/wizard/",
        {
            "first_name": "Prince",
            "last_name": "Afeez",
            "phone": "4155552671",
            "step": "1",
        },
    )
    assert response.status_code == 200


@pytest.mark.django_db
def test_wizard_invalid_step_returns_404(client):
    assert client.post("/forms/wizard/step/99/", {"step": "99"}).status_code == 404


@pytest.mark.django_db
def test_wizard_invalid_step_two_shows_errors(client):
    response = client.post(
        "/forms/wizard/step/2/",
        {"step": "2"},
        HTTP_HX_REQUEST="true",
    )
    assert response.status_code == 200
    assert (
        b"error" in response.content.lower()
        or b"required" in response.content.lower()
    )


@pytest.mark.django_db
def test_wizard_non_htmx_step_renders_full_page(client):
    response = client.post(
        "/forms/wizard/step/1/",
        {
            "first_name": "Prince",
            "last_name": "Afeez",
            "phone": "4155552671",
            "step": "1",
        },
    )
    assert response.status_code == 200
    assert b"form_detail" in response.content or b"Wizard" in response.content


@pytest.mark.django_db
def test_wizard_completion_fails_when_session_step_invalid(client):
    session = client.session
    session["wizard_state"] = {
        "1": {"first_name": "Prince", "last_name": "Afeez", "phone": "not-a-phone"},
        "2": {"preferred_contact": "email", "topics": ["forms"]},
    }
    session.save()
    response = client.post(
        "/forms/wizard/step/3/",
        {"confirm": "on", "step": "3"},
        HTTP_HX_REQUEST="true",
    )
    assert response.status_code == 200
    assert b"Wizard completed" not in response.content


@pytest.mark.django_db
def test_signup_post_rejects_honeypot(client, valid_signup_payload):
    valid_signup_payload["website"] = "http://spam.example"
    response = client.post("/forms/signup/", valid_signup_payload)
    assert response.status_code == 200
    assert b"Validation passed" not in response.content


@pytest.mark.django_db
def test_signup_post_rejects_fast_submit(client, valid_signup_payload):
    valid_signup_payload["started_at"] = datetime.now(timezone.utc).isoformat()
    response = client.post("/forms/signup/", valid_signup_payload)
    assert b"Validation passed" not in response.content


@pytest.mark.django_db
def test_address_post_valid_and_invalid(client, valid_address_payload):
    ok = client.post("/forms/address/", valid_address_payload)
    assert b"Validation passed" in ok.content
    bad = valid_address_payload.copy()
    bad["postal_code"] = "BAD"
    fail = client.post("/forms/address/", bad)
    assert b"Validation passed" not in fail.content


@pytest.mark.django_db
def test_payment_post_valid_and_expired(client, valid_payment_payload):
    ok = client.post("/forms/payment/", valid_payment_payload)
    assert b"Validation passed" in ok.content
    expired = valid_payment_payload.copy()
    expired["expiry_year"] = "2020"
    fail = client.post("/forms/payment/", expired)
    assert b"Validation passed" not in fail.content


@pytest.mark.django_db
def test_survey_post_valid(client):
    response = client.post(
        "/forms/survey/",
        {
            "satisfaction": "5",
            "interests": ["forms"],
            "availability_date": "2026-06-01",
            "availability_time": "12:00",
            "favorite_color": "#00aa99",
            "rating": "8",
        },
    )
    assert b"Validation passed" in response.content


@pytest.mark.django_db
def test_formset_post_valid(client, valid_formset_payload):
    response = client.post("/forms/formset/", valid_formset_payload)
    assert b"Validation passed" in response.content


@pytest.mark.django_db
def test_file_upload_post_invalid_without_resume(client):
    response = client.post("/forms/file-upload/", {})
    assert b"Validation passed" not in response.content


@pytest.mark.django_db
def test_file_upload_post_valid(client, pdf_upload):
    response = client.post(
        "/forms/file-upload/",
        {"resume": pdf_upload},
    )
    assert b"Validation passed" in response.content


@pytest.mark.django_db
def test_field_validate_endpoint_email(client):
    response = client.post(
        "/forms/signup/field/email/",
        {"email": "bot@mailinator.com"},
        HTTP_HX_REQUEST="true",
    )
    assert response.status_code == 200
    assert "fieldValidated" in response["HX-Trigger"]
    assert (
        b"disposable" in response.content.lower()
        or b"permanent" in response.content.lower()
    )


@pytest.mark.django_db
def test_signup_check_username_and_email_aliases(client):
    user = client.post(
        "/forms/signup/check-username/",
        {"username": "admin"},
        HTTP_HX_REQUEST="true",
    )
    assert b"unavailable" in user.content
    email = client.post(
        "/forms/signup/check-email/",
        {"email": "x@example.com"},
        HTTP_HX_REQUEST="true",
    )
    assert email.status_code == 200


@pytest.mark.django_db
def test_address_field_htmx_postal(client, valid_address_payload):
    response = client.post(
        "/forms/address/field/postal_code/",
        {
            "country": valid_address_payload["country"],
            "postal_code": valid_address_payload["postal_code"],
        },
        HTTP_HX_REQUEST="true",
    )
    assert response.status_code == 200
    assert "fieldValidated" in response["HX-Trigger"]


@pytest.mark.django_db
def test_payment_brand_detect_visa_and_unknown(client):
    visa = client.post(
        "/forms/payment/brand-detect/",
        {"card_number": "4242424242424242"},
        HTTP_HX_REQUEST="true",
    )
    assert b"visa" in visa.content
    unknown = client.post(
        "/forms/payment/brand-detect/",
        {"card_number": "0000000000000000"},
        HTTP_HX_REQUEST="true",
    )
    assert "cardBrandDetected" in unknown["HX-Trigger"]


@pytest.mark.django_db
def test_survey_toggle_passport_hidden(client):
    response = client.post(
        "/forms/survey/toggle-passport/",
        {"has_passport": ""},
        HTTP_HX_REQUEST="true",
    )
    assert response.status_code == 200


@pytest.mark.django_db
def test_formset_add_row_invalid_total_defaults_to_zero(client):
    response = client.post(
        "/forms/formset/add-row/",
        {"addresses-TOTAL_FORMS": "not-int"},
        HTTP_HX_REQUEST="true",
    )
    assert b"formset-row-0" in response.content


@pytest.mark.django_db
def test_file_scan_invalid_shows_failure(client):
    response = client.post(
        "/forms/file-upload/scan/",
        {},
        HTTP_HX_REQUEST="true",
    )
    assert (
        b"Validation failed" in response.content
        or b"required" in response.content.lower()
    )


@pytest.mark.parametrize(
    "path",
    [
        "/forms/signup/field/username/",
        "/forms/payment/brand-detect/",
        "/forms/wizard/step/1/",
    ],
)
@pytest.mark.django_db
def test_post_only_endpoints_reject_get(client, path):
    assert client.get(path).status_code == 405


@pytest.mark.django_db
def test_field_validate_404_for_unknown_demo(client):
    assert client.post("/forms/unknown/field/username/").status_code == 404
