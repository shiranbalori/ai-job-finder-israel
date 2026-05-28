"""Clean skill labels extracted from job HTML or noisy text."""

from __future__ import annotations

import html
import re

_TAG_RE = re.compile(r"<[^>]*>", re.IGNORECASE)
_WS_RE = re.compile(r"\s+")
_CORP_SUFFIXES = frozenset({"ltd", "inc", "corp", "llc", "co", "gmbh", "plc"})


def clean_skill_label(value: str) -> str:
    """Strip HTML tags and normalize to readable plain text."""
    raw = html.unescape(str(value or ""))
    text = _TAG_RE.sub(" ", raw)
    text = _WS_RE.sub(" ", text).strip()
    text = re.sub(r"^At\s+", "", text, flags=re.IGNORECASE)

    words = text.split()
    if not words:
        return ""

    if len(words) > 2:
        text = words[0].rstrip(".,;:")
    elif len(words) == 2:
        second = words[1].rstrip(".,;:").lower()
        if second in _CORP_SUFFIXES or len(text) > 28:
            text = words[0].rstrip(".,;:")

    return text.rstrip(".,;:…")


def is_valid_skill_label(value: str) -> bool:
    """Reject HTML fragments and sentence-like noise."""
    if not value:
        return False
    if len(value) > 48:
        return False
    if "<" in value or ">" in value:
        return False
    if _TAG_RE.search(value):
        return False
    lowered = value.lower()
    if lowered.startswith(("http://", "https://", "www.")):
        return False
    if len(value.split()) > 4:
        return False
    return True
