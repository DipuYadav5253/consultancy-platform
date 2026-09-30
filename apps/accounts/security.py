def axes_username(request, credentials=None):
    """Identify the account being attacked, for login lockout.

    Django's login form always names the field "username", even when the model logs in by
    email. The value is lower-cased so `A@x.com` and `a@x.com` share one lockout counter.
    """
    value = (credentials or {}).get("username")
    if value is None and request is not None:
        value = request.POST.get("username")
    return value.strip().lower() if isinstance(value, str) else None
