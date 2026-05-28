"""
Mock AI extraction and job-matching logic.

Used when AI_PROVIDER=mock (default) or when live API keys are missing.
"""

import logging
import re
from typing import Any

from app.models.cv_profile import CVProfile
from app.models.job import Job
from app.services.cv_extraction import apply_skill_extraction
from app.services.matching_engine import compute_job_match
from app.services.skill_registry import extract_job_titles, extract_years_experience

logger = logging.getLogger(__name__)

_AI_TECH_PRIORITY = [
    "Python", "SQL", "OpenAI", "Gemini", "LangChain", "Generative AI", "LLMs", "RAG",
    "Prompt Engineering", "Azure AI", "Watson", "ChromaDB", "Vector DB", "NLP",
    "FastAPI", "APIs", "AI Automation", "Machine Learning",
]


def mock_extract_cv(text: str) -> dict[str, Any]:
    """Parse CV fields; skills always finalized via merged heuristic pipeline."""
    years = extract_years_experience(text)
    titles = extract_job_titles(text)

    parsed: dict[str, Any] = {
        "full_name": _guess_name(text),
        "email": _guess_email(text),
        "summary": _extract_summary(text),
        "years_experience": years,
        "job_titles": titles[:5],
        "skills": [],
        "tools": [],
        "technologies": [],
        "languages": _detect_languages(text),
        "language": "he" if re.search(r"[\u0590-\u05FF]", text) else "en",
        "extraction_method": "merged_heuristic",
    }

    return apply_skill_extraction(parsed, text, limit=20)


def enrich_parsed_cv(parsed: dict[str, Any], text: str) -> dict[str, Any]:
    """Merge live-AI (or partial) parse with heuristic skill extraction."""
    parsed.setdefault("extraction_method", "live_ai+heuristic")
    return apply_skill_extraction(parsed, text, limit=20)


def _finalize_technologies(parsed: dict[str, Any]) -> None:
    skills = parsed.get("skills") or []
    technologies = [t for t in _AI_TECH_PRIORITY if t in skills]
    if not technologies:
        technologies = skills[:14]
    parsed["technologies"] = technologies


def _extract_summary(text: str) -> str:
    patterns = [
        r"(?is)(?:summary|profile|about me|professional summary)\s*[:\-]?\s*\n(.{80,600}?)(?:\n\s*\n|\n(?:experience|education|skills|work)\b)",
        r"(?is)(?:summary|profile)\s*[:\-]\s*(.{80,400})",
    ]
    for pattern in patterns:
        if m := re.search(pattern, text):
            summary = re.sub(r"\s+", " ", m.group(1)).strip()
            if len(summary) >= 60:
                return summary[:500] + ("..." if len(summary) > 500 else "")

    for line in text.splitlines()[1:8]:
        stripped = re.sub(r"\s+", " ", line.strip())
        if len(stripped) >= 80 and "@" not in stripped:
            return stripped[:500] + ("..." if len(stripped) > 500 else "")

    compact = re.sub(r"\s+", " ", text[:400]).strip()
    return compact + ("..." if len(text) > 400 else "")


def _guess_name(text: str) -> str:
    for line in text.splitlines()[:6]:
        line = line.strip()
        if 2 <= len(line.split()) <= 5 and "@" not in line and len(line) < 60:
            if re.match(r"^[A-Za-z\u0590-\u05FF\s.'-]+$", line):
                if not re.search(r"(?i)(resume|curriculum|vitae|phone|email|linkedin)", line):
                    return line
    return "Candidate"


def _guess_email(text: str) -> str | None:
    if m := re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text):
        return m.group(0)
    return None


def _detect_languages(text: str) -> list[str]:
    lower = text.lower()
    found: list[str] = []
    language_map = {
        "hebrew": "Hebrew", "english": "English", "arabic": "Arabic",
        "russian": "Russian", "french": "French", "spanish": "Spanish", "german": "German",
    }
    for keyword, label in language_map.items():
        if keyword in lower and label not in found:
            found.append(label)
    if re.search(r"[\u0590-\u05FF]", text) and "Hebrew" not in found:
        found.append("Hebrew")
    if re.search(r"[A-Za-z]{20,}", text) and "English" not in found:
        found.append("English")
    return found or (["Hebrew", "English"] if re.search(r"[\u0590-\u05FF]", text) else ["English"])


def mock_match_job(
    cv: CVProfile,
    job: Job,
    *,
    cv_skills: list[str] | None = None,
    job_skills: list[str] | None = None,
    job_debug: dict[str, Any] | None = None,
    cv_blob: str | None = None,
    cv_titles: list[str] | None = None,
    job_scan: str | None = None,
    embedding_similarity: float | None = None,
    quiet: bool = True,
    fast: bool = False,
) -> dict[str, Any]:
    return compute_job_match(
        cv,
        job,
        cv_skills=cv_skills,
        job_skills=job_skills,
        job_debug=job_debug,
        cv_blob=cv_blob,
        cv_titles=cv_titles,
        job_scan=job_scan,
        embedding_similarity=embedding_similarity,
        quiet=quiet,
        fast=fast,
    )
