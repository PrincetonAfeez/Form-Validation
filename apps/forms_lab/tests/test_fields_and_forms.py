from __future__ import annotations

from datetime import date
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from apps.forms_lab.fields import PhoneField
from apps.forms_lab.forms.address import AddressForm
from apps.forms_lab.forms.file_upload import FileUploadForm
from apps.forms_lab.forms.formset import PreviousAddressFormSet
from apps.forms_lab.forms.payment import PaymentForm
from apps.forms_lab.forms.signup import SignupForm
from apps.forms_lab.forms.survey import SurveyForm
from apps.forms_lab.forms.wizard import WizardStepOneForm, WizardStepTwoForm


def test_phone_field_normalizes_us_numbers():
    field = PhoneField()
    assert field.clean("(415) 555-2671") == "+14155552671"
    assert field.clean("+14155552671") == "+14155552671"


def test_signup_form_validates_and_redacts_sensitive_data_through_service(
    signup_started_at,
):
    form = SignupForm(
        {
            "username": "princeton",
            "email": "princeton@example.com",
            "password": "CorrectHorse9!",
            "confirm_password": "CorrectHorse9!",
            "phone": "(415) 555-2671",
            "accept_terms": "on",
            "website": "",
            "started_at": signup_started_at,
        }
    )
    assert form.is_valid(), form.errors
    assert form.cleaned_data["phone"] == "+14155552671"


def test_signup_form_blocks_reserved_username_and_password_mismatch(signup_started_at):
    form = SignupForm(
        {
            "username": "admin",
            "email": "bot@mailinator.com",
            "password": "CorrectHorse9!",
            "confirm_password": "DifferentHorse9!",
            "phone": "4155552671",
            "accept_terms": "on",
            "started_at": signup_started_at,
        }
    )
    assert not form.is_valid()
    assert "username" in form.errors
    assert "email" in form.errors
    assert "confirm_password" in form.errors


def test_address_form_normalizes_canadian_postal_code():
    form = AddressForm(
        {
            "country": "CA",
            "state_province": "ON",
            "postal_code": "k1a0b1",
            "street": "111 Wellington St",
            "city": "Ottawa",
        }
    )
    assert form.is_valid(), form.errors
    assert form.cleaned_data["postal_code"] == "K1A 0B1"


def test_payment_form_masks_card_and_derives_brand():
    form = PaymentForm(
        {
            "card_number": "4242 4242 4242 4242",
            "expiry_month": "12",
            "expiry_year": str(date.today().year + 1),
            "cvv": "123",
            "name_on_card": "Prince Afeez",
        }
    )
    assert form.is_valid(), form.errors
    assert form.cleaned_data["card_number"].endswith("4242")
    assert form.cleaned_data["card_brand"] == "visa"


def test_payment_form_enforces_brand_specific_cvv():
    form = PaymentForm(
        {
            "card_number": "378282246310005",
            "expiry_month": "12",
            "expiry_year": str(date.today().year + 1),
            "cvv": "123",
            "name_on_card": "Prince Afeez",
        }
    )
    assert not form.is_valid()
    assert "cvv" in form.errors


def test_file_upload_form_accepts_pdf_resume():
    form = FileUploadForm(
        data={},
        files={
            "resume": SimpleUploadedFile(
                "resume.pdf",
                b"%PDF-1.4\nbody",
                content_type="application/pdf",
            )
        },
    )
    assert form.is_valid(), form.errors


def test_file_upload_form_accepts_avatar_and_supporting_docs():
    image_io = BytesIO()
    Image.new("RGB", (10, 10), "white").save(image_io, format="PNG")
    avatar = SimpleUploadedFile(
        "avatar.png",
        image_io.getvalue(),
        content_type="image/png",
    )
    resume = SimpleUploadedFile(
        "resume.pdf",
        b"%PDF-1.4\nbody",
        content_type="application/pdf",
    )
    doc = SimpleUploadedFile(
        "support.pdf",
        b"%PDF-1.4\nbody",
        content_type="application/pdf",
    )
    form = FileUploadForm(
        data={}, files={"avatar": avatar, "resume": resume, "supporting_docs": [doc]}
    )
    assert form.is_valid(), form.errors


def test_formset_detects_duplicate_addresses():
    formset = PreviousAddressFormSet(
        {
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
        },
        prefix="addresses",
    )
    assert not formset.is_valid()
    assert "Duplicate" in str(formset.non_form_errors())


def test_formset_normalizes_canadian_postal_code():
    formset = PreviousAddressFormSet(
        {
            "addresses-TOTAL_FORMS": "1",
            "addresses-INITIAL_FORMS": "0",
            "addresses-MIN_NUM_FORMS": "1",
            "addresses-MAX_NUM_FORMS": "5",
            "addresses-0-country": "CA",
            "addresses-0-state_province": "ON",
            "addresses-0-street": "111 Wellington St",
            "addresses-0-city": "Ottawa",
            "addresses-0-postal_code": "k1a0b1",
        },
        prefix="addresses",
    )
    assert formset.is_valid(), formset.errors
    assert formset.forms[0].cleaned_data["postal_code"] == "K1A 0B1"


def test_formset_accepts_single_valid_address():
    formset = PreviousAddressFormSet(
        {
            "addresses-TOTAL_FORMS": "1",
            "addresses-INITIAL_FORMS": "0",
            "addresses-MIN_NUM_FORMS": "1",
            "addresses-MAX_NUM_FORMS": "5",
            "addresses-0-country": "US",
            "addresses-0-state_province": "CA",
            "addresses-0-street": "1 Market St",
            "addresses-0-city": "San Francisco",
            "addresses-0-postal_code": "94105",
        },
        prefix="addresses",
    )
    assert formset.is_valid(), formset.errors


def test_survey_requires_other_interest_and_passport_number():
    form = SurveyForm(
        {
            "satisfaction": "5",
            "interests": ["other"],
            "availability_date": "2026-06-01",
            "availability_time": "12:00",
            "favorite_color": "#00aa99",
            "rating": "8",
            "has_passport": "on",
        }
    )
    assert not form.is_valid()
    assert "other_interest" in form.errors
    assert "passport_number" in form.errors


def test_survey_accepts_conditional_values():
    form = SurveyForm(
        {
            "satisfaction": "5",
            "interests": ["other"],
            "other_interest": "Accessibility",
            "availability_date": "2026-06-01",
            "availability_time": "12:00",
            "favorite_color": "#00aa99",
            "rating": "8",
            "has_passport": "on",
            "passport_number": "X1234567",
        }
    )
    assert form.is_valid(), form.errors


def test_wizard_forms_and_result_helper():
    step_one = WizardStepOneForm(
        {"first_name": "Prince", "last_name": "Afeez", "phone": "4155552671"}
    )
    assert step_one.is_valid(), step_one.errors
    step_two = WizardStepTwoForm(
        {
            "preferred_contact": "email",
            "topics": ["forms", "testing"],
            "notes": "Plain note",
        }
    )
    assert step_two.is_valid(), step_two.errors
    assert step_two.cleaned_data["preferred_contact"] == "email"
