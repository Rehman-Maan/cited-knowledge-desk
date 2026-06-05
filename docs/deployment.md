# Deployment

This project is ready for a small production-style deployment with Django ASGI, PostgreSQL/pgvector, Redis, Celery, and persistent media storage.

## Required Environment Variables

Use `config.settings.production`. Start from `.env.production.example`, copy it to the host as `.env`, then replace every placeholder:

```env
DJANGO_SETTINGS_MODULE=config.settings.production
SECRET_KEY=replace-with-a-long-random-secret
DEBUG=False
ALLOWED_HOSTS=your-domain.com
CSRF_TRUSTED_ORIGINS=https://your-domain.com
DATABASE_URL=postgres://user:password@db:5432/cited_knowledge_desk
REDIS_URL=redis://redis:6379/0
POSTGRES_DB=cited_knowledge_desk
POSTGRES_USER=cited
POSTGRES_PASSWORD=replace-me
OPENAI_API_KEY=sk-...
EMBEDDING_PROVIDER=openai
LLM_PROVIDER=openai
```

For free smoke deployments, use:

```env
EMBEDDING_PROVIDER=local
LLM_PROVIDER=local
```

## GitHub Release Prep

Initialize the repository locally:

```powershell
git init
git add .
git commit -m "Initial Cited Knowledge Desk release"
git branch -M main
```

Create an empty GitHub repository, then connect and push:

```powershell
git remote add origin https://github.com/YOUR_USERNAME/cited-knowledge-desk.git
git push -u origin main
```

Never commit `.env`, uploaded `media/`, `.venv/`, or `staticfiles/`. They are ignored by `.gitignore`.

After pushing, GitHub Actions should run the CI workflow in `.github/workflows/ci.yml`.

## Docker Compose Production Example

On the server, create `.env` from `.env.production.example`, then build and start:

```bash
docker compose -f docker-compose.prod.yml up --build -d
```

Run migrations:

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py migrate
```

Collect static files:

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

Create an admin user:

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

Check health:

```text
https://your-domain.com/health/
```

## Reverse Proxy Notes

Terminate TLS at a reverse proxy such as Caddy, Nginx, Traefik, or a managed platform load balancer. Forward HTTP and WebSocket traffic to the `web` service on port `8000`.

Production settings enable HTTPS redirect, secure cookies, HSTS, and content-type nosniff. Keep `CSRF_TRUSTED_ORIGINS` in sync with your public HTTPS origin.

For WebSockets, make sure the proxy forwards upgrade headers. For example, Nginx needs `Upgrade` and `Connection` headers for `/ws/`.

## Demo Mode

The public demo can use the `Continue as guest` button on login/signup. Guest sessions are limited to Dashboard, Documents/upload, and Chat. Retrieval diagnostics, Feedback review, and Evaluations are hidden and server-blocked for guests.

For a LinkedIn/public demo, use these defaults:

```env
EMBEDDING_PROVIDER=openai
LLM_PROVIDER=openai
DOCUMENT_INGESTION_AUTO_QUEUE=True
MAX_DOCUMENT_UPLOAD_SIZE=10485760
```

If you want to avoid OpenAI spend during a public smoke test, use local providers:

```env
EMBEDDING_PROVIDER=local
LLM_PROVIDER=local
```

## Persistent Data

Persist these volumes:

- PostgreSQL data
- Redis data if you need result history
- `media/` uploaded source documents
- `staticfiles/` collected static assets

Back up PostgreSQL and media together so document metadata and files stay consistent.

## Release Checklist

- Run `python -m pytest`.
- Run `python manage.py makemigrations --check --dry-run`.
- Build the Docker image.
- Run Trivy or equivalent image scan.
- Rotate any exposed `.env` secrets.
- Apply migrations before routing production traffic.
- Run a chat smoke test and a health check.
