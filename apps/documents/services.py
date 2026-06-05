from pathlib import Path

from django.conf import settings
from django.db import transaction
from django.http import Http404

from apps.documents.models import Document, DocumentChunk
from apps.workspaces.models import Workspace
from apps.workspaces.services import get_user_workspaces, user_can_administer_workspace


def get_document_for_user(user, pk: int) -> Document:
    document = (
        Document.objects.select_related("workspace", "uploaded_by")
        .prefetch_related("chunks")
        .filter(pk=pk, workspace__in=get_user_workspaces(user))
        .first()
    )
    if document is None:
        raise Http404("Document not found.")
    return document


def create_document(*, workspace: Workspace, user, title: str, file) -> Document:
    document = Document.objects.create(
        workspace=workspace,
        uploaded_by=user,
        title=title,
        file=file,
        file_type=Path(file.name).suffix.lower().lstrip("."),
        status=Document.Status.UPLOADED,
    )
    queue_document_ingestion(document)
    return document


def retry_document_ingestion(*, document: Document, user) -> Document:
    if not user_can_administer_workspace(user, document.workspace):
        raise PermissionError("Only workspace admins can retry ingestion.")

    document.status = Document.Status.UPLOADED
    document.error_message = ""
    document.save(update_fields=["status", "error_message", "updated_at"])
    queue_document_ingestion(document)
    return document


def queue_document_ingestion(document: Document) -> None:
    if not settings.DOCUMENT_INGESTION_AUTO_QUEUE:
        return

    from workers.document_ingestion import ingest_document

    transaction.on_commit(lambda: ingest_document.delay(document.pk))


def replace_document_chunks(*, document: Document, chunks) -> int:
    DocumentChunk.objects.filter(document=document).delete()
    chunk_rows = [
        DocumentChunk(
            workspace=document.workspace,
            document=document,
            chunk_index=index,
            content=chunk.content,
            token_count=chunk.token_count,
            page_number=chunk.page_number,
            section_title=chunk.section_title,
            source_metadata=chunk.source_metadata,
        )
        for index, chunk in enumerate(chunks)
    ]
    DocumentChunk.objects.bulk_create(chunk_rows)
    return len(chunk_rows)
