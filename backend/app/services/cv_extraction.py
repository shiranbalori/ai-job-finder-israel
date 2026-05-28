"""
Unified CV skill extraction — single source of truth for API + DB persistence.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from app.services.skill_registry import (
    MAX_OUTPUT_SKILLS,
    PRIORITY_SKILLS,
    TOOL_SKILLS,
    ExtractedSkill,
    SkillExtractionResult,
    extract_ai_tools,
    extract_skills_balanced,
    extract_tools_from_skills,
    normalize_skill_list,
)
from app.utils.text_normalize import normalize_extracted_text

logger = logging.getLogger(__name__)

_EXTRA_SKILL_SPLIT = re.compile(r"[,;|/•]+")


def _split_skill_tokens(raw: list[str]) -> list[str]:
    out: list[str] = []
    for item in raw:
        if not item or not str(item).strip():
            continue
        parts = _EXTRA_SKILL_SPLIT.split(str(item))
        if len(parts) > 1:
            out.extend(p.strip() for p in parts if p.strip())
        else:
            out.append(str(item).strip())
    return out


def _confidence_map(skills: list[ExtractedSkill]) -> dict[str, ExtractedSkill]:
    return {s.skill.lower(): s for s in skills}


def _merge_confidence(
    heuristic: SkillExtractionResult,
    extra_names: list[str],
    *,
    extra_confidence: float = 0.58,
    limit: int = MAX_OUTPUT_SKILLS,
) -> tuple[list[str], list[dict[str, Any]], dict[str, Any]]:
    merged_map = _confidence_map(heuristic.skills)
    cap_filtered: list[str] = []

    for name in normalize_skill_list(_split_skill_tokens(extra_names)):
        key = name.lower()
        if key in merged_map:
            continue
        merged_map[key] = ExtractedSkill(name, extra_confidence, "external", name)

    ordered = sorted(merged_map.values(), key=lambda s: s.confidence, reverse=True)
    if len(ordered) > limit:
        kept = ordered[:limit]
        cap_filtered = [s.skill for s in ordered[limit:]]
    else:
        kept = ordered

    skills = [s.skill for s in kept]
    skills_confidence = [
        {"skill": s.skill, "confidence": s.confidence, "method": s.method}
        for s in kept
    ]

    debug = {
        "scan_text_len": heuristic.scan_text_len,
        "raw_regex": heuristic.raw_regex,
        "raw_keyword": heuristic.raw_keyword,
        "raw_fuzzy": heuristic.raw_fuzzy,
        "raw_semantic": heuristic.raw_semantic,
        "raw_heuristic": heuristic.raw_heuristic,
        "merged": heuristic.merged,
        "heuristic_merged": heuristic.normalized,
        "filtered_out": cap_filtered + heuristic.filtered_out + heuristic.rejected,
        "merged_skills": skills,
        "skills_confidence": skills_confidence,
        "priority_missing": [p for p in PRIORITY_SKILLS if p not in skills],
    }
    return skills, skills_confidence, debug


def apply_skill_extraction(
    parsed: dict[str, Any],
    text: str,
    *,
    limit: int = MAX_OUTPUT_SKILLS,
) -> dict[str, Any]:
    """
    Finalize parsed CV dict using FULL normalized CV text (not summary).
    """
    scan_text = normalize_extracted_text(text)
    logger.info(
        "[cv-pipeline] input_len=%s scan_len=%s scan_preview=%s",
        len(text or ""),
        len(scan_text),
        scan_text[:180].replace("\n", " "),
    )

    extraction = extract_skills_balanced(scan_text, limit=limit)

    existing_skills = list(parsed.get("skills") or [])
    existing_tools = list(parsed.get("tools") or [])
    existing_tech = list(parsed.get("technologies") or [])
    extra = existing_skills + existing_tools + existing_tech

    skills, skills_confidence, debug = _merge_confidence(extraction, extra, limit=limit)

    if not skills:
        skills = ["Machine Learning", "Python", "SQL"]
        skills_confidence = [
            {"skill": s, "confidence": 0.5, "method": "fallback"} for s in skills
        ]
        debug["fallback_applied"] = True

    parsed["skills"] = skills
    parsed["skills_confidence"] = skills_confidence
    parsed["extraction_debug"] = debug

    tool_from_skills = extract_tools_from_skills(skills)
    tool_from_existing = normalize_skill_list(_split_skill_tokens(existing_tools))
    ai_tools = extract_ai_tools(skills, scan_text)
    parsed["ai_tools"] = ai_tools
    parsed["tools"] = normalize_skill_list(tool_from_skills + tool_from_existing + ai_tools)[:14]

    parsed["technologies"] = [
        t for t in (
            "Python", "SQL", "OpenAI", "Gemini", "LangChain", "Generative AI", "LLMs", "RAG",
            "Prompt Engineering", "Azure AI", "Watson", "ChromaDB", "Vector DB", "NLP",
            "FastAPI", "APIs", "AI Automation", "Machine Learning",
        )
        if t in skills
    ] or skills[:14]

    logger.info(
        "[cv-pipeline] method=%s final_skills=%s tools=%s ai_tools=%s priority_missing=%s",
        parsed.get("extraction_method", "?"),
        skills,
        parsed["tools"],
        ai_tools,
        debug["priority_missing"],
    )
    for stage in ("raw_regex", "raw_keyword", "raw_semantic", "raw_heuristic", "merged", "merged_skills"):
        logger.info("[cv-pipeline] stage_%s=%s", stage, debug.get(stage, []))

    return parsed


def log_api_payload(label: str, parsed: dict[str, Any]) -> None:
    logger.info(
        "[%s] response_skills=%s response_confidence=%s tools=%s languages=%s titles=%s",
        label,
        parsed.get("skills", []),
        [(s["skill"], s["confidence"]) for s in (parsed.get("skills_confidence") or [])],
        parsed.get("tools", []),
        parsed.get("languages", []),
        parsed.get("job_titles", []),
    )
