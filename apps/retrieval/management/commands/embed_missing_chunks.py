from django.conf import settings
from django.core.management.base import BaseCommand

from apps.documents.models import DocumentChunk
from services.retrieval.vector_search import embed_chunks


class Command(BaseCommand):
    help = "Embed document chunks that do not yet have vectors."

    def add_arguments(self, parser):
        parser.add_argument("--batch-size", type=int, default=100)
        parser.add_argument(
            "--force",
            action="store_true",
            help="Re-embed all chunks, including chunks that already have embeddings.",
        )

    def handle(self, *args, **options):
        batch_size = options["batch_size"]
        force = options["force"]
        total = 0
        last_seen_id = 0

        while True:
            queryset = DocumentChunk.objects.filter(id__gt=last_seen_id)
            if not force:
                queryset = queryset.filter(embedding__isnull=True)

            chunks = list(queryset.order_by("id")[:batch_size])
            if not chunks:
                break

            total += embed_chunks(chunks, model_name=settings.EMBEDDING_MODEL)
            last_seen_id = chunks[-1].id

        self.stdout.write(self.style.SUCCESS(f"Embedded {total} chunks."))
