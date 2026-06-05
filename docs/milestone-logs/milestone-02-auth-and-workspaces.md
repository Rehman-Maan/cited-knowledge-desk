# Milestone 2: Auth and Workspaces

Date: 2026-06-02

## Goal

Add the first product layer: authentication, workspaces, memberships, role checks, and a basic dashboard.

## Completed

- Added login and logout routes using Django authentication views.
- Added `Workspace` and `WorkspaceMembership` models.
- Added owner, admin, and member role choices.
- Added role helper services for workspace permission checks.
- Added a post-save signal that creates a default owner workspace for each new user.
- Added a login-protected dashboard at `/`.
- Added admin registrations for workspaces and memberships.
- Added responsive base, login, and dashboard templates.
- Added tests for login, default workspace creation, role helpers, login protection, and dashboard rendering.

## Verification

- Ran `python manage.py makemigrations workspaces`: created `apps/workspaces/migrations/0001_initial.py`.
- Ran `python manage.py check`: passed with no issues.
- Ran `python manage.py migrate`: applied the workspace migration against Docker PostgreSQL.
- Ran `python -m pytest`: passed, 7 tests.
- Ran `python manage.py showmigrations workspaces`: confirmed `0001_initial` is applied.
- Ran `docker compose ps`: PostgreSQL and Redis were healthy.
- Created a disposable `demo` user for live-server smoke testing.
- Started Django with `python manage.py runserver 127.0.0.1:8000`.
- Verified `http://localhost:8000/health/` returned `{"status": "ok"}`.
- Verified login as `demo` redirected to a dashboard containing `demo's Workspace`.
- Stopped the background Django dev server after verification.

## Notes

The dashboard uses placeholder counts until document models are introduced in Milestone 3.

There is no public registration page yet. Users can be created through Django admin, `createsuperuser`, or the Django shell.

Browser automation could not initialize because the local browser plugin reported an asset path error. The live login/dashboard flow was verified with HTTP requests against the running Django server instead.
