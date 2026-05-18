""" Formset demo with previous address validation. """

from __future__ import annotations

from django import forms
from django.forms import BaseFormSet, formset_factory

from apps.forms_lab.mixins import FieldStateMixin, HTMXFormMixin, TailwindFormMixin
from apps.forms_lab.validators.address import validate_postal_for_country

from .address import COUNTRIES, SUBDIVISIONS


class PreviousAddressForm(FieldStateMixin, TailwindFormMixin, forms.Form):
    country = forms.ChoiceField(choices=COUNTRIES)
    state_province = forms.ChoiceField(label="State / province")
    street = forms.CharField(max_length=120)
    city = forms.CharField(max_length=80)
    postal_code = forms.CharField(max_length=16)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        country = self.data.get(f"{self.prefix}-country") or "US"
        self.fields["state_province"].choices = SUBDIVISIONS.get(country, [])
        self.style_fields()

    def clean_postal_code(self):
        value = self.cleaned_data["postal_code"].upper().strip()
        country = self.cleaned_data.get("country", "US")
        if country == "CA" and len(value) == 6:
            value = f"{value[:3]} {value[3:]}"
        validate_postal_for_country(value, country)
        return value


class BasePreviousAddressFormSet(BaseFormSet):
    def clean(self):
        super().clean()
        seen = set()

        for form in self.forms:
            if form.errors:
                continue
            if not hasattr(form, "cleaned_data") or form.cleaned_data.get("DELETE"):
                continue

            street = (form.cleaned_data.get("street") or "").casefold()
            city = (form.cleaned_data.get("city") or "").casefold()
            postal = (form.cleaned_data.get("postal_code") or "").casefold()

            if not street or not city or not postal:
                continue

            key = (street, city, postal)
            if key in seen:
                raise forms.ValidationError(
                    "Duplicate previous addresses are not allowed.",
                    code="duplicate_address",
                )
            seen.add(key)


PreviousAddressFormSet = formset_factory(
    PreviousAddressForm,
    formset=BasePreviousAddressFormSet,
    extra=1,
    can_delete=True,
    min_num=1,
    max_num=5,
    validate_min=True,
    validate_max=True,
)


class FormsetShowcase(HTMXFormMixin):
    validator_names = ["address.postal.country"]
    demonstrates = [
        "Django formsets with management-form state",
        "Per-row field validation",
        "Formset-level duplicate-address validation",
        "HTMX add-row; client-side remove with prefix reindex",
    ]
