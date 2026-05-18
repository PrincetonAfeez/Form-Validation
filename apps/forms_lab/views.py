""" Views for the forms lab app. """

from __future__ import annotations

import json

from django.contrib import messages
from django.db.models import Count
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .forms import DEMOS, WIZARD_STEPS
from .forms.address import AddressForm
from .forms.file_upload import FileUploadForm
from .forms.formset import PreviousAddressForm, PreviousAddressFormSet
from .forms.survey import SurveyForm
from .models import ValidationLog
from .services import (
    build_artifact,
    get_demo,
    serialize_cleaned_data,
    validate_and_clean,
    validate_file_upload_field,
    validate_single_field,
)
from .templatetags.form_extras import bound_field_context
from .validators import all_validators, describe
from .validators.payment import detect_card_brand


def index(request):
    return render(request, "forms_lab/index.html", {"demos": DEMOS})


def form_detail(request, slug: str):
    demo = _demo_or_404(slug)
    result = None
    current_step = (
        _resolve_wizard_step(request.GET.get("step"))
        if demo.kind == "wizard"
        else None
    )

    if request.method == "POST":
        if demo.kind == "wizard":
            return wizard_step(request, _resolve_wizard_step(request.POST.get("step")))
        result = validate_and_clean(slug, request.POST, request.FILES)
        artifact = result.form
        if result.is_valid:
            messages.success(request, "Validation passed.")
    else:
        if demo.kind == "wizard":
            artifact = _wizard_form_from_session(request, current_step)
        else:
            artifact = build_artifact(slug)

    return render(
        request,
        "forms_lab/form_detail.html",
        {
            "demo": demo,
            "artifact": artifact,
            "form": artifact if demo.kind == "form" else None,
            "formset": artifact if demo.kind == "formset" else None,
            "result": result,
            "rules": describe(demo.validator_names),
            "current_step": current_step,
        },
    )


@require_POST
def field_validate(request, slug: str, name: str):
    _demo_or_404(slug)
    try:
        form, field, state, message = validate_single_field(
            slug,
            name,
            request.POST,
            request.FILES,
        )
    except ValueError as exc:
        raise Http404("Field not found") from exc
    response = render(
        request,
        "forms/_field.html",
        bound_field_context(form, field, state=state, message=message),
    )
    response["HX-Trigger"] = json.dumps(
        {
            "fieldValidated": {
                "field": name,
                "state": state,
                "message": message,
            }
        }
    )
    return response


@require_POST
def signup_check_username(request):
    return field_validate(request, "signup", "username")


@require_POST
def signup_check_email(request):
    return field_validate(request, "signup", "email")


@require_POST
def address_country_change(request):
    # Unbound (initial=) so dependent fields render neutral, not premature "required".
    form = AddressForm(initial=request.POST.dict())
    return render(
        request,
        "forms_lab/partials/_country_dependent_fields.html",
        {"form": form},
    )


@require_POST
def payment_brand_detect(request):
    brand = detect_card_brand(request.POST.get("card_number", ""))
    response = render(
        request,
        "forms_lab/partials/_payment_brand.html",
        {"brand": brand, "cvv_length": 4 if brand == "amex" else 3},
    )
    cvv_length = 4 if brand == "amex" else 3
    response["HX-Trigger"] = json.dumps(
        {"cardBrandDetected": {"cvvLength": cvv_length, "brand": brand}}
    )
    return response


@require_POST
def wizard_step(request, n: int):
    if n not in WIZARD_STEPS:
        raise Http404("Wizard step not found")
    form = WIZARD_STEPS[n](request.POST)
    step_data = request.session.setdefault("wizard_state", {})
    result = None
    if form.is_valid():
        step_data[str(n)] = serialize_cleaned_data(form.cleaned_data)
        request.session.modified = True
        if n < 3:
            current_step = n + 1
            next_form = _wizard_form_from_session(request, current_step)
        else:
            current_step = 3
            combined = {}
            for step, form_class in WIZARD_STEPS.items():
                payload = step_data.get(str(step), {})
                check_form = form_class(payload)
                if not check_form.is_valid():
                    next_form = check_form
                    result = None
                    current_step = step
                    break
                combined[f"step_{step}"] = serialize_cleaned_data(
                    check_form.cleaned_data
                )
            else:
                next_form = form
                result = {
                    "is_valid": True,
                    "cleaned_data": combined,
                    "message": "Wizard completed and revalidated.",
                }
    else:
        current_step = n
        next_form = form

    context = {
        "demo": _demo_or_404("wizard"),
        "form": next_form,
        "current_step": current_step,
        "result": result,
        "rules": describe(_demo_or_404("wizard").validator_names),
    }
    template = (
        "forms_lab/partials/_wizard_step.html"
        if request.htmx
        else "forms_lab/form_detail.html"
    )
    context["artifact"] = next_form
    return render(request, template, context)


@require_POST
def file_upload_scan(request):
    field_name = request.POST.get("_field")
    if not field_name or field_name not in FileUploadForm.base_fields:
        raise Http404("Unknown file field")
    try:
        result = validate_file_upload_field(
            field_name, request.POST, request.FILES
        )
    except ValueError as exc:
        raise Http404("Unknown file field") from exc
    return render(request, "forms_lab/partials/_file_progress.html", {"result": result})


@require_POST
def formset_add_row(request):
    try:
        index = int(request.POST.get("addresses-TOTAL_FORMS", "0"))
    except ValueError:
        index = 0
    if index >= PreviousAddressFormSet.max_num:
        return HttpResponse(status=204)
    form = PreviousAddressForm(prefix=f"addresses-{index}")
    return render(
        request,
        "forms_lab/partials/_formset_row.html",
        {"form": form, "index": index},
    )


@require_POST
def survey_toggle_passport(request):
    form = SurveyForm(request.POST)
    return render(
        request,
        "forms_lab/partials/_passport_field.html",
        {"form": form, "show": request.POST.get("has_passport") in {"on", "true", "1"}},
    )


def stats(request):
    failures = (
        ValidationLog.objects.values("form_name", "field_name", "error_code")
        .annotate(total=Count("id"))
        .order_by("-total", "form_name")[:20]
    )
    return render(request, "forms_lab/stats.html", {"failures": failures})


def reference(request):
    return render(
        request,
        "forms_lab/reference.html",
        {"validators": all_validators()},
    )


def _wizard_form_from_session(request, step: int):
    if step not in WIZARD_STEPS:
        raise Http404("Wizard step not found")
    state = request.session.get("wizard_state", {})
    return WIZARD_STEPS[step](initial=state.get(str(step), {}))


def _resolve_wizard_step(raw: str | None, *, default: int = 1) -> int:
    """Parse a wizard step from GET/POST; 404 on missing/non-numeric/out-of-range."""
    if raw is None or raw == "":
        return default
    try:
        step = int(raw)
    except (TypeError, ValueError):
        raise Http404("Wizard step not found") from None
    if step not in WIZARD_STEPS:
        raise Http404("Wizard step not found")
    return step


def _demo_or_404(slug: str):
    try:
        return get_demo(slug)
    except Exception as exc:
        raise Http404("Demo not found") from exc
