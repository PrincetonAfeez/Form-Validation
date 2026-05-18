from __future__ import annotations

import re

from django import forms
from django.core.exceptions import ValidationError

try:
    import phonenumbers
except ImportError:  # pragma: no cover - optional dependency fallback
    phonenumbers = None

E164_RE = re.compile(r"^\+[1-9]\d{7,14}$")


class PhoneField(forms.CharField):
    """Normalizes phone input to E.164 strings."""

    default_error_messages = {
        "invalid": "Enter a valid phone number.",
    }

    def __init__(self, *args, region: str = "US", **kwargs):
        self.region = region
        kwargs.setdefault(
            "widget",
            forms.TextInput(
                attrs={
                    "type": "tel",
                    "placeholder": "+1 415 555 2671",
                    "autocomplete": "tel",
                }
            ),
        )
        super().__init__(*args, **kwargs)

    def to_python(self, value):
        value = super().to_python(value)
        if not value:
            return ""
        return self._normalize(value)

    def _normalize(self, value: str) -> str:
        if phonenumbers:
            try:
                parsed = phonenumbers.parse(value, self.region)
            except phonenumbers.NumberParseException as exc:
                raise ValidationError(
                    self.error_messages["invalid"],
                    code="invalid_phone",
                ) from exc
            if not phonenumbers.is_valid_number(parsed):
                raise ValidationError(
                    self.error_messages["invalid"],
                    code="invalid_phone",
                )
            return phonenumbers.format_number(
                parsed,
                phonenumbers.PhoneNumberFormat.E164,
            )

        stripped = re.sub(r"[^\d+]", "", value)
        digits = re.sub(r"\D", "", stripped)
        if stripped.startswith("+") and E164_RE.match(stripped):
            return stripped
        if self.region == "US" and len(digits) == 10:
            return f"+1{digits}"
        if self.region == "US" and len(digits) == 11 and digits.startswith("1"):
            return f"+{digits}"
        if stripped.startswith("+") and len(digits) >= 8 and len(digits) <= 15:
            return f"+{digits}"
        raise ValidationError(self.error_messages["invalid"], code="invalid_phone")
