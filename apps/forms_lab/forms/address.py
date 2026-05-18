""" Address form demo with country-dependent state and postal validation. """

from __future__ import annotations

from django import forms

from apps.forms_lab.mixins import HTMXFormMixin, TailwindFormMixin
from apps.forms_lab.validators.address import validate_postal_for_country

COUNTRIES = [
    ("US", "United States"),
    ("CA", "Canada"),
    ("GB", "United Kingdom"),
]

SUBDIVISIONS = {
    "US": [
        ("CA", "California"),
        ("NY", "New York"),
        ("TX", "Texas"),
        ("WA", "Washington"),
    ],
    "CA": [("ON", "Ontario"), ("QC", "Quebec"), ("BC", "British Columbia")],
    "GB": [("ENG", "England"), ("SCT", "Scotland"), ("WLS", "Wales")],
}


class AddressForm(HTMXFormMixin, TailwindFormMixin, forms.Form):
    htmx_field_dependencies = {
        "postal_code": ("country",),
        "state_province": ("country",),
    }
    validator_names = ["address.postal.country"]
    demonstrates = [
        "Dependent country/state fields",
        "Country-aware postal-code validation",
        "Normalization of postal codes before cleaned_data is returned",
        "HTMX out-of-band dependent field swaps",
    ]

    country = forms.ChoiceField(choices=COUNTRIES)
    state_province = forms.ChoiceField(label="State / province")
    postal_code = forms.CharField(max_length=16)
    street = forms.CharField(max_length=120)
    city = forms.CharField(max_length=80)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        country = self.data.get("country") or self.initial.get("country") or "US"
        self.fields["state_province"].choices = SUBDIVISIONS.get(country, [])
        self.style_fields()
        self.add_htmx_attrs(
            "country",
            "/forms/address/country-change/",
            trigger="change",
            target="#dependent-address-fields",
            swap="innerHTML",
        )
        self.add_htmx_attrs("postal_code", "/forms/address/field/postal_code/")

    def clean_postal_code(self):
        value = self.cleaned_data["postal_code"].upper().strip()
        country = self.cleaned_data.get("country", "US")
        if country == "CA" and len(value) == 6:
            value = f"{value[:3]} {value[3:]}"
        validate_postal_for_country(value, country)
        return value
