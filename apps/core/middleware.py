from django.shortcuts import redirect
from django.urls import Resolver404, resolve

# Pages a staff member may open before they have finished two-factor setup.
ALLOWED_VIEW_NAMES = {
    "two_factor:login",
    "two_factor:setup",
    "two_factor:setup_complete",
    "two_factor:qr",
    "two_factor:backup_tokens",
    "admin:logout",
}


class StaffTwoFactorMiddleware:
    """Force every logged-in staff member to complete two-factor before using the site.

    Students are not affected. Staff without a second factor are sent to the setup page;
    staff who have one but did not enter a code this session are sent back to log in.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        if user.is_authenticated and user.is_staff and not user.is_verified():
            try:
                view_name = resolve(request.path_info).view_name
            except Resolver404:
                view_name = ""
            is_static = request.path_info.startswith("/static/")
            if view_name not in ALLOWED_VIEW_NAMES and not is_static:
                has_device = user.totpdevice_set.filter(confirmed=True).exists()
                return redirect("two_factor:login" if has_device else "two_factor:setup")
        return self.get_response(request)
