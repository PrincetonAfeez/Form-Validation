""" Test mixins, registry, and models. """

from __future__ import annotations

import pytest
from django import forms
from django.core.exceptions import ValidationError

from apps.forms_lab.context_processors import demo_navigation
from apps.forms_lab.forms import DEMO_BY_SLUG, DEMOS
from apps.forms_lab.forms.signup import SignupForm
from apps.forms_lab.middleware import SimpleHtmxDetails, SimpleHtmxMiddleware
from apps.forms_lab.models import ValidationLog
from apps.forms_lab.validators import describe, get, info, register, register_callable
from apps.forms_lab.validators.registry import ValidatorInfo, all_validators


def test_demo_catalog_covers_all_slugs():
    assert len(DEMOS) == len(DEMO_BY_SLUG)
    assert {demo.slug for demo in DEMOS} == set(DEMO_BY_SLUG.keys())


def test_describe_returns_validator_info_objects():
    described = describe(["password.strength", "payment.luhn"])
    assert len(described) == 2
    assert all(isinstance(item, ValidatorInfo) for item in described)


def test_register_decorator_and_register_callable():
    @register("test.demo_rule", examples=("ok",))
    def demo_rule(value: str) -> None:
        if value == "bad":
            raise ValidationError("Nope", code="demo")

    assert get("test.demo_rule") is demo_rule
    meta = info("test.demo_rule")
    assert meta.layer == "field"
    assert "ok" in meta.examples

    def other(value: str) -> None:
        return None

    register_callable("test.other", other, description="Other", layer="form")
    assert info("test.other").layer == "form"


def test_all_validators_includes_registered_rules():
    names = {v.name for v in all_validators()}
    assert "test.demo_rule" in names or "password.strength" in names


@pytest.mark.django_db
def test_validation_log_str():
    row = ValidationLog.objects.create(
        form_name="signup",
        field_name=None,
        error_code="honeypot",
    )
    assert str(row) == "signup.__all__: honeypot"


def test_demo_navigation_context_processor(rf):
    request = rf.get("/")
    context = demo_navigation(request)
    assert context["demo_navigation"] == DEMOS


def test_htmx_middleware_sets_request_flag(rf):
    def get_response(request):
        assert bool(request.htmx) is False
        return request

    middleware = SimpleHtmxMiddleware(get_response)
    request = rf.get("/")
    middleware(request)

    htmx_request = rf.get("/", HTTP_HX_REQUEST="true")

    def htmx_response(request):
        assert bool(request.htmx) is True
        assert isinstance(request.htmx, SimpleHtmxDetails)
        return request

    SimpleHtmxMiddleware(htmx_response)(htmx_request)


class _DemoForm(SignupForm):
    sample_hidden = forms.CharField(widget=forms.HiddenInput)
    sample_check = forms.BooleanField(required=False)
    sample_radio = forms.ChoiceField(
        choices=[("a", "A")], widget=forms.RadioSelect, required=False
    )


def test_htmx_mixin_field_states_and_helpers():
    unbound = SignupForm()
    assert unbound.field_state("username") == ("neutral", "")

    bound_ok = SignupForm({"username": "validuser"})
    bound_ok.is_valid()
    state, msg = bound_ok.field_state("username")
    assert state == "valid"
    assert msg == "Looks good."

    bound_bad = SignupForm({"username": "admin"})
    bound_bad.is_valid()
    state, msg = bound_bad.field_state("username")
    assert state == "invalid"

    form = _DemoForm()
    form.add_htmx_attrs("username", "/check/", trigger="keyup", target="#t")
    assert form.fields["username"].widget.attrs["hx-post"] == "/check/"
    form.style_fields()
    assert "rounded-md" in form.fields["username"].widget.attrs.get("class", "")
