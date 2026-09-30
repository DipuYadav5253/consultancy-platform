import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.audit.models import AuditLog

User = get_user_model()
pytestmark = pytest.mark.django_db

PASSWORD = "a-Strong-pass-123"


@pytest.fixture
def staff():
    return User.objects.create_superuser("staff@example.com", PASSWORD)


def login(client, email, password):
    return client.post(reverse("admin:login"), {"username": email, "password": password})


def test_successful_login_is_audited(client, staff):
    response = login(client, "staff@example.com", PASSWORD)
    assert response.status_code == 302
    assert AuditLog.objects.filter(action="auth.login", actor=staff).exists()


def test_failed_login_is_audited_without_password(client, staff):
    login(client, "staff@example.com", "wrong-password")
    entry = AuditLog.objects.get(action="auth.login_failed")
    assert entry.metadata == {"identifier": "staff@example.com"}
    assert "wrong-password" not in str(entry.metadata)


def test_account_locks_after_five_failures(client, staff):
    for _ in range(5):
        login(client, "staff@example.com", "wrong-password")
    response = login(client, "staff@example.com", PASSWORD)  # correct password, still locked
    assert response.status_code == 429


def test_admin_requires_login(client):
    response = client.get(reverse("admin:index"))
    assert response.status_code == 302


def test_security_headers_present(client):
    response = client.get("/")
    assert response["X-Frame-Options"] == "DENY"
    assert response["X-Content-Type-Options"] == "nosniff"
    assert "default-src 'self'" in response["Content-Security-Policy"]


def test_audit_log_is_read_only_in_admin(client, staff):
    client.force_login(staff)
    assert client.get(reverse("admin:audit_auditlog_add")).status_code == 403


def test_lockout_cannot_be_bypassed_by_changing_email_case(client, staff):
    variants = [
        "staff@example.com",
        "STAFF@example.com",
        "Staff@Example.com",
        "staff@EXAMPLE.com",
        "STAFF@EXAMPLE.COM",
    ]
    for email in variants:
        login(client, email, "wrong-password")
    response = login(client, "staff@example.com", PASSWORD)
    assert response.status_code == 429
