""" Text validation. """

import re

from django.core.exceptions import ValidationError

from .registry import register

PROFANITY = {"darnedbadword", "heckword"}
TAG_RE = re.compile(r"</?[a-zA-Z][^>]*>")


@register("text.no_profanity", examples=("Helpful comment", "heckword"))
def validate_no_profanity(value: str) -> None:
    """Rejects demo blocklisted words in free-text fields."""
    words = {word.strip(".,!?;:").lower() for word in (value or "").split()}
    if words & PROFANITY:
        raise ValidationError("Please keep the text professional.", code="profanity")


@register("text.no_html", examples=("Plain text", "<script>alert(1)</script>"))
def validate_no_html(value: str) -> None:
    """Disallows HTML tags; plain &, <, and > in text are allowed."""
    if not value:
        return
    if TAG_RE.search(value):
        raise ValidationError("HTML is not allowed here.", code="html")
