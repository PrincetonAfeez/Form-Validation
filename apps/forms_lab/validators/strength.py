""" Password strength validation. """

from __future__ import annotations

from pathlib import Path

from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible

from .registry import register, register_callable

COMMON_PASSWORDS = {
    "password",
    "password123",
    "letmein",
    "qwerty123",
    "welcome123",
    "passwordpassword",
    "qwerty123456",
}


def _character_classes(value: str) -> int:
    return sum(
        bool(check(value))
        for check in (
            lambda s: any(c.islower() for c in s),
            lambda s: any(c.isupper() for c in s),
            lambda s: any(c.isdigit() for c in s),
            lambda s: any(not c.isalnum() for c in s),
        )
    )


@register(
    "password.strength",
    examples=("CorrectHorse9!", "too-short"),
)
def validate_password_strength(value: str) -> None:
    """Requires 12+ characters, three character classes, and no common password."""
    if not value:
        return
    if value.lower() in COMMON_PASSWORDS:
        raise ValidationError("Choose a less common password.", code="common")
    if len(value) < 12:
        raise ValidationError("Use at least 12 characters.", code="too_short")
    if _character_classes(value) < 3:
        raise ValidationError(
            "Mix upper, lower, numbers, or symbols.",
            code="missing_character_classes",
        )


@deconstructible
class PasswordStrengthValidator:
    """Configurable password-strength validator safe to serialize in migrations."""

    def __init__(
        self,
        min_length: int = 12,
        require_classes: int = 3,
        blocklist_path: str | None = None,
    ):
        self.min_length = min_length
        self.require_classes = require_classes
        self.blocklist_path = blocklist_path

    def __call__(self, value: str) -> None:
        if not value:
            return
        if value.lower() in self._blocklist():
            raise ValidationError("Choose a less common password.", code="common")
        if len(value) < self.min_length:
            raise ValidationError(
                f"Use at least {self.min_length} characters.",
                code="too_short",
            )
        if _character_classes(value) < self.require_classes:
            raise ValidationError(
                f"Use at least {self.require_classes} character classes.",
                code="missing_character_classes",
            )

    def _blocklist(self) -> set[str]:
        if not self.blocklist_path:
            return COMMON_PASSWORDS
        path = Path(self.blocklist_path)
        if not path.exists():
            return COMMON_PASSWORDS
        return {line.strip().lower() for line in path.read_text().splitlines() if line}

    def __eq__(self, other):
        return (
            isinstance(other, PasswordStrengthValidator)
            and self.min_length == other.min_length
            and self.require_classes == other.require_classes
            and self.blocklist_path == other.blocklist_path
        )


password_strength_configurable = register_callable(
    "password.strength.configurable",
    PasswordStrengthValidator(min_length=14, require_classes=3),
    description=PasswordStrengthValidator.__doc__,
    examples=("LongerPassphrase9!",),
)
