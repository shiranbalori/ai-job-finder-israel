"""Normalize fetched jobs into the unified application schema."""

from __future__ import annotations

from app.domain.job_dto import FetchedJobDTO
from app.services.job_tag_extractor import extract_ai_data_tags, merge_tags_into_skills


def normalize_collected_job(dto: FetchedJobDTO) -> FetchedJobDTO:
    """
    Apply unified normalization: AI/Data tags, merged skills, trimmed fields.
    All sources (Greenhouse, Lever, RemoteOK) pass through here before save.
    """
    tags = extract_ai_data_tags(
        dto.title,
        dto.description,
        skills=dto.skills,
    )
    dto.tags = tags
    dto.skills = merge_tags_into_skills(tags, dto.skills)

    dto.title = (dto.title or "").strip()[:300]
    dto.company = (dto.company or "").strip()[:200]
    dto.location = (dto.location or "Remote").strip()[:200]
    dto.description = (dto.description or dto.title).strip()[:8000]
    dto.category = (dto.category or "AI / ML").strip()[:100]
    dto.work_mode = (dto.work_mode or "remote").strip()[:50]

    if dto.url:
        dto.url = dto.url.strip()[:500]

    return dto
