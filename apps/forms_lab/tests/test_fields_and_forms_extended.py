""" Test fields and forms extended. """

from __future__ import annotations

from datetime import date
from io import BytesIO
from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from apps.forms_lab.fields import PhoneField
from apps.forms_lab.forms.address import SUBDIVISIONS, AddressForm
from apps.forms_lab.forms.file_upload import FileUploadForm, MultipleFileField
from apps.forms_lab.forms.formset import PreviousAddressForm
from apps.forms_lab.forms.payment import PaymentForm
from apps.forms_lab.forms.signup import SignupForm
from apps.forms_lab.forms.survey import SurveyForm
from apps.forms_lab.forms.wizard import WizardStepThreeForm


def test_phone_field_empty_returns_blank_when_optional():
    assert PhoneField(required=False).clean("") == ""


def test_phone_field_phonenumbers_invalid_number():
    field = PhoneField()

    class NumberParseException(Exception):
        pass

    with patch("apps.forms_lab.fields.phonenumbers") as mock_pn:
        mock_pn.NumberParseException = NumberParseException
        mock_pn.parse.side_effect = NumberParseException("invalid")
        with pytest.raises(ValidationError, match="valid phone"):
            field.clean("not-a-number")


def test_phone_field_phonenumbers_formats_valid_number():
    field = PhoneField()

    class NumberParseException(Exception):
        pass

    parsed = object()
    with patch("apps.forms_lab.fields.phonenumbers") as mock_pn:
        mock_pn.NumberParseException = NumberParseException
        mock_pn.parse.return_value = parsed
        mock_pn.is_valid_number.return_value = True
        mock_pn.PhoneNumberFormat.E164 = "E164"
        mock_pn.format_number.return_value = "+14155552671"
        assert field.clean("415-555-2671") == "+14155552671"


def test_phone_field_phonenumbers_not_valid_number():
    field = PhoneField()

    class NumberParseException(Exception):
        pass

    with patch("apps.forms_lab.fields.phonenumbers") as mock_pn:
        mock_pn.NumberParseException = NumberParseException
        mock_pn.parse.return_value = object()
        mock_pn.is_valid_number.return_value = False
        mock_pn.PhoneNumberFormat.E164 = "E164"
        mock_pn.format_number.return_value = "+14155552671"
        with pytest.raises(ValidationError):
            field.clean("4155552671")


def test_address_form_gb_submotion_and_invalid_postal():
    form = AddressForm(
        {
            "country": "GB",
            "state_province": "ENG",
            "postal_code": "SW1A 1AA",
            "street": "10 Downing St",
            "city": "London",
        }
    )
    assert form.is_valid(), form.errors
    assert SUBDIVISIONS["GB"]


def test_address_form_rejects_invalid_us_zip():
    form = AddressForm(
        {
            "country": "US",
            "state_province": "CA",
            "postal_code": "ABCDE",
            "street": "1 Market St",
            "city": "San Francisco",
        }
    )
    assert not form.is_valid()
    assert "postal_code" in form.errors


def test_payment_form_rejects_bad_luhn():
    form = PaymentForm(
        {
            "card_number": "4242 4242 4242 4241",
            "expiry_month": "12",
            "expiry_year": str(date.today().year + 1),
            "cvv": "123",
            "name_on_card": "Test",
        }
    )
    assert not form.is_valid()
    assert "card_number" in form.errors


def test_payment_invalid_luhn_amex_pattern_does_not_add_cvv_error():
    """Amex-shaped number that fails Luhn must not trigger a misleading 3-digit CVV error."""
    form = PaymentForm(
        {
            "card_number": "378282246310001",
            "expiry_month": "12",
            "expiry_year": str(date.today().year + 1),
            "cvv": "123",
            "name_on_card": "Test",
        }
    )
    assert not form.is_valid()
    assert "card_number" in form.errors
    assert "cvv" not in form.errors
    assert form.detected_brand == "amex"


def test_payment_amex_valid_cvv():
    form = PaymentForm(
        {
            "card_number": "378282246310005",
            "expiry_month": "12",
            "expiry_year": str(date.today().year + 1),
            "cvv": "1234",
            "name_on_card": "Test",
        }
    )
    assert form.is_valid(), form.errors
    assert form.cleaned_data["card_brand"] == "amex"


def test_file_upload_rejects_oversized_resume():
    huge = SimpleUploadedFile(
        "big.pdf",
        b"%PDF-1.4\n" + b"x" * (6 * 1024 * 1024),
        content_type="application/pdf",
    )
    form = FileUploadForm(data={}, files={"resume": huge})
    assert not form.is_valid()


def test_file_upload_rejects_wrong_magic_bytes():
    fake = SimpleUploadedFile(
        "resume.pdf",
        b"not a pdf",
        content_type="text/plain",
    )
    form = FileUploadForm(data={}, files={"resume": fake})
    assert not form.is_valid()


def test_multiple_file_field_empty_optional():
    field = MultipleFileField(required=False)
    assert field.clean([], None) == []


def test_multiple_file_field_single_file():
    upload = SimpleUploadedFile("a.pdf", b"%PDF", content_type="application/pdf")
    field = MultipleFileField(required=False)
    result = field.clean(upload, None)
    assert len(result) == 1


def test_previous_address_form_uses_prefix_country():
    form = PreviousAddressForm(
        data={
            "addresses-0-country": "CA",
            "addresses-0-state_province": "ON",
            "addresses-0-street": "1",
            "addresses-0-city": "Ottawa",
            "addresses-0-postal_code": "K1A 0B1",
        },
        prefix="addresses-0",
    )
    assert form.fields["state_province"].choices == SUBDIVISIONS["CA"]


def test_signup_rejects_honeypot():
    form = SignupForm(
        {
            "username": "princeton",
            "email": "princeton@example.com",
            "password": "CorrectHorse9!",
            "confirm_password": "CorrectHorse9!",
            "phone": "4155552671",
            "accept_terms": "on",
            "website": "filled",
        }
    )
    assert not form.is_valid()


def test_survey_valid_without_passport():
    form = SurveyForm(
        {
            "satisfaction": "4",
            "interests": ["forms"],
            "availability_date": "2026-06-01",
            "availability_time": "09:30",
            "favorite_color": "#112233",
            "rating": "5",
        }
    )
    assert form.is_valid(), form.errors


def test_file_upload_validates_image_in_supporting_docs():
    image_io = BytesIO()
    Image.new("RGB", (10, 10), "white").save(image_io, format="PNG")
    avatar = SimpleUploadedFile(
        "doc.png",
        image_io.getvalue(),
        content_type="image/png",
    )
    resume = SimpleUploadedFile(
        "resume.pdf",
        b"%PDF-1.4\nbody",
        content_type="application/pdf",
    )
    form = FileUploadForm(
        data={},
        files={"resume": resume, "supporting_docs": [avatar]},
    )
    assert form.is_valid(), form.errors


def test_wizard_step_three_requires_confirm():
    form = WizardStepThreeForm({})
    assert not form.is_valid()
    form = WizardStepThreeForm({"confirm": "on"})
    assert form.is_valid()
