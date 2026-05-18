from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.forms_lab.fields import PhoneField
from apps.forms_lab.validators.files import sniff_mime


def test_phone_fallback_normalizes_us_11_digit_with_country_code():
    with patch("apps.forms_lab.fields.phonenumbers", None):
        field = PhoneField()
        assert field.clean("14155552671") == "+14155552671"


def test_phone_fallback_normalizes_international_e164_when_plus_present():
    with patch("apps.forms_lab.fields.phonenumbers", None):
        field = PhoneField()
        assert field.clean("+44 20 7946 0958") == "+442079460958"


def test_phone_fallback_rejects_non_us_bare_digits_without_plus():
    with patch("apps.forms_lab.fields.phonenumbers", None):
        field = PhoneField(region="GB")
        with pytest.raises(ValidationError) as exc_info:
            field.clean("02079460958")
        assert exc_info.value.code == "invalid_phone"


def test_sniff_mime_delegates_to_python_magic_when_installed():
    upload = SimpleUploadedFile("doc.pdf", b"binary", content_type="text/plain")
    mock_magic = MagicMock()
    mock_magic.from_buffer.return_value = "application/pdf"
    with patch("apps.forms_lab.validators.files.magic", mock_magic):
        assert sniff_mime(upload) == "application/pdf"
        mock_magic.from_buffer.assert_called_once()


def test_sniff_mime_unknown_bytes_falls_back_to_upload_content_type():
    upload = SimpleUploadedFile(
        "unknown.bin",
        b"not a known signature",
        content_type="application/custom",
    )
    with patch("apps.forms_lab.validators.files.magic", None):
        assert sniff_mime(upload) == "application/custom"
