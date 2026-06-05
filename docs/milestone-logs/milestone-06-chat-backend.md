# Milestone 6: Chat Backend


Date: 2026-06-03

## Goal

Add chat sessions, chat messages, retrieval before generation, an LLM gateway, citation parsing, and assistant message persistence.

## Completed

- Added `ChatSession`, `ChatMessage`, and `Citation` models.
- Added chat admin registrations.
- Added chat question form.
- Added citation label builder and parser for labels like `[D3-C12]`.
- Added LLM gateway with local test provider and OpenAI Responses API provider.
- Added grounded prompt contract with source excerpts and citation IDs.
- Added chat orchestration service that retrieves workspace-scoped chunks before generation.
- Persisted user messages, assistant messages, latency, token count, model name, and citations.
- Added basic chat pages at `/chat/` and `/chat/sessions/<id>/`.
- Added tests for citation parsing, prompt construction, message persistence, citations, login protection, and view flow.
- Hardened tests so they use local embeddings and local LLM by default, avoiding accidental paid API calls.

## Verification

- Checked official OpenAI Responses API/model docs for the current generation interface.
- Ran `python manage.py makemigrations chat`: created `apps/chat/migrations/0001_initial.py`.
- Ran `python manage.py check`: passed with no issues.
- Ran `python manage.py migrate`: applied the chat migration against Docker PostgreSQL.
- Ran `python manage.py makemigrations --check --dry-run`: passed with no pending migrations.
- Ran `python -m pytest`: passed, 28 tests.

## Notes

The app is configured for OpenAI in `.env`, so real chat requests can call the paid OpenAI API. Tests intentionally force local providers unless they explicitly opt into another provider.

Milestone 7 will add the streaming chat UI over Channels/WebSockets.
