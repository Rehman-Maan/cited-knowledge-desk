import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command

from apps.chat.models import Citation
from apps.chat.services import create_chat_session, create_citations_for_message
from apps.documents.models import Document, DocumentChunk
from apps.workspaces.models import Workspace
from services.citation_builder.parser import build_citation_label
from services.retrieval.vector_search import RetrievalResult, embed_chunks


@pytest.mark.django_db
def test_chat_citation_quote_is_compact_and_focused():
    user = get_user_model().objects.create_user(username="compact-citation", password="test-pass")
    workspace = Workspace.objects.get(created_by=user)
    document = Document.objects.create(
        workspace=workspace,
        uploaded_by=user,
        title="Quiz",
        file=SimpleUploadedFile("quiz.md", b"# Quiz"),
        file_type="md",
        status=Document.Status.READY,
    )
    chunk = DocumentChunk.objects.create(
        workspace=workspace,
        document=document,
        chunk_index=0,
        content=" ".join(
            [
                *[f"before{i}" for i in range(100)],
                "If MANGO is coded as OCPIQ, APPLE is coded as CRRNG.",
                *[f"after{i}" for i in range(100)],
            ]
        ),
        token_count=220,
    )
    session = create_chat_session(workspace=workspace, user=user)
    message = session.messages.create(role="assistant", content=f"APPLE is CRRNG. {build_citation_label(chunk)}")

    create_citations_for_message(
        assistant_message=message,
        answer_text=message.content,
        retrieval_results=[RetrievalResult(chunk=chunk, score=0.9)],
        question="MANGO OCPIQ APPLE",
    )
    citation = Citation.objects.get(assistant_message=message)

    assert "MANGO is coded as OCPIQ" in citation.quote
    assert len(citation.quote) < 260
    assert citation.quote.startswith("...\n")
    assert citation.quote.endswith("\n...")


@pytest.mark.django_db
def test_saved_chat_renders_collapsed_clickable_citations(client):
    user = get_user_model().objects.create_user(username="linked-citation", password="test-pass")
    workspace = Workspace.objects.get(created_by=user)
    document = Document.objects.create(
        workspace=workspace,
        uploaded_by=user,
        title="Quiz",
        file=SimpleUploadedFile("quiz.md", b"# Quiz"),
        file_type="md",
        status=Document.Status.READY,
    )
    chunk = DocumentChunk.objects.create(
        workspace=workspace,
        document=document,
        chunk_index=0,
        content="If MANGO is coded as OCPIQ, APPLE is coded as CRRNG.",
        token_count=10,
    )
    session = create_chat_session(workspace=workspace, user=user)
    message = session.messages.create(role="assistant", content=f"APPLE is CRRNG. {build_citation_label(chunk)}")
    create_citations_for_message(
        assistant_message=message,
        answer_text=message.content,
        retrieval_results=[RetrievalResult(chunk=chunk, score=0.9)],
        question="MANGO OCPIQ APPLE",
    )

    client.force_login(user)
    response = client.get(session.get_absolute_url())

    assert response.status_code == 200
    assert b"View citations (1)" in response.content
    assert b'data-citation-target="citation-' in response.content
    assert b'class="inline-citation"' in response.content
    assert b"<details class=\"citation-disclosure\">" not in response.content
    assert b"<template id=\"message-citations-" in response.content


@pytest.mark.django_db
def test_saved_chat_strips_message_whitespace(client):
    user = get_user_model().objects.create_user(username="trimmed-chat", password="test-pass")
    workspace = Workspace.objects.get(created_by=user)
    session = create_chat_session(workspace=workspace, user=user)
    session.messages.create(role="user", content="\n\n  TRANSIENT can we have the negative of it?  \n\n")

    client.force_login(user)
    response = client.get(session.get_absolute_url())
    html = response.content.decode()

    assert response.status_code == 200
    assert "\n\n  TRANSIENT can we have the negative of it?" not in html
    assert "TRANSIENT can we have the negative of it?" in html


@pytest.mark.django_db
def test_grouped_citation_labels_create_and_render_clickable_links(client):
    user = get_user_model().objects.create_user(username="grouped-citation", password="test-pass")
    workspace = Workspace.objects.get(created_by=user)
    document = Document.objects.create(
        workspace=workspace,
        uploaded_by=user,
        title="Quiz",
        file=SimpleUploadedFile("quiz.md", b"# Quiz"),
        file_type="md",
        status=Document.Status.READY,
    )
    first_chunk = DocumentChunk.objects.create(
        workspace=workspace,
        document=document,
        chunk_index=0,
        content="MANGO is coded as OCPIQ, so APPLE is CRRNG.",
        token_count=10,
    )
    second_chunk = DocumentChunk.objects.create(
        workspace=workspace,
        document=document,
        chunk_index=1,
        content="Nitrogen is the most abundant gas in Earth's atmosphere.",
        token_count=9,
    )
    session = create_chat_session(workspace=workspace, user=user)
    answer = f"APPLE is CRRNG and the gas is Nitrogen. [D{first_chunk.document_id}-C{first_chunk.id}, D{second_chunk.document_id}-C{second_chunk.id}]"
    message = session.messages.create(role="assistant", content=answer)
    create_citations_for_message(
        assistant_message=message,
        answer_text=message.content,
        retrieval_results=[
            RetrievalResult(chunk=first_chunk, score=0.9),
            RetrievalResult(chunk=second_chunk, score=0.8),
        ],
        question="APPLE and atmosphere",
    )

    assert Citation.objects.filter(assistant_message=message).count() == 2

    client.force_login(user)
    response = client.get(session.get_absolute_url())

    assert response.status_code == 200
    assert response.content.count(b'class="inline-citation"') == 2
    assert b"View citations (2)" in response.content


@pytest.mark.django_db
def test_repair_chat_citations_backfills_grouped_saved_answers(settings):
    settings.EMBEDDING_PROVIDER = "local"
    user = get_user_model().objects.create_user(username="repair-citation", password="test-pass")
    workspace = Workspace.objects.get(created_by=user)
    document = Document.objects.create(
        workspace=workspace,
        uploaded_by=user,
        title="Quiz",
        file=SimpleUploadedFile("quiz.md", b"# Quiz"),
        file_type="md",
        status=Document.Status.READY,
    )
    chunk = DocumentChunk.objects.create(
        workspace=workspace,
        document=document,
        chunk_index=0,
        content="Nitrogen is the most abundant gas in Earth's atmosphere.",
        token_count=9,
    )
    embed_chunks([chunk], model_name="text-embedding-3-small")
    session = create_chat_session(workspace=workspace, user=user)
    session.messages.create(role="user", content="oxygen is most abundant?")
    message = session.messages.create(
        role="assistant",
        content=f"No. Nitrogen is most abundant. [D{document.id}-C{chunk.id}]",
    )

    call_command("repair_chat_citations")

    citation = Citation.objects.get(assistant_message=message)
    assert citation.chunk == chunk
    assert "Nitrogen" in citation.quote
    assert citation.score > 0
