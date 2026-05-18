from __future__ import annotations

import pytest

from apps.forms_lab.forms import DEMO_BY_SLUG
from apps.forms_lab.tests.e2e_helpers import (
    RESUME_PDF,
    assert_validation_passed,
    fill_address,
    fill_formset_row,
    fill_payment,
    fill_signup,
    fill_survey,
    run_wizard_full_flow,
)

pytest.importorskip("playwright.sync_api")

from playwright.sync_api import sync_playwright

pytestmark = pytest.mark.e2e

SUBMIT_LABELS = {
    "signup": "Validate",
    "address": "Validate",
    "payment": "Validate",
    "file-upload": "Validate",
    "formset": "Validate formset",
    "survey": "Validate",
}


@pytest.mark.parametrize("slug", [s for s in DEMO_BY_SLUG if s != "wizard"])
@pytest.mark.django_db(transaction=True)
def test_demo_full_submit_passes_validation(live_server, slug):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"{live_server.url}/forms/{slug}/")

        if slug == "signup":
            fill_signup(page)
        elif slug == "address":
            fill_address(page)
        elif slug == "payment":
            fill_payment(page)
        elif slug == "survey":
            fill_survey(page)
        elif slug == "formset":
            fill_formset_row(page)
        elif slug == "file-upload":
            page.set_input_files("#id_resume", str(RESUME_PDF))

        page.get_by_role("button", name=SUBMIT_LABELS[slug]).click()
        page.wait_for_load_state("networkidle")
        assert_validation_passed(page)
        browser.close()


@pytest.mark.django_db(transaction=True)
def test_wizard_full_submit_completes_all_steps(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"{live_server.url}/forms/wizard/")
        run_wizard_full_flow(page)
        browser.close()
