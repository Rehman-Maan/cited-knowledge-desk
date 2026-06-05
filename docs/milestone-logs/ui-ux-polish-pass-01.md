# UI/UX Polish Pass 01

## Status

Complete. This polish pass focused on making the product feel more professional, with the most attention on the chat experience.

## What Changed

- Refined the global visual system in `templates/base.html`.
- Reworked the app color palette toward a quieter professional interface:
  - neutral paper background
  - crisp white surfaces
  - teal primary actions
  - indigo secondary signal color
  - clearer green, amber, and red status colors
- Improved top navigation spacing, brand treatment, buttons, panels, tables, forms, empty states, and status pills.
- Added cleaner focus states for inputs, textareas, and selects.
- Removed the decorative radial background treatment so the UI feels more like a serious workspace product.
- Reworked `templates/chat/session_detail.html`:
  - tighter three-column chat layout
  - compact chat history
  - dedicated chat thread surface
  - smaller, cleaner user and assistant message cards
  - fixed preserved template whitespace inside messages
  - less bulky citation cards and citation excerpts
  - improved citation rail empty state
  - tighter composer spacing
  - cleaner feedback thumb controls
  - better mobile stacking
- Replaced the wrapped mobile navigation with a compact hamburger menu in `templates/base.html`.
- Kept the desktop navigation visible while moving authenticated mobile links, username, and logout into the mobile menu.
- Changed saved chat citations so `View citations` and inline citation clicks load citation cards into the right-side citation rail instead of expanding bulky cards under the answer.
- Fixed feedback popovers so thumbs up/down comment forms open inside the chat surface without being clipped.
- Expanded citation parsing/rendering to support grouped model output such as `[D6-C106, D5-C66]`.
- Added `repair_chat_citations` to backfill missing citation rows for saved answers that already contain citation labels.
- Extended `repair_chat_citations` with score refresh support, including a deterministic lexical fallback for old repaired citations when vector refresh is unavailable.
- Updated repaired local citations so the right rail can show match percentages instead of `Saved citation`.
- Added outside-click and Escape-key closing behavior for thumbs up/down feedback popovers while preserving any typed text.
- Added a mobile-friendly guest entry path from login/signup.
- Added guest mode with limited access to Dashboard, Documents/upload, and Chat.
- Hid restricted navigation items for guest users on desktop and mobile.
- Blocked guest access to Retrieval, Feedback Review, and Evaluations server-side.
- Hid answer feedback controls in guest chat sessions.
- Made mobile citation interactions scroll to the stacked citation panel.

## Visual QA

- Started the local server at `http://127.0.0.1:8000/`.
- Used a temporary local preview account to inspect:
  - dashboard
  - chat list
  - empty chat
  - populated chat with citations and feedback controls
  - mobile chat layout
  - mobile navigation closed and open states
- Tested the mobile guest signup CTA, guest dashboard, and guest hamburger menu.
- Ran `repair_chat_citations` locally after a dry run found 2 missing saved citations.
- Ran `repair_chat_citations --score-mode lexical` locally after a dry run found 2 old citations with missing scores.
- Removed the temporary preview account and screenshot files after QA.

## Verification

- `.\.venv\Scripts\python.exe manage.py check`
  - Passed.
- `.\.venv\Scripts\python.exe -m pytest tests\test_chat.py tests\test_chat_websocket.py tests\test_citation_excerpt.py tests\test_text_excerpts.py`
  - Passed with `12 passed`.
- `.\.venv\Scripts\python.exe -m pytest`
  - Passed with `51 passed, 1 skipped`.
- `.\.venv\Scripts\python.exe -m ruff check .`
  - Passed.
- `.\.venv\Scripts\python.exe manage.py repair_chat_citations --dry-run --score-mode lexical`
  - Passed with 0 missing citations and 0 score updates after repair.
- Guest access tests passed as part of the focused account/chat/feedback suite.

## Notes

- The browser plugin was unavailable in this session, so local Playwright with the installed Chromium executable was used for visual screenshots.
- Playwright's normal browser installer initially hit a local certificate verification issue, but the existing Chromium executable was usable for screenshots.
