import re

from django import template
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

from services.text_excerpts import plural_tolerant_pattern, query_terms

register = template.Library()


@register.filter(needs_autoescape=True)
def highlight_query(value, query, autoescape=True):
    text = "" if value is None else str(value)
    escaped_text = conditional_escape(text) if autoescape else text
    terms = query_terms(query or "")
    if not terms:
        return escaped_text

    pattern = re.compile(
        r"\b(" + "|".join(plural_tolerant_pattern(term) for term in terms) + r")\b",
        flags=re.IGNORECASE,
    )
    highlighted = pattern.sub(r"<mark>\1</mark>", escaped_text)
    return mark_safe(highlighted)
