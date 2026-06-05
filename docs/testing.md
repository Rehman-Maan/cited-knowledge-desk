# Testing

## Local Checks

Run the same core checks used by CI:

```powershell
python -m ruff check .
python manage.py check
python manage.py makemigrations --check --dry-run
python -m pytest
```

Tests default to local deterministic LLM and embedding providers through `tests/conftest.py`, so they do not spend OpenAI credits.

## Browser Smoke Test

The Playwright smoke test lives in `tests/e2e/test_playwright_smoke.py`.

Install Chromium locally when you want to run it for real:

```powershell
python -m playwright install chromium
python -m pytest tests/e2e
```

If Chromium is not installed, the smoke test skips locally. CI installs Chromium and runs it.

## CI

`.github/workflows/ci.yml` runs:

- Ruff lint
- Django system check
- pending-migration check
- full pytest suite against PostgreSQL/pgvector and Redis services
- Docker image build
- Trivy image scan uploaded as SARIF

Dependabot is configured for Python dependencies, GitHub Actions, and Docker base images.
