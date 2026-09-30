from django.contrib.auth.models import Group, Permission

from apps.accounts.roles import Role

MODELS = ("country", "university", "program")

# Content managers maintain the catalogue (no deleting); counsellors and application
# officers can look things up. Nobody else gets access.
ROLE_ACTIONS = {
    Role.CONTENT_MANAGER: ("view", "add", "change"),
    Role.COUNSELLOR: ("view",),
    Role.APPLICATION_OFFICER: ("view",),
}


def grant_catalogue_permissions(sender, **kwargs):
    """Runs after every migrate; safe to repeat."""
    for role, actions in ROLE_ACTIONS.items():
        group = Group.objects.filter(name=role).first()
        if group is None:
            continue
        codenames = [f"{action}_{model}" for action in actions for model in MODELS]
        perms = Permission.objects.filter(
            content_type__app_label="catalogue", codename__in=codenames
        )
        group.permissions.add(*perms)
