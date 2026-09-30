from .models import AuditLog


def record(action, *, actor=None, target=None, ip=None, metadata=None):
    """Write one audit entry. `target` may be any saved model instance."""
    return AuditLog.objects.create(
        action=action,
        actor=actor if getattr(actor, "pk", None) else None,
        target_type=target._meta.label_lower if target is not None else "",
        target_id=str(target.pk) if target is not None else "",
        ip_address=ip,
        metadata=metadata or {},
    )
