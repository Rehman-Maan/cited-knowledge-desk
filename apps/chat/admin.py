from django.contrib import admin

from apps.chat.models import ChatMessage, ChatSession, Citation


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    readonly_fields = ["role", "model_name", "latency_ms", "token_count", "created_at"]
    fields = ["role", "content", "model_name", "latency_ms", "token_count", "created_at"]


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ["title", "workspace", "user", "created_at", "updated_at"]
    list_filter = ["created_at", "updated_at"]
    search_fields = ["title", "workspace__name", "user__username"]
    autocomplete_fields = ["workspace", "user"]
    inlines = [ChatMessageInline]


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ["session", "role", "model_name", "latency_ms", "created_at"]
    list_filter = ["role", "model_name", "created_at"]
    search_fields = ["content", "session__title"]
    autocomplete_fields = ["session"]
    readonly_fields = ["created_at"]


@admin.register(Citation)
class CitationAdmin(admin.ModelAdmin):
    list_display = ["assistant_message", "document", "chunk", "page_number", "score", "created_at"]
    search_fields = ["quote", "document__title", "assistant_message__content"]
    autocomplete_fields = ["assistant_message", "document", "chunk"]
    readonly_fields = ["created_at"]
