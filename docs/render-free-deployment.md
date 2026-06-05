# Render Free Deployment

This project includes a `render.yaml` Blueprint for a free Render portfolio preview.

## What This Deploys

- One free Render web service running the Django ASGI app with Daphne
- One free Render Postgres database
- One free Render Key Value instance for Redis-compatible Channels/Celery settings
- A seeded public demo workspace with professional sample data

## Free Tier Limitations

This is suitable for a portfolio preview, not production.

- Free Render web services spin down after inactivity and take about a minute to wake up.
- Free Render Postgres databases expire after 30 days unless upgraded.
- Free Render Key Value is in-memory only and can lose state on restart.
- Free Render does not provide a separate free background worker, so this preview disables automatic Celery ingestion.
- Uploaded files on the web service filesystem are ephemeral on redeploy/restart/spin-down.

For a serious hosted version, use a paid web service, paid Postgres, persistent media storage, and a paid background worker.

## Deploy Steps

1. Open Render and connect your GitHub account.
2. Create a new Blueprint from `https://github.com/Rehman-Maan/cited-knowledge-desk`.
3. Render will detect `render.yaml`.
4. When prompted for `DEMO_USER_PASSWORD`, enter a password you can use to log in to the seeded demo account.
5. Wait for the first deploy to finish.
6. Open the Render URL.
7. Log in with username `demo_public` and the password you entered.

The pre-deploy command runs migrations, collects static files, and seeds the public demo workspace:

```bash
python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py seed_public_demo
```

Guest mode also works, but the seeded demo workspace is best for showing Documents, Chat, Citations, Feedback, and Evaluations.

## Environment Notes

The free Blueprint uses local deterministic providers:

```text
EMBEDDING_PROVIDER=local
LLM_PROVIDER=local
```

This avoids requiring paid OpenAI usage for the public preview. To enable OpenAI later, update the Render service environment variables:

```text
EMBEDDING_PROVIDER=openai
LLM_PROVIDER=openai
OPENAI_API_KEY=...
```

Then add a paid background worker if you want uploaded documents to ingest automatically.
