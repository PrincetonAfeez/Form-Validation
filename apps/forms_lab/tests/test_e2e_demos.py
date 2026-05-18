from __future__ import annotations

import pytest

from apps.forms_lab.forms import DEMO_BY_SLUG

pytest.importorskip("playwright.sync_api")

from playwright.sync_api import expect, sync_playwright

pytestmark = pytest.mark.e2e

DEMO_SLUGS = list(DEMO_BY_SLUG.keys())


@pytest.mark.parametrize("slug", DEMO_SLUGS)
@pytest.mark.django_db(transaction=True)
def test_demo_page_loads(live_server, slug):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"{live_server.url}/forms/{slug}/")
        expect(page.locator("h1")).to_be_visible()
        browser.close()


@pytest.mark.django_db(transaction=True)
def test_address_country_change_twice_in_browser(live_server):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"{live_server.url}/forms/address/")
        page.locator("#id_country").select_option("CA")
        expect(page.locator("#dependent-address-fields")).to_contain_text("Ontario")
        page.locator("#id_country").select_option("GB")
        expect(page.locator("#dependent-address-fields")).to_contain_text("England")
        browser.close()
