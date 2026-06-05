import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.documents.models import Document
from apps.workspaces.models import Workspace, WorkspaceMembership


def upload_file(name="handbook.md", content=b"# Handbook\nVacation policy"):
    return SimpleUploadedFile(name, content, content_type="text/markdown")


@pytest.mark.django_db
def test_document_list_requires_login(client):
    response = client.get(reverse("documents:list"))

    assert response.status_code == 302
    assert reverse("accounts:login") in response["Location"]


@pytest.mark.django_db
def test_owner_can_upload_document(client):
    user = get_user_model().objects.create_user(username="owner-docs", password="test-pass")
    workspace = Workspace.objects.get(created_by=user)
    client.force_login(user)

    response = client.post(
        f"{reverse('documents:upload')}?workspace={workspace.slug}",
        {
            "title": "Employee Handbook",
            "file": upload_file(),
        },
    )

    document = Document.objects.get(workspace=workspace)

    assert response.status_code == 302
    assert response["Location"] == document.get_absolute_url()
    assert document.title == "Employee Handbook"
    assert document.file_type == "md"
    assert document.status == Document.Status.UPLOADED
    assert document.uploaded_by == user


@pytest.mark.django_db
def test_member_cannot_upload_document(client):
    owner = get_user_model().objects.create_user(username="library-owner", password="test-pass")
    member = get_user_model().objects.create_user(username="library-member", password="test-pass")
    workspace = Workspace.objects.get(created_by=owner)
    WorkspaceMembership.objects.create(
        workspace=workspace,
        user=member,
        role=WorkspaceMembership.Role.MEMBER,
    )
    client.force_login(member)

    response = client.post(
        f"{reverse('documents:upload')}?workspace={workspace.slug}",
        {
            "title": "Runbook",
            "file": upload_file(),
        },
    )

    assert response.status_code == 403
    assert Document.objects.filter(workspace=workspace, title="Runbook").count() == 0


@pytest.mark.django_db
def test_upload_rejects_unsupported_file_type(client):
    user = get_user_model().objects.create_user(username="validator", password="test-pass")
    workspace = Workspace.objects.get(created_by=user)
    client.force_login(user)

    response = client.post(
        f"{reverse('documents:upload')}?workspace={workspace.slug}",
        {
            "title": "Spreadsheet",
            "file": upload_file("sheet.xlsx", b"not allowed"),
        },
    )

    assert response.status_code == 200
    assert b"Upload a supported file type" in response.content
    assert Document.objects.filter(workspace=workspace).count() == 0


@pytest.mark.django_db
def test_failed_document_retry_resets_status_for_admin(client):
    user = get_user_model().objects.create_user(username="retry-owner", password="test-pass")
    workspace = Workspace.objects.get(created_by=user)
    document = Document.objects.create(
        workspace=workspace,
        uploaded_by=user,
        title="Broken Source",
        file=upload_file(),
        file_type="md",
        status=Document.Status.FAILED,
        error_message="Parser failed",
    )
    client.force_login(user)

    response = client.post(reverse("documents:retry", kwargs={"pk": document.pk}))
    document.refresh_from_db()

    assert response.status_code == 302
    assert document.status == Document.Status.UPLOADED
    assert document.error_message == ""
