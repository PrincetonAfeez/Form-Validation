""" Phone validation. """

import re

from django.core.exceptions import ValidationError

from .registry import register

E164_RE = re.compile(r"^\+[1-9]\d{7,14}$")


@register("phone.e164", examples=("+14155552671", "415-555-2671"))
def validate_e164(value: str) -> None:
    """Requires an already-normalized E.164 phone number."""
    if value and not E164_RE.match(value):
        raise ValidationError("Enter an E.164 phone number.", code="invalid_e164")
