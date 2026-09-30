import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.audit.models import AuditLog

from .conftest import PASSWORD, current_code, password_step, token_step

User = get_user_model()
pytestmark = pytest.mark.django_db


def test_successful_login_is_audited(client, staff):
    response = password_step(client, "staff@example.com", PASSWORD)
    assert response.status_code == 302
    assert AuditLog.objects.filter(action="auth.login", actor=staff).exists()


def test_failed_login_is_audited_without_password(client, staff):
    password_step(client, "staff@example.com", "wrong-password")
    entry = AuditLog.objects.get(action="auth.login_failed")
    assert entry.metadata == {"identifier": "staff@example.com"}
    assert "wrong-password" not in str(entry.metadata)


def test_account_locks_after_five_failures(client, staff):
    for _ in range(5):
        password_step(client, "staff@example.com", "wrong-password")
    response = password_step(client, "staff@example.com", PASSWORD)  # right password, still locked
    assert response.status_code == 429


def test_lockout_cannot_be_bypassed_by_changing_email_case(client, staff):
    variants = [
        "staff@example.com",
        "STAFF@example.com",
        "Staff@Example.com",
        "staff@EXAMPLE.com",
        "STAFF@EXAMPLE.COM",
    ]
    for email in variants:
        password_step(client, email, "wrong-password")
    response = password_step(client, "staff@example.com", PASSWORD)
    assert response.status_code == 429


def test_security_headers_present(client):
    response = client.get("/")
    assert response["X-Frame-Options"] == "DENY"
    assert response["X-Content-Type-Options"] == "nosniff"
    assert "default-src 'self'" in response["Content-Security-Policy"]


def test_admin_requires_login(client):
    assert client.get(reverse("admin:index")).status_code == 302


def test_admin_login_page_redirects_to_main_login(client):
    response = client.get(reverse("admin:login"))
    assert response.status_code == 302
    assert reverse("two_factor:login") in response["Location"]


def test_staff_without_second_factor_is_sent_to_setup(client, staff):
    password_step(client, staff.email, PASSWORD)
    response = client.get(reverse("admin:index"))
    assert response.status_code == 302
    assert response["Location"] == reverse("two_factor:setup")


def test_staff_without_second_factor_cannot_reach_any_other_page(client, staff):
    password_step(client, staff.email, PASSWORD)
    response = client.get("/")
    assert response.status_code == 302
    assert response["Location"] == reverse("two_factor:setup")


def test_staff_with_device_must_enter_code(client, staff, staff_device):
    response = password_step(client, staff.email, PASSWORD)
    assert response.status_code == 200  # token form shown, not logged in yet
    assert client.get(reverse("admin:index")).status_code == 302


def test_wrong_code_is_rejected(client, staff, staff_device):
    password_step(client, staff.email, PASSWORD)
    response = token_step(client, "000000" if current_code(staff_device) != "000000" else "111111")
    assert response.status_code == 200
    assert client.get(reverse("admin:index")).status_code == 302


def test_correct_code_opens_admin(client, staff, staff_device):
    password_step(client, staff.email, PASSWORD)
    response = token_step(client, current_code(staff_device))
    assert response.status_code == 302
    assert client.get(reverse("admin:index")).status_code == 200


def test_students_are_not_forced_into_two_factor(client):
    User.objects.create_user("student@example.com", PASSWORD)
    password_step(client, "student@example.com", PASSWORD)
    assert client.get("/").status_code == 200


def test_students_cannot_open_admin(client):
    User.objects.create_user("student@example.com", PASSWORD)
    password_step(client, "student@example.com", PASSWORD)
    assert client.get(reverse("admin:index")).status_code == 302


def test_audit_log_is_read_only_in_admin(verified_client):
    assert verified_client.get(reverse("admin:audit_auditlog_add")).status_code == 403


def test_axes_username_helper_handles_all_shapes():
    from apps.accounts.security import axes_username

    assert axes_username(None, {"username": " A@X.com "}) == "a@x.com"
    assert axes_username(None, {"email": "A@X.com"}) == "a@x.com"
    assert axes_username(None, {}) is None
