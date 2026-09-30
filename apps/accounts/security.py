def axes_username(request, credentials=None):
    """Identify the account being attacked, for login lockout.

    The value is lower-cased and trimmed so `A@x.com` and `a@x.com` share one lockout counter.
    Depending on the code path, the identifier arrives under "username" or "email".
    """
    credentials = credentials or {}
    value = credentials.get("username") or credentials.get("email")
    if value is None and request is not None:
        value = request.POST.get("auth-username") or request.POST.get("username")
    return value.strip().lower() if isinstance(value, str) else None
