""" Email rules validation. """

from __future__ import annotations

import re

from django.core.exceptions import ValidationError

from .registry import register

DISPOSABLE_DOMAINS = {
    "mailinator.com",
    "10minutemail.com",
    "guerrillamail.com",
    "tempmail.com",
    "yopmail.com",
    "throwaway.email",
    "sharklasers.com",
}

# Demo-only shape checks (no live DNS/MX lookups).
_DOMAIN_RE = re.compile(
    r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+$"
)


def _split_email(value: str) -> tuple[str, str] | None:
    if not value or "@" not in value:
        return None
    local, domain = value.rsplit("@", 1)
    if not local or not domain:
        return None
    return local, domain.lower()


@register("email.not_disposable", examples=("name@example.com", "bot@mailinator.com"))
def validate_not_disposable(value: str) -> None:
    """Rejects addresses from a bundled disposable-email blocklist (lab demo)."""
    parts = _split_email(value)
    if not parts:
        return
    _, domain = parts
    if domain in DISPOSABLE_DOMAINS:
        raise ValidationError(
            "Use a permanent email address.",
            code="disposable_email",
        )


@register("email.mx", examples=("name@example.com", "name@invalid"))
def validate_email_mx(value: str) -> None:
    """Demo domain-shape check only — not a real MX/DNS lookup.

    Rejects malformed domains and the ``.invalid`` TLD used in tests.
    """
    parts = _split_email(value)
    if not parts:
        return
    local, domain = parts
    if ".." in local or ".." in domain:
        raise ValidationError("Email address is malformed.", code="malformed_email")
    if domain.endswith(".invalid") or not _DOMAIN_RE.match(domain):
        raise ValidationError("Email domain does not look reachable.", code="mx")
