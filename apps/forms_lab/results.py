""" Validation results. """

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ValidationResult:
    form_name: str
    is_valid: bool
    cleaned_data: dict[str, Any] = field(default_factory=dict)
    errors: dict[str, list[str]] = field(default_factory=dict)
    form: Any | None = None
    message: str = ""
