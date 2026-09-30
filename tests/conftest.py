import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django_otp.oath import totp
from django_otp.plugins.otp_totp.models import TOTPDevice

PASSWORD = "a-Strong-pass-123"


def password_step(client, email, password):
    """Submit the first login step (email + password)."""
    return client.post(
        reverse("two_factor:login"),
        {
            "login_view-current_step": "auth",
            "auth-username": email,
            "auth-password": password,
        },
    )


def token_step(client, token):
    """Submit the second login step (authenticator code)."""
    return client.post(
        reverse("two_factor:login"),
        {"login_view-current_step": "token", "token-otp_token": token},
    )


def current_code(device):
    return f"{totp(device.bin_key, step=device.step, t0=device.t0, digits=device.digits):06d}"


@pytest.fixture
def staff(db):
    return get_user_model().objects.create_superuser("staff@example.com", PASSWORD)


@pytest.fixture
def staff_device(staff):
    return TOTPDevice.objects.create(user=staff, name="default", confirmed=True)


@pytest.fixture
def verified_client(client, staff, staff_device):
    """A client logged in as staff who has completed both login steps."""
    password_step(client, staff.email, PASSWORD)
    token_step(client, current_code(staff_device))
    return client
