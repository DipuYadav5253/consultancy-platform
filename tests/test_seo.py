from datetime import date
from decimal import Decimal

import pytest
from django.conf import settings

from apps.catalogue.models import Country, Program, University

pytestmark = pytest.mark.django_db


def make_program(published=True):
    country = Country.objects.create(
        name="Canada",
        slug="canada",
        iso_code="CA",
        currency="CAD",
        is_published=published,
        last_reviewed_on=date(2026, 3, 5) if published else None,
    )
    uni = University.objects.create(
        country=country, name="Maple University", slug="maple-university", is_published=True
    )
    return Program.objects.create(
        university=uni,
        name="Alpha Course",
        slug="alpha-course",
        level="master",
        field_of_study="Computing",
        duration_months=12,
        tuition_per_year=Decimal("10000"),
        tuition_currency="CAD",
        is_published=True,
    )


def test_sitemap_lists_published_pages(client):
    make_program()
    response = client.get("/sitemap.xml")
    xml = response.content.decode()
    assert response.status_code == 200
    assert response["Content-Type"].startswith("application/xml")
    for path in ("/study/canada/", "/programs/alpha-course/", "/programs/", "/book/"):
        assert path in xml


def test_sitemap_never_lists_drafts(client):
    make_program(published=False)
    xml = client.get("/sitemap.xml").content.decode()
    assert "/study/canada/" not in xml
    assert "/programs/alpha-course/" not in xml


def test_robots_points_to_the_sitemap(client):
    response = client.get("/robots.txt")
    body = response.content.decode()
    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/plain")
    assert "Sitemap: http://testserver/sitemap.xml" in body
    assert "User-agent: *" in body


def test_robots_does_not_reveal_the_admin_path(client):
    body = client.get("/robots.txt").content.decode()
    assert settings.ADMIN_URL.strip("/") not in body
    assert "admin" not in body.lower()


def test_robots_blocks_login_pages(client):
    assert "Disallow: /account/" in client.get("/robots.txt").content.decode()
