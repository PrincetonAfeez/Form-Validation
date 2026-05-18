""" Test view error handling. """

from __future__ import annotations

import pytest


@pytest.mark.parametrize(
    "query",
    ["abc", "0", "99", "-1"],
)
@pytest.mark.django_db
def test_wizard_get_invalid_step_query_returns_404(client, query):
    assert client.get(f"/forms/wizard/?step={query}").status_code == 404


@pytest.mark.django_db
def test_wizard_get_valid_step_query_returns_200(client):
    assert client.get("/forms/wizard/?step=2").status_code == 200


@pytest.mark.django_db
def test_wizard_post_invalid_step_in_form_detail_returns_404(client):
    response = client.post(
        "/forms/wizard/",
        {"step": "not-a-number", "first_name": "A"},
    )
    assert response.status_code == 404


@pytest.mark.django_db
def test_wizard_post_out_of_range_step_in_form_detail_returns_404(client):
    assert client.post("/forms/wizard/", {"step": "0"}).status_code == 404


@pytest.mark.django_db
def test_field_validate_unknown_field_returns_404(client):
    response = client.post(
        "/forms/signup/field/bogus/",
        {"bogus": "x"},
        HTTP_HX_REQUEST="true",
    )
    assert response.status_code == 404
