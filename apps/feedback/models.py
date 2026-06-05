from django.conf import settings
from django.db import models

from apps.chat.models import ChatMessage


class AnswerFeedback(models.Model):
    class Rating(models.TextChoices):
        UP = "up", "Thumbs up"
        DOWN = "down", "Thumbs down"

    class FailureTag(models.TextChoices):
        WRONG_ANSWER = "wrong_answer", "Wrong answer"
        MISSING_CITATION = "missing_citation", "Missing citation"
        WEAK_CITATION = "weak_citation", "Weak citation"
        HALLUCINATION = "hallucination", "Hallucination"
        OUTDATED_SOURCE = "outdated_source", "Outdated source"
        UNCLEAR_ANSWER = "unclear_answer", "Unclear answer"
        ACCESS_ISSUE = "access_issue", "Access issue"
        OTHER = "other", "Other"

    message = models.ForeignKey(
        ChatMessage,
        on_delete=models.CASCADE,
        related_name="feedback",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="answer_feedback",
    )
    rating = models.CharField(max_length=10, choices=Rating.choices)
    comment = models.TextField(blank=True)
    failure_tag = models.CharField(max_length=40, choices=FailureTag.choices, blank=True)
    reviewed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["message", "user"],
                name="unique_answer_feedback_per_user",
            ),
        ]
        indexes = [
            models.Index(fields=["rating", "created_at"]),
            models.Index(fields=["reviewed", "created_at"]),
            models.Index(fields=["failure_tag", "created_at"]),
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.get_rating_display()} for message {self.message_id}"
