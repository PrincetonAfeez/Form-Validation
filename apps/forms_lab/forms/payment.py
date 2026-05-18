from __future__ import annotations

from datetime import date

from django import forms

from apps.forms_lab.mixins import HTMXFormMixin, TailwindFormMixin
from apps.forms_lab.validators.payment import (
    detect_card_brand,
    normalize_card_number,
    validate_cvv_for_brand,
    validate_luhn,
    validate_not_expired,
)


class PaymentForm(HTMXFormMixin, TailwindFormMixin, forms.Form):
    validator_names = ["payment.luhn", "payment.cvv", "payment.not_expired"]
    demonstrates = [
        "Input normalization before validation",
        "Luhn checksum validation",
        "Derived card brand with brand-specific CVV rules",
        "Cross-field expiry validation",
        "HTMX brand detection while typing",
    ]

    MONTHS = [(i, f"{i:02d}") for i in range(1, 13)]
    YEARS = [
        (year, str(year)) for year in range(date.today().year, date.today().year + 12)
    ]

    card_number = forms.CharField(max_length=24)
    expiry_month = forms.ChoiceField(choices=MONTHS)
    expiry_year = forms.ChoiceField(choices=YEARS)
    cvv = forms.CharField(max_length=4)
    name_on_card = forms.CharField(max_length=80)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.detected_brand = "unknown"
        self._raw_card_digits = ""
        self.style_fields()
        self.add_htmx_attrs(
            "card_number",
            "/forms/payment/brand-detect/",
            trigger="keyup changed delay:300ms",
            target="#payment-brand-panel",
        )

    def clean_card_number(self):
        value = self.cleaned_data["card_number"]
        validate_luhn(value)
        self._raw_card_digits = normalize_card_number(value)
        self.detected_brand = detect_card_brand(value)
        last4 = self._raw_card_digits[-4:]
        return f"************{last4}"

    def clean(self):
        cleaned = super().clean()
        month = cleaned.get("expiry_month")
        year = cleaned.get("expiry_year")
        cvv = cleaned.get("cvv")
        if month and year:
            try:
                validate_not_expired(int(month), int(year))
            except forms.ValidationError as exc:
                self.add_error("expiry_month", exc)
        if cvv:
            try:
                validate_cvv_for_brand(cvv, self.detected_brand)
            except forms.ValidationError as exc:
                self.add_error("cvv", exc)
        cleaned["card_brand"] = self.detected_brand
        return cleaned
