import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.chat.models import ChatMessage, ChatSession, Citation
from apps.chat.services import ask_question, build_answer_prompt, create_chat_session
from apps.documents.models import Document, DocumentChunk
from apps.workspaces.models import Workspace
from services.citation_builder.parser import build_citation_label, parse_citation_labels
from services.retrieval.vector_search import embed_chunks


def create_ready_document(user, workspace, content):
    document = Document.objects.create(
        workspace=workspace,
        uploaded_by=user,
        title="Handbook",
        file=SimpleUploadedFile("handbook.md", b"# Handbook"),
        file_type="md",
        status=Document.Status.READY,
    )
    chunk = DocumentChunk.objects.create(
        workspace=workspace,
        document=document,
        chunk_index=0,
        content=content,
        token_count=len(content.split()),
    )
    embed_chunks([chunk], model_name="text-embedding-3-small")
    chunk.refresh_from_db()
    return document, chunk


@pytest.mark.django_db
def test_citation_label_parser_round_trip():
    user = get_user_model().objects.create_user(username="citation-owner", password="test-pass")
    workspace = Workspace.objects.get(created_by=user)
    _, chunk = create_ready_document(
        user,
        workspace,
        "Vacation policy gives employees annual leave.",
    )

    label = build_citation_label(chunk)

    assert parse_citation_labels(f"The policy says so {label}") == {
        (chunk.document_id, chunk.id)
    }


@pytest.mark.django_db
def test_citation_label_parser_accepts_grouped_labels():
    assert parse_citation_labels("Answer cites [D6-C106, D5-C66].") == {
        (6, 106),
        (5, 66),
    }


@pytest.mark.django_db
def test_build_answer_prompt_includes_source_labels(settings):
    settings.EMBEDDING_PROVIDER = "local"
    user = get_user_model().objects.create_user(username="prompt-owner", password="test-pass")
    workspace = Workspace.objects.get(created_by=user)
    _, chunk = create_ready_document(
        user,
        workspace,
        "Vacation policy gives employees annual leave.",
    )
    from services.retrieval.vector_search import search_similar_chunks

    results = search_similar_chunks(workspace=workspace, query="vacation leave", top_k=1)
    prompt = build_answer_prompt(question="What is vacation policy?", retrieval_results=results)

    assert build_citation_label(chunk) in prompt
    assert "Vacation policy" in prompt


@pytest.mark.django_db
def test_ask_question_persists_messages_and_citations(settings):
    settings.EMBEDDING_PROVIDER = "local"
    settings.LLM_PROVIDER = "local"
    user = get_user_model().objects.create_user(username="chat-owner", password="test-pass")
    workspace = Workspace.objects.get(created_by=user)
    create_ready_document(
        user,
        workspace,
        "Vacation policy gives employees annual leave.",
    )
    session = create_chat_session(workspace=workspace, user=user)

    assistant_message = ask_question(session=session, question="What is the vacation policy?")

    assert assistant_message.role == ChatMessage.Role.ASSISTANT
    assert session.messages.filter(role=ChatMessage.Role.USER).count() == 1
    assert session.messages.filter(role=ChatMessage.Role.ASSISTANT).count() == 1
    assert Citation.objects.filter(assistant_message=assistant_message).count() == 1
    session.refresh_from_db()
    assert session.title == "What is the vacation policy?"


@pytest.mark.django_db
def test_chat_home_requires_login(client):
    response = client.get(reverse("chat:home"))

    assert response.status_code == 302
    assert reverse("accounts:login") in response["Location"]


@pytest.mark.django_db
def test_chat_view_flow_creates_answer(client, settings):
    settings.EMBEDDING_PROVIDER = "local"
    settings.LLM_PROVIDER = "local"
    user = get_user_model().objects.create_user(username="chat-view", password="test-pass")
    workspace = Workspace.objects.get(created_by=user)
    create_ready_document(
        user,
        workspace,
        "The psychology quiz says zenith means peak.",
    )
    client.force_login(user)

    create_response = client.post(f"{reverse('chat:create-session')}?workspace={workspace.slug}")
    session = ChatSession.objects.get(user=user)
    ask_response = client.post(
        reverse("chat:ask", kwargs={"pk": session.pk}),
        {"question": "What does zenith mean?"},
    )

    assert create_response.status_code == 302
    assert ask_response.status_code == 302
    assert session.messages.filter(role=ChatMessage.Role.ASSISTANT).exists()
