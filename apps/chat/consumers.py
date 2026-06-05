import asyncio
import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.exceptions import PermissionDenied

from apps.chat.models import ChatSession
from apps.chat.services import ask_question


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.session_id = self.scope["url_route"]["kwargs"]["session_id"]
        self.user = self.scope.get("user")

        if not self.user or not self.user.is_authenticated:
            await self.close(code=4401)
            return

        has_access = await self.user_can_access_session()
        if not has_access:
            await self.close(code=4403)
            return

        await self.accept()

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return

        try:
            payload = json.loads(text_data)
            question = payload.get("question", "").strip()
        except json.JSONDecodeError:
            await self.send_json({"type": "error", "message": "Invalid chat payload."})
            return

        if not question:
            await self.send_json({"type": "error", "message": "Enter a question."})
            return

        await self.send_json({"type": "status", "message": "Retrieving sources..."})

        try:
            response = await self.answer_question(question)
        except PermissionDenied as exc:
            await self.send_json({"type": "error", "message": str(exc)})
            return
        except Exception:
            await self.send_json({"type": "error", "message": "Unable to generate an answer."})
            return

        await self.send_json(
            {
                "type": "user_message",
                "content": question,
            }
        )
        await self.send_json({"type": "status", "message": "Writing answer..."})
        await self.stream_text(response["content"])
        await self.send_json(
            {
                "type": "complete",
                "message_id": response["message_id"],
                "content": response["content"],
                "citations": response["citations"],
            }
        )

    async def send_json(self, payload: dict):
        await self.send(text_data=json.dumps(payload))

    async def stream_text(self, text: str):
        words = text.split(" ")
        for index, word in enumerate(words):
            suffix = "" if index == len(words) - 1 else " "
            await self.send_json({"type": "delta", "content": word + suffix})
            await asyncio.sleep(0.01)

    @database_sync_to_async
    def user_can_access_session(self) -> bool:
        return ChatSession.objects.filter(pk=self.session_id, user=self.user).exists()

    @database_sync_to_async
    def answer_question(self, question: str) -> dict:
        session = ChatSession.objects.select_related("workspace", "user").get(
            pk=self.session_id,
            user=self.user,
        )
        assistant_message = ask_question(session=session, question=question)
        citations = [
            {
                "document": citation.document.title,
                "page_number": citation.page_number,
                "score": citation.score,
                "quote": citation.quote,
                "source_url": citation.document.get_absolute_url(),
            }
            for citation in assistant_message.citations.select_related("document", "chunk")
        ]
        return {
            "message_id": assistant_message.id,
            "content": assistant_message.content,
            "citations": citations,
        }
