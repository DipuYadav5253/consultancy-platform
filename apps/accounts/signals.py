from axes.helpers import get_client_ip_address
from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.dispatch import receiver

from apps.audit.services import record


@receiver(user_logged_in)
def on_login(sender, request, user, **kwargs):
    record("auth.login", actor=user, target=user, ip=get_client_ip_address(request))


@receiver(user_login_failed)
def on_login_failed(sender, credentials, request=None, **kwargs):
    # Only the identifier is stored. Passwords are never logged.
    identifier = str((credentials or {}).get("username", ""))[:254]
    ip = get_client_ip_address(request) if request is not None else None
    record("auth.login_failed", ip=ip, metadata={"identifier": identifier})
