""" E2E test helpers for the form validation showcase. """

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from playwright.sync_api import Page, expect

E2E_FIXTURES = Path(__file__).resolve().parent / "fixtures" / "e2e"
RESUME_PDF = E2E_FIXTURES / "resume.pdf"


def assert_validation_passed(page: Page) -> None:
    """Result panel or Django message after a successful full submit."""
    expect(page.get_by_text("Validation passed", exact=False).first).to_be_visible(
        timeout=10_000
    )


def _set_time_trap(page: Page) -> None:
    started = (datetime.now(timezone.utc) - timedelta(seconds=10)).isoformat()
    page.locator("#id_started_at").evaluate(
        "(el, value) => { el.value = value; }",
        started,
    )


def fill_signup(page: Page) -> None:
    suffix = uuid.uuid4().hex[:8]
    page.fill("#id_username", f"e2e_{suffix}")
    page.fill("#id_email", f"e2e_{suffix}@example.com")
    page.fill("#id_password", "CorrectHorse9!")
    page.fill("#id_confirm_password", "CorrectHorse9!")
    page.fill("#id_phone", "4155552671")
    page.locator("#id_accept_terms").check()
    _set_time_trap(page)


def fill_address(page: Page) -> None:
    page.select_option("#id_country", "US")
    page.select_option("#id_state_province", "CA")
    page.fill("#id_postal_code", "94105")
    page.fill("#id_street", "1 Market St")
    page.fill("#id_city", "San Francisco")


def fill_payment(page: Page) -> None:
    from datetime import date

    page.fill("#id_card_number", "4242 4242 4242 4242")
    page.select_option("#id_expiry_month", "12")
    page.select_option("#id_expiry_year", str(date.today().year + 1))
    page.fill("#id_cvv", "123")
    page.fill("#id_name_on_card", "E2E Tester")


def fill_survey(page: Page) -> None:
    page.locator('input[name="satisfaction"][value="5"]').check()
    page.locator('input[name="interests"][value="forms"]').check()
    page.fill("#id_availability_date", "2026-06-01")
    page.fill("#id_availability_time", "12:00")
    page.fill("#id_favorite_color", "#00aa99")
    page.fill("#id_rating", "8")


def fill_formset_row_at(
    page: Page,
    index: int,
    *,
    street: str,
    city: str,
    postal_code: str,
    country: str = "US",
    state: str = "CA",
) -> None:
    page.select_option(f"#id_addresses-{index}-country", country)
    page.select_option(f"#id_addresses-{index}-state_province", state)
    page.fill(f"#id_addresses-{index}-street", street)
    page.fill(f"#id_addresses-{index}-city", city)
    page.fill(f"#id_addresses-{index}-postal_code", postal_code)


def fill_formset_row(page: Page) -> None:
    fill_formset_row_at(
        page,
        0,
        street="1 Market St",
        city="San Francisco",
        postal_code="94105",
    )
    extra_row = page.locator("#formset-row-1")
    if extra_row.count():
        extra_row.get_by_role("button", name="Remove").click()
        page.wait_for_timeout(300)


def remove_formset_row(page: Page, row_index: int) -> None:
    row = page.locator(f"#formset-row-{row_index}")
    row.get_by_role("button", name="Remove").click()
    page.wait_for_timeout(300)


def run_wizard_full_flow(page: Page) -> None:
    page.fill("#id_first_name", "Prince")
    page.fill("#id_last_name", "Afeez")
    page.fill("#id_phone", "4155552671")
    page.get_by_role("button", name="Next").click()
    expect(page.locator("#wizard-shell")).to_contain_text("Step 2 of 3", timeout=10_000)
    page.locator('input[name="preferred_contact"][value="email"]').check()
    page.locator('input[name="topics"][value="forms"]').check()
    page.get_by_role("button", name="Next").click()
    expect(page.locator("#wizard-shell")).to_contain_text("Step 3 of 3", timeout=10_000)
    page.locator("#id_confirm").check()
    page.get_by_role("button", name="Finish").click()
    expect(page.locator("#wizard-shell")).to_contain_text(
        "Wizard completed", timeout=10_000
    )
