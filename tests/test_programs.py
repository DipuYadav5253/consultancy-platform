from datetime import date
from decimal import Decimal

import pytest

from apps.catalogue.models import Country, Program, University
from apps.web.templatetags.web_extras import money, tone

pytestmark = pytest.mark.django_db


def make_country(name="Canada", slug="canada", iso="CA", currency="CAD", published=True):
    return Country.objects.create(
        name=name,
        slug=slug,
        iso_code=iso,
        currency=currency,
        is_published=published,
        last_reviewed_on=date(2026, 3, 5) if published else None,
    )


def make_uni(country, name="Maple University", published=True):
    return University.objects.create(
        country=country, name=name, slug=name.lower().replace(" ", "-"), is_published=published
    )


def make_program(uni, name, **extra):
    fields = {
        "slug": name.lower().replace(" ", "-"),
        "level": "master",
        "field_of_study": "Computing",
        "duration_months": 12,
        "tuition_per_year": Decimal("10000"),
        "tuition_currency": uni.country.currency,
        "ielts_min": Decimal("6.5"),
        "pte_min": 60,
        "is_published": True,
        **extra,
    }
    return Program.objects.create(university=uni, name=name, **fields)


def page(client, url):
    return client.get(url).content.decode()


def test_search_lists_only_visible_programs(client):
    uni = make_uni(make_country())
    make_program(uni, "Alpha Course")
    make_program(uni, "Draft Course", is_published=False)
    html = page(client, "/programs/")
    assert "Alpha Course" in html
    assert "Draft Course" not in html
    assert "<strong>1</strong> program found" in html


def test_programs_hidden_when_university_or_country_is_unpublished(client):
    hidden_uni = make_uni(make_country(), "Hidden University", published=False)
    make_program(hidden_uni, "Alpha Course")
    hidden_country = make_country("Hidden Land", "hidden", "HL", published=False)
    make_program(make_uni(hidden_country, "Other University"), "Bravo Course")
    html = page(client, "/programs/")
    assert "Alpha Course" not in html and "Bravo Course" not in html


def test_filter_by_country_level_and_text(client):
    canada = make_uni(make_country())
    uk = make_uni(make_country("United Kingdom", "uk", "GB", "GBP"), "Thames University")
    make_program(canada, "Alpha Course", level="bachelor", field_of_study="Nursing")
    make_program(uk, "Bravo Course", level="master", field_of_study="Data Science")
    assert "Bravo Course" not in page(client, "/programs/?country=canada")
    assert "Alpha Course" not in page(client, "/programs/?level=master")
    html = page(client, "/programs/?q=data")
    assert "Bravo Course" in html and "Alpha Course" not in html


def test_ielts_filter_only_shows_confirmed_matches(client):
    uni = make_uni(make_country())
    make_program(uni, "Alpha Course", ielts_min=Decimal("6.0"))
    make_program(uni, "Bravo Course", ielts_min=Decimal("7.5"))
    make_program(uni, "Charlie Course", ielts_min=None)
    html = page(client, "/programs/?ielts=6.5")
    assert "Alpha Course" in html
    assert "Bravo Course" not in html and "Charlie Course" not in html


def test_pte_filter(client):
    uni = make_uni(make_country())
    make_program(uni, "Alpha Course", pte_min=50)
    make_program(uni, "Bravo Course", pte_min=70)
    html = page(client, "/programs/?pte=55")
    assert "Alpha Course" in html and "Bravo Course" not in html


def test_giving_both_scores_matches_either(client):
    uni = make_uni(make_country())
    make_program(uni, "Alpha Course", ielts_min=Decimal("7.5"), pte_min=50)
    assert "Alpha Course" in page(client, "/programs/?ielts=6.5&pte=55")


def test_budget_needs_a_country(client):
    make_program(make_uni(make_country()), "Alpha Course")
    response = client.get("/programs/?max_tuition=20000")
    assert response.status_code == 200
    assert "Choose a country" in response.content.decode()


def test_budget_uses_the_countrys_currency(client):
    canada = make_uni(make_country())
    uk = make_uni(make_country("United Kingdom", "uk", "GB", "GBP"), "Thames University")
    make_program(canada, "Alpha Course", tuition_per_year=Decimal("15000"))
    make_program(canada, "Bravo Course", tuition_per_year=Decimal("30000"))
    make_program(uk, "Charlie Course", tuition_per_year=Decimal("5000"))
    html = page(client, "/programs/?country=canada&max_tuition=20000")
    assert "Alpha Course" in html
    assert "Bravo Course" not in html and "Charlie Course" not in html


def test_bad_input_never_crashes_the_page(client):
    make_program(make_uni(make_country()), "Alpha Course")
    for query in [
        "ielts=abc",
        "ielts=99",
        "pte=5",
        "level=nope",
        "country=nope",
        "sort=drop",
        "page=999",
        "page=abc",
        "max_tuition=-5",
    ]:
        assert client.get(f"/programs/?{query}").status_code == 200, query


def test_sort_by_lowest_tuition(client):
    uni = make_uni(make_country())
    make_program(uni, "Alpha Course", tuition_per_year=Decimal("20000"))
    make_program(uni, "Bravo Course", tuition_per_year=Decimal("10000"))
    html = page(client, "/programs/?sort=tuition")
    assert html.index("Bravo Course") < html.index("Alpha Course")


def test_results_are_paginated(client):
    uni = make_uni(make_country())
    for i in range(13):
        make_program(uni, f"Course {i:02d}")
    html = page(client, "/programs/")
    assert "Page 1 of 2" in html and "page=2" in html
    assert "<strong>13</strong> programs found" in html
    assert "Course 12" in page(client, "/programs/?page=2")


def test_program_detail_page(client):
    program = make_program(make_uni(make_country()), "Alpha Course", description="Nice course")
    response = client.get(program.get_absolute_url())
    html = response.content.decode()
    assert response.status_code == 200
    assert "Alpha Course" in html and "Nice course" in html and "C$10,000" in html


def test_draft_program_detail_is_not_reachable(client):
    program = make_program(make_uni(make_country()), "Alpha Course", is_published=False)
    assert client.get(program.get_absolute_url()).status_code == 404


def test_program_detail_hidden_when_university_is_unpublished(client):
    uni = make_uni(make_country(), published=False)
    program = make_program(uni, "Alpha Course")
    assert client.get(program.get_absolute_url()).status_code == 404


def test_search_text_is_escaped(client):
    html = page(client, "/programs/?q=<script>alert(1)</script>")
    assert "alert(1)" not in html.replace("&lt;script&gt;alert(1)&lt;/script&gt;", "")


def test_home_features_programs_and_search_points_to_results(client):
    make_program(make_uni(make_country()), "Alpha Course")
    html = page(client, "/")
    assert "Alpha Course" in html and 'id="programs"' in html
    assert 'action="/programs/"' in html
    assert 'data-base="/programs/"' in html


def test_country_page_lists_programs_and_links_to_all(client):
    uni = make_uni(make_country())
    for i in range(7):
        make_program(uni, f"Course {i}")
    html = page(client, "/study/canada/")
    assert "See all 7 programs" in html
    assert "/programs/?country=canada" in html


def test_money_filter():
    assert money(Decimal("18000"), "GBP") == "£18,000"
    assert money(Decimal("5000"), "XYZ") == "XYZ 5,000"
    assert money(None, "GBP") == ""


def test_main_destinations_get_distinct_colours():
    assert len({tone(code) for code in ["GB", "CA", "AU", "US", "IE", "DE"]}) == 6
    assert tone("fr") == tone("FR")
