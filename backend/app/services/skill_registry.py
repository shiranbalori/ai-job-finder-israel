"""
Canonical skill taxonomy and multi-pass extraction engine.

Pipeline stages (all logged):
  regex -> keyword -> fuzzy -> semantic -> heuristic -> merge -> normalize -> filter
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

# Hardcoded technical skill dictionary (must-detect)
TECH_SKILL_DICTIONARY: tuple[str, ...] = (
    "Python", "SQL", "FastAPI", "OpenAI", "Gemini", "LangChain", "RAG", "LLMs",
    "NLP", "Machine Learning", "Automation", "AI Automation", "Prompt Engineering",
    "APIs", "Docker", "Git", "n8n", "Make", "JavaScript", "Vector DB", "ChromaDB",
    "Azure AI", "Watson", "PyTorch", "Kubernetes",
)

JOB_SKILL_DICTIONARY: tuple[str, ...] = TECH_SKILL_DICTIONARY

# Job-description phrase → canonical skill (applied before extraction)
JOB_PHRASE_ALIASES: dict[str, str] = {
    "ai agents": "AI Automation",
    "ai agent": "AI Automation",
    "workflow orchestration": "Automation",
    "engineering workflows": "Automation",
    "test automation": "Automation",
    "qa automation": "Automation",
    "prompt design": "Prompt Engineering",
    "prompt engineering": "Prompt Engineering",
    "generative ai": "Generative AI",
    "gen ai": "Generative AI",
    "llm workflows": "LLMs",
    "llm workflow": "LLMs",
    "llm powered": "LLMs",
    "large language model": "LLMs",
    "retrieval augmented generation": "RAG",
    "retrieval-augmented generation": "RAG",
    "vector database": "Vector DB",
    "vector db": "Vector DB",
    "machine learning": "Machine Learning",
    "natural language processing": "NLP",
    "open ai": "OpenAI",
    "fast api": "FastAPI",
    "lang chain": "LangChain",
    "rest apis": "APIs",
    "rest api": "APIs",
    "webhook": "APIs",
    "webhooks": "APIs",
    "azure ai": "Azure AI",
    "ibm watson": "Watson",
    "chroma db": "ChromaDB",
}

# Semantic related-skill graph for matching (bidirectional lookup)
SEMANTIC_SKILL_GRAPH: dict[str, set[str]] = {
    "automation": {
        "ai automation", "n8n", "make", "rpa", "python", "apis", "javascript",
        "llms", "langchain", "docker", "git",
    },
    "ai automation": {
        "automation", "n8n", "make", "llms", "langchain", "python", "apis",
        "prompt engineering", "rag", "generative ai",
    },
    "qa": {"automation", "python", "apis", "javascript", "sql", "git"},
    "llms": {
        "nlp", "langchain", "openai", "gemini", "prompt engineering", "rag",
        "generative ai", "python", "machine learning",
    },
    "rag": {"llms", "langchain", "vector db", "chromadb", "python", "openai"},
    "nlp": {"llms", "machine learning", "python", "pytorch"},
    "machine learning": {"python", "pytorch", "sql", "nlp", "deep learning"},
    "prompt engineering": {"llms", "openai", "gemini", "rag", "generative ai"},
    "apis": {"python", "fastapi", "javascript", "rest api", "automation"},
    "python": {"sql", "fastapi", "apis", "machine learning", "langchain", "automation"},
    "generative ai": {"llms", "openai", "gemini", "prompt engineering", "rag"},
    "langchain": {"llms", "rag", "python", "openai", "vector db"},
    "n8n": {"make", "automation", "ai automation", "apis", "python"},
    "make": {"n8n", "automation", "ai automation", "apis"},
    "docker": {"kubernetes", "python", "git", "mlops"},
    "kubernetes": {"docker", "python", "mlops"},
}

PRIORITY_SKILLS: tuple[str, ...] = TECH_SKILL_DICTIONARY

MAX_OUTPUT_SKILLS = 20
MIN_OUTPUT_CONFIDENCE = 0.40
_FUZZY_ACCEPT = 0.72
_FUZZY_REJECT_LOG = 0.58

# Explicit normalization mappings (also applied in text_normalize.py)
NORMALIZATION_MAP: dict[str, str] = {
    "machine learning": "Machine Learning",
    "deep learning": "Deep Learning",
    "prompt engineering": "Prompt Engineering",
    "ai automation": "AI Automation",
    "generative ai": "Generative AI",
    "natural language processing": "NLP",
    "retrieval augmented generation": "RAG",
    "retrieval-augmented generation": "RAG",
    "vector database": "Vector DB",
    "vector db": "Vector DB",
    "azure ai": "Azure AI",
    "azure openai": "Azure AI",
    "ibm watson": "Watson",
    "watsonx": "Watson",
    "open ai": "OpenAI",
    "openai": "OpenAI",
    "chat gpt": "OpenAI",
    "chatgpt": "OpenAI",
    "gpt-4": "OpenAI",
    "gpt-4o": "OpenAI",
    "fast api": "FastAPI",
    "fastapi": "FastAPI",
    "lang chain": "LangChain",
    "langchain": "LangChain",
    "chroma db": "ChromaDB",
    "chromadb": "ChromaDB",
    "gemini api": "Gemini",
    "google gemini": "Gemini",
    "large language model": "LLMs",
    "large language models": "LLMs",
    "llm": "LLMs",
    "llms": "LLMs",
    "ml": "Machine Learning",
    "rag": "RAG",
    "nlp": "NLP",
    "python": "Python",
    "python3": "Python",
    "sql": "SQL",
    "rest apis": "APIs",
    "rest api": "APIs",
    "apis": "APIs",
    "api": "APIs",
    "docker": "Docker",
    "git": "Git",
    "github": "Git",
    "n8n": "n8n",
    "make": "Make",
    "make.com": "Make",
    "automation": "Automation",
    "workflow automation": "AI Automation",
}

# Regex patterns per canonical skill (run on full normalized text)
TECH_SKILL_PATTERNS: dict[str, tuple[str, ...]] = {
    "Python": (r"\bpython(?:3|2)?\b",),
    "SQL": (r"\bsql\b", r"\bpostgresql\b", r"\bmysql\b", r"\btsql\b", r"\bpl/?sql\b"),
    "FastAPI": (r"\bfastapi\b", r"\bfast[\s-]?api\b"),
    "OpenAI": (r"\bopenai\b", r"\bopen[\s-]?ai\b", r"\bgpt[-\s]?4", r"\bchatgpt\b", r"\bgpt[-\s]?3"),
    "Gemini": (r"\bgemini\b", r"\bgemini[\s-]?api\b", r"\bgoogle[\s-]?gemini\b"),
    "LangChain": (r"\blangchain\b", r"\blang[\s-]?chain\b"),
    "RAG": (r"\brag\b", r"\bretrieval[\s-]?augmented", r"\brag[\s-]?based\b", r"\brag[\s-]?pipeline"),
    "LLMs": (r"\bllms?\b", r"\blarge[\s-]?language[\s-]?models?\b", r"\bllm[\s-]?powered\b"),
    "NLP": (r"\bnlp\b", r"\bnatural[\s-]?language[\s-]?processing\b"),
    "Machine Learning": (r"\bmachine[\s-]?learning\b", r"\bml[\s-]?engineer", r"\bml\b"),
    "Azure AI": (r"\bazure[\s-]?ai\b", r"\bazure[\s-]?openai\b", r"\bazure[\s-]?ml\b"),
    "ChromaDB": (r"\bchromadb\b", r"\bchroma[\s-]?db\b"),
    "Vector DB": (r"\bvector[\s-]?db\b", r"\bvector[\s-]?database", r"\bvectordb\b"),
    "Watson": (r"\bwatson\b", r"\bibm[\s-]?watson\b", r"\bwatsonx\b"),
    "Prompt Engineering": (r"\bprompt[\s-]?engineering\b", r"\bprompt[\s-]?engineer", r"\bprompt[\s-]?architect"),
    "APIs": (r"\bapis\b", r"\brest[\s-]?apis?\b", r"\bapi[\s-]?integration", r"\bwebhooks?\b"),
    "Docker": (r"\bdocker\b", r"\bcontainer(?:s|ized)?\b"),
    "Git": (r"\bgit\b", r"\bgithub\b", r"\bgitlab\b"),
    "n8n": (r"\bn8n\b",),
    "Make": (r"\bmake\.com\b", r"\bintegromat\b", r"\bmake\b(?=[,\s]|$)"),
    "Automation": (r"\bautomation\b", r"\bautomations\b", r"\bautomated\b", r"\bqa[\s-]?automation\b"),
    "AI Automation": (r"\bai[\s-]?automation\b", r"\bworkflow[\s-]?automation\b", r"\bintelligent[\s-]?automation\b"),
    "JavaScript": (r"\bjavascript\b", r"\bjava[\s-]?script\b", r"\bjs\b"),
    "PyTorch": (r"\bpytorch\b", r"\btorch\b"),
    "Kubernetes": (r"\bkubernetes\b", r"\bk8s\b"),
}

TOOL_SKILLS: frozenset[str] = frozenset({
    "Docker", "Git", "n8n", "Make", "FastAPI", "Redis", "Kubernetes", "Jupyter",
})

AI_TOOL_SKILLS: frozenset[str] = frozenset({
    "OpenAI", "Gemini", "LangChain", "RAG", "LLMs", "Prompt Engineering",
    "Generative AI", "Vector DB", "ChromaDB", "Azure AI", "Watson", "NLP",
    "AI Automation", "Automation", "APIs", "PyTorch", "Machine Learning",
    "Deep Learning", "MLOps",
})

_SKILLS_SECTION = re.compile(
    r"(?is)"
    r"(?:skills|technical\s+skills|technologies|tech\s+stack|tools|competencies|expertise)"
    r"\s*[:\-]?\s*\n(.{20,4000}?)"
    r"(?:\n\s*\n|\n(?:experience|education|projects|employment|work\s+history|certifications)\b)"
)


@dataclass(frozen=True)
class SkillDefinition:
    canonical: str
    aliases: tuple[str, ...]
    category: str
    weight: float = 1.0
    synonyms: tuple[str, ...] = ()


@dataclass
class ExtractedSkill:
    skill: str
    confidence: float
    method: str
    matched_term: str = ""


@dataclass
class SkillExtractionResult:
    skills: list[ExtractedSkill] = field(default_factory=list)
    raw_regex: list[str] = field(default_factory=list)
    raw_keyword: list[str] = field(default_factory=list)
    raw_fuzzy: list[str] = field(default_factory=list)
    raw_semantic: list[str] = field(default_factory=list)
    raw_heuristic: list[str] = field(default_factory=list)
    merged: list[str] = field(default_factory=list)
    normalized: list[str] = field(default_factory=list)
    filtered_out: list[str] = field(default_factory=list)
    rejected: list[str] = field(default_factory=list)
    scan_text_len: int = 0


SKILL_DEFINITIONS: list[SkillDefinition] = [
    SkillDefinition("Prompt Engineering", ("prompt engineering", "prompt engineer", "prompt architect"), "ai", 1.3),
    SkillDefinition("AI Automation", ("ai automation", "workflow automation", "intelligent automation"), "automation", 1.2),
    SkillDefinition("Automation", ("automation", "automations"), "automation", 0.95),
    SkillDefinition("Generative AI", ("generative ai", "gen ai", "genai"), "ai", 1.3),
    SkillDefinition("Machine Learning", ("machine learning", "ml engineer", "ml engineering"), "ai", 1.4, ("ml",)),
    SkillDefinition("RAG", ("rag", "retrieval augmented generation", "retrieval-augmented generation", "rag pipeline"), "ai", 1.3),
    SkillDefinition("LangChain", ("langchain", "lang chain"), "ai", 1.2),
    SkillDefinition("Vector DB", ("vector db", "vector database", "vector databases", "vectordb"), "ai", 1.1),
    SkillDefinition("ChromaDB", ("chromadb", "chroma db"), "ai", 1.1, ("chroma",)),
    SkillDefinition("Azure AI", ("azure ai", "azure openai", "azure ml"), "cloud", 1.1),
    SkillDefinition("Watson", ("watson", "ibm watson", "watsonx"), "ai", 1.0),
    SkillDefinition("OpenAI", ("openai", "gpt-4", "gpt-4o", "gpt-3.5", "chatgpt", "chat gpt"), "ai", 1.3, ("gpt",)),
    SkillDefinition("Gemini", ("gemini", "google gemini", "gemini pro", "gemini api"), "ai", 1.2),
    SkillDefinition("LLMs", ("llms", "llm", "large language model", "large language models"), "ai", 1.3),
    SkillDefinition("NLP", ("nlp", "natural language processing"), "ai", 1.2),
    SkillDefinition("FastAPI", ("fastapi", "fast api"), "tool", 1.0),
    SkillDefinition("Make", ("make", "make.com", "integromat"), "automation", 1.0),
    SkillDefinition("n8n", ("n8n",), "automation", 1.1),
    SkillDefinition("APIs", ("rest api", "rest apis", "api integration", "apis", "webhooks"), "tool", 0.9, ("api",)),
    SkillDefinition("Python", ("python", "python3"), "language", 1.2),
    SkillDefinition("SQL", ("sql", "postgresql", "postgres", "mysql", "tsql"), "data", 1.1),
    SkillDefinition("PyTorch", ("pytorch", "torch"), "ai", 1.1),
    SkillDefinition("Docker", ("docker",), "tool", 0.9),
    SkillDefinition("Kubernetes", ("kubernetes", "k8s"), "tool", 0.9),
    SkillDefinition("Git", ("git", "github", "gitlab"), "tool", 0.6),
    SkillDefinition("JavaScript", ("javascript", "java script"), "language", 0.85),
    SkillDefinition("MLOps", ("mlops", "ml ops"), "ai", 1.1),
    SkillDefinition("Deep Learning", ("deep learning",), "ai", 1.1),
]

ALIAS_OVERRIDES: dict[str, str] = NORMALIZATION_MAP.copy()

SEMANTIC_RULES: list[tuple[tuple[str, ...], str, float]] = [
    (("openai", "gpt", "chatgpt"), "LLMs", 0.72),
    (("langchain", "llm", "llms"), "RAG", 0.68),
    (("rag", "retrieval"), "Vector DB", 0.65),
    (("chromadb", "chroma"), "Vector DB", 0.70),
    (("fastapi", "python"), "APIs", 0.62),
    (("machine learning", "ml", "pytorch"), "Python", 0.60),
    (("nlp", "natural language"), "Machine Learning", 0.62),
    (("prompt", "llm"), "Prompt Engineering", 0.68),
    (("azure openai", "azure ai"), "OpenAI", 0.75),
    (("gemini", "google"), "LLMs", 0.65),
    (("n8n", "make"), "Automation", 0.65),
    (("n8n", "automation"), "AI Automation", 0.68),
    (("python", "sql"), "Machine Learning", 0.55),
]

_TITLE_PATTERNS: list[tuple[str, str]] = [
    (r"ai solutions engineer", "AI Solutions Engineer"),
    (r"ai automation engineer", "AI Automation Engineer"),
    (r"prompt engineer(?:ing)?", "Prompt Engineer"),
    (r"generative ai engineer", "Generative AI Engineer"),
    (r"machine learning engineer", "Machine Learning Engineer"),
    (r"data(?:\s+&|\s+and)\s+ai specialist", "Data & AI Specialist"),
    (r"data scientist", "Data Scientist"),
    (r"ai engineer", "AI Engineer"),
    (r"llm engineer", "LLM Engineer"),
    (r"nlp engineer", "NLP Engineer"),
]

_SORTED_DEFS = sorted(SKILL_DEFINITIONS, key=lambda d: max(len(a) for a in d.aliases), reverse=True)


def _boundary_pattern(alias: str) -> re.Pattern[str]:
    escaped = re.escape(alias)
    if len(alias) <= 3 and " " not in alias:
        return re.compile(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", re.I)
    if " " in alias or "-" in alias:
        return re.compile(escaped, re.I)
    return re.compile(rf"\b{escaped}\b", re.I)


def _alias_in_text(alias: str, lower: str) -> bool:
    if _boundary_pattern(alias).search(lower):
        return True
    if len(alias) >= 3 and alias in lower:
        for m in re.finditer(re.escape(alias), lower):
            before = lower[m.start() - 1] if m.start() > 0 else " "
            after = lower[m.end()] if m.end() < len(lower) else " "
            if not before.isalnum() and not after.isalnum():
                return True
    return False


def _fuzzy_ratio(a: str, b: str) -> float:
    a = a.lower().replace(" ", "").replace("-", "")
    b = b.lower().replace(" ", "").replace("-", "")
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def _regex_pass(text: str) -> list[ExtractedSkill]:
    """Dictionary regex scan on full text."""
    if not text:
        return []
    lower = text.lower()
    found: dict[str, ExtractedSkill] = {}
    for canonical, patterns in TECH_SKILL_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, lower, re.I):
                conf = 0.94 if canonical in TECH_SKILL_DICTIONARY else 0.86
                found[canonical.lower()] = ExtractedSkill(canonical, conf, "regex", pat)
                break
    return list(found.values())


def _keyword_pass(text: str) -> list[ExtractedSkill]:
    if not text:
        return []
    lower = text.lower()
    found: dict[str, ExtractedSkill] = {}

    def add(defn: SkillDefinition, conf: float, method: str, term: str) -> None:
        key = defn.canonical.lower()
        skill = ExtractedSkill(defn.canonical, round(conf, 2), method, term)
        if key not in found or skill.confidence > found[key].confidence:
            found[key] = skill

    for definition in _SORTED_DEFS:
        for alias in sorted(definition.aliases + definition.synonyms, key=len, reverse=True):
            if _alias_in_text(alias, lower):
                conf = 0.90 if len(alias) >= 5 else 0.84
                if definition.canonical in TECH_SKILL_DICTIONARY:
                    conf = min(0.98, conf + 0.04)
                add(definition, conf, "keyword", alias)
                break

    segments = re.split(r"[,;|•\n/]+", lower)
    for segment in segments:
        segment = segment.strip(" .-•")
        if len(segment) < 2:
            continue
        for definition in SKILL_DEFINITIONS:
            for alias in definition.aliases + definition.synonyms:
                if segment == alias or segment.endswith(f" {alias}") or segment.startswith(f"{alias} "):
                    add(definition, 0.88, "keyword", alias)

    return list(found.values())


def _fuzzy_pass(text: str, already: set[str]) -> tuple[list[ExtractedSkill], list[str]]:
    lower = text.lower()
    tokens = re.findall(r"[a-z0-9+#.-]{2,}", lower)
    bigrams = [f"{tokens[i]} {tokens[i+1]}" for i in range(len(tokens) - 1)]
    candidates = tokens + bigrams
    found: list[ExtractedSkill] = []
    rejected: list[str] = []

    for definition in SKILL_DEFINITIONS:
        if definition.canonical.lower() in already:
            continue
        best_ratio = 0.0
        best_alias = ""
        for candidate in candidates:
            for alias in definition.aliases:
                ratio = _fuzzy_ratio(candidate, alias)
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_alias = alias
        if best_ratio >= _FUZZY_ACCEPT:
            conf = 0.62 + (best_ratio - _FUZZY_ACCEPT) * 1.2
            found.append(ExtractedSkill(definition.canonical, round(min(0.88, conf), 2), "fuzzy", best_alias))
        elif best_ratio >= _FUZZY_REJECT_LOG:
            rejected.append(f"{definition.canonical}~{best_alias}({best_ratio:.2f})")

    return found, rejected


def _semantic_pass(text: str, already: set[str]) -> list[ExtractedSkill]:
    lower = text.lower()
    found: list[ExtractedSkill] = []
    for anchors, canonical, conf in SEMANTIC_RULES:
        if canonical.lower() in already:
            continue
        if any(anchor in lower for anchor in anchors):
            found.append(ExtractedSkill(canonical, conf, "semantic", anchors[0]))
    return found


def _heuristic_pass(text: str, already: set[str]) -> list[ExtractedSkill]:
    """Skills-section focus + co-mention lines from CV layout."""
    found: list[ExtractedSkill] = []
    sections = [text]
    if m := _SKILLS_SECTION.search(text):
        sections.append(m.group(1))

    # Lines that look like skill lists (comma-separated tech terms)
    for line in text.splitlines():
        if line.count(",") >= 2 and len(line) < 200:
            sections.append(line)

    seen = set(already)
    for section in sections:
        hits = _regex_pass(section) + _keyword_pass(section)
        for skill in hits:
            key = skill.skill.lower()
            if key not in seen:
                seen.add(key)
                found.append(ExtractedSkill(skill.skill, min(0.91, skill.confidence), "heuristic", skill.matched_term))

    return found


def _merge_skills(*groups: list[ExtractedSkill]) -> tuple[list[ExtractedSkill], list[str]]:
    merged: dict[str, ExtractedSkill] = {}
    methods_seen: dict[str, set[str]] = {}
    filtered_out: list[str] = []

    for group in groups:
        for skill in group:
            key = skill.skill.lower()
            methods_seen.setdefault(key, set()).add(skill.method)
            existing = merged.get(key)
            if not existing:
                merged[key] = skill
            else:
                new_conf = max(existing.confidence, skill.confidence)
                if len(methods_seen[key]) > 1:
                    new_conf = min(0.99, new_conf + 0.04 * (len(methods_seen[key]) - 1))
                merged[key] = ExtractedSkill(
                    skill.skill,
                    round(new_conf, 2),
                    "merged" if len(methods_seen[key]) > 1 else existing.method,
                    existing.matched_term or skill.matched_term,
                )

    pre_filter = sorted(merged.values(), key=lambda s: s.confidence, reverse=True)
    for skill in pre_filter:
        if skill.confidence < MIN_OUTPUT_CONFIDENCE:
            filtered_out.append(f"{skill.skill}({skill.confidence:.2f})")

    result = [s for s in pre_filter if s.confidence >= MIN_OUTPUT_CONFIDENCE]
    return result, filtered_out


def _normalize_skills(skills: list[ExtractedSkill]) -> list[ExtractedSkill]:
    """Apply explicit normalization map to skill names."""
    out: list[ExtractedSkill] = []
    seen: set[str] = set()
    for skill in skills:
        canonical = NORMALIZATION_MAP.get(skill.skill.lower(), skill.skill)
        key = canonical.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(ExtractedSkill(canonical, skill.confidence, skill.method, skill.matched_term))
    return out


def extract_skills_balanced(text: str, limit: int = MAX_OUTPUT_SKILLS, *, quiet: bool = False) -> SkillExtractionResult:
    """Full multi-pass extraction on entire CV text."""
    regex_hits = _regex_pass(text)
    regex_keys = {s.skill.lower() for s in regex_hits}

    keyword_hits = _keyword_pass(text)
    keyword_keys = regex_keys | {s.skill.lower() for s in keyword_hits}

    fuzzy_hits, rejected = _fuzzy_pass(text, keyword_keys)
    fuzzy_keys = keyword_keys | {s.skill.lower() for s in fuzzy_hits}

    semantic_hits = _semantic_pass(text, fuzzy_keys)
    semantic_keys = fuzzy_keys | {s.skill.lower() for s in semantic_hits}

    heuristic_hits = _heuristic_pass(text, semantic_keys)

    merged, filtered_out = _merge_skills(regex_hits, keyword_hits, fuzzy_hits, semantic_hits, heuristic_hits)
    normalized_list = _normalize_skills(merged)
    final = normalized_list[:limit]
    normalized = [s.skill for s in final]

    if not quiet:
        logger.info(
            "[skill-extract] text_len=%s stages: regex=%s keyword=%s fuzzy=%s semantic=%s heuristic=%s",
            len(text),
            [s.skill for s in regex_hits],
            [s.skill for s in keyword_hits],
            [s.skill for s in fuzzy_hits],
            [s.skill for s in semantic_hits],
            [s.skill for s in heuristic_hits],
        )
        logger.info(
            "[skill-extract] merged=%s normalized=%s filtered_out=%s rejected=%s",
            [s.skill for s in merged],
            normalized,
            filtered_out[:20],
            rejected[:15],
        )
        logger.info(
            "[skill-extract] confidence=%s",
            [(s.skill, s.confidence, s.method) for s in final],
        )

    return SkillExtractionResult(
        skills=final,
        raw_regex=[s.skill for s in regex_hits],
        raw_keyword=[s.skill for s in keyword_hits],
        raw_fuzzy=[s.skill for s in fuzzy_hits],
        raw_semantic=[s.skill for s in semantic_hits],
        raw_heuristic=[s.skill for s in heuristic_hits],
        merged=[s.skill for s in merged],
        normalized=normalized,
        filtered_out=filtered_out,
        rejected=rejected,
        scan_text_len=len(text),
    )


def extract_skills_semantic(text: str, limit: int = MAX_OUTPUT_SKILLS) -> list[ExtractedSkill]:
    return extract_skills_balanced(text, limit=limit).skills


def extract_skills_from_text(text: str, limit: int = MAX_OUTPUT_SKILLS) -> list[str]:
    return extract_skills_balanced(text, limit=limit).normalized


def normalize_skill_token(token: str) -> str | None:
    cleaned = token.strip()
    if not cleaned:
        return None
    lower = cleaned.lower()
    if lower in NORMALIZATION_MAP:
        return NORMALIZATION_MAP[lower]
    for definition in SKILL_DEFINITIONS:
        if lower == definition.canonical.lower():
            return definition.canonical
        if lower in definition.aliases or lower in definition.synonyms:
            return definition.canonical
    return cleaned.title() if len(cleaned) > 2 else None


def normalize_skill_list(items: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for item in items:
        canonical = normalize_skill_token(item)
        if canonical and canonical.lower() not in seen:
            seen.add(canonical.lower())
            result.append(canonical)
    return result


def normalize_skill_set(items: list[str]) -> set[str]:
    return {s.lower() for s in normalize_skill_list(items)}


def get_skill_weight(canonical: str) -> float:
    for definition in SKILL_DEFINITIONS:
        if definition.canonical.lower() == canonical.lower():
            return definition.weight
    return 0.8


def _normalize_key(skill: str) -> str:
    return NORMALIZATION_MAP.get(skill.lower(), skill).lower()


def get_related_skills(skill: str) -> set[str]:
    """Return related skill keys for semantic matching."""
    key = _normalize_key(skill)
    related: set[str] = {key}
    if key in SEMANTIC_SKILL_GRAPH:
        related |= SEMANTIC_SKILL_GRAPH[key]
    for graph_key, graph_vals in SEMANTIC_SKILL_GRAPH.items():
        if key in graph_vals or key == graph_key:
            related.add(graph_key)
            related |= graph_vals
    return related


def resolve_skill_match(job_skill: str, cv_labels: dict[str, str]) -> tuple[str | None, str]:
    """
    Find best CV skill match for a job skill.
    Returns (cv_canonical_label, match_type) where match_type is exact|related|fuzzy.
    """
    job_key = _normalize_key(job_skill)
    cv_keys = set(cv_labels.keys())

    if job_key in cv_keys:
        return cv_labels[job_key], "exact"

    for cv_key, cv_label in cv_labels.items():
        if job_key in cv_key or cv_key in job_key:
            return cv_label, "exact"

    job_related = get_related_skills(job_skill)
    for cv_key, cv_label in cv_labels.items():
        cv_related = get_related_skills(cv_label)
        if job_related & cv_related:
            return cv_label, "related"
        if cv_key in job_related or job_key in cv_related:
            return cv_label, "related"

    for cv_key, cv_label in cv_labels.items():
        if SequenceMatcher(None, job_key, cv_key).ratio() >= 0.88:
            return cv_label, "fuzzy"

    return None, ""


def extract_job_titles(text: str, limit: int = 5) -> list[str]:
    lower = text.lower()
    titles: list[str] = []
    seen: set[str] = set()
    for pattern, label in _TITLE_PATTERNS:
        if re.search(pattern, lower, re.I) and label.lower() not in seen:
            seen.add(label.lower())
            titles.append(label)
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or len(stripped) > 120:
            continue
        if "@" in stripped:
            continue
        role_part = re.split(r"[|@•–—\-/]", stripped)[0].strip()
        for pattern, label in _TITLE_PATTERNS:
            if re.search(pattern, role_part.lower(), re.I) and label.lower() not in seen:
                seen.add(label.lower())
                titles.append(label)
                break
    return titles[:limit] or ["AI / Data Professional"]


def extract_years_experience(text: str) -> int:
    lower = text.lower()
    explicit_years: list[int] = []
    for m in re.finditer(r"(\d{1,2})\+?\s*(?:years?|yrs?)(?:\s+of)?\s+(?:experience|exp\b)", lower):
        explicit_years.append(int(m.group(1)))
    for m in re.finditer(r"(\d{1,2})\+?\s*years?\b", lower):
        explicit_years.append(int(m.group(1)))
    if explicit_years:
        return max(explicit_years)
    return 3


def extract_tools_from_skills(skills: list[str]) -> list[str]:
    return [s for s in skills if s in TOOL_SKILLS]


def extract_ai_tools(skills: list[str], text: str = "") -> list[str]:
    """AI-specific tools/platforms from extracted skills and raw CV text."""
    found = [s for s in normalize_skill_list(skills) if s in AI_TOOL_SKILLS]
    if text:
        mined = extract_skills_balanced(text, limit=24, quiet=True).normalized
        for skill in mined:
            if skill in AI_TOOL_SKILLS and skill not in found:
                found.append(skill)
    return found[:14]
