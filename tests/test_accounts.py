import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import IntegrityError, transaction

from apps.accounts.roles import Role

User = get_user_model()
pytestmark = pytest.mark.django_db


def test_email_is_normalised_to_lowercase():
    user = User.objects.create_user("  Student@Example.COM ", "a-Strong-pass-123")
    assert user.email == "student@example.com"


def test_email_is_unique_ignoring_case():
    User.objects.create_user("a@example.com", "a-Strong-pass-123")
    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.create_user("A@EXAMPLE.COM", "a-Strong-pass-123")


def test_email_is_required():
    with pytest.raises(ValueError):
        User.objects.create_user("", "a-Strong-pass-123")


def test_password_is_hashed_not_stored_plain():
    user = User.objects.create_user("b@example.com", "a-Strong-pass-123")
    assert user.password != "a-Strong-pass-123"
    assert user.check_password("a-Strong-pass-123")


def test_new_user_is_not_staff():
    user = User.objects.create_user("c@example.com", "a-Strong-pass-123")
    assert not user.is_staff and not user.is_superuser


def test_superuser_flags():
    admin = User.objects.create_superuser("root@example.com", "a-Strong-pass-123")
    assert admin.is_staff and admin.is_superuser


def test_superuser_cannot_be_created_without_flags():
    with pytest.raises(ValueError):
        User.objects.create_superuser("x@example.com", "a-Strong-pass-123", is_staff=False)


def test_primary_key_is_uuid():
    user = User.objects.create_user("d@example.com", "a-Strong-pass-123")
    assert len(str(user.pk)) == 36


def test_all_roles_exist():
    names = set(Group.objects.values_list("name", flat=True))
    assert set(Role.ALL) <= names


def test_has_role():
    user = User.objects.create_user("e@example.com", "a-Strong-pass-123")
    user.groups.add(Group.objects.get(name=Role.COUNSELLOR))
    assert user.has_role(Role.COUNSELLOR)
    assert not user.has_role(Role.FINANCE)
