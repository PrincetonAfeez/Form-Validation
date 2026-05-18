""" Test validators extended. """

from __future__ import annotations

from datetime import date
from io import BytesIO
from unittest.mock import patch

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from apps.forms_lab.validators import get
from apps.forms_lab.validators.address import validate_postal_for_country
from apps.forms_lab.validators.antispam import validate_time_trap
from apps.forms_lab.validators.email_rules import (
    validate_email_mx,
    validate_not_disposable,
)
from apps.forms_lab.validators.files import (
    sniff_mime,
)
from apps.forms_lab.validators.payment import (
    detect_card_brand,
    normalize_card_number,
    validate_luhn,
    validate_not_expired,
)
from apps.forms_lab.validators.phone import validate_e164
from apps.forms_lab.validators.text import validate_no_html, validate_no_profanity


def test_address_postal_empty_and_gb_valid():
    validate_postal_for_country("", "US")
    validate_postal_for_country("SW1A 1AA", "GB")
    with pytest.raises(ValidationError):
        validate_postal_for_country("123", "GB")


def test_payment_brand_detection_matrix():
    assert detect_card_brand("4111111111111111") == "visa"
    assert detect_card_brand("2221000000000009") == "mastercard"
    assert detect_card_brand("6011000000000004") == "discover"
    assert normalize_card_number("4111-1111") == "41111111"
    validate_luhn("6011111111111117")


def test_payment_expiry_current_month():
    today = date.today()
    validate_not_expired(today.month, today.year)


def test_phone_e164_empty_skips():
    validate_e164("")


def test_email_skips_blank_values():
    validate_not_disposable("")
    validate_email_mx("")


def test_text_no_html_allows_plain_punctuation():
    validate_no_html("Tom & Jerry")
    validate_no_html("50% > 40%")
    validate_no_html("if x < y > z then ok")
    validate_no_html("Plain text")


def test_text_no_html_rejects_markup():
    with pytest.raises(ValidationError) as exc:
        validate_no_html("<i>x</i>")
    assert exc.value.code == "html"


def test_text_profanity_word_stripping():
    with pytest.raises(ValidationError):
        validate_no_profanity("What a heckword!")


def test_files_sniff_mime_fallbacks():
    pdf = SimpleUploadedFile("a.pdf", b"%PDF-1.4", content_type="application/pdf")
    assert sniff_mime(pdf) == "application/pdf"
    png = SimpleUploadedFile(
        "a.png",
        b"\x89PNG\r\n\x1a\n" + b"x" * 4,
        content_type="image/png",
    )
    assert sniff_mime(png) == "image/png"
    jpeg = SimpleUploadedFile(
        "a.jpg",
        b"\xff\xd8\xff\xe0" + b"x" * 4,
        content_type="image/jpeg",
    )
    assert sniff_mime(jpeg) == "image/jpeg"
    gif = SimpleUploadedFile(
        "a.gif",
        b"GIF89a" + b"x" * 4,
        content_type="image/gif",
    )
    assert sniff_mime(gif) == "image/gif"
    plain = SimpleUploadedFile("t.txt", b"hello", content_type="text/plain")
    assert sniff_mime(plain) == "text/plain"


def test_files_image_dimensions_within_limits():
    image_io = BytesIO()
    Image.new("RGB", (100, 100), "white").save(image_io, format="PNG")
    png = SimpleUploadedFile(
        "ok.png",
        image_io.getvalue(),
        content_type="image/png",
    )
    from apps.forms_lab.validators.files import validate_image_dimensions

    validate_image_dimensions(png, max_w=200, max_h=200)
    with pytest.raises(ValidationError):
        validate_image_dimensions(png, max_w=10, max_h=10)


def test_files_image_dimensions_without_pillow_skips():
    png = SimpleUploadedFile("x.png", b"\x89PNG\r\n\x1a\n", content_type="image/png")
    with patch("apps.forms_lab.validators.files.Image", None):
        from apps.forms_lab.validators.files import validate_image_dimensions

        validate_image_dimensions(png)


def test_password_strength_common_and_class_branches():
    from apps.forms_lab.validators.strength import validate_password_strength

    with pytest.raises(ValidationError) as exc:
        validate_password_strength("password123")
    assert exc.value.code == "common"

    with pytest.raises(ValidationError) as exc:
        validate_password_strength("passwordpassword")
    assert exc.value.code == "common"

    with pytest.raises(ValidationError) as exc:
        validate_password_strength("Short1!")
    assert exc.value.code == "too_short"

    with pytest.raises(ValidationError) as exc:
        validate_password_strength("alllowercaseletters")
    assert exc.value.code == "missing_character_classes"


def test_antispam_time_trap_naive_datetime():
    from datetime import datetime

    payload = {
        "started_at": (datetime.now() - __import__("datetime").timedelta(seconds=10))
        .replace(tzinfo=None)
        .isoformat()
    }
    validate_time_trap(payload, min_seconds=3)


def test_registry_configurable_password_validator():
    validator = get("password.strength.configurable")
    validator("LongEnoughPass9!")
    with pytest.raises(ValidationError):
        validator("short")
