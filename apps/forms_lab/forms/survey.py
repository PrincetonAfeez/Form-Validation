from __future__ import annotations

from django import forms

from apps.forms_lab.fields import PhoneField
from apps.forms_lab.mixins import HTMXFormMixin, TailwindFormMixin
from apps.forms_lab.validators.text import validate_no_html, validate_no_profanity


class SurveyForm(HTMXFormMixin, TailwindFormMixin, forms.Form):
    validator_names = ["phone.e164", "text.no_html", "text.no_profanity"]
    demonstrates = [
        "Broad widget coverage in one form",
        "Other-option pattern",
        "Conditional passport field enforced server-side",
        "HTMX reveal/hide of dependent fields",
        "PhoneField reuse outside signup",
    ]

    satisfaction = forms.ChoiceField(
        choices=[("1", "1"), ("2", "2"), ("3", "3"), ("4", "4"), ("5", "5")],
        widget=forms.RadioSelect,
    )
    interests = forms.MultipleChoiceField(
        choices=[
            ("forms", "Forms"),
            ("validators", "Validators"),
            ("testing", "Testing"),
            ("other", "Other"),
        ],
        widget=forms.CheckboxSelectMultiple,
    )
    other_interest = forms.CharField(required=False, validators=[validate_no_html])
    availability_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    availability_time = forms.TimeField(widget=forms.TimeInput(attrs={"type": "time"}))
    favorite_color = forms.CharField(widget=forms.TextInput(attrs={"type": "color"}))
    rating = forms.IntegerField(
        min_value=0, max_value=10, widget=forms.NumberInput(attrs={"type": "range"})
    )
    phone = PhoneField(required=False)
    has_passport = forms.BooleanField(required=False)
    passport_number = forms.CharField(required=False, max_length=20)
    feedback = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
        validators=[validate_no_html, validate_no_profanity],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style_fields()
        self.add_htmx_attrs(
            "has_passport",
            "/forms/survey/toggle-passport/",
            trigger="change",
            target="#passport-field",
            swap="innerHTML",
        )

    def clean(self):
        cleaned = super().clean()
        interests = cleaned.get("interests") or []
        if "other" in interests and not cleaned.get("other_interest"):
            self.add_error(
                "other_interest",
                forms.ValidationError(
                    "Tell us the other interest.", code="required_other"
                ),
            )
        if cleaned.get("has_passport") and not cleaned.get("passport_number"):
            self.add_error(
                "passport_number",
                forms.ValidationError(
                    "Passport number is required.", code="passport_required"
                ),
            )
        return cleaned
