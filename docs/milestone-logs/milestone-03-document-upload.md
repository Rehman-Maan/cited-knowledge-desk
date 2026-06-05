# Milestone 3: Document Upload

Date: 2026-06-02

## Goal

Add document upload, document library, document detail, upload validation, failed-ingestion retry action, and signup.

## Completed

- Added signup using Django's `UserCreationForm` and automatic login after account creation.
- Added `Document` model with workspace, title, file, file type, status, uploader, error message, and timestamps.
- Added document statuses: uploaded, processing, ready, and failed.
- Added upload validation for `.pdf`, `.md`, `.txt`, and `.docx`.
- Added a default 10 MB upload limit through `MAX_DOCUMENT_UPLOAD_SIZE`.
- Added document list, upload, detail, and retry routes.
- Restricted upload and retry actions to workspace owners/admins.
- Added document admin registration.
- Updated dashboard counts to use real document data.
- Refined the app UI shell, dashboard, auth pages, document library, upload page, and detail page.
- Added tests for signup, upload, validation, permissions, retry, and document auth protection.

## Verification

- Ran `python manage.py makemigrations documents`: created `apps/documents/migrations/0001_initial.py`.
- Ran `python manage.py check`: passed with no issues.
- Ran `python manage.py migrate`: applied the document migration against Docker PostgreSQL.
- Ran `python -m pytest`: passed, 13 tests.
- Ran `python manage.py makemigrations --check --dry-run`: passed with no pending migrations.
- Ran `docker compose ps`: PostgreSQL and Redis were healthy.
- Started Django with `python manage.py runserver 127.0.0.1:8000`.
- Verified `http://localhost:8000/health/` returned `{"status": "ok"}`.
- Verified live signup created a workspace and landed on the dashboard.
- Verified the authenticated document library page rendered successfully.
- Cleaned up the temporary live-smoke signup user and workspace.
- Stopped the background Django dev server after verification.

## Notes

Document ingestion is intentionally not implemented in this milestone. Uploaded documents stay in `uploaded` status until Milestone 4 adds the Celery ingestion worker.

Browser automation could not initialize because the local browser plugin reported an asset path error. Live UI behavior was verified with HTTP requests against the running Django server instead.
