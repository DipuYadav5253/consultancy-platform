from datetime import date

import pytest

from apps.catalogue.models import Country, University

pytestmark = pytest.mark.django_db


def make_country(name="Canada", slug="canada", iso="CA", published=True, **extra):
    return Country.objects.create(
        name=name,
        slug=slug,
        iso_code=iso,
        currency="CAD",
        is_published=published,
        last_reviewed_on=date(2026, 3, 5) if published else None,
        **extra,
    )


def test_country_list_shows_only_published(client):
    make_country()
    make_country("Hidden Land", "hidden", "HL", published=False)
    html = client.get("/study/").content.decode()
    assert "Canada" in html
    assert "Hidden Land" not in html


def test_country_detail_shows_facts_and_review_date(client):
    make_country(intakes="September", summary="A great place", visa_overview="Visa text")
    response = client.get("/study/canada/")
    html = response.content.decode()
    assert response.status_code == 200
    assert "Study in Canada" in html
    assert "5 Mar 2026" in html
    assert "Visa text" in html


def test_draft_country_is_not_reachable(client):
    make_country(published=False)
    assert client.get("/study/canada/").status_code == 404


def test_unpublished_university_is_hidden(client):
    country = make_country()
    University.objects.create(
        country=country, name="Public Uni", slug="public-uni", is_published=True
    )
    University.objects.create(country=country, name="Secret Uni", slug="secret-uni")
    html = client.get("/study/canada/").content.decode()
    assert "Public Uni" in html
    assert "Secret Uni" not in html


def test_user_text_is_escaped(client):
    make_country(summary="<script>alert(1)</script>")
    html = client.get("/study/canada/").content.decode()
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_official_source_link_is_safe(client):
    make_country(visa_overview="Visa text", source_url="https://example.org/visa")
    assert 'rel="noopener nofollow"' in client.get("/study/canada/").content.decode()


def test_home_shows_destination_cards(client):
    make_country()
    html = client.get("/").content.decode()
    assert 'href="/study/canada/"' in html
    assert "dest-name" in html


def test_footer_lists_destinations(client):
    make_country()
    footer = client.get("/book/").content.decode().split('class="site-footer"')[1]
    assert "Canada" in footer


def test_country_url(client):
    assert make_country().get_absolute_url() == "/study/canada/"


def test_mobile_menu_is_outside_the_blurred_header(client):
    html = client.get("/").content.decode()
    assert html.index("</header>") < html.index('id="mobile-menu"')
