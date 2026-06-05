from django.contrib.auth import get_user_model

from apps.workspaces.models import Workspace, WorkspaceMembership

User = get_user_model()


def create_default_workspace_for_user(user: User) -> Workspace:
    workspace = Workspace.objects.create(
        name=f"{user.get_username()}'s Workspace",
        created_by=user,
    )
    WorkspaceMembership.objects.create(
        workspace=workspace,
        user=user,
        role=WorkspaceMembership.Role.OWNER,
    )
    return workspace


def get_user_workspaces(user: User):
    if not user.is_authenticated:
        return Workspace.objects.none()

    return Workspace.objects.filter(memberships__user=user).distinct()


def user_has_workspace_role(user: User, workspace: Workspace, roles: set[str]) -> bool:
    if not user.is_authenticated:
        return False

    return WorkspaceMembership.objects.filter(
        user=user,
        workspace=workspace,
        role__in=roles,
    ).exists()


def user_can_administer_workspace(user: User, workspace: Workspace) -> bool:
    return user_has_workspace_role(
        user,
        workspace,
        {WorkspaceMembership.Role.OWNER, WorkspaceMembership.Role.ADMIN},
    )
