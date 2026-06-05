from django.contrib import admin

from apps.documents.models import Document, DocumentChunk


class DocumentChunkInline(admin.TabularInline):
    model = DocumentChunk
    extra = 0
    readonly_fields = ["chunk_index", "token_count", "page_number", "section_title", "created_at"]
    fields = ["chunk_index", "token_count", "page_number", "section_title", "created_at"]
    can_delete = False


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "workspace",
        "status",
        "file_type",
        "uploaded_by",
        "chunk_total",
        "created_at",
    ]
    list_filter = ["status", "file_type", "created_at"]
    search_fields = ["title", "workspace__name", "uploaded_by__username"]
    autocomplete_fields = ["workspace", "uploaded_by"]
    readonly_fields = ["created_at", "updated_at"]
    inlines = [DocumentChunkInline]

    def chunk_total(self, obj):
        return obj.chunks.count()


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ["document", "workspace", "chunk_index", "token_count", "page_number", "created_at"]
    list_filter = ["created_at", "page_number"]
    search_fields = ["document__title", "content", "section_title"]
    autocomplete_fields = ["document", "workspace"]
    readonly_fields = ["created_at"]
