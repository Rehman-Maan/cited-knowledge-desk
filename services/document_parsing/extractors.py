from dataclasses import dataclass
from pathlib import Path

from docx import Document as DocxDocument
from pypdf import PdfReader


@dataclass(frozen=True)
class ExtractedPage:
    text: str
    page_number: int | None = None
    source_metadata: dict | None = None


def extract_document_pages(file_path: str | Path, file_type: str) -> list[ExtractedPage]:
    normalized_type = file_type.lower().lstrip(".")
    path = Path(file_path)

    if normalized_type == "pdf":
        return extract_pdf_pages(path)
    if normalized_type in {"md", "txt"}:
        return extract_text_pages(path)
    if normalized_type == "docx":
        return extract_docx_pages(path)

    raise ValueError(f"Unsupported document type: {file_type}")


def extract_pdf_pages(path: Path) -> list[ExtractedPage]:
    reader = PdfReader(str(path))
    pages = []

    for index, page in enumerate(reader.pages, start=1):
        text = normalize_text(page.extract_text() or "")
        if text:
            pages.append(
                ExtractedPage(
                    text=text,
                    page_number=index,
                    source_metadata={"source_page": index},
                )
            )

    return pages


def extract_text_pages(path: Path) -> list[ExtractedPage]:
    text = path.read_text(encoding="utf-8", errors="replace")
    normalized = normalize_text(text)
    return [ExtractedPage(text=normalized, source_metadata={"source_file": path.name})] if normalized else []


def extract_docx_pages(path: Path) -> list[ExtractedPage]:
    document = DocxDocument(str(path))
    text = "\n".join(paragraph.text for paragraph in document.paragraphs)
    normalized = normalize_text(text)
    return [ExtractedPage(text=normalized, source_metadata={"source_file": path.name})] if normalized else []


def normalize_text(text: str) -> str:
    lines = [" ".join(line.split()) for line in text.replace("\x00", "").splitlines()]
    compact_lines = [line for line in lines if line]
    return "\n".join(compact_lines).strip()
