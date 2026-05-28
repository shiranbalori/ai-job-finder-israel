"""
Enhanced CV-to-job matching: multi-signal scoring with semantic skill graph.
"""

from __future__ import annotations

import logging
import re
from difflib import SequenceMatcher
from typing import Any

from app.models.cv_profile import CVProfile
from app.models.job import Job
from app.services.job_skill_parser import build_job_scan_text, extract_job_skills
from app.services.skill_registry import (
    extract_skills_balanced,
    get_skill_weight,
    normalize_skill_list,
    resolve_skill_match,
)
from app.utils.json_helpers import from_json_list

logger = logging.getLogger(__name__)

AI_DOMAIN_TERMS = frozenset({
    "ai", "ml", "llm", "llms", "nlp", "machine learning", "deep learning",
    "generative ai", "rag", "langchain", "openai", "gemini", "prompt",
    "data scientist", "ml engineer", "ai engineer", "automation",
})

GENERIC_QA_PATTERN = re.compile(r"\bqa\b|\bquality assurance\b|\btest engineer\b", re.I)


def _cv_skill_items(cv: CVProfile) -> list[str]:
    return normalize_skill_list(
        from_json_list(cv.skills_json)
        + from_json_list(cv.tools_json)
        + from_json_list(cv.technologies_json)
    )


def _extract_cv_skills(cv: CVProfile, *, fast: bool = False) -> list[str]:
    """CV skills from profile; optional raw-text mining (skip in fast upload path)."""
    skills = _cv_skill_items(cv)
    if not fast and cv.raw_text:
        mined = extract_skills_balanced(cv.raw_text, limit=20, quiet=True).normalized
        skills = normalize_skill_list(skills + mined)
    return skills


def _extract_job_requirements(job: Job) -> tuple[list[str], dict[str, Any]]:
    """Full job skill extraction via same pipeline as CV."""
    requirements = from_json_list(job.requirements_json)
    existing = from_json_list(job.skills_json)
    skills, debug = extract_job_skills(
        job.title,
        job.description,
        requirements=requirements,
        existing_skills=existing,
        limit=20,
        quiet=True,
    )
    return skills, debug


def _title_similarity(cv_titles: list[str], job_title: str) -> float:
    job_lower = job_title.lower()
    best = 0.0
    for title in cv_titles:
        ratio = SequenceMatcher(None, title.lower(), job_lower).ratio()
        if title.lower() in job_lower or job_lower in title.lower():
            ratio = max(ratio, 0.85)
        best = max(best, ratio)

    job_tokens = set(re.findall(r"[a-z]{3,}", job_lower))
    for title in cv_titles:
        title_tokens = set(re.findall(r"[a-z]{3,}", title.lower()))
        if title_tokens & job_tokens:
            overlap = len(title_tokens & job_tokens) / max(len(job_tokens), 1)
            best = max(best, overlap * 0.9)

    # AI title keyword boost
    if any(t in job_lower for t in ("ai", "llm", "ml", "data", "automation")):
        for title in cv_titles:
            if any(t in title.lower() for t in ("ai", "llm", "ml", "data", "automation", "engineer")):
                best = max(best, 0.75)
    return min(1.0, best)


def _text_semantic_overlap(
    cv: CVProfile,
    job: Job,
    job_scan: str,
    *,
    cv_blob: str | None = None,
    fast: bool = False,
) -> float:
    if cv_blob is None:
        cv_blob = " ".join(
            [
                cv.summary or "",
                " ".join(from_json_list(cv.skills_json)),
                " ".join(from_json_list(cv.job_titles_json)),
                (cv.raw_text or "")[:2000 if fast else 3000],
            ]
        ).lower()
    job_blob = job_scan.lower()

    cv_tokens = set(re.findall(r"[a-z0-9+#]{3,}", cv_blob))
    job_tokens = set(re.findall(r"[a-z0-9+#]{3,}", job_blob))
    if not cv_tokens or not job_tokens:
        return 0.0

    jaccard = len(cv_tokens & job_tokens) / len(cv_tokens | job_tokens)
    if fast:
        return min(1.0, jaccard * 0.85)
    seq = SequenceMatcher(None, cv_blob[:600], job_blob[:600]).ratio()
    return min(1.0, jaccard * 0.55 + seq * 0.45)


def _ai_domain_scores(cv_skills: list[str], job_title: str, job_skills: list[str], job_scan: str) -> tuple[float, float]:
    """Return (cv_ai_score, job_ai_score) in 0..1."""
    cv_blob = " ".join(s.lower() for s in cv_skills)
    job_blob = f"{job_title} {' '.join(job_skills)} {job_scan}".lower()

    def score(blob: str) -> float:
        hits = sum(1 for t in AI_DOMAIN_TERMS if t in blob)
        return min(1.0, hits / 6.0)

    return score(cv_blob), score(job_blob)


def _match_skill_sets(
    cv_skills: list[str],
    job_skills: list[str],
    job_scan: str,
    *,
    fast: bool = False,
) -> tuple[list[str], list[str], list[str], float, float]:
    """
    Compare CV vs job skills with exact + semantic graph matching.
    Also mines job description for CV skills present in text.
    Returns exact_matched, semantic_matched, missing, exact_ratio, semantic_ratio.
    """
    cv_labels = {s.lower(): s for s in cv_skills}
    job_unique = list(dict.fromkeys(normalize_skill_list(job_skills)))

    exact: list[str] = []
    semantic: list[str] = []
    missing: list[str] = []

    exact_weight = 0.0
    semantic_weight = 0.0
    total_weight = 0.0

    matched_cv_keys: set[str] = set()

    for job_skill in job_unique:
        weight = get_skill_weight(job_skill)
        total_weight += weight
        cv_label, match_type = resolve_skill_match(job_skill, cv_labels)

        if cv_label and match_type in {"exact", "fuzzy"}:
            exact.append(cv_label)
            matched_cv_keys.add(cv_label.lower())
            exact_weight += weight
        elif cv_label and match_type == "related":
            semantic.append(cv_label)
            matched_cv_keys.add(cv_label.lower())
            semantic_weight += weight * 0.85
        else:
            missing.append(job_skill)

    # CV skills mentioned in job description but not in job skill list
    if fast:
        job_text_lower = job_scan.lower()
        for cv_skill in cv_skills:
            cv_key = cv_skill.lower()
            if cv_key in matched_cv_keys:
                continue
            if cv_key in job_text_lower:
                semantic.append(cv_skill)
                matched_cv_keys.add(cv_key)
                semantic_weight += get_skill_weight(cv_skill) * 0.65
    else:
        job_text_skills = extract_skills_balanced(job_scan, limit=12, quiet=True).normalized
        for cv_skill in cv_skills:
            cv_key = cv_skill.lower()
            if cv_key in matched_cv_keys:
                continue
            if cv_key in {s.lower() for s in job_text_skills}:
                semantic.append(cv_skill)
                matched_cv_keys.add(cv_key)
                semantic_weight += get_skill_weight(cv_skill) * 0.7
            elif cv_skill.lower() in job_scan.lower():
                semantic.append(cv_skill)
                matched_cv_keys.add(cv_key)
                semantic_weight += get_skill_weight(cv_skill) * 0.6

    exact_ratio = exact_weight / total_weight if total_weight else 0.0
    semantic_ratio = semantic_weight / total_weight if total_weight else 0.0

    return (
        list(dict.fromkeys(exact)),
        list(dict.fromkeys(semantic)),
        missing,
        exact_ratio,
        semantic_ratio,
    )


def _build_match_reason(
    *,
    exact: list[str],
    semantic: list[str],
    missing: list[str],
    cv_titles: list[str],
    title_sim: float,
    text_semantic: float,
    embedding_sim: float | None,
    years: int,
    cv_ai: float,
    job_ai: float,
) -> str:
    parts: list[str] = []

    all_matched = exact + [s for s in semantic if s not in exact]
    if all_matched:
        highlight = ", ".join(all_matched[:8])
        parts.append(f"Strong overlap in {highlight}.")
    elif semantic:
        parts.append(f"Semantic alignment via {', '.join(semantic[:6])}.")

    if cv_titles and title_sim >= 0.45:
        bg = cv_titles[0]
        if "ai" in bg.lower() or "automation" in bg.lower():
            parts.append(
                f"Your background in {bg} aligns well with the role requirements."
            )
        else:
            parts.append(f"Title alignment with your experience as {bg}.")

    if semantic:
        sem_preview = ", ".join(semantic[:5])
        parts.append(f"Related strengths: {sem_preview}.")

    workflow_terms = [s for s in all_matched if s.lower() in {"automation", "ai automation", "n8n", "make", "apis", "llms", "langchain"}]
    if len(workflow_terms) >= 2:
        parts.append(
            f"AI workflow fit — {', '.join(workflow_terms[:5])} match orchestration and integration needs."
        )

    if embedding_sim is not None and embedding_sim >= 0.55:
        parts.append(
            f"High semantic similarity ({round(embedding_sim * 100)}%) between your CV and this job description."
        )
    elif text_semantic >= 0.12:
        parts.append(
            f"Domain terminology overlap {round(text_semantic * 100)}% across CV and job description."
        )

    if years >= 3:
        parts.append(f"{years}+ years of experience supports role seniority.")

    if cv_ai >= 0.5 and job_ai >= 0.5:
        parts.append("High AI/Data domain fit — profile and role both emphasize intelligent systems.")

    if missing:
        parts.append(f"Gaps to develop: {', '.join(missing[:5])}.")

    return " ".join(parts) if parts else "Partial fit based on AI/Data background and transferable skills."


def compute_job_match(
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
    quiet: bool = False,
    fast: bool = False,
) -> dict[str, Any]:
    """
    Score CV against job (0–100) with explainable multi-signal breakdown.

    Weights (with embeddings):
    - Exact skill overlap: 30%
    - Semantic skill matches: 15%
    - Embedding / description similarity: 20%
    - Text token overlap: 10%
    - Title alignment: 15%
    - Experience fit: 10%
    - AI/domain similarity: 5%
    """
    cv_skills = cv_skills if cv_skills is not None else _extract_cv_skills(cv, fast=fast)
    if job_skills is None:
        job_skills, job_debug = _extract_job_requirements(job)
    else:
        job_debug = job_debug or {}
    if job_scan is None:
        job_scan = build_job_scan_text(
            job.title,
            job.description,
            from_json_list(job.requirements_json),
            job_skills,
        )
    if cv_titles is None:
        cv_titles = from_json_list(cv.job_titles_json)

    exact, semantic, missing, exact_ratio, semantic_ratio = _match_skill_sets(
        cv_skills, job_skills, job_scan, fast=fast
    )
    semantic_only = [s for s in semantic if s not in exact]
    matched = list(dict.fromkeys(exact + semantic_only))

    exact_score = exact_ratio * 30.0
    semantic_skill_score = min(15.0, semantic_ratio * 15.0 + len(semantic) * 0.8)

    text_semantic = _text_semantic_overlap(cv, job, job_scan, cv_blob=cv_blob, fast=fast)
    text_score = text_semantic * 10.0

    if embedding_similarity is not None:
        embed_sim = max(0.0, min(1.0, embedding_similarity))
        embedding_score = embed_sim * 20.0
        semantic_overlap = embed_sim
    else:
        embed_sim = None
        embedding_score = 0.0
        semantic_overlap = text_semantic

    title_sim = _title_similarity(cv_titles, job.title)
    title_score = title_sim * 15.0

    years = cv.years_experience or 0
    seniority_hint = 5 if re.search(r"senior|lead|staff|principal", job.title, re.I) else 3
    if years >= seniority_hint:
        exp_score = 10.0
    elif years >= max(seniority_hint - 2, 1):
        exp_score = 7.0
    elif years >= 1:
        exp_score = 4.0
    else:
        exp_score = 1.0

    cv_ai, job_ai = _ai_domain_scores(cv_skills, job.title, job_skills, job_scan)
    domain_score = min(5.0, (cv_ai * job_ai) * 5.0)

    total = min(100.0, round(
        exact_score
        + semantic_skill_score
        + embedding_score
        + text_score
        + title_score
        + exp_score
        + domain_score,
        1,
    ))

    # Rank AI/Data jobs above generic QA when CV is AI-heavy
    if cv_ai >= 0.55 and GENERIC_QA_PATTERN.search(job.title) and job_ai < 0.35:
        total = max(0.0, round(total - 10.0, 1))
    elif cv_ai >= 0.5 and job_ai >= 0.45:
        total = min(100.0, round(total + 3.0, 1))

    reason = _build_match_reason(
        exact=exact,
        semantic=semantic_only,
        missing=missing,
        cv_titles=cv_titles,
        title_sim=title_sim,
        text_semantic=text_semantic,
        embedding_sim=embed_sim,
        years=years,
        cv_ai=cv_ai,
        job_ai=job_ai,
    )

    if not quiet:
        logger.info(
            "[match] cv=%s job=%s title=%s score=%.1f exact=%s semantic=%s missing=%s job_skills=%s",
            cv.id,
            job.id,
            job.title,
            total,
            exact[:8],
            semantic[:8],
            missing[:8],
            job_skills[:10],
        )

    scoring_method = (
        "semantic_recruiter_v3_embeddings"
        if embedding_similarity is not None
        else "semantic_recruiter_v2"
    )

    return {
        "match_score": total,
        "match_reason": reason,
        "missing_skills": missing[:12],
        "matched_skills": matched[:15],
        "semantic_matches": semantic_only[:12],
        "semantic_overlap": round(semantic_overlap, 3),
        "scoring_method": scoring_method,
        "score_breakdown": {
            "skills": round(exact_score, 1),
            "semantic": round(text_score + semantic_skill_score, 1),
            "semantic_skills": round(semantic_skill_score, 1),
            "embedding": round(embedding_score, 1),
            "title": round(title_score, 1),
            "experience": round(exp_score, 1),
            "domain": round(domain_score, 1),
        },
        "job_skills_debug": {} if fast else job_debug,
        "job_skills_extracted": job_skills,
    }
