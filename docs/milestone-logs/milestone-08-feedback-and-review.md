# Milestone 8: Feedback and Review

Date: 2026-06-03

## Goal

Add answer feedback so users can mark responses as helpful or report issues, and give workspace admins a review queue for bad answers and comments.

## Completed

- Added `AnswerFeedback` model with rating, comment, failure tag, reviewed status, timestamp, indexes, and one-feedback-per-user-per-message constraint.
- Added feedback form validation that clears failure tags for thumbs-up feedback.
- Added feedback service functions for permission-aware submission and admin review marking.
- Added feedback URLs and views:
  - `POST /feedback/messages/<message_id>/`
  - `GET /feedback/`
  - `POST /feedback/<feedback_id>/reviewed/`
- Added Django admin registration for answer feedback.
- Added chat UI controls under assistant messages:
  - `Helpful`
  - collapsible `Report issue` with failure tag and comment
- Added feedback controls for newly streamed WebSocket answers.
- Added workspace-admin feedback review page with open-chat and mark-reviewed actions.
- Added navigation link to the feedback review queue.
- Updated README feature list, local URLs, RAG status, and limitations.

## Verification

- Ran `.\.venv\Scripts\python.exe manage.py makemigrations feedback`: created `feedback.0001_initial`.
- Ran `.\.venv\Scripts\python.exe -m pytest tests\test_feedback.py tests\test_chat.py`: passed, 12 tests.
- Ran `.\.venv\Scripts\python.exe manage.py migrate`: applied `feedback.0001_initial`.
- Ran `.\.venv\Scripts\python.exe manage.py check`: passed with no issues.
- Ran `.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run`: no changes detected.
- Ran `.\.venv\Scripts\python.exe -m pytest tests\test_feedback.py`: passed, 8 tests.
- Ran `.\.venv\Scripts\python.exe -m pytest`: passed, 41 tests.
- Ran `docker compose ps`: PostgreSQL and Redis were healthy.

## Notes

Feedback submission is scoped to the user who owns the chat session. Feedback review is scoped to workspace owners/admins.

The review queue is intentionally simple for the MVP. Milestone 9 will add evaluation datasets and metrics, which can later be connected to this feedback data.

## UI Polish Follow-Up

- Reworked chat feedback controls into compact `Helpful` and `Needs review` pill actions.
- Added saved-feedback state text and clarified that feedback is visible to workspace reviewers.
- Reworked the feedback review page into a more scannable triage queue with chips, clipped answer cards, comments, and admin-scope helper text.
- Re-ran `.\.venv\Scripts\python.exe manage.py check`: passed.
- Re-ran `.\.venv\Scripts\python.exe -m pytest tests\test_feedback.py`: passed, 8 tests.
- Re-ran `.\.venv\Scripts\python.exe -m pytest`: passed, 41 tests.
- Ran a Django client render smoke check for the chat page and feedback review page: both returned 200 and included the expected UI text.
