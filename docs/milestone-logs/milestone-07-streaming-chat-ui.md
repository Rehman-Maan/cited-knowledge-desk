# Milestone 7: Streaming Chat UI

Date: 2026-06-03

## Goal

Add Channels WebSocket routing, streamed token display, chat history sidebar, citation cards, loading states, and error handling.

## Completed

- Added `daphne` dependency so local `runserver` can serve the ASGI app.
- Added ASGI WebSocket routing through `AuthMiddlewareStack`.
- Added `/ws/chat/<session_id>/` WebSocket route.
- Added `ChatConsumer` for authenticated chat sessions.
- Added WebSocket question submission, status events, streamed answer deltas, completion events, and error events.
- Updated the chat detail UI with a three-column layout: chat history, conversation, and citation rail.
- Added sticky composer, loading/status line, streamed assistant message rendering, and live citation cards.
- Kept the existing POST fallback route for non-WebSocket form submission.
- Added WebSocket tests for streaming answer events and anonymous-user rejection.
- Added async test support with `pytest-asyncio`.
- Added focused excerpt rendering for retrieval results and citation cards so long chunks are shortened around matching query terms.
- Added query-term highlighting and overflow-safe citation cards.

## Verification

- Ran `python -m pip install -e ".[dev]"`: installed `daphne` and `pytest-asyncio`.
- Ran `python manage.py check`: passed with no issues after moving `daphne` before `django.contrib.staticfiles`.
- Ran `python manage.py makemigrations --check --dry-run`: passed with no pending migrations.
- Ran focused chat/WebSocket tests: passed, 7 tests.
- Ran `python -m pytest`: passed, 30 tests.
- After focused excerpt polish, ran `python -m pytest`: passed, 32 tests.
- Ran `docker compose ps`: PostgreSQL and Redis were healthy.
- Ran a Django client smoke render for a temporary chat session: page returned 200 and included the WebSocket URL, chat history, and live citation rail.

## Notes

The WebSocket consumer currently streams the completed assistant answer back to the browser in small deltas after generation. True provider-native token streaming can be added later without changing the UI event contract.

The app is still configured for OpenAI in `.env`, so manual chat testing can make paid API calls. Set `LLM_PROVIDER=local` for free UI-only testing.
