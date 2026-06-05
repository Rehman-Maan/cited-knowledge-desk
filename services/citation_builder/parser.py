import re

from apps.documents.models import DocumentChunk

LABEL_PATTERN = re.compile(r"D(?P<document_id>\d+)-C(?P<chunk_id>\d+)")
CITATION_PATTERN = re.compile(r"\[D(?P<document_id>\d+)-C(?P<chunk_id>\d+)\]")
CITATION_GROUP_PATTERN = re.compile(
    r"\[(?P<body>D\d+-C\d+(?:\s*,\s*D\d+-C\d+)*)\]",
)


def build_citation_label(chunk: DocumentChunk) -> str:
    return f"[D{chunk.document_id}-C{chunk.id}]"


def parse_citation_labels(text: str) -> set[tuple[int, int]]:
    pairs = set()
    for group_match in CITATION_GROUP_PATTERN.finditer(text):
        for label_match in LABEL_PATTERN.finditer(group_match.group("body")):
            pairs.add(
                (
                    int(label_match.group("document_id")),
                    int(label_match.group("chunk_id")),
                )
            )
    return pairs
