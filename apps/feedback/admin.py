from django.contrib import admin

from apps.feedback.models import AnswerFeedback


@admin.register(AnswerFeedback)
class AnswerFeedbackAdmin(admin.ModelAdmin):
    list_display = ["message", "user", "rating", "failure_tag", "reviewed", "created_at"]
    list_filter = ["rating", "failure_tag", "reviewed", "created_at"]
    search_fields = ["message__content", "comment", "user__username"]
    autocomplete_fields = ["message", "user"]
    readonly_fields = ["created_at"]
