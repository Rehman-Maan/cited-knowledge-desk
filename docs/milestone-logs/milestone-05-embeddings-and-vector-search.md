# Milestone 5: Embeddings and Vector Search

Date: 2026-06-02

## Goal

Install pgvector, store embeddings on document chunks, add an embedding service, implement workspace-scoped vector search, and verify retrieval behavior.

## Completed

- Added dependencies: `pgvector` and `openai`.
- Added embedding settings for provider, model, dimensions, and API key.
- Added `embedding` vector field and `embedding_model` field to `DocumentChunk`.
- Added a migration that enables the PostgreSQL `vector` extension.
- Added deterministic local hash embeddings for development and tests.
- Added OpenAI embedding provider path for hosted embeddings.
- Updated ingestion so new chunks are embedded before a document becomes `ready`.
- Added workspace-scoped similarity search using pgvector cosine distance.
- Added retrieval search page at `/retrieval/search/`.
- Added `embed_missing_chunks` management command for backfilling existing chunks.
- Added tests for embedding storage, workspace-scoped retrieval, retrieval UI, and backfill command.
- Backfilled embeddings for existing local chunks.

## Verification

- Ran `python -m pip install -e ".[dev]"`: installed new embedding/vector dependencies.
- Ran `python manage.py makemigrations documents`: created `apps/documents/migrations/0003_documentchunk_embedding_and_more.py`.
- Added `VectorExtension()` to the migration before creating the vector field.
- Ran `python manage.py check`: passed with no issues.
- Ran `python manage.py migrate`: applied the pgvector migration against Docker PostgreSQL.
- Ran `python manage.py makemigrations --check --dry-run`: passed with no pending migrations.
- Ran `python -m pytest`: passed, 22 tests.
- Ran `python manage.py embed_missing_chunks --batch-size 50`: embedded 2 existing chunks.
- Ran a direct retrieval smoke against Docker PostgreSQL: found 2 embedded chunks and returned workspace-scoped results.

## Notes

The default `local` embedding provider is deterministic and useful for development, but it is not semantically strong. Set `EMBEDDING_PROVIDER=openai` and `OPENAI_API_KEY` to use hosted embeddings.

Milestone 6 will use retrieval results before answer generation and persistence.
