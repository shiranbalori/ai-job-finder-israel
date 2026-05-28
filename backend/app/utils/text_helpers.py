"""Strip HTML and extract skill-like tokens from job descriptions."""

import re
from html import unescape

from app.services.skill_registry import extract_skills_from_text, normalize_skill_list


def strip_html(html: str) -> str:
    if not html:
        return ""
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def extract_skills_from_text_legacy(text: str, limit: int = 12) -> list[str]:
    """Backward-compatible alias — delegates to skill registry."""
    return extract_skills_from_text(text, limit=limit)


__all__ = ["strip_html", "extract_skills_from_text", "extract_skills_from_job_text", "extract_requirements_from_text"]


def extract_skills_from_job_text(text: str, limit: int = 20, title: str = "") -> list[str]:
    from app.services.job_skill_parser import extract_job_skills

    skills, _ = extract_job_skills(title, text, limit=limit)
    return skills[:limit]


def extract_requirements_from_text(text: str, limit: int = 8) -> list[str]:
    """Pull bullet-like lines from plain text."""
    lines = [ln.strip(" •-\t") for ln in re.split(r"[\n\r]+", text) if ln.strip()]
    reqs = [ln for ln in lines if 20 <= len(ln) <= 200][:limit]
    return reqs or [text[:200]] if text else []
