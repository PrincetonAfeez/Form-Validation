""" Multi-step wizard demo with session-backed state, per-step validation, and back navigation. """

from __future__ import annotations

from django import forms

from apps.forms_lab.fields import PhoneField
from apps.forms_lab.mixins import HTMXFormMixin, TailwindFormMixin
from apps.forms_lab.validators.text import validate_no_html


class WizardStepOneForm(HTMXFormMixin, TailwindFormMixin, forms.Form):
    first_name = forms.CharField(max_length=60)
    last_name = forms.CharField(max_length=60)
    phone = PhoneField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style_fields()


class WizardStepTwoForm(HTMXFormMixin, TailwindFormMixin, forms.Form):
    CONTACT_CHOICES = [("email", "Email"), ("sms", "SMS"), ("phone", "Phone call")]

    preferred_contact = forms.ChoiceField(
        choices=CONTACT_CHOICES, widget=forms.RadioSelect
    )
    topics = forms.MultipleChoiceField(
        choices=[
            ("forms", "Django forms"),
            ("htmx", "HTMX"),
            ("testing", "Testing"),
        ],
        widget=forms.CheckboxSelectMultiple,
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
        validators=[validate_no_html],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style_fields()


class WizardStepThreeForm(HTMXFormMixin, TailwindFormMixin, forms.Form):
    confirm = forms.BooleanField(label="I confirm this wizard state is ready")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style_fields()


WIZARD_STEPS = {
    1: WizardStepOneForm,
    2: WizardStepTwoForm,
    3: WizardStepThreeForm,
}

WIZARD_DEMONSTRATES = [
    "Session-backed multi-step state",
    "Per-step validation before navigation",
    "Back navigates via HTMX (session-preserved answers)",
    "Final submit revalidates every step server-side",
    "HTMX swaps the step partial without a page reload",
]

WIZARD_VALIDATORS = ["phone.e164", "text.no_html"]
