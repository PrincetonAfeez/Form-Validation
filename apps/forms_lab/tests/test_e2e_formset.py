from __future__ import annotations

import pytest

from apps.forms_lab.tests.e2e_helpers import (
    assert_validation_passed,
    fill_formset_row_at,
    remove_formset_row,
)

pytest.importorskip("playwright.sync_api")

from playwright.sync_api import expect, sync_playwright

pytestmark = pytest.mark.e2e


@pytest.mark.django_db(transaction=True)
def test_formset_middle_row_removal_then_submit(live_server):
    """Removing a middle row reindexes prefixes; submit must still validate."""
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"{live_server.url}/forms/formset/")

        fill_formset_row_at(
            page, 0, street="1 Market St", city="San Francisco", postal_code="94105"
        )
        fill_formset_row_at(
            page, 1, street="2 Second St", city="Oakland", postal_code="94607"
        )

        page.get_by_role("button", name="Add row").click()
        page.wait_for_timeout(300)
        expect(page.locator("#formset-row-2")).to_be_visible(timeout=5_000)

        fill_formset_row_at(
            page, 2, street="3 Third St", city="Berkeley", postal_code="94704"
        )

        remove_formset_row(page, 1)
        expect(page.locator("#id_addresses-1-street")).to_have_value(
            "3 Third St", timeout=5_000
        )
        expect(page.locator("#formset-rows .formset-row")).to_have_count(2)

        page.get_by_role("button", name="Validate formset").click()
        page.wait_for_load_state("networkidle")
        assert_validation_passed(page)
        browser.close()
