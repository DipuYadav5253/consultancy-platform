from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.urls import reverse
from django_otp.plugins.otp_totp.models import TOTPDevice

from apps.accounts.roles import Role
from apps.audit.models import AuditLog
from apps.catalogue.models import Country, Program, University

from .conftest import PASSWORD, current_code, password_step, token_step

User = get_user_model()
pytestmark = pytest.mark.django_db


def make_country(**kw):
    defaults = {"name": "United Kingdom", "slug": "uk", "iso_code": "GB", "currency": "GBP"}
    return Country.objects.create(**{**defaults, **kw})


def make_university(country, **kw):
    defaults = {"name": "Test University", "slug": "test-university"}
    return University.objects.create(country=country, **{**defaults, **kw})


def make_program(university, **kw):
    defaults = {
        "name": "MSc Data Science",
        "slug": "msc-data-science",
        "level": Program.Level.MASTER,
        "field_of_study": "Data Science",
        "duration_months": 12,
        "tuition_per_year": Decimal("18000.00"),
        "tuition_currency": "GBP",
        "ielts_min": Decimal("6.5"),
        "pte_min": 60,
    }
    return Program.objects.create(university=university, **{**defaults, **kw})


# ---- publishing rules -------------------------------------------------------------------


def test_new_content_is_draft_by_default():
    assert make_country().is_published is False


def test_published_at_is_set_when_published_and_cleared_when_unpublished():
    country = make_country(is_published=True, last_reviewed_on=date.today())
    assert country.published_at is not None
    country.is_published = False
    country.save()
    assert country.published_at is None


def test_published_country_requires_review_date():
    country = make_country(is_published=True)
    with pytest.raises(ValidationError):
        country.full_clean()


def test_living_cost_min_cannot_exceed_max():
    country = make_country(
        living_cost_per_year_min=Decimal("20000"), living_cost_per_year_max=Decimal("10000")
    )
    with pytest.raises(ValidationError):
        country.full_clean()


def test_program_hidden_unless_whole_chain_is_published():
    country = make_country(is_published=True, last_reviewed_on=date.today())
    uni = make_university(country, is_published=True)
    program = make_program(uni, is_published=True)
    assert list(Program.objects.visible()) == [program]

    uni.is_published = False
    uni.save()
    assert Program.objects.visible().count() == 0

    uni.is_published = True
    uni.save()
    country.is_published = False
    country.save()
    assert Program.objects.visible().count() == 0
    assert University.objects.visible().count() == 0


def test_draft_program_is_hidden_even_if_parents_are_published():
    country = make_country(is_published=True, last_reviewed_on=date.today())
    uni = make_university(country, is_published=True)
    make_program(uni, is_published=False)
    assert Program.objects.visible().count() == 0


# ---- data integrity ---------------------------------------------------------------------


@pytest.mark.parametrize(
    "bad",
    [{"ielts_min": Decimal("9.5")}, {"pte_min": 95}, {"pte_min": 5}, {"duration_months": 0}],
)
def test_database_rejects_impossible_scores_and_durations(bad):
    uni = make_university(make_country())
    with pytest.raises(IntegrityError), transaction.atomic():
        make_program(uni, **bad)


def test_negative_tuition_is_rejected():
    uni = make_university(make_country())
    with pytest.raises(IntegrityError), transaction.atomic():
        make_program(uni, tuition_per_year=Decimal("-1"))


def test_form_validation_rejects_bad_currency_and_iso_codes():
    country = Country(name="X", slug="x", iso_code="gbr", currency="gbp")
    with pytest.raises(ValidationError) as excinfo:
        country.full_clean()
    assert {"iso_code", "currency"} <= set(excinfo.value.message_dict)


def test_same_program_name_and_level_cannot_repeat_in_one_university():
    uni = make_university(make_country())
    make_program(uni)
    with pytest.raises(IntegrityError), transaction.atomic():
        make_program(uni, slug="another-slug")


def test_country_with_universities_cannot_be_deleted_by_accident():
    country = make_country()
    make_university(country)
    with pytest.raises(Exception):  # noqa: B017,PT011  (ProtectedError)
        country.delete()


# ---- who may do what --------------------------------------------------------------------


def staff_member(email, role):
    user = User.objects.create_user(email, PASSWORD, is_staff=True)
    user.groups.add(Group.objects.get(name=role))
    return user, TOTPDevice.objects.create(user=user, name="default", confirmed=True)


def login_staff(client, user, device):
    password_step(client, user.email, PASSWORD)
    token_step(client, current_code(device))


def test_content_manager_can_add_and_change_but_not_delete(client):
    user, device = staff_member("cm@example.com", Role.CONTENT_MANAGER)
    login_staff(client, user, device)
    assert client.get(reverse("admin:catalogue_country_add")).status_code == 200
    country = make_country()
    assert (
        client.get(reverse("admin:catalogue_country_change", args=[country.pk])).status_code == 200
    )
    assert (
        client.get(reverse("admin:catalogue_country_delete", args=[country.pk])).status_code == 403
    )


def test_counsellor_can_view_but_not_change(client):
    user, device = staff_member("co@example.com", Role.COUNSELLOR)
    login_staff(client, user, device)
    country = make_country()
    assert client.get(reverse("admin:catalogue_country_changelist")).status_code == 200
    assert client.get(reverse("admin:catalogue_country_add")).status_code == 403
    response = client.post(
        reverse("admin:catalogue_country_change", args=[country.pk]), {"name": "Hacked"}
    )
    assert response.status_code == 403
    country.refresh_from_db()
    assert country.name == "United Kingdom"


def test_finance_staff_cannot_see_the_catalogue(client):
    user, device = staff_member("fin@example.com", Role.FINANCE)
    login_staff(client, user, device)
    assert client.get(reverse("admin:catalogue_country_changelist")).status_code == 403


# ---- audit trail ------------------------------------------------------------------------


def test_admin_changes_are_audited_with_changed_fields(client):
    user, device = staff_member("cm2@example.com", Role.CONTENT_MANAGER)
    login_staff(client, user, device)
    response = client.post(
        reverse("admin:catalogue_country_add"),
        {
            "name": "Canada",
            "slug": "canada",
            "iso_code": "CA",
            "currency": "CAD",
            "summary": "",
            "intakes": "",
            "visa_overview": "",
            "scholarships_overview": "",
            "source_url": "",
        },
    )
    assert response.status_code == 302, response.content[:500]
    entry = AuditLog.objects.get(action="admin.create", actor=user)
    assert entry.target_type == "catalogue.country"
    assert "name" in entry.metadata["fields"]
