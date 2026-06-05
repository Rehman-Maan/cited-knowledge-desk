# Release Checklist

Use this before pushing the public demo or posting the project.

## Local Verification

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe -m pytest
docker build --progress=plain -t cited-knowledge-desk:release .
```

## Secrets

- Confirm `.env` is not committed.
- Rotate any OpenAI key that may have appeared in screenshots, logs, or pasted text.
- Use `.env.production.example` as the host template.
- Set a fresh production `SECRET_KEY`.
- Set production `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`.

## Server

- Start PostgreSQL/pgvector and Redis.
- Start Django ASGI web service.
- Start Celery worker.
- Run migrations.
- Run `collectstatic`.
- Create an admin user.
- Confirm `/health/` returns `{"status": "ok"}`.
- Upload a small document.
- Confirm Celery ingestion reaches `Ready`.
- Ask a chat question and open citations.
- Test `Continue as guest` from mobile width.

## Public Demo Notes

- Guest mode is available from login/signup.
- Guest users can use Dashboard, Documents/upload, and Chat.
- Guest users cannot access Retrieval diagnostics, Feedback review, or Evaluations.
- Keep demo upload size modest to control storage and API spend.
