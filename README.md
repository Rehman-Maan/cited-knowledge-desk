# Cited Knowledge Desk

Cited Knowledge Desk is a Django RAG assistant that answers questions from uploaded documents with source citations, permission-aware retrieval, and an evaluation harness for groundedness.

## Problem

Internal teams often need quick answers from scattered documents, but unsupported chatbot answers are risky. This project is designed around trust: retrieve the right workspace-scoped sources, answer only from those sources, and show citations.

## Key Features

- Django backend with split local and production settings
- PostgreSQL database foundation, ready for pgvector in the retrieval milestone
- Redis-backed Celery worker setup
- Redis-backed Channels layer for future streaming chat
- Docker Compose for local app, database, Redis, and worker services
- Health check endpoint at `/health/`
- Django auth login/logout flow
- Signup flow with automatic default workspace creation
- Guest demo mode from login/signup with limited access to Dashboard, Documents, and Chat
- Workspace and membership models with owner, admin, and member roles
- Login-protected dashboard at `/`
- Document library, upload, detail, and retry views
- Upload validation for PDF, Markdown, text, and DOCX source files
- Celery ingestion task for extracting text and creating document chunks
- pgvector-backed embeddings on document chunks
- Workspace-scoped vector retrieval diagnostic page
- Chat sessions, grounded answer generation, and citation persistence
- Channels WebSocket chat route with streamed answer display
- Chat history sidebar, loading states, and live citation cards
- Answer feedback with helpful/report controls, failure tags, and comments
- Workspace-admin feedback review queue
- Gold-question evaluation harness with retrieval, citation, answer, abstention, and latency metrics
- CI workflow for lint, tests, Docker build, and Trivy scan
- Production Docker Compose example and deployment notes
- Milestone logs in `docs/milestone-logs/`

## Architecture

```text
Browser
  -> Django + DRF
  -> PostgreSQL
  -> Redis
  -> Celery workers
  -> future LLM and embedding services
```

## Tech Stack

- Django
- Django REST Framework
- Django Channels
- Celery
- Redis
- PostgreSQL
- Docker Compose

## Local Setup

Create a local environment file:

```powershell
Copy-Item .env.example .env
```

Create and activate a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Run checks and tests:

```powershell
python -m ruff check .
python manage.py check
pytest
```

Start the full local stack:

```powershell
docker compose up --build
```

Docker Compose publishes PostgreSQL on host port `5433` to avoid conflicts with any local PostgreSQL using `5432`. Inside Docker, the app still connects to `db:5432`.

In another terminal, run migrations:

```powershell
docker compose exec web python manage.py migrate
```

For local WebSocket chat with Django's dev server, `daphne` is installed and `runserver` serves the ASGI app:

```powershell
python manage.py runserver
```

Open:

- App: <http://localhost:8000/>
- Health check: <http://localhost:8000/health/>
- Admin: <http://localhost:8000/admin/>
- Retrieval search: <http://localhost:8000/retrieval/search/>
- Chat: <http://localhost:8000/chat/>
- Feedback review: <http://localhost:8000/feedback/>
- Evaluations: <http://localhost:8000/evaluations/>

Create an admin user:

```powershell
python manage.py createsuperuser
```

Or create a user through signup:

- Signup: <http://localhost:8000/accounts/signup/>
- Login: <http://localhost:8000/accounts/login/>

## How RAG Works

The project now supports document upload, background ingestion, text extraction, chunk creation, embedding storage, workspace-scoped vector retrieval, grounded chat answers, citation persistence, answer feedback review, and regression evaluation.

For local development, embeddings default to a deterministic hash provider so the app works without secrets. For hosted embeddings, set:

```powershell
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=your-api-key
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536
```

Backfill vectors for existing chunks:

```powershell
python manage.py embed_missing_chunks
```

For OpenAI answer generation, set:

```powershell
LLM_PROVIDER=openai
LLM_MODEL=gpt-5-mini
LLM_MAX_OUTPUT_TOKENS=700
```

## Evaluation Results

The evaluation harness reads YAML gold questions from `eval/gold_questions.yml`, runs retrieval and answer generation, then stores aggregate and per-question metrics.

Run from the UI:

- Evaluations: <http://localhost:8000/evaluations/>

Run from the terminal:

```powershell
python manage.py run_rag_eval --workspace your-workspace-slug --user your-username --dataset eval/gold_questions.yml --top-k 8
```

Tracked metrics:

- retrieval recall@k
- citation precision
- answer faithfulness
- answer relevance
- abstention accuracy
- average, p50, and p95 latency

## Security Model

Secrets load from environment variables and `.env` stays out of version control. Workspace-scoped permissions protect documents, chat, feedback review, evaluations, and retrieval. See `docs/security.md`.

## Deployment

Docker Compose is included for local development and `docker-compose.prod.yml` provides a production-style example with Daphne, Celery, PostgreSQL/pgvector, Redis, and persistent volumes.

See:

- `docs/testing.md`
- `docs/deployment.md`
- `docs/release-checklist.md`
- `.github/workflows/ci.yml`

## Limitations

- Feedback review is workspace-admin scoped, but richer triage workflows and analytics are future work.
- Evaluation metrics are deterministic heuristics for local regression testing, not a replacement for human review or model-graded evals.

## Roadmap

1. Auth and workspaces
2. Document upload
3. Ingestion worker
4. Embeddings and vector search
5. Chat backend
6. Streaming chat UI
7. Feedback and review
8. Evaluation harness
9. Testing, CI, and deployment
