from django.conf import settings
from django.db import models
from django.urls import reverse

from apps.documents.models import Document, DocumentChunk
from apps.workspaces.models import Workspace


class ChatSession(models.Model):
    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="chat_sessions",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_sessions",
    )
    title = models.CharField(max_length=180)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["workspace", "-updated_at"]),
            models.Index(fields=["user", "-updated_at"]),
        ]

    def __str__(self) -> str:
        return self.title

    def get_absolute_url(self) -> str:
        return reverse("chat:detail", kwargs={"pk": self.pk})


class ChatMessage(models.Model):
    class Role(models.TextChoices):
        USER = "user", "User"
        ASSISTANT = "assistant", "Assistant"
        SYSTEM = "system", "System"

    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    role = models.CharField(max_length=20, choices=Role.choices)
    content = models.TextField()
    model_name = models.CharField(max_length=120, blank=True)
    latency_ms = models.PositiveIntegerField(null=True, blank=True)
    token_count = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["session", "created_at"]),
            models.Index(fields=["role", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.role}: {self.content[:60]}"


class Citation(models.Model):
    assistant_message = models.ForeignKey(
        ChatMessage,
        on_delete=models.CASCADE,
        related_name="citations",
    )
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="citations",
    )
    chunk = models.ForeignKey(
        DocumentChunk,
        on_delete=models.CASCADE,
        related_name="citations",
    )
    quote = models.TextField()
    page_number = models.PositiveIntegerField(null=True, blank=True)
    score = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["assistant_message", "created_at"]),
            models.Index(fields=["document", "chunk"]),
        ]

    def __str__(self) -> str:
        return f"{self.document} citation for message {self.assistant_message_id}"
