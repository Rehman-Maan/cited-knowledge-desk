# Milestone 10: Testing, CI, and Deployment

## Status

Complete and verified. The testing, CI, deployment documentation, production Compose file, Dockerfile hardening, full test suite, Compose validation, and Docker image build are in place.

## What Was Created

- Added GitHub Actions CI at `.github/workflows/ci.yml`.
- Added Dependabot configuration at `.github/dependabot.yml`.
- Added `.dockerignore` to keep secrets, virtualenvs, caches, media, and build noise out of images.
- Hardened `Dockerfile` for ASGI runtime with Daphne and a non-root app user.
- Added `docker-compose.prod.yml` for a production-style stack:
  - Django ASGI web service
  - Celery worker
  - PostgreSQL with pgvector
  - Redis
  - persistent media, static, database, and Redis volumes
- Added Playwright browser smoke coverage in `tests/e2e/test_playwright_smoke.py`.
- Added `playwright` to the development dependencies.
- Added Ruff lint configuration and an `e2e` pytest marker in `pyproject.toml`.
- Added testing documentation in `docs/testing.md`.
- Added deployment documentation in `docs/deployment.md`.
- Updated `docs/security.md` with the current security model.
- Updated `README.md` with CI, testing, deployment, and evaluation references.
- Added production proxy SSL support in `config/settings/production.py`.

## What Was Verified

- `.\.venv\Scripts\python.exe -m ruff check .`
  - Passed.
- `.\.venv\Scripts\python.exe manage.py check`
  - Passed.
- `.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run`
  - Passed with no model changes detected.
- `.\.venv\Scripts\python.exe -m pytest`
  - Passed with `48 passed, 1 skipped`.
- `docker compose -f docker-compose.prod.yml config --quiet`
  - Passed.
- `docker build --progress=plain -t cited-knowledge-desk:milestone10 .`
  - Passed.
- `docker images cited-knowledge-desk --format "{{.Repository}}:{{.Tag}} {{.ID}} {{.Size}}"`
  - Confirmed local image `cited-knowledge-desk:milestone10`.

## Docker Desktop Recovery Note

During verification, Docker Desktop entered a stale half-running state. The Windows process list showed Docker Desktop and `com.docker.backend` processes, but `com.docker.service` was stopped. Docker logs reported that the backend server was already running and that an existing process was holding Docker's backend log file open.

Recovery steps used:

```powershell
Get-Process | Where-Object { $_.ProcessName -like '*Docker*' -or $_.ProcessName -like '*com.docker*' -or $_.ProcessName -eq 'docker-compose' -or $_.ProcessName -eq 'docker' } | Stop-Process -Force -ErrorAction SilentlyContinue
wsl --shutdown
Start-Process -FilePath "C:\Program Files\Docker\Docker\Docker Desktop.exe" -WindowStyle Hidden
docker compose up -d db redis
docker compose ps
docker build --progress=plain -t cited-knowledge-desk:milestone10 .
```

## Production-Style Stack Commands

```powershell
docker compose -f docker-compose.prod.yml up --build -d
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

## Important Notes

- This folder is not currently a Git repository, so the GitHub Actions workflow will not run until the project is initialized as a repo and pushed to GitHub.
- Tests use local deterministic LLM and embedding providers, so the test suite should not spend OpenAI credits.
- Production Compose forces `DEBUG=False` even if the local `.env` contains `DEBUG=True`.

## Next Step

Milestone 10 is complete. The next project step is to review the remaining build plan and decide whether to move into polish, deployment packaging, or any milestone beyond the original testing/CI/deployment scope.
