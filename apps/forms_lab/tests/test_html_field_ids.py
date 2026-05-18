from __future__ import annotations

from html.parser import HTMLParser

import pytest

from apps.forms_lab.forms import DEMO_BY_SLUG

DEMO_URLS = [f"/forms/{slug}/" for slug in DEMO_BY_SLUG]
WIZARD_URLS = [f"/forms/wizard/?step={n}" for n in (1, 2, 3)]
FIELD_ID_SUFFIXES = ("-wrap", "-message")


class _IdCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for name, value in attrs:
            if name == "id" and value:
                self.ids.append(value)


def _field_ids(html: bytes) -> list[str]:
    parser = _IdCollector()
    parser.feed(html.decode())
    return [id_ for id_ in parser.ids if id_.endswith(FIELD_ID_SUFFIXES)]


@pytest.mark.django_db
@pytest.mark.parametrize("url", DEMO_URLS + WIZARD_URLS)
def test_field_wrapper_and_message_ids_are_unique(client, url):
    response = client.get(url)
    assert response.status_code == 200
    field_ids = _field_ids(response.content)
    duplicates = sorted({id_ for id_ in field_ids if field_ids.count(id_) > 1})
    assert field_ids, f"expected field partial ids on {url}"
    assert not duplicates, f"duplicate field ids on {url}: {duplicates}"


@pytest.mark.django_db
def test_survey_radio_field_uses_fieldset(client):
    response = client.get("/forms/survey/")
    html = response.content.decode()
    assert "<fieldset" in html
    assert "<legend" in html
    assert html.count('id="id_satisfaction-wrap"') == 1
    assert html.count('id="id_interests-wrap"') == 1
