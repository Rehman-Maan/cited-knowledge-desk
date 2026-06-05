import re

WORD_PATTERN = re.compile(r"[A-Za-z0-9]+")


def query_terms(query: str) -> list[str]:
    terms = []
    for term in WORD_PATTERN.findall(query.lower()):
        if len(term) <= 1 and not term.isdigit():
            continue
        terms.append(term)
    return terms


def build_focused_excerpt(text: str, query: str, *, radius: int = 320) -> str:
    compact_text = normalize_inline_text(text)
    if not compact_text:
        return ""

    match = find_best_match(compact_text, query)
    if match is None:
        return trim_excerpt(compact_text, 0, min(len(compact_text), radius * 2), len(compact_text))

    start = max(0, match.start() - radius)
    end = min(len(compact_text), match.end() + radius)
    return trim_excerpt(compact_text, start, end, len(compact_text))


def normalize_inline_text(text: str) -> str:
    return " ".join(text.split())


def find_best_match(text: str, query: str):
    terms = query_terms(query)
    if not terms:
        return None

    phrase_match = find_phrase_match(text, terms)
    if phrase_match:
        return phrase_match

    for term in terms:
        match = find_term_match(text, term)
        if match:
            return match

    return None


def find_phrase_match(text: str, terms: list[str]):
    if len(terms) < 2:
        return None

    pattern = r"\b" + r"[\W_]+".join(plural_tolerant_pattern(term) for term in terms) + r"\b"
    return re.search(pattern, text, flags=re.IGNORECASE)


def find_term_match(text: str, term: str):
    pattern = r"\b" + plural_tolerant_pattern(term) + r"\b"
    return re.search(pattern, text, flags=re.IGNORECASE)


def plural_tolerant_pattern(term: str) -> str:
    escaped = re.escape(term)
    if term.isdigit():
        return escaped
    if term.endswith("s") and len(term) > 3:
        return re.escape(term[:-1]) + "(?:s|d)?"
    return escaped + "s?"


def trim_excerpt(text: str, start: int, end: int, total_length: int) -> str:
    while start > 0 and start < total_length and not text[start].isspace():
        start += 1
    while end < total_length and end > 0 and not text[end - 1].isspace():
        end -= 1

    excerpt = text[start:end].strip()
    if start > 0:
        excerpt = "...\n" + excerpt
    if end < total_length:
        excerpt = excerpt + "\n..."
    return excerpt
