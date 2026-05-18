from __future__ import annotations

from datetime import datetime, timezone

from django import forms
from django.core.validators import RegexValidator

from apps.forms_lab.fields import PhoneField
from apps.forms_lab.mixins import HTMXFormMixin, TailwindFormMixin
from apps.forms_lab.validators import get
from apps.forms_lab.validators.antispam import validate_honeypot, validate_time_trap

RESERVED_USERNAMES = {"admin", "root", "support", "test", "codex"}


class SignupForm(HTMXFormMixin, TailwindFormMixin, forms.Form):
    validator_names = [
        "password.strength",
        "email.not_disposable",
        "email.mx",
        "phone.e164",
        "antispam.honeypot",
        "antispam.time_trap",
    ]
    demonstrates = [
        "Custom PhoneField normalization to E.164",
        "Function validators referenced through the registry",
        "clean_<field>() plus clean() cross-field validation",
        "HTMX blur checks via dedicated username/email endpoints "
        "(reserved-name blocklist demo)",
        "Alpine-powered client-only password strength meter",
    ]

    username = forms.CharField(
        min_length=3,
        max_length=30,
        validators=[
            RegexValidator(
                r"^[a-zA-Z0-9_]+$",
                "Use letters, numbers, and underscores only.",
                code="username_chars",
            )
        ],
    )
    email = forms.EmailField(validators=[get("email.not_disposable"), get("email.mx")])
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        validators=[get("password.strength")],
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"})
    )
    phone = PhoneField()
    accept_terms = forms.BooleanField(label="I accept the validation lab terms")
    website = forms.CharField(required=False, widget=forms.HiddenInput)
    started_at = forms.CharField(required=False, widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            self.initial["started_at"] = datetime.now(timezone.utc).isoformat()
        self.style_fields()
        self.add_htmx_attrs(
            "username",
            "/forms/signup/check-username/",
            indicator="#htmx-spinner",
        )
        self.add_htmx_attrs(
            "email",
            "/forms/signup/check-email/",
            indicator="#htmx-spinner",
        )
        self.fields["password"].widget.attrs.update(
            {
                "x-model": "password",
                "x-on:keyup.debounce.200ms": "scorePassword()",
            }
        )

    def clean_username(self):
        username = self.cleaned_data["username"]
        if username.lower() in RESERVED_USERNAMES:
            raise forms.ValidationError(
                "That username is unavailable.", code="unavailable"
            )
        return username

    def clean(self):
        cleaned = super().clean()
        validate_honeypot(self.data)
        validate_time_trap(self.data)
        password = cleaned.get("password")
        confirm = cleaned.get("confirm_password")
        if password and confirm and password != confirm:
            self.add_error(
                "confirm_password",
                forms.ValidationError(
                    "Passwords must match.", code="password_mismatch"
                ),
            )
        return cleaned
