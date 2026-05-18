import re

from django.core.exceptions import ValidationError

from .registry import register

POSTAL_PATTERNS = {
    "US": re.compile(r"^\d{5}(-\d{4})?$"),
    "CA": re.compile(r"^[A-Z]\d[A-Z] ?\d[A-Z]\d$"),
    "GB": re.compile(r"^[A-Z]{1,2}\d[A-Z\d]? ?\d[A-Z]{2}$"),
}


@register("address.postal.country", examples=("94105/US", "K1A 0B1/CA"))
def validate_postal_for_country(value: str, country: str = "US") -> None:
    """Applies a country-specific postal-code pattern."""
    if not value:
        return
    pattern = POSTAL_PATTERNS.get(country)
    if pattern and not pattern.match(value.upper()):
        raise ValidationError(
            f"Enter a valid postal code for {country}.",
            code="postal_country",
        )
