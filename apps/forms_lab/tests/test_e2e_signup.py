from __future__ import annotations

import pytest

pytest.importorskip("playwright.sync_api")

from playwright.sync_api import expect, sync_playwright

pytestmark = pytest.mark.e2e


@pytest.mark.django_db(transaction=True)
def test_signup_username_htmx_blur_validation(live_server):
    """Smoke test: username blur triggers an HTMX partial swap with validation."""
    base = live_server.url
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"{base}/forms/signup/")

        username = page.locator("#id_username")
        with page.expect_response(
            lambda r: "check-username" in r.url and r.request.method == "POST"
        ):
            username.fill("admin")
            username.blur()
        expect(page.locator("#id_username-wrap")).to_contain_text(
            "unavailable", timeout=10_000
        )

        with page.expect_response(
            lambda r: "check-username" in r.url and r.request.method == "POST"
        ):
            username.fill("e2e_avail_user")
            username.blur()
        expect(page.locator("#id_username-wrap")).to_contain_text(
            "Looks good", timeout=10_000
        )

        browser.close()
