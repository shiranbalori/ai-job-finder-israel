"""
Job description skill extraction — same multi-pass pipeline as CV parsing.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from app.services.skill_registry import (
    JOB_PHRASE_ALIASES,
    MAX_OUTPUT_SKILLS,
    SkillExtractionResult,
    extract_skills_balanced,
    normalize_skill_list,
)
from app.utils.text_helpers import strip_html
from app.utils.text_normalize import normalize_extracted_text

logger = logging.getLogger(__name__)

_TITLE_SKILL_HINTS: list[tuple[str, tuple[str, ...]]] = [
    (r"qa\s+automation", ("Automation", "Python", "APIs", "JavaScript", "AI Automation")),
    (r"automation\s+engineer", ("Automation", "Python", "APIs", "n8n", "Make", "AI Automation")),
    (r"ai\s+automation", ("AI Automation", "Automation", "LLMs", "Python", "n8n", "LangChain")),
    (r"llm|large\s+language", ("LLMs", "LangChain", "RAG", "Prompt Engineering", "Python")),
    (r"machine\s+learning|ml\s+engineer", ("Machine Learning", "Python", "SQL", "PyTorch")),
    (r"data\s+scientist", ("Machine Learning", "Python", "SQL", "NLP")),
    (r"prompt\s+engineer", ("Prompt Engineering", "LLMs", "OpenAI", "RAG")),
    (r"nlp", ("NLP", "LLMs", "Python", "Machine Learning")),
    (r"devops|mlops", ("Docker", "Kubernetes", "Python", "Git")),
]


def _apply_job_phrase_aliases(text: str) -> str:
    """Expand job-description phrases to canonical skill tokens for extraction."""
    lower = text.lower()
    for phrase, canonical in sorted(JOB_PHRASE_ALIASES.items(), key=lambda x: len(x[0]), reverse=True):
        if phrase in lower:
            text = re.sub(re.escape(phrase), f" {canonical} ", text, flags=re.I)
            lower = text.lower()
    return re.sub(r" {2,}", " ", text)


def _infer_skills_from_title(title: str) -> list[str]:
    inferred: list[str] = []
    lower = title.lower()
    for pattern, skills in _TITLE_SKILL_HINTS:
        if re.search(pattern, lower, re.I):
            inferred.extend(skills)
    return normalize_skill_list(inferred)


def build_job_scan_text(job_title: str, description: str, requirements: list[str], skills: list[str]) -> str:
    """Combine all job fields into one normalized blob for full-text skill mining."""
    req_blob = "\n".join(requirements) if requirements else ""
    skills_blob = ", ".join(skills) if skills else ""
    raw = f"{job_title}\n{skills_blob}\n{req_blob}\n{strip_html(description)}"
    text = normalize_extracted_text(raw)
    return _apply_job_phrase_aliases(text)


def extract_job_skills(
    job_title: str,
    description: str,
    *,
    requirements: list[str] | None = None,
    existing_skills: list[str] | None = None,
    limit: int = MAX_OUTPUT_SKILLS,
    quiet: bool = True,
) -> tuple[list[str], dict[str, Any]]:
    """
    Extract normalized skills from a job using the full CV-quality pipeline.
    Returns (skills, debug_dict).
    """
    requirements = requirements or []
    existing_skills = existing_skills or []

    scan_text = build_job_scan_text(job_title, description, requirements, existing_skills)
    extraction: SkillExtractionResult = extract_skills_balanced(scan_text, limit=limit, quiet=quiet)

    title_inferred = _infer_skills_from_title(job_title)
    merged = normalize_skill_list(extraction.normalized + title_inferred + existing_skills + requirements)[:limit]

    debug = {
        "scan_text_len": len(scan_text),
        "scan_preview": scan_text[:240].replace("\n", " "),
        "raw_regex": extraction.raw_regex,
        "raw_keyword": extraction.raw_keyword,
        "raw_fuzzy": extraction.raw_fuzzy,
        "raw_semantic": extraction.raw_semantic,
        "raw_heuristic": extraction.raw_heuristic,
        "merged": extraction.merged,
        "title_inferred": title_inferred,
        "final_skills": merged,
    }

    if not quiet:
        logger.info(
            "[job-skills] title=%s final=%s regex=%s keyword=%s title_inferred=%s",
            job_title,
            merged,
            extraction.raw_regex,
            extraction.raw_keyword,
            title_inferred,
        )

    return merged, debug
