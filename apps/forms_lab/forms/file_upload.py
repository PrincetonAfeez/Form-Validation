""" File upload form demo with image dimension and magic-byte validation. """

from __future__ import annotations

import json

from django import forms

from apps.forms_lab.mixins import HTMXFormMixin, TailwindFormMixin
from apps.forms_lab.validators.files import (
    validate_file_size,
    validate_image_dimensions,
    validate_magic_bytes,
)


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def clean(self, data, initial=None):
        single_clean = super().clean
        if not data and not self.required:
            return []
        if isinstance(data, (list, tuple)):
            return [single_clean(item, initial) for item in data]
        return [single_clean(data, initial)]


class FileUploadForm(HTMXFormMixin, TailwindFormMixin, forms.Form):
    validator_names = ["file.size", "file.magic_bytes", "file.image_dimensions"]
    demonstrates = [
        "Extension allowlist plus magic-byte sniffing",
        "5 MB max per file",
        "Image dimension checks only for image uploads",
        "Multiple-file handling",
        "HTMX per-field scan on change (not whole-form validation)",
    ]

    avatar = forms.FileField(required=False)
    resume = forms.FileField(required=True)
    supporting_docs = MultipleFileField(required=False, widget=MultipleFileInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style_fields()
        for name, field in self.fields.items():
            field.widget.attrs.update(
                {
                    "hx-post": "/forms/file-upload/scan/",
                    "hx-trigger": "change",
                    "hx-target": "#file-scan-result",
                    "hx-swap": "outerHTML",
                    "hx-encoding": "multipart/form-data",
                    "hx-indicator": "#htmx-spinner",
                    "hx-vals": json.dumps({"_field": name}),
                }
            )

    def clean_avatar(self):
        file = self.cleaned_data.get("avatar")
        if file:
            validate_file_size(file)
            validate_magic_bytes(file, {"image/png", "image/jpeg"})
            validate_image_dimensions(file)
        return file

    def clean_resume(self):
        file = self.cleaned_data["resume"]
        validate_file_size(file)
        validate_magic_bytes(file, {"application/pdf"})
        return file

    def clean_supporting_docs(self):
        files = self.cleaned_data.get("supporting_docs", [])
        for file in files:
            validate_file_size(file)
            validate_magic_bytes(file, {"application/pdf", "image/png", "image/jpeg"})
            if (file.content_type or "").startswith("image/"):
                validate_image_dimensions(file)
        return files
