import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.documents.models import Document, DocumentChunk
from apps.workspaces.models import Workspace
from services.chunking.text import chunk_pages
from services.document_parsing.extractors import ExtractedPage, extract_document_pages
from workers.document_ingestion import ingest_document


@pytest.mark.django_db
def test_extract_text_document_pages(tmp_path):
    path = tmp_path / "policy.md"
    path.write_text("# Policy\n\nEmployees can upload documents.", encoding="utf-8")

    pages = extract_document_pages(path, "md")

    assert len(pages) == 1
    assert "Employees can upload documents." in pages[0].text


def test_chunk_pages_creates_overlapping_chunks():
    page = ExtractedPage(
        text=" ".join(f"word{i}" for i in range(20)),
        page_number=3,
        source_metadata={"source_page": 3},
    )

    chunks = chunk_pages([page], target_tokens=8, overlap_tokens=2)

    assert len(chunks) == 3
    assert chunks[0].page_number == 3
    assert chunks[0].token_count == 8
    assert chunks[1].content.startswith("word6")


@pytest.mark.django_db
def test_ingest_document_creates_chunks_and_marks_ready(settings):
    settings.DOCUMENT_CHUNK_TARGET_TOKENS = 8
    settings.DOCUMENT_CHUNK_OVERLAP_TOKENS = 2
    user = get_user_model().objects.create_user(username="ingest-owner", password="test-pass")
    workspace = Workspace.objects.get(created_by=user)
    document = Document.objects.create(
        workspace=workspace,
        uploaded_by=user,
        title="Policy",
        file=SimpleUploadedFile(
            "policy.md",
            b"# Policy\nEmployees can upload markdown documents for trusted answers.",
        ),
        file_type="md",
    )

    result = ingest_document(document.pk)
    document.refresh_from_db()

    assert result["status"] == Document.Status.READY
    assert document.status == Document.Status.READY
    assert document.error_message == ""
    assert DocumentChunk.objects.filter(document=document).count() >= 1


@pytest.mark.django_db
def test_ingest_document_marks_failed_when_no_text():
    user = get_user_model().objects.create_user(username="empty-owner", password="test-pass")
    workspace = Workspace.objects.get(created_by=user)
    document = Document.objects.create(
        workspace=workspace,
        uploaded_by=user,
        title="Empty",
        file=SimpleUploadedFile("empty.txt", b""),
        file_type="txt",
    )

    with pytest.raises(ValueError, match="No extractable text"):
        ingest_document(document.pk)

    document.refresh_from_db()
    assert document.status == Document.Status.FAILED
    assert "No extractable text" in document.error_message
