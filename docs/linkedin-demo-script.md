# LinkedIn Demo Script

## Short Post

I built Cited Knowledge Desk, a Django RAG workspace for asking questions over uploaded documents with source-backed answers.

The goal was not just to make a chatbot. The goal was to make answers reviewable:

- Upload documents into a workspace
- Ingest and chunk source files in the background
- Retrieve relevant chunks with pgvector
- Ask questions in a streaming chat UI
- Show citation cards with source, page, match score, and highlighted excerpt
- Collect answer feedback
- Run gold-question evaluations for recall, citation precision, faithfulness, relevance, abstention, and latency

Tech stack:
Django, Channels, Celery, Redis, PostgreSQL/pgvector, Docker, OpenAI-compatible LLM and embedding providers, pytest, Playwright, and GitHub Actions.

Repo:
https://github.com/Rehman-Maan/cited-knowledge-desk

## Demo Flow

1. Open the dashboard and show the workspace metrics.
2. Open the document library and show uploaded source files.
3. Open a chat session and ask a source-specific question.
4. Click "View citations" and show the citation card in the right panel.
5. Show the page number, match score, highlighted excerpt, and source link.
6. Submit thumbs-up or thumbs-down feedback.
7. Open the evaluation page and show aggregate metrics.
8. Mention that GitHub Actions runs linting, tests, migration checks, Docker build, and Trivy scanning.

## One-Minute Voiceover

"This is Cited Knowledge Desk, a Django RAG project I built to make document chat more trustworthy. Users can upload documents into a workspace, the background worker extracts and chunks the content, and the app stores embeddings in PostgreSQL with pgvector.

When a user asks a question, the chat retrieves relevant chunks, generates a grounded answer, and attaches citations that point back to the source document, page, match score, and excerpt. I also added feedback review and a gold-question evaluation harness so the system can be tested beyond a manual demo.

The stack is Django, Channels, Celery, Redis, PostgreSQL/pgvector, Docker, OpenAI-compatible providers, pytest, Playwright, and GitHub Actions."

## Screenshot Checklist

- Dashboard
- Document library
- Chat with right-side citation card
- Mobile chat
- Evaluation dashboard
