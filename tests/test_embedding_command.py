import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command

from apps.documents.models import Document, DocumentChunk
from apps.workspaces.models import Workspace


@pytest.mark.django_db
def test_embed_missing_chunks_command(settings):
    settings.EMBEDDING_PROVIDER = "local"
    settings.EMBEDDING_DIMENSIONS = 1536
    settings.EMBEDDING_MODEL = "test-local"
    user = get_user_model().objects.create_user(username="command-owner", password="test-pass")
    workspace = Workspace.objects.get(created_by=user)
    document = Document.objects.create(
        workspace=workspace,
        uploaded_by=user,
        title="Command Source",
        file=SimpleUploadedFile("command.md", b"# Command"),
        file_type="md",
        status=Document.Status.READY,
    )
    chunk = DocumentChunk.objects.create(
        workspace=workspace,
        document=document,
        chunk_index=0,
        content="Command should embed this missing chunk.",
        token_count=7,
    )

    call_command("embed_missing_chunks", batch_size=10)
    chunk.refresh_from_db()

    assert chunk.embedding is not None
    assert chunk.embedding_model == "test-local"


@pytest.mark.django_db
def test_embed_missing_chunks_command_force_reembeds_existing_chunks(settings):
    settings.EMBEDDING_PROVIDER = "local"
    settings.EMBEDDING_DIMENSIONS = 1536
    settings.EMBEDDING_MODEL = "forced-local"
    user = get_user_model().objects.create_user(username="force-command-owner", password="test-pass")
    workspace = Workspace.objects.get(created_by=user)
    document = Document.objects.create(
        workspace=workspace,
        uploaded_by=user,
        title="Force Command Source",
        file=SimpleUploadedFile("force-command.md", b"# Command"),
        file_type="md",
        status=Document.Status.READY,
    )
    chunk = DocumentChunk.objects.create(
        workspace=workspace,
        document=document,
        chunk_index=0,
        content="Force command should replace the model marker.",
        token_count=7,
        embedding=[0.0] * 1536,
        embedding_model="old-local",
    )

    call_command("embed_missing_chunks", batch_size=10, force=True)
    chunk.refresh_from_db()

    assert chunk.embedding is not None
    assert chunk.embedding_model == "forced-local"
