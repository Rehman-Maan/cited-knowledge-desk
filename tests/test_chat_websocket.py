import pytest
from asgiref.sync import sync_to_async
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.chat.models import ChatMessage
from apps.chat.routing import websocket_urlpatterns
from apps.chat.services import create_chat_session
from apps.documents.models import Document, DocumentChunk
from apps.workspaces.models import Workspace
from services.retrieval.vector_search import embed_chunks


def create_ready_document(user, workspace, content):
    document = Document.objects.create(
        workspace=workspace,
        uploaded_by=user,
        title="Streaming Handbook",
        file=SimpleUploadedFile("streaming.md", b"# Streaming"),
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
    return document, chunk


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_chat_websocket_streams_answer(settings):
    settings.EMBEDDING_PROVIDER = "local"
    settings.LLM_PROVIDER = "local"
    user = await get_user_model().objects.acreate(username="socket-user")
    user.set_password("test-pass")
    await user.asave()
    workspace = await Workspace.objects.aget(created_by=user)
    await Document.objects.acreate(
        workspace=workspace,
        uploaded_by=user,
        title="Socket Source",
        file=SimpleUploadedFile("socket.md", b"# Socket"),
        file_type="md",
        status=Document.Status.READY,
    )
    document = await Document.objects.aget(title="Socket Source")
    chunk = await DocumentChunk.objects.acreate(
        workspace=workspace,
        document=document,
        chunk_index=0,
        content="Zenith means peak in the practice quiz.",
        token_count=8,
    )
    await sync_embed_chunk(chunk)
    session = await sync_create_session(workspace, user)
    communicator = WebsocketCommunicator(
        URLRouter(websocket_urlpatterns),
        f"/ws/chat/{session.pk}/",
    )
    communicator.scope["user"] = user

    connected, _ = await communicator.connect()
    assert connected

    await communicator.send_json_to({"question": "What does zenith mean?"})
    message_types = []
    complete_payload = None

    for _ in range(80):
        payload = await communicator.receive_json_from(timeout=5)
        message_types.append(payload["type"])
        if payload["type"] == "complete":
            complete_payload = payload
            break

    await communicator.disconnect()

    assert "status" in message_types
    assert "delta" in message_types
    assert complete_payload is not None
    assert complete_payload["citations"]
    assert await ChatMessage.objects.filter(session=session, role=ChatMessage.Role.ASSISTANT).aexists()
    await sync_close_connections()


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_chat_websocket_rejects_anonymous_user():
    session_id = 999
    communicator = WebsocketCommunicator(
        URLRouter(websocket_urlpatterns),
        f"/ws/chat/{session_id}/",
    )

    connected, _ = await communicator.connect()

    assert not connected
    await sync_close_connections()


@sync_to_async
def sync_embed_chunk(chunk):
    embed_chunks([chunk], model_name="text-embedding-3-small")


@sync_to_async
def sync_create_session(workspace, user):
    return create_chat_session(workspace=workspace, user=user)


@sync_to_async
def sync_close_connections():
    from django.db import connections

    connections.close_all()
