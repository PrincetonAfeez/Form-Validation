from __future__ import annotations

from datetime import date
from re import sub

from django.core.exceptions import ValidationError

from .registry import register


def normalize_card_number(value: str) -> str:
    return sub(r"\D", "", value or "")


def detect_card_brand(value: str) -> str:
    digits = normalize_card_number(value)
    if digits.startswith(("34", "37")):
        return "amex"
    if digits.startswith("4"):
        return "visa"
    if len(digits) >= 4 and 2221 <= int(digits[:4]) <= 2720:
        return "mastercard"
    if digits[:2] in {"51", "52", "53", "54", "55"}:
        return "mastercard"
    if digits.startswith(("6011", "65")):
        return "discover"
    return "unknown"


@register("payment.luhn", examples=("4242 4242 4242 4242", "4111"))
def validate_luhn(value: str) -> None:
    """Validates card numbers with the Luhn checksum after stripping separators."""
    digits = normalize_card_number(value)
    if len(digits) < 12 or not digits.isdigit():
        raise ValidationError("Enter a valid card number.", code="invalid_card")
    total = 0
    reverse_digits = list(map(int, reversed(digits)))
    for idx, digit in enumerate(reverse_digits):
        if idx % 2:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    if total % 10 != 0:
        raise ValidationError("Card number failed checksum.", code="luhn")


@register("payment.cvv", examples=("123", "1234"))
def validate_cvv_for_brand(value: str, brand: str = "unknown") -> None:
    """Requires a three-digit CVV, or four digits for American Express."""
    expected = 4 if brand == "amex" else 3
    if not value or not value.isdigit() or len(value) != expected:
        raise ValidationError(f"Enter a {expected}-digit CVV.", code="cvv")


@register("payment.not_expired", layer="form", examples=("12/2030", "01/2020"))
def validate_not_expired(month: int, year: int) -> None:
    """Rejects expiry month/year pairs that are already in the past."""
    today = date.today()
    if year < today.year or (year == today.year and month < today.month):
        raise ValidationError("Card is expired.", code="expired")
