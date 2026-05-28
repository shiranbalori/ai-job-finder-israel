"""
Extract standardized AI/Data technology tags from job title + description.

Tags: Python, LLM, RAG, NLP, SQL, LangChain, GenAI
"""

from __future__ import annotations

import re

# Canonical tag → regex patterns (case-insensitive)
AI_DATA_TAG_PATTERNS: list[tuple[str, tuple[str, ...]]] = [
    ("Python", (r"\bpython\b", r"\bpython3\b", r"\bpy\b")),
    ("LLM", (r"\bllm\b", r"\bllms\b", r"large language model", r"foundation model")),
    ("RAG", (r"\brag\b", r"retrieval[\s-]?augmented", r"retrieval augmented generation")),
    ("NLP", (r"\bnlp\b", r"natural language processing", r"text analytics")),
    ("SQL", (r"\bsql\b", r"\bpostgresql\b", r"\bpostgres\b", r"\bmysql\b", r"\bsnowflake\b")),
    ("LangChain", (r"\blangchain\b", r"\blang chain\b", r"\blanggraph\b")),
    ("GenAI", (r"\bgenai\b", r"\bgen ai\b", r"generative ai", r"generative artificial intelligence")),
]

CANONICAL_TAGS = [t[0] for t in AI_DATA_TAG_PATTERNS]


def extract_ai_data_tags(
    title: str = "",
    description: str = "",
    *,
    extra_text: str = "",
    skills: list[str] | None = None,
) -> list[str]:
    """Return matched canonical tags in stable order."""
    blob = f"{title} {description} {extra_text}".lower()
    if skills:
        blob = f"{blob} {' '.join(skills).lower()}"

    found: list[str] = []
    for tag, patterns in AI_DATA_TAG_PATTERNS:
        if any(re.search(p, blob, re.I) for p in patterns):
            found.append(tag)
        elif skills and tag.lower() in {s.lower() for s in skills}:
            found.append(tag)

    return found


def merge_tags_into_skills(tags: list[str], skills: list[str]) -> list[str]:
    """Merge tags into skills list without duplicates."""
    merged = list(skills)
    seen = {s.lower() for s in merged}
    for tag in tags:
        if tag.lower() not in seen:
            merged.append(tag)
            seen.add(tag.lower())
    return merged
