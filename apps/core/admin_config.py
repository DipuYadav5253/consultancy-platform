from django.contrib.admin.apps import AdminConfig


class SecureAdminConfig(AdminConfig):
    """Swap Django's admin site for one that only admits staff who passed two-factor login."""

    default_site = "apps.core.admin_site.SecureAdminSite"
