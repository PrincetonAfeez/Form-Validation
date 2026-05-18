""" Test formset behavior. """

from __future__ import annotations

import pytest

from apps.forms_lab.services import validate_and_clean


@pytest.mark.django_db
def test_formset_add_row_rejects_at_max(client):
    response = client.post(
        "/forms/formset/add-row/",
        {"addresses-TOTAL_FORMS": "5"},
        HTTP_HX_REQUEST="true",
    )
    assert response.status_code == 204
    assert response.content == b""


@pytest.mark.django_db
def test_formset_add_row_returns_next_index(client):
    response = client.post(
        "/forms/formset/add-row/",
        {"addresses-TOTAL_FORMS": "2"},
        HTTP_HX_REQUEST="true",
    )
    assert response.status_code == 200
    assert b"formset-row-2" in response.content
    assert b"addresses-2-country" in response.content


@pytest.mark.django_db
def test_formset_valid_with_contiguous_indices_after_middle_removed(
    valid_formset_payload,
):
    """Simulates client reindex after deleting the middle row of three."""
    payload = {
        "addresses-TOTAL_FORMS": "2",
        "addresses-INITIAL_FORMS": "0",
        "addresses-MIN_NUM_FORMS": "1",
        "addresses-MAX_NUM_FORMS": "5",
        "addresses-0-country": "US",
        "addresses-0-state_province": "CA",
        "addresses-0-street": "1 Market St",
        "addresses-0-city": "San Francisco",
        "addresses-0-postal_code": "94105",
        "addresses-1-country": "US",
        "addresses-1-state_province": "CA",
        "addresses-1-street": "3 Third St",
        "addresses-1-city": "Berkeley",
        "addresses-1-postal_code": "94704",
    }
    result = validate_and_clean("formset", payload)
    assert result.is_valid, result.errors


@pytest.mark.django_db
def test_formset_page_includes_remove_controls_and_limits(client):
    response = client.get("/forms/formset/")
    html = response.content.decode()
    assert 'id="formset-add-row"' in html
    assert "data-formset-remove" in html
    assert 'id="id_addresses-MIN_NUM_FORMS"' in html
    assert 'id="id_addresses-MAX_NUM_FORMS"' in html
    assert "updateFormsetControls" in html
