from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .address import AddressForm
from .file_upload import FileUploadForm
from .formset import FormsetShowcase, PreviousAddressFormSet
from .payment import PaymentForm
from .signup import SignupForm
from .survey import SurveyForm
from .wizard import WIZARD_DEMONSTRATES, WIZARD_STEPS, WIZARD_VALIDATORS


@dataclass(frozen=True)
class DemoDefinition:
    slug: str
    title: str
    kind: str
    form_class: Any | None
    demonstrates: tuple[str, ...]
    validator_names: tuple[str, ...]


DEMOS = [
    DemoDefinition(
        "signup",
        "Signup Form",
        "form",
        SignupForm,
        tuple(SignupForm.demonstrates),
        tuple(SignupForm.validator_names),
    ),
    DemoDefinition(
        "address",
        "Address Form",
        "form",
        AddressForm,
        tuple(AddressForm.demonstrates),
        tuple(AddressForm.validator_names),
    ),
    DemoDefinition(
        "payment",
        "Payment Form",
        "form",
        PaymentForm,
        tuple(PaymentForm.demonstrates),
        tuple(PaymentForm.validator_names),
    ),
    DemoDefinition(
        "wizard",
        "Multi-step Wizard",
        "wizard",
        None,
        tuple(WIZARD_DEMONSTRATES),
        tuple(WIZARD_VALIDATORS),
    ),
    DemoDefinition(
        "file-upload",
        "File Upload Form",
        "form",
        FileUploadForm,
        tuple(FileUploadForm.demonstrates),
        tuple(FileUploadForm.validator_names),
    ),
    DemoDefinition(
        "formset",
        "Dynamic Formset",
        "formset",
        PreviousAddressFormSet,
        tuple(FormsetShowcase.demonstrates),
        tuple(FormsetShowcase.validator_names),
    ),
    DemoDefinition(
        "survey",
        "Survey Form",
        "form",
        SurveyForm,
        tuple(SurveyForm.demonstrates),
        tuple(SurveyForm.validator_names),
    ),
]

DEMO_BY_SLUG = {demo.slug: demo for demo in DEMOS}

__all__ = [
    "AddressForm",
    "DEMOS",
    "DEMO_BY_SLUG",
    "DemoDefinition",
    "FileUploadForm",
    "PaymentForm",
    "PreviousAddressFormSet",
    "SignupForm",
    "SurveyForm",
    "WIZARD_STEPS",
]
