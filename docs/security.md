# Security

## Secrets

Secrets are loaded from environment variables and local `.env` files. Do not commit real API keys, database passwords, or production `SECRET_KEY` values.

GitHub Actions uses local LLM/embedding providers by default, so CI does not need `OPENAI_API_KEY`.

## Authentication And Permissions

- Django auth protects dashboard, documents, retrieval, chat, feedback, and evaluations.
- Signup creates a default workspace and owner membership.
- Document upload and retry require workspace owner/admin role.
- Chat sessions are only visible to their owning user.
- Feedback submission is limited to answers in the submitting user’s own chat.
- Feedback review and evaluation runs are limited to workspace owners/admins.

## Retrieval Isolation

Similarity search filters by `workspace_id` before ranking chunks. Evaluation and chat use the same workspace-scoped retrieval path.

## Upload Controls

Allowed source extensions:

- `.pdf`
- `.md`
- `.txt`
- `.docx`

Default max upload size is 10 MB and can be changed with `MAX_DOCUMENT_UPLOAD_SIZE`.

## Prompt Injection Defense

Document text is treated as untrusted reference content. The system prompt tells the model not to follow instructions inside source excerpts and to cite factual claims using provided citation IDs.

## Production Settings

`config.settings.production` enables:

- `DEBUG=False`
- HTTPS redirect
- secure cookies
- HSTS
- content-type nosniff
- browser XSS filter compatibility setting

Set `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` for the exact production domain.

## Operational Checklist

- Keep `.env` out of version control.
- Rotate leaked OpenAI keys immediately.
- Back up PostgreSQL and uploaded media together.
- Run dependency and image scans in CI.
- Use HTTPS at the reverse proxy.
- Review feedback and evaluation failures for possible hallucination or retrieval drift.
