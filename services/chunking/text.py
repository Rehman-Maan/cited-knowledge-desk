from dataclasses import dataclass, field

from services.document_parsing.extractors import ExtractedPage


@dataclass(frozen=True)
class TextChunk:
    content: str
    token_count: int
    page_number: int | None = None
    section_title: str = ""
    source_metadata: dict = field(default_factory=dict)


def chunk_pages(
    pages: list[ExtractedPage],
    *,
    target_tokens: int,
    overlap_tokens: int,
) -> list[TextChunk]:
    chunks: list[TextChunk] = []

    for page in pages:
        words = page.text.split()
        if not words:
            continue

        start = 0
        while start < len(words):
            end = min(start + target_tokens, len(words))
            chunk_words = words[start:end]
            content = " ".join(chunk_words).strip()
            if content:
                chunks.append(
                    TextChunk(
                        content=content,
                        token_count=len(chunk_words),
                        page_number=page.page_number,
                        section_title=guess_section_title(page.text),
                        source_metadata={
                            **(page.source_metadata or {}),
                            "word_start": start,
                            "word_end": end,
                        },
                    )
                )

            if end >= len(words):
                break

            start = max(end - overlap_tokens, start + 1)

    return chunks


def guess_section_title(text: str) -> str:
    for line in text.splitlines():
        candidate = line.strip().lstrip("#").strip()
        if candidate:
            return candidate[:240]
    return ""
