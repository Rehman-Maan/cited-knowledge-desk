import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.workspaces.models import WorkspaceMembership


@pytest.mark.django_db
def test_login_page_renders(client):
    response = client.get(reverse("accounts:login"))

    assert response.status_code == 200
    assert b"Log in" in response.content


@pytest.mark.django_db
def test_login_redirects_to_dashboard(client):
    get_user_model().objects.create_user(username="katherine", password="test-pass")

    response = client.post(
        reverse("accounts:login"),
        {"username": "katherine", "password": "test-pass"},
    )

    assert response.status_code == 302
    assert response["Location"] == reverse("workspaces:dashboard")


@pytest.mark.django_db
def test_signup_creates_user_workspace_and_logs_in(client):
    response = client.post(
        reverse("accounts:signup"),
        {
            "username": "dorothy",
            "email": "dorothy@example.com",
            "password1": "complex-pass-12345",
            "password2": "complex-pass-12345",
        },
        follow=True,
    )

    user = get_user_model().objects.get(username="dorothy")

    assert response.status_code == 200
    assert b"dorothy&#x27;s Workspace" in response.content
    assert user.workspace_memberships.exists()


@pytest.mark.django_db
def test_guest_login_creates_limited_guest_session(client):
    response = client.post(reverse("accounts:guest-login"), follow=True)
    user = get_user_model().objects.get(username__startswith="guest_")

    assert response.status_code == 200
    assert b"Guest Workspace" in response.content
    assert b"Guest mode" in response.content
    assert user.has_usable_password() is False
    assert WorkspaceMembership.objects.filter(user=user).count() == 1


@pytest.mark.django_db
def test_guest_navigation_hides_restricted_sections(client):
    client.post(reverse("accounts:guest-login"), follow=True)

    response = client.get(reverse("workspaces:dashboard"))

    assert response.status_code == 200
    assert b"Documents" in response.content
    assert b"Chat" in response.content
    assert b"Retrieval" not in response.content
    assert b"Feedback" not in response.content
    assert b"Evaluations" not in response.content


@pytest.mark.django_db
def test_guest_is_redirected_from_restricted_routes(client):
    client.post(reverse("accounts:guest-login"), follow=True)

    response = client.get(reverse("retrieval:search"), follow=True)

    assert response.redirect_chain[-1][0] == reverse("workspaces:dashboard")
