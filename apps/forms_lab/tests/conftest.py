""" Test fixtures for the form validation showcase. """

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile


@pytest.fixture
def valid_signup_payload():
    started = (datetime.now(timezone.utc) - timedelta(seconds=10)).isoformat()
    return {
        "username": "princeton",
        "email": "princeton@example.com",
        "password": "CorrectHorse9!",
        "confirm_password": "CorrectHorse9!",
        "phone": "4155552671",
        "accept_terms": "on",
        "website": "",
        "started_at": started,
    }


@pytest.fixture
def signup_started_at():
    return (datetime.now(timezone.utc) - timedelta(seconds=10)).isoformat()


@pytest.fixture
def valid_address_payload():
    return {
        "country": "US",
        "state_province": "CA",
        "postal_code": "94105",
        "street": "1 Market St",
        "city": "San Francisco",
    }


@pytest.fixture
def valid_payment_payload():
    return {
        "card_number": "4242 4242 4242 4242",
        "expiry_month": "12",
        "expiry_year": str(date.today().year + 1),
        "cvv": "123",
        "name_on_card": "Prince Afeez",
    }


@pytest.fixture
def valid_formset_payload():
    return {
        "addresses-TOTAL_FORMS": "1",
        "addresses-INITIAL_FORMS": "0",
        "addresses-MIN_NUM_FORMS": "1",
        "addresses-MAX_NUM_FORMS": "5",
        "addresses-0-country": "US",
        "addresses-0-state_province": "CA",
        "addresses-0-street": "1 Market St",
        "addresses-0-city": "San Francisco",
        "addresses-0-postal_code": "94105",
    }


@pytest.fixture
def pdf_upload():
    return SimpleUploadedFile(
        "resume.pdf",
        b"%PDF-1.4\nbody",
        content_type="application/pdf",
    )
