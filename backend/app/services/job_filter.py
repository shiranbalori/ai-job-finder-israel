"""Keyword and Israel-only location filters for job fetching."""

import re
from dataclasses import dataclass

# Title/content must match at least one role keyword
ROLE_KEYWORDS = [
    r"\bai\b",
    r"artificial intelligence",
    r"machine learning",
    r"\bml\b",
    r"deep learning",
    r"\bnlp\b",
    r"\bllm\b",
    r"large language model",
    r"data scientist",
    r"data engineer",
    r"data analyst",
    r"analytics engineer",
    r"automation",
    r"\brpa\b",
    r"applied ai",
    r"prompt engineer",
    r"mlops",
    r"computer vision",
    r"research scientist",
]

# Location must contain one of these (primary field — not description)
ISRAEL_LOCATION_PATTERNS = [
    r"\bisrael\b",
    r",\s*il\b",
    r"\bil\s*,",
    r"\bIL\s*-",
    r"\(\s*il\s*\)",
    r"\bisr\b",
    r"tel aviv",
    r"tel-?aviv",
    r"herzliya",
    r"haifa",
    r"ramat gan",
    r"petah tikva",
    r"petach tikva",
    r"jerusalem",
    r"ra'anana",
    r"raanana",
    r"netanya",
    r"yokneam",
    r"yokne'am",
    r"be'er sheva",
    r"beer sheva",
    r"beersheba",
    r"remote israel",
    r"israel remote",
    r"remote\s*[-–]\s*israel",
    r"israel\s*[-–]\s*remote",
    r"remote\s*\(\s*israel\s*\)",
]

# Exclude jobs targeting these regions unless Israel is also in the location string
EXCLUDED_REGION_PATTERNS = [
    r"\busa\b",
    r"united states",
    r"\bu\.s\.\b",
    r"\bus\b",
    r"north america",
    r"\buk\b",
    r"united kingdom",
    r"\beurope\b",
    r"\bgermany\b",
    r"\bde\b",
    r"netherlands",
    r"\bnl\b",
    r"poland",
    r"\bindia\b",
    r"singapore",
    r"\bcanada\b",
    r"australia",
    r"san francisco",
    r"new york",
    r"seattle",
    r"austin",
    r"boston",
    r"chicago",
    r"los angeles",
    r"london",
    r"berlin",
    r"amsterdam",
    r"warsaw",
    r"paris",
    r"dublin",
    r"emea",
]

CATEGORY_RULES: list[tuple[str, list[str]]] = [
    ("Prompt Engineering", [r"prompt engineer", r"prompt engineering"]),
    ("Applied AI", [r"applied ai", r"ai product", r"ai solutions"]),
    ("Automation", [r"automation", r"\brpa\b", r"process automation"]),
    ("Data", [r"data engineer", r"data scientist", r"data analyst", r"analytics", r"\betl\b", r"\bdbt\b"]),
    ("AI / ML", [r"\bai\b", r"machine learning", r"\bml\b", r"\bnlp\b", r"\bllm\b", r"deep learning", r"mlops"]),
]

# Known Israeli AI / tech employers — used for RemoteOK and remote listings
ISRAELI_AI_COMPANY_PATTERNS = [
    r"monday\.?com",
    r"\bmonday\b",
    r"ai21",
    r"\bwix\b",
    r"mobileye",
    r"riskified",
    r"taboola",
    r"jfrog",
    r"similarweb",
    r"fiverr",
    r"walkme",
    r"\bgong\b",
    r"lemonade",
    r"intel",
    r"habana",
    r"trigo",
    r"sentinel\s*one",
    r"\bnice\b",
    r"fireblocks",
    r"pagaya",
    r"lightricks",
    r"or\s*cam",
    r"orca\s*security",
    r"cyberark",
    r"check\s*point",
]


@dataclass
class JobFilterStats:
    total_input: int = 0
    total_israel: int = 0
    total_excluded: int = 0
    role_excluded: int = 0
    location_excluded: int = 0


def _matches_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(p, text, re.I) for p in patterns)


def _has_israel_marker(location: str) -> bool:
    loc = (location or "").strip().lower()
    if not loc:
        return False
    return _matches_any(loc, ISRAEL_LOCATION_PATTERNS)


def _is_excluded_region(location: str) -> bool:
    """True when location targets a non-Israel region without an Israel marker."""
    loc = (location or "").strip().lower()
    if not loc:
        return True
    if _has_israel_marker(loc):
        return False
    if _matches_any(loc, EXCLUDED_REGION_PATTERNS):
        return True
    # Global remote with no Israel mention
    if re.search(r"\bremote\b", loc) and not re.search(
        r"remote\s*[-–(]?\s*israel|israel\s*[-–)]?\s*remote", loc, re.I
    ):
        return True
    return False


def matches_israel_location(location: str) -> bool:
    """
    Include only when location contains an Israel marker and is not a global/other-region listing.
    """
    loc = (location or "").strip()
    if not loc:
        return False
    if _is_excluded_region(loc):
        return False
    return _has_israel_marker(loc)


def matches_role_filter(title: str, description: str = "") -> bool:
    blob = f"{title} {description}".lower()
    return _matches_any(blob, ROLE_KEYWORDS)


def detect_location_tag(location: str) -> str:
    """Return israel | remote_israel | hybrid for UI badges."""
    loc = (location or "").lower()
    if re.search(r"\bhybrid\b", loc):
        return "hybrid"
    if re.search(
        r"remote\s*[-–]?\s*israel|israel\s*[-–]?\s*remote|remote\s*\(\s*israel\s*\)",
        loc,
        re.I,
    ):
        return "remote_israel"
    if re.search(r"\bremote\b", loc) and _has_israel_marker(loc):
        return "remote_israel"
    return "israel"


def detect_work_mode(location: str, description: str = "") -> str:
    """Legacy work_mode field — aligned with location_tag."""
    tag = detect_location_tag(location)
    if tag == "hybrid":
        return "hybrid"
    if tag == "remote_israel":
        return "remote"
    return "onsite"


def detect_category(title: str, description: str = "") -> str:
    blob = f"{title} {description}".lower()
    for category, patterns in CATEGORY_RULES:
        if _matches_any(blob, patterns):
            return category
    return "AI / ML"


def classify_job_location(location: str) -> tuple[bool, str | None]:
    """Return (is_israel, location_tag)."""
    if matches_israel_location(location):
        return True, detect_location_tag(location)
    return False, None


def matches_israeli_company(company: str) -> bool:
    name = (company or "").strip().lower()
    if not name:
        return False
    return _matches_any(name, ISRAELI_AI_COMPANY_PATTERNS)


def filter_board_jobs(jobs: list) -> tuple[list, JobFilterStats]:
    """
    Greenhouse / Lever boards from known Israeli tech companies.
    Accept AI/Data roles when location is Israel/Remote Israel OR company is Israeli.
    """
    from app.domain.job_dto import FetchedJobDTO

    stats = JobFilterStats(total_input=len(jobs))
    result: list[FetchedJobDTO] = []

    for job in jobs:
        if not isinstance(job, FetchedJobDTO):
            stats.total_excluded += 1
            continue

        if not matches_role_filter(job.title, job.description):
            stats.role_excluded += 1
            stats.total_excluded += 1
            continue

        israel_match = matches_israel_location(job.location)
        company_match = matches_israeli_company(job.company)
        if not israel_match and not company_match:
            stats.location_excluded += 1
            stats.total_excluded += 1
            continue

        if company_match and not israel_match:
            job.location = f"Remote Israel — {job.company}"

        job.is_israel = True
        job.location_tag = detect_location_tag(job.location)
        job.work_mode = detect_work_mode(job.location, job.description)
        result.append(job)

    stats.total_israel = len(result)
    return result, stats


def filter_fetched_jobs(jobs: list) -> tuple[list, JobFilterStats]:
    """Apply role + Israel location filters. Returns (jobs, stats)."""
    from app.domain.job_dto import FetchedJobDTO

    stats = JobFilterStats(total_input=len(jobs))
    result: list[FetchedJobDTO] = []

    for job in jobs:
        if not isinstance(job, FetchedJobDTO):
            stats.total_excluded += 1
            continue

        if not matches_role_filter(job.title, job.description):
            stats.role_excluded += 1
            stats.total_excluded += 1
            continue

        if not matches_israel_location(job.location):
            stats.location_excluded += 1
            stats.total_excluded += 1
            continue

        job.is_israel = True
        job.location_tag = detect_location_tag(job.location)
        job.work_mode = detect_work_mode(job.location, job.description)
        result.append(job)

    stats.total_israel = len(result)
    return result, stats


def matches_remoteok_israel(job) -> bool:
    """RemoteOK listings often omit Israel in location — check tags/description too."""
    if matches_israel_location(job.location):
        return True
    blob = f"{job.location or ''} {job.description or ''}".strip()
    if not blob:
        return False
    if _is_excluded_region(job.location or ""):
        # Allow Israel markers in description when location is generic "Remote"
        if not _has_israel_marker(blob):
            return False
    return _has_israel_marker(blob)


def filter_remoteok_jobs(jobs: list) -> tuple[list, JobFilterStats]:
    """RemoteOK: AI/Data roles in Israel OR from known Israeli AI companies."""
    from app.domain.job_dto import FetchedJobDTO

    stats = JobFilterStats(total_input=len(jobs))
    result: list[FetchedJobDTO] = []

    for job in jobs:
        if not isinstance(job, FetchedJobDTO):
            stats.total_excluded += 1
            continue

        if not matches_role_filter(job.title, job.description):
            stats.role_excluded += 1
            stats.total_excluded += 1
            continue

        israel_match = matches_remoteok_israel(job)
        company_match = matches_israeli_company(job.company)
        if not israel_match and not company_match:
            stats.location_excluded += 1
            stats.total_excluded += 1
            continue

        if company_match and not israel_match:
            job.location = f"Remote Israel — {job.company}"

        job.is_israel = True
        job.location_tag = detect_location_tag(job.location)
        job.work_mode = detect_work_mode(job.location, job.description)
        result.append(job)

    stats.total_israel = len(result)
    return result, stats
