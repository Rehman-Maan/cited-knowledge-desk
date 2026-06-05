from django.core.management.base import BaseCommand

from apps.chat.models import ChatMessage, Citation
from apps.documents.models import DocumentChunk
from services.citation_builder.parser import parse_citation_labels
from services.llm_gateway.embeddings import TOKEN_PATTERN
from services.retrieval.vector_search import search_similar_chunks
from services.text_excerpts import build_focused_excerpt


def lexical_match_score(query: str, content: str) -> float:
    query_tokens = set(TOKEN_PATTERN.findall(query.lower()))
    content_tokens = set(TOKEN_PATTERN.findall(content.lower()))
    if not query_tokens or not content_tokens:
        return 0.0

    overlap = query_tokens & content_tokens
    return min(1.0, len(overlap) / len(query_tokens))


class Command(BaseCommand):
    help = "Create missing citation rows for saved assistant messages that contain citation labels."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report missing citations without creating them.",
        )
        parser.add_argument(
            "--score-mode",
            choices=["auto", "vector", "lexical"],
            default="auto",
            help="How to refresh zero citation scores. Auto tries vector search, then lexical fallback.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        score_mode = options["score_mode"]
        scanned = 0
        created = 0
        updated = 0
        missing_chunks = 0

        messages = (
            ChatMessage.objects.filter(role=ChatMessage.Role.ASSISTANT)
            .select_related("session", "session__workspace")
            .prefetch_related("citations")
            .order_by("id")
        )

        for message in messages:
            cited_pairs = parse_citation_labels(message.content)
            if not cited_pairs:
                continue

            scanned += 1
            existing_pairs = {
                (citation.document_id, citation.chunk_id)
                for citation in message.citations.all()
            }
            missing_pairs = cited_pairs - existing_pairs

            previous_question = (
                ChatMessage.objects.filter(
                    session=message.session,
                    role=ChatMessage.Role.USER,
                    created_at__lt=message.created_at,
                )
                .order_by("-created_at")
                .first()
            )
            question = previous_question.content if previous_question else message.content
            score_by_pair = {}
            if score_mode in {"auto", "vector"}:
                try:
                    score_by_pair = {
                        (result.chunk.document_id, result.chunk.id): result.score
                        for result in search_similar_chunks(
                            workspace=message.session.workspace,
                            query=question,
                            top_k=50,
                        )
                    }
                except Exception as exc:
                    if score_mode == "vector":
                        raise
                    self.stdout.write(
                        self.style.WARNING(
                            f"Vector score refresh failed for message {message.id}: {exc}"
                        )
                    )

            for citation in message.citations.all():
                if citation.score > 0:
                    continue

                refreshed_score = score_by_pair.get((citation.document_id, citation.chunk_id))
                if refreshed_score is None:
                    refreshed_score = lexical_match_score(question, citation.chunk.content)
                if refreshed_score <= 0:
                    continue

                if not dry_run:
                    citation.score = refreshed_score
                    citation.save(update_fields=["score"])
                updated += 1

            for document_id, chunk_id in sorted(missing_pairs):
                chunk = (
                    DocumentChunk.objects.select_related("document")
                    .filter(
                        id=chunk_id,
                        document_id=document_id,
                        workspace=message.session.workspace,
                    )
                    .first()
                )
                if chunk is None:
                    missing_chunks += 1
                    continue

                if not dry_run:
                    Citation.objects.create(
                        assistant_message=message,
                        document=chunk.document,
                        chunk=chunk,
                        quote=build_focused_excerpt(chunk.content, question, radius=55),
                        page_number=chunk.page_number,
                        score=score_by_pair.get(
                            (document_id, chunk_id),
                            lexical_match_score(question, chunk.content),
                        ),
                    )
                created += 1

        action = "Would create" if dry_run else "Created"
        update_action = "would update" if dry_run else "updated"
        self.stdout.write(
            self.style.SUCCESS(
                f"{action} {created} missing citations and {update_action} {updated} scores "
                f"across {scanned} cited messages. "
                f"Missing chunks: {missing_chunks}."
            )
        )
