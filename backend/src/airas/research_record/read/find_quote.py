import re
import unicodedata


def _normalize(text: str) -> str:
    # Ligatures, soft hyphens and line breaks are the extractor's, not the author's.
    return " ".join(unicodedata.normalize("NFKC", text).replace("­", "").split())


def find_quote(fulltext: str, quote: str) -> tuple[str, int, int] | None:
    """(normalized fulltext, start, end) of the quote's first occurrence."""
    needle = _normalize(quote)
    if not needle:
        return None
    # A word the extractor broke with a hyphen at the line end ("gen-\ner-
    # alization") is matched joined as well as as written.
    for text in (fulltext, re.sub(r"-\n(?=\w)", "", fulltext)):
        hay = _normalize(text)
        if (at := hay.find(needle)) != -1:
            return hay, at, at + len(needle)
    return None
