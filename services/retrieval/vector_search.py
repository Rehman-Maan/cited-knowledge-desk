from dataclasses import dataclass

from pgvector.django import CosineDistance

from apps.documents.models import DocumentChunk
from apps.workspaces.models import Workspace
from services.llm_gateway.embeddings import embed_texts
from services.text_excerpts import build_focused_excerpt


@dataclass(frozen=True)
class RetrievalResult:
    chunk: DocumentChunk
    score: float
    excerpt: str = ""


def embed_chunks(chunks, *, model_name: str) -> int:
    chunk_list = list(chunks)
    if not chunk_list:
        return 0

    vectors = embed_texts([chunk.content for chunk in chunk_list])
    for chunk, vector in zip(chunk_list, vectors, strict=True):
        chunk.embedding = vector
        chunk.embedding_model = model_name

    DocumentChunk.objects.bulk_update(chunk_list, ["embedding", "embedding_model"])
    return len(chunk_list)


def search_similar_chunks(
    *,
    workspace: Workspace,
    query: str,
    top_k: int = 8,
    model_name: str = "",
) -> list[RetrievalResult]:
    query_embedding = embed_texts([query])[0]
    queryset = DocumentChunk.objects.filter(
        workspace=workspace,
        embedding__isnull=False,
    ).select_related("document", "workspace")

    if model_name:
        queryset = queryset.filter(embedding_model=model_name)

    rows = queryset.annotate(distance=CosineDistance("embedding", query_embedding)).order_by(
        "distance", "id"
    )[:top_k]

    return [
        RetrievalResult(
            chunk=row,
            score=max(0.0, 1.0 - float(row.distance)),
            excerpt=build_focused_excerpt(row.content, query),
        )
        for row in rows
    ]
