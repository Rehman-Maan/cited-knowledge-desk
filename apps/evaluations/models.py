from django.conf import settings
from django.db import models
from django.urls import reverse

from apps.workspaces.models import Workspace


class EvaluationRun(models.Model):
    class Status(models.TextChoices):
        RUNNING = "running", "Running"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    workspace = models.ForeignKey(
        Workspace,
        on_delete=models.CASCADE,
        related_name="evaluation_runs",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="evaluation_runs",
    )
    name = models.CharField(max_length=180)
    dataset_name = models.CharField(max_length=180)
    model_name = models.CharField(max_length=120, blank=True)
    retrieval_top_k = models.PositiveIntegerField(default=8)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.RUNNING)
    average_retrieval_recall = models.FloatField(default=0.0)
    average_citation_precision = models.FloatField(default=0.0)
    average_faithfulness = models.FloatField(default=0.0)
    average_answer_relevance = models.FloatField(default=0.0)
    abstention_accuracy = models.FloatField(default=0.0)
    average_latency_ms = models.PositiveIntegerField(default=0)
    p50_latency_ms = models.PositiveIntegerField(default=0)
    p95_latency_ms = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["workspace", "-created_at"]),
            models.Index(fields=["status", "-created_at"]),
        ]

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        return reverse("evaluations:detail", kwargs={"pk": self.pk})


class EvaluationResult(models.Model):
    run = models.ForeignKey(
        EvaluationRun,
        on_delete=models.CASCADE,
        related_name="results",
    )
    question = models.TextField()
    expected_answer = models.TextField(blank=True)
    answer = models.TextField(blank=True)
    expected_sources = models.JSONField(default=list, blank=True)
    retrieved_sources = models.JSONField(default=list, blank=True)
    cited_sources = models.JSONField(default=list, blank=True)
    should_abstain = models.BooleanField(default=False)
    retrieval_recall = models.FloatField(default=0.0)
    citation_precision = models.FloatField(default=0.0)
    faithfulness = models.FloatField(default=0.0)
    answer_relevance = models.FloatField(default=0.0)
    abstention_correct = models.BooleanField(default=False)
    latency_ms = models.PositiveIntegerField(default=0)
    model_name = models.CharField(max_length=120, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]
        indexes = [
            models.Index(fields=["run", "retrieval_recall"]),
            models.Index(fields=["run", "faithfulness"]),
        ]

    def __str__(self) -> str:
        return f"{self.run}: {self.question[:60]}"
