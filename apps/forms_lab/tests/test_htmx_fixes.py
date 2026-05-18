from __future__ import annotations

import pytest


@pytest.mark.django_db
def test_wizard_back_link_uses_htmx_partial_navigation(client):
    response = client.get("/forms/wizard/?step=2")
    assert response.status_code == 200
    html = response.content.decode()
    assert 'hx-get="/forms/wizard/?step=1"' in html
    assert 'hx-target="#wizard-shell"' in html
    assert 'hx-select="#wizard-shell"' in html


@pytest.mark.django_db
def test_address_country_change_works_twice(client):
    first = client.post(
        "/forms/address/country-change/",
        {"country": "CA"},
        HTTP_HX_REQUEST="true",
    )
    assert first.status_code == 200
    assert b"Ontario" in first.content

    second = client.post(
        "/forms/address/country-change/",
        {"country": "GB"},
        HTTP_HX_REQUEST="true",
    )
    assert second.status_code == 200
    assert b"England" in second.content
    assert b"id=\"dependent-address-fields\"" not in second.content


@pytest.mark.django_db
def test_survey_passport_toggle_works_twice(client):
    show = client.post(
        "/forms/survey/toggle-passport/",
        {"has_passport": "on"},
        HTTP_HX_REQUEST="true",
    )
    assert b"Passport number" in show.content

    hide = client.post(
        "/forms/survey/toggle-passport/",
        {"has_passport": ""},
        HTTP_HX_REQUEST="true",
    )
    assert hide.status_code == 200
    assert b"Passport number" not in hide.content

    show_again = client.post(
        "/forms/survey/toggle-passport/",
        {"has_passport": "on"},
        HTTP_HX_REQUEST="true",
    )
    assert b"Passport number" in show_again.content


@pytest.mark.django_db
def test_payment_brand_detect_leaves_panel_in_dom(client):
    first = client.post(
        "/forms/payment/brand-detect/",
        {"card_number": "4242424242424242"},
        HTTP_HX_REQUEST="true",
    )
    assert b'id="payment-brand-panel"' in first.content
    assert b"visa" in first.content

    second = client.post(
        "/forms/payment/brand-detect/",
        {"card_number": "378282246310005"},
        HTTP_HX_REQUEST="true",
    )
    assert b'id="payment-brand-panel"' in second.content
    assert b"amex" in second.content


@pytest.mark.django_db
def test_wizard_revalidation_shows_failing_step(client):
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
    assert b"Step 1 of 3" in response.content
    assert b"Personal info" in response.content
    assert b'name="step" value="1"' in response.content


@pytest.mark.django_db
def test_invalid_signup_post_renders_field_errors_with_invalid_state(client):
    response = client.post(
        "/forms/signup/",
        {
            "username": "admin",
            "email": "princeton@example.com",
            "password": "short",
            "confirm_password": "short",
            "phone": "4155552671",
        },
    )
    assert response.status_code == 200
    assert b"text-red-700" in response.content or b"border-red-500" in response.content
    assert b"unavailable" in response.content
