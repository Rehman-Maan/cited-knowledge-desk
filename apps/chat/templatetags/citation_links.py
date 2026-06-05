import re

from django import template
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

from services.citation_builder.parser import (
    CITATION_GROUP_PATTERN,
    LABEL_PATTERN,
    build_citation_label,
)

register = template.Library()


@register.filter
def strip_text(value):
    return "" if value is None else str(value).strip()


@register.filter(needs_autoescape=True)
def citation_links(value, citations, autoescape=True):
    text = "" if value is None else str(value).strip()
    escaped_text = conditional_escape(text) if autoescape else text
    citation_map = {
        build_citation_label(citation.chunk): citation.pk
        for citation in citations
        if citation.chunk_id
    }
    if not citation_map:
        return escaped_text

    def build_link(label: str) -> str:
        bracketed_label = f"[{label}]"
        citation_id = citation_map.get(bracketed_label)
        if citation_id is None:
            return bracketed_label
        return (
            f'<a class="inline-citation" href="#citation-{citation_id}" '
            f'data-citation-target="citation-{citation_id}">{bracketed_label}</a>'
        )

    def replace(match: re.Match) -> str:
        body = match.group("body")
        links = []
        for label_match in LABEL_PATTERN.finditer(body):
            label = label_match.group(0)
            links.append(build_link(label))
        if not links:
            return match.group(0)
        return " ".join(links)

    return mark_safe(CITATION_GROUP_PATTERN.sub(replace, escaped_text))
