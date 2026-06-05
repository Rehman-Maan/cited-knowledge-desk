# Milestone 1: Project Setup

Date: 2026-06-02

## Goal

Create the backend foundation for Cited Knowledge Desk.

## Completed

- Created the Django project shell with `config/`, split settings, ASGI, WSGI, URLs, and Celery app configuration.
- Configured PostgreSQL through `DATABASE_URL`.
- Configured Redis for Celery and Channels through `REDIS_URL`.
- Added Docker Compose services for Django, PostgreSQL with pgvector, Redis, and Celery.
- Added a `/health/` endpoint returning JSON status.
- Added project directories from the build plan for apps, services, workers, eval, tests, docs, templates, static, and media.
- Added an initial README and environment variable template.
- Added a basic health endpoint test.

## Verification

- Created `.env` from `.env.example` for local verification.
- Created a local virtual environment in `.venv`.
- Installed project dependencies with `python -m pip install -e ".[dev]"`.
- Ran `python manage.py check`: passed with no issues.
- Ran `pytest`: passed, 1 test.
- Ran `docker compose config`: passed and rendered the expected web, celery, db, redis, and volume configuration.
- Ran a direct Celery import/config check: passed and resolved the Redis broker/result backend.
- Ran `docker compose up -d db redis`: passed after Docker Desktop was started and PostgreSQL was moved to host port `5433`.
- Ran `docker compose ps`: PostgreSQL and Redis were both healthy.
- Ran `docker compose exec db pg_isready -U cited -d cited_knowledge_desk`: passed.
- Ran `python manage.py migrate`: passed against the Docker PostgreSQL database.

## Notes

This milestone intentionally avoids domain models. Auth, workspaces, documents, retrieval, chat, feedback, and evaluations begin in later milestones.

The local `.env` uses `localhost` for PostgreSQL and Redis so commands run from the host can connect to published ports. Docker Compose overrides those URLs to use the `db` and `redis` service names inside containers.

PostgreSQL is published on host port `5433` because the default `5432` port was already used by another local PostgreSQL service. Docker-internal connections still use `db:5432`.
