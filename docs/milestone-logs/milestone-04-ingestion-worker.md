# Milestone 4: Ingestion Worker

Date: 2026-06-02

## Goal

Add background document ingestion: parse uploaded files, normalize text, split text into chunks, store chunk records, and handle ingestion failures.

## Completed

- Added parser dependencies: `pypdf` and `python-docx`.
- Added `DocumentChunk` model with workspace, document, chunk index, content, token count, page number, section title, source metadata, and timestamp.
- Added text extraction services for PDF, Markdown, text, and DOCX files.
- Added whitespace normalization for extracted content.
- Added chunking service with configurable target size and overlap.
- Added Celery task `ingest_document` in `workers/document_ingestion.py`.
- Configured Celery to import the ingestion worker module.
- Queued ingestion after document upload and retry when `DOCUMENT_INGESTION_AUTO_QUEUE=True`.
- Added failure handling that marks documents as `failed` and stores the error message.
- Added chunk replacement so retries clear old chunks before saving new ones.
- Updated document detail UI to show ingestion state and extracted chunk previews.
- Updated document library to show chunk counts.
- Added admin visibility for chunks.
- Added ingestion tests for text extraction, overlapping chunking, successful ingestion, and failed ingestion.

## Verification

- Ran `python -m pip install -e ".[dev]"`: installed new parser dependencies.
- Ran `python manage.py makemigrations documents`: created `apps/documents/migrations/0002_documentchunk.py`.
- Ran `python manage.py check`: passed with no issues.
- Ran `python manage.py migrate`: applied the document chunk migration against Docker PostgreSQL.
- Ran `python -m pytest`: passed, 17 tests.
- Ran `python manage.py makemigrations --check --dry-run`: passed with no pending migrations.
- Ran `docker compose ps`: PostgreSQL and Redis were healthy.
- Ran a direct ingestion smoke against Docker PostgreSQL: created a temporary Markdown document, called `ingest_document`, confirmed status `ready` and 1 chunk, then removed the temporary data and file.

## Notes

Uploaded documents are now queued for ingestion, but a Celery worker must be running for automatic processing outside direct task calls.

Run the worker locally with:

```powershell
celery -A config worker --loglevel=info --pool=solo
```

Embeddings and vector search are intentionally not implemented in this milestone. That work starts in Milestone 5.
