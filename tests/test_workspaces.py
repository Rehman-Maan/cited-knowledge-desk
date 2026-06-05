import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.workspaces.models import Workspace, WorkspaceMembership
from apps.workspaces.services import user_can_administer_workspace, user_has_workspace_role


@pytest.mark.django_db
def test_new_user_gets_default_workspace_with_owner_membership():
    user = get_user_model().objects.create_user(username="ada", password="test-pass")

    workspace = Workspace.objects.get(created_by=user)
    membership = WorkspaceMembership.objects.get(user=user, workspace=workspace)

    assert workspace.name == "ada's Workspace"
    assert workspace.slug == "adas-workspace"
    assert membership.role == WorkspaceMembership.Role.OWNER


@pytest.mark.django_db
def test_workspace_role_helpers_check_membership_roles():
    owner = get_user_model().objects.create_user(username="owner", password="test-pass")
    member = get_user_model().objects.create_user(username="member", password="test-pass")
    workspace = Workspace.objects.get(created_by=owner)
    WorkspaceMembership.objects.create(
        user=member,
        workspace=workspace,
        role=WorkspaceMembership.Role.MEMBER,
    )

    assert user_can_administer_workspace(owner, workspace)
    assert not user_can_administer_workspace(member, workspace)
    assert user_has_workspace_role(member, workspace, {WorkspaceMembership.Role.MEMBER})


@pytest.mark.django_db
def test_dashboard_requires_login(client):
    response = client.get(reverse("workspaces:dashboard"))

    assert response.status_code == 302
    assert reverse("accounts:login") in response["Location"]


@pytest.mark.django_db
def test_dashboard_renders_user_workspace(client):
    user = get_user_model().objects.create_user(username="grace", password="test-pass")
    client.force_login(user)

    response = client.get(reverse("workspaces:dashboard"))

    assert response.status_code == 200
    assert b"grace&#x27;s Workspace" in response.content
