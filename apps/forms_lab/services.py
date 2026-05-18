""" Services for the forms lab app. """

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

from django.core.exceptions import ObjectDoesNotExist
from django.db import DatabaseError

from .field_validation import clean_form_field
from .forms import DEMO_BY_SLUG, WIZARD_STEPS, PreviousAddressFormSet
from .models import ValidationLog
from .results import ValidationResult

logger = logging.getLogger(__name__)


def get_demo(slug: str):
    try:
        return DEMO_BY_SLUG[slug]
    except KeyError as exc:
        raise ObjectDoesNotExist(f"No form demo named {slug!r}.") from exc


def build_artifact(slug: str, data=None, files=None, *, step: int = 1, initial=None):
    demo = get_demo(slug)
    if demo.kind == "formset":
        return PreviousAddressFormSet(data=data, prefix="addresses")
    if demo.kind == "wizard":
        form_class = WIZARD_STEPS[step]
        return form_class(data=data, initial=initial)
    kwargs = {"data": data or None}
    if files is not None:
        kwargs["files"] = files
    if initial is not None:
        kwargs["initial"] = initial
    return demo.form_class(**kwargs)


def serialize_value(value: Any) -> Any:
    if hasattr(value, "name") and hasattr(value, "size"):
        return {"name": value.name, "size": value.size}
    if isinstance(value, list):
        return [serialize_value(item) for item in value]
    if isinstance(value, tuple):
        return [serialize_value(item) for item in value]
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def serialize_cleaned_data(cleaned_data: Mapping[str, Any]) -> dict[str, Any]:
    redacted = {"password", "confirm_password", "cvv", "passport_number"}
    return {
        key: "[redacted]" if key in redacted and value else serialize_value(value)
        for key, value in cleaned_data.items()
    }


def validate_and_clean(slug: str, payload, files=None) -> ValidationResult:
    artifact = build_artifact(slug, payload, files)
    is_valid = artifact.is_valid()
    if is_valid:
        if hasattr(artifact, "forms"):
            cleaned = {
                "rows": [
                    serialize_cleaned_data(form.cleaned_data)
                    for form in artifact.forms
                    if form.cleaned_data and not form.cleaned_data.get("DELETE")
                ]
            }
        else:
            cleaned = serialize_cleaned_data(artifact.cleaned_data)
    else:
        cleaned = {}
        log_validation_errors(slug, artifact)

    return ValidationResult(
        form_name=slug,
        is_valid=is_valid,
        cleaned_data=cleaned,
        errors=collect_errors(artifact),
        form=artifact,
        message="Validation passed." if is_valid else "Validation failed.",
    )


def validate_file_upload_field(field_name: str, payload, files=None) -> ValidationResult:
    """Validate one file-upload field for HTMX scan (not the whole form)."""
    from .forms.file_upload import FileUploadForm

    if field_name not in FileUploadForm.base_fields:
        raise ValueError(f"Unknown file field {field_name!r}.")
    form = build_artifact("file-upload", payload, files)
    form.cleaned_data = {}
    _, error_message = clean_form_field(form, field_name)
    if error_message:
        return ValidationResult(
            form_name="file-upload",
            is_valid=False,
            cleaned_data={},
            errors={field_name: [error_message]},
            form=form,
            message="Validation failed.",
        )
    value = form.cleaned_data.get(field_name)
    if isinstance(value, list):
        cleaned = {field_name: [serialize_value(item) for item in value]}
    elif value:
        cleaned = {field_name: serialize_value(value)}
    else:
        cleaned = {}
    return ValidationResult(
        form_name="file-upload",
        is_valid=True,
        cleaned_data=cleaned,
        errors={},
        form=form,
        message="Validation passed.",
    )


def validate_single_field(slug: str, field_name: str, payload, files=None):
    form = build_artifact(slug, payload, files)
    if field_name not in form.fields:
        raise ValueError(f"Field {field_name!r} is not on the {slug!r} form.")
    form.cleaned_data = {}
    _, error_message = clean_form_field(form, field_name)
    state = "invalid" if error_message else "valid"
    message = error_message or "Looks good."
    return form, form[field_name], state, message


def collect_errors(artifact) -> dict[str, list[str]]:
    if hasattr(artifact, "forms"):
        errors: dict[str, list[str]] = {}
        for index, form in enumerate(artifact.forms):
            for field, field_errors in form.errors.items():
                errors[f"row_{index}.{field}"] = [str(error) for error in field_errors]
        non_form = artifact.non_form_errors()
        if non_form:
            errors["__all__"] = [str(error) for error in non_form]
        return errors
    return {
        field: [str(error) for error in field_errors]
        for field, field_errors in artifact.errors.items()
    }


def log_validation_errors(slug: str, artifact) -> None:
    rows = []
    if hasattr(artifact, "forms"):
        for form in artifact.forms:
            rows.extend(_log_rows(slug, form.errors.as_data()))
        for error in artifact.non_form_errors().as_data():
            rows.append(
                ValidationLog(
                    form_name=slug,
                    field_name=None,
                    error_code=error.code or "invalid",
                )
            )
    else:
        rows.extend(_log_rows(slug, artifact.errors.as_data()))
    try:
        ValidationLog.objects.bulk_create(rows)
    except DatabaseError as exc:
        logger.warning("Could not persist validation log rows: %s", exc)


def _log_rows(slug: str, errors) -> list[ValidationLog]:
    rows = []
    for field_name, field_errors in errors.items():
        for error in field_errors:
            rows.append(
                ValidationLog(
                    form_name=slug,
                    field_name=None if field_name == "__all__" else field_name,
                    error_code=error.code or "invalid",
                )
            )
    return rows
