from celery import shared_task
from django.conf import settings
from django.db import transaction

from apps.documents.models import Document
from apps.documents.services import replace_document_chunks
from services.chunking.text import chunk_pages
from services.document_parsing.extractors import extract_document_pages
from services.retrieval.vector_search import embed_chunks


@shared_task(bind=True, autoretry_for=(), max_retries=0)
def ingest_document(self, document_id: int) -> dict:
    document = Document.objects.select_related("workspace").get(pk=document_id)

    try:
        document.status = Document.Status.PROCESSING
        document.error_message = ""
        document.save(update_fields=["status", "error_message", "updated_at"])

        pages = extract_document_pages(document.file.path, document.file_type)
        if not pages:
            raise ValueError("No extractable text was found in this document.")

        chunks = chunk_pages(
            pages,
            target_tokens=settings.DOCUMENT_CHUNK_TARGET_TOKENS,
            overlap_tokens=settings.DOCUMENT_CHUNK_OVERLAP_TOKENS,
        )
        if not chunks:
            raise ValueError("No chunks could be created from this document.")

        with transaction.atomic():
            chunk_count = replace_document_chunks(document=document, chunks=chunks)
            document_chunks = list(document.chunks.order_by("chunk_index"))
            embedded_count = embed_chunks(document_chunks, model_name=settings.EMBEDDING_MODEL)
            document.status = Document.Status.READY
            document.error_message = ""
            document.save(update_fields=["status", "error_message", "updated_at"])

        return {
            "document_id": document.pk,
            "status": document.status,
            "chunks": chunk_count,
            "embedded_chunks": embedded_count,
        }
    except Exception as exc:
        document.status = Document.Status.FAILED
        document.error_message = str(exc)[:4000]
        document.save(update_fields=["status", "error_message", "updated_at"])
        raise
