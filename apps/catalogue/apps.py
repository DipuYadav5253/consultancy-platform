from django.apps import AppConfig
from django.db.models.signals import post_migrate


class CatalogueConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.catalogue"

    def ready(self):
        from .permissions import grant_catalogue_permissions

        post_migrate.connect(grant_catalogue_permissions, sender=self)
