from axes.helpers import get_client_ip_address

from .services import record


class AuditedAdminMixin:
    """Record who created, changed or deleted an object in the admin, and which fields."""

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        record(
            "admin.update" if change else "admin.create",
            actor=request.user,
            target=obj,
            ip=get_client_ip_address(request),
            metadata={"fields": sorted(form.changed_data)},
        )

    def delete_model(self, request, obj):
        record(
            "admin.delete",
            actor=request.user,
            target=obj,
            ip=get_client_ip_address(request),
            metadata={"repr": str(obj)[:200]},
        )
        super().delete_model(request, obj)
