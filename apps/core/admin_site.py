from django.contrib.admin import AdminSite
from two_factor.admin import AdminSiteOTPRequiredMixin


class SecureAdminSite(AdminSiteOTPRequiredMixin, AdminSite):
    """Admin that requires a verified second factor and sends logins to the main login page."""
