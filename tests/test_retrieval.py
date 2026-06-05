import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.documents.models import Document, DocumentChunk
from apps.workspaces.models import Workspace
from services.retrieval.vector_search import embed_chunks, search_similar_chunks


def create_document_with_chunks(user, workspace, title, contents):
    document = Document.objects.create(
        workspace=workspace,
        uploaded_by=user,
        title=title,
        file=SimpleUploadedFile(f"{title}.md", b"# Test"),
        file_type="md",
        status=Document.Status.READY,
    )
    chunks = [
        DocumentChunk.objects.create(
            workspace=workspace,
            document=document,
            chunk_index=index,
            content=content,
            token_count=len(content.split()),
        )
        for index, content in enumerate(contents)
    ]
    embed_chunks(chunks, model_name="test-local")
    return document, chunks


@pytest.mark.django_db
def test_embed_chunks_stores_vectors(settings):
    settings.EMBEDDING_PROVIDER = "local"
    settings.EMBEDDING_DIMENSIONS = 1536
    user = get_user_model().objects.create_user(username="embed-owner", password="test-pass")
    workspace = Workspace.objects.get(created_by=user)
    _, chunks = create_document_with_chunks(
        user,
        workspace,
        "Benefits",
        ["Vacation policy allows annual leave."],
    )

    chunks[0].refresh_from_db()

    assert chunks[0].embedding is not None
    assert len(chunks[0].embedding) == 1536
    assert chunks[0].embedding_model == "test-local"


@pytest.mark.django_db
def test_similarity_search_returns_workspace_scoped_results(settings):
    settings.EMBEDDING_PROVIDER = "local"
    settings.EMBEDDING_DIMENSIONS = 1536
    owner = get_user_model().objects.create_user(username="retrieval-owner", password="test-pass")
    other = get_user_model().objects.create_user(username="retrieval-other", password="test-pass")
    workspace = Workspace.objects.get(created_by=owner)
    other_workspace = Workspace.objects.get(created_by=other)

    create_document_with_chunks(
        owner,
        workspace,
        "Policies",
        [
            "Vacation policy includes annual leave and paid time off.",
            "Incident response requires security review.",
        ],
    )
    create_document_with_chunks(
        other,
        other_workspace,
        "Other Policies",
        ["Vacation policy from another workspace should not appear."],
    )

    results = search_similar_chunks(
        workspace=workspace,
        query="vacation leave policy",
        top_k=5,
        model_name="test-local",
    )

    assert results
    assert results[0].chunk.workspace == workspace
    assert "Vacation policy" in results[0].chunk.content
    assert all(result.chunk.workspace == workspace for result in results)


@pytest.mark.django_db
def test_retrieval_search_view_requires_login(client):
    response = client.get(reverse("retrieval:search"))

    assert response.status_code == 302
    assert reverse("accounts:login") in response["Location"]


@pytest.mark.django_db
def test_retrieval_search_view_renders_results(client, settings):
    settings.EMBEDDING_PROVIDER = "local"
    settings.EMBEDDING_DIMENSIONS = 1536
    user = get_user_model().objects.create_user(username="search-view", password="test-pass")
    workspace = Workspace.objects.get(created_by=user)
    create_document_with_chunks(
        user,
        workspace,
        "Handbook",
        ["Employees receive vacation leave after onboarding."],
    )
    client.force_login(user)

    response = client.get(
        reverse("retrieval:search"),
        {"q": "vacation leave", "top_k": 3, "workspace": workspace.slug},
    )

    assert response.status_code == 200
    assert b"Employees receive" in response.content
    assert b"<mark>vacation</mark>" in response.content
    assert b"<mark>leave</mark>" in response.content
