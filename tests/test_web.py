from datetime import date

import pytest
from django.test import RequestFactory

from apps.catalogue.models import Country
from apps.core.views import error_500

pytestmark = pytest.mark.django_db


def test_home_page_shows_hero_and_search_form(client):
    response = client.get("/")
    assert response.status_code == 200
    html = response.content.decode()
    assert "Study abroad, planned" in html
    assert 'name="country"' in html and 'name="level"' in html


def test_brand_name_comes_from_settings(client, settings):
    settings.SITE_NAME = "Acme Education"
    assert "Acme Education" in client.get("/").content.decode()


def test_home_page_has_one_main_heading(client):
    assert client.get("/").content.decode().count("<h1") == 1


def test_book_page_lists_contact_email(client, settings):
    settings.CONTACT_EMAIL = "team@example.org"
    response = client.get("/book/")
    assert response.status_code == 200
    assert "mailto:team@example.org" in response.content.decode()


def test_error_500_page_works_without_database_or_request_context():
    response = error_500(RequestFactory().get("/"))
    assert response.status_code == 500
    assert b"Something went wrong" in response.content


def make_countries(names, published=True):
    for i, name in enumerate(names):
        Country.objects.create(
            name=name,
            slug=name.lower(),
            iso_code=f"{chr(65 + i)}{chr(65 + i)}",
            currency="GBP",
            is_published=published,
            last_reviewed_on=date.today(),
        )


def test_home_page_has_all_sections(client):
    html = client.get("/").content.decode()
    for marker in ('id="process"', 'id="coaching"', 'id="ielts-range"', "Ready to plan your move?"):
        assert marker in html


def test_marquee_uses_default_destinations_when_catalogue_is_small(client):
    assert "United Kingdom" in client.get("/").content.decode()


def test_marquee_uses_published_countries(client):
    make_countries(["Alpha", "Bravo", "Charlie", "Delta"])
    html = client.get("/").content.decode()
    assert "Delta" in html
    assert "United Kingdom" not in html


def test_unpublished_country_never_appears_on_home_page(client):
    make_countries(["Alpha", "Bravo", "Charlie", "Delta"])
    Country.objects.create(name="Hidden", slug="hidden", iso_code="ZZ", currency="GBP")
    assert "Hidden" not in client.get("/").content.decode()
