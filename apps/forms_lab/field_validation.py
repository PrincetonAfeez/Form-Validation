from __future__ import annotations

from typing import Any

from django.core.exceptions import ValidationError
from django.forms import Form


def clean_form_field(form: Form, field_name: str) -> tuple[Any | None, str | None]:
    """
    Validate one bound field (plus any HTMX dependencies) without running clean().

    Returns (cleaned_value, error_message). error_message is None when the field passes.
    """
    if field_name not in form.fields:
        raise ValueError(f"Unknown field {field_name!r} on {form.__class__.__name__}.")

    if not getattr(form, "cleaned_data", None):
        form.cleaned_data = {}

    dependencies = getattr(form.__class__, "htmx_field_dependencies", {}).get(
        field_name, ()
    )
    for dependency in dependencies:
        if dependency in form.cleaned_data:
            continue
        _, dependency_error = _clean_one(form, dependency)
        if dependency_error:
            return None, dependency_error

    return _clean_one(form, field_name)


def _clean_one(form: Form, field_name: str) -> tuple[Any | None, str | None]:
    field = form.fields[field_name]
    prefix = form.add_prefix(field_name)
    raw = field.widget.value_from_datadict(form.data, form.files, prefix)
    try:
        value = field.clean(raw)
    except ValidationError as exc:
        return None, _first_message(exc)

    form.cleaned_data[field_name] = value
    field_cleaner = getattr(form, f"clean_{field_name}", None)
    if field_cleaner is not None:
        try:
            value = field_cleaner()
        except ValidationError as exc:
            form.cleaned_data.pop(field_name, None)
            return None, _first_message(exc)
        form.cleaned_data[field_name] = value

    return value, None


def _first_message(exc: ValidationError) -> str:
    if hasattr(exc, "message"):
        return str(exc.message)
    if exc.messages:
        return str(exc.messages[0])
    return str(exc)
