from __future__ import annotations

from datetime import date

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from apps.forms_lab.validators import all_validators, get
from apps.forms_lab.validators.address import validate_postal_for_country
from apps.forms_lab.validators.antispam import validate_honeypot
from apps.forms_lab.validators.email_rules import (
    validate_email_mx,
    validate_not_disposable,
)
from apps.forms_lab.validators.files import validate_file_size, validate_magic_bytes
from apps.forms_lab.validators.payment import (
    detect_card_brand,
    normalize_card_number,
    validate_cvv_for_brand,
    validate_luhn,
    validate_not_expired,
)
from apps.forms_lab.validators.phone import validate_e164
from apps.forms_lab.validators.strength import PasswordStrengthValidator
from apps.forms_lab.validators.text import validate_no_html, validate_no_profanity


def test_registry_exposes_named_validators():
    names = {validator.name for validator in all_validators()}
    assert "password.strength" in names
    assert get("payment.luhn") is validate_luhn


def test_password_strength_function_and_class():
    get("password.strength")("CorrectHorse9!")
    PasswordStrengthValidator(min_length=10, require_classes=2)("Correct999")
    with pytest.raises(ValidationError):
        get("password.strength")("short")
    with pytest.raises(ValidationError):
        PasswordStrengthValidator(min_length=8, require_classes=4)("Correct99")


def test_email_rules():
    validate_not_disposable("person@example.com")
    validate_email_mx("person@example.com")
    with pytest.raises(ValidationError):
        validate_not_disposable("bot@mailinator.com")
    with pytest.raises(ValidationError):
        validate_email_mx("person@invalid")
    with pytest.raises(ValidationError):
        validate_email_mx("user@bad..example.com")


def test_phone_and_address_validators():
    validate_e164("+14155552671")
    validate_postal_for_country("94105", "US")
    validate_postal_for_country("K1A 0B1", "CA")
    with pytest.raises(ValidationError):
        validate_e164("4155552671")
    with pytest.raises(ValidationError):
        validate_postal_for_country("ABCDE", "US")


def test_payment_validators():
    validate_luhn("4242 4242 4242 4242")
    assert normalize_card_number("4242 4242") == "42424242"
    assert detect_card_brand("378282246310005") == "amex"
    assert detect_card_brand("5555555555554444") == "mastercard"
    assert detect_card_brand("6011111111111117") == "discover"
    assert detect_card_brand("0000000000000000") == "unknown"
    validate_cvv_for_brand("1234", "amex")
    validate_not_expired(12, date.today().year + 1)
    with pytest.raises(ValidationError):
        validate_luhn("4242 4242 4242 4241")
    with pytest.raises(ValidationError):
        validate_cvv_for_brand("123", "amex")
    with pytest.raises(ValidationError):
        validate_not_expired(1, 2020)


@settings(
    max_examples=25,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)
@given(st.lists(st.integers(min_value=0, max_value=9), min_size=12, max_size=18))
def test_luhn_rejects_mutated_check_digit(digits):
    number = "".join(map(str, digits))
    mutated = number[:-1] + str((int(number[-1]) + 1) % 10)
    try:
        validate_luhn(number)
    except ValidationError:
        return
    with pytest.raises(ValidationError):
        validate_luhn(mutated)


def test_text_and_antispam_validators():
    validate_no_html("Plain text")
    validate_no_profanity("Helpful note")
    validate_honeypot({"website": ""})
    with pytest.raises(ValidationError):
        validate_no_html("<b>bad</b>")
    with pytest.raises(ValidationError):
        validate_no_profanity("heckword")
    with pytest.raises(ValidationError):
        validate_honeypot({"website": "spam"})


def test_time_trap_validator():
    from datetime import datetime, timezone

    from apps.forms_lab.validators.antispam import validate_time_trap

    with pytest.raises(ValidationError):
        validate_time_trap(
            {"started_at": datetime.now(timezone.utc).isoformat()}, min_seconds=3
        )
    validate_time_trap({"started_at": "not-a-date"})
    with pytest.raises(ValidationError):
        validate_time_trap({})


def test_file_validators():
    pdf = SimpleUploadedFile(
        "resume.pdf",
        b"%PDF-1.4\nbody",
        content_type="application/pdf",
    )
    validate_file_size(pdf)
    validate_magic_bytes(pdf, {"application/pdf"})
    oversized = SimpleUploadedFile(
        "large.pdf", b"x" * 12, content_type="application/pdf"
    )
    with pytest.raises(ValidationError):
        validate_file_size(oversized, max_bytes=4)


def test_image_dimensions_rejects_unreadable_image_bytes():
    png = SimpleUploadedFile(
        "broken.png",
        b"\x89PNG\r\n\x1a\n" + b"not-a-real-image",
        content_type="image/png",
    )
    with pytest.raises(ValidationError):
        from apps.forms_lab.validators.files import validate_image_dimensions

        validate_image_dimensions(png)


def test_file_magic_bytes_rejects_bad_mime_and_reads_images():
    png = SimpleUploadedFile(
        "avatar.png",
        b"\x89PNG\r\n\x1a\n" + b"0" * 20,
        content_type="image/png",
    )
    validate_magic_bytes(png, {"image/png"})
    bad = SimpleUploadedFile("bad.txt", b"plain text", content_type="text/plain")
    with pytest.raises(ValidationError):
        validate_magic_bytes(bad, {"application/pdf"})


def test_password_validator_reads_blocklist_file(tmp_path):
    path = tmp_path / "blocked.txt"
    path.write_text("UniqueBlocked99!\n")
    validator = PasswordStrengthValidator(
        min_length=8, require_classes=2, blocklist_path=str(path)
    )
    with pytest.raises(ValidationError):
        validator("UniqueBlocked99!")
    assert validator == PasswordStrengthValidator(
        min_length=8,
        require_classes=2,
        blocklist_path=str(path),
    )
