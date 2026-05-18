from __future__ import annotations

from datetime import datetime, timezone

from django.core.exceptions import ValidationError

from .registry import register


@register("antispam.honeypot", layer="form", examples=("empty website field",))
def validate_honeypot(payload) -> None:
    """Rejects submissions when the hidden website honeypot field is filled."""
    if payload.get("website"):
        raise ValidationError("Spam check failed.", code="honeypot")


@register("antispam.time_trap", layer="form", examples=("submitted after 3 seconds",))
def validate_time_trap(payload, min_seconds: int = 3) -> None:
    """Rejects submissions that arrive too quickly to be human-entered."""
    started_at = payload.get("started_at")
    if not started_at:
        raise ValidationError(
            "Invalid submission timing.",
            code="missing_trap",
        )
    try:
        started = datetime.fromisoformat(started_at)
    except ValueError:
        return
    if started.tzinfo is None:
        started = started.replace(tzinfo=timezone.utc)
    if (datetime.now(timezone.utc) - started).total_seconds() < min_seconds:
        raise ValidationError(
            "Please take a moment before submitting.", code="too_fast"
        )
