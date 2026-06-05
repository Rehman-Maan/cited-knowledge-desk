from django.contrib import admin

from apps.evaluations.models import EvaluationResult, EvaluationRun


class EvaluationResultInline(admin.TabularInline):
    model = EvaluationResult
    extra = 0
    readonly_fields = [
        "question",
        "retrieval_recall",
        "citation_precision",
        "faithfulness",
        "answer_relevance",
        "latency_ms",
    ]
    can_delete = False


@admin.register(EvaluationRun)
class EvaluationRunAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "workspace",
        "status",
        "average_retrieval_recall",
        "average_faithfulness",
        "average_latency_ms",
        "created_at",
    ]
    list_filter = ["status", "workspace", "dataset_name"]
    search_fields = ["name", "dataset_name", "workspace__name"]
    inlines = [EvaluationResultInline]


@admin.register(EvaluationResult)
class EvaluationResultAdmin(admin.ModelAdmin):
    list_display = [
        "run",
        "question",
        "retrieval_recall",
        "citation_precision",
        "faithfulness",
        "answer_relevance",
        "latency_ms",
    ]
    list_filter = ["run", "should_abstain", "abstention_correct"]
    search_fields = ["question", "answer", "expected_answer"]
