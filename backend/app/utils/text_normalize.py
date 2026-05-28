"""Clean and normalize text extracted from PDF/DOCX CVs."""

import re
import unicodedata

# Applied after spaced-letter repair
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
    "vector databases": "Vector DB",
    "azure ai": "Azure AI",
    "azure openai": "Azure AI",
    "ibm watson": "Watson",
    "watsonx": "Watson",
    "open ai": "OpenAI",
    "openai": "OpenAI",
    "chat gpt": "ChatGPT",
    "chatgpt": "OpenAI",
    "gpt-4": "OpenAI",
    "gpt-4o": "OpenAI",
    "gpt-3.5": "OpenAI",
    "fast api": "FastAPI",
    "fastapi": "FastAPI",
    "lang chain": "LangChain",
    "langchain": "LangChain",
    "chroma db": "ChromaDB",
    "chromadb": "ChromaDB",
    "gemini api": "Gemini",
    "google gemini": "Gemini",
    "gemini": "Gemini",
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
    "postgresql": "SQL",
    "mysql": "SQL",
    "rest api": "APIs",
    "rest apis": "APIs",
    "apis": "APIs",
    "api": "APIs",
    "javascript": "JavaScript",
    "docker": "Docker",
    "git": "Git",
    "github": "Git",
    "n8n": "n8n",
    "make": "Make",
    "automation": "Automation",
    "java script": "JavaScript",
}

_KNOWN_PHRASES: tuple[str, ...] = tuple(
    sorted(set(NORMALIZATION_MAP.keys()) | {
        "prompt engineer", "workflow automation", "intelligent automation",
        "hugging face", "scikit-learn", "pytorch", "tensorflow", "kubernetes",
    }, key=len, reverse=True)
)

# PDF often extracts "P y t h o n" — collapse letter-space-letter runs
_SPACED_LETTERS = re.compile(
    r"(?<![A-Za-z0-9])([A-Za-z](?: [A-Za-z]){1,})(?![A-Za-z0-9])"
)


def collapse_spaced_letters(text: str) -> str:
    """
    Repair PDF extraction that inserts spaces between every letter.
    'P y t h o n' -> 'Python', 'S Q L' -> 'SQL', 'L L M' -> 'LLM'
    Preserves tokens like 'n8n' (digit breaks the pattern).
    """
    prev = None
    while prev != text:
        prev = text
        text = _SPACED_LETTERS.sub(lambda m: m.group(1).replace(" ", ""), text)
    return text


def apply_normalization_map(text: str) -> str:
    """Replace known lowercase phrases with canonical skill labels in-place."""
    lower = text.lower()
    for phrase in _KNOWN_PHRASES:
        canonical = NORMALIZATION_MAP.get(phrase, phrase)
        start = 0
        while True:
            idx = lower.find(phrase, start)
            if idx == -1:
                break
            end = idx + len(phrase)
            before = lower[idx - 1] if idx > 0 else " "
            after = lower[end] if end < len(lower) else " "
            if not before.isalnum() and not after.isalnum():
                text = text[:idx] + canonical + text[end:]
                lower = text.lower()
                start = idx + len(canonical)
            else:
                start = idx + 1
    return text


def normalize_extracted_text(text: str) -> str:
    """Fix PDF/DOCX spacing issues while preserving word boundaries."""
    if not text:
        return ""

    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\u00ad", "").replace("\ufb01", "fi").replace("\ufb02", "fl")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[\u200b-\u200d\ufeff]", "", text)

    # Join hyphenated line breaks (soft hyphen already removed)
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)

    # CRITICAL: repair letter-spaced PDF text BEFORE other transforms
    text = collapse_spaced_letters(text)

    # camelCase / digits — adds spaces, never removes interior word spaces
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
    text = re.sub(r"([a-zA-Z])(\d)", r"\1 \2", text)
    text = re.sub(r"(\d)([a-zA-Z])", r"\1 \2", text)

    # Normalize list delimiters for skill parsing
    text = re.sub(r"\s*[|·]\s*", ", ", text)
    text = re.sub(r"\s*/\s*", ", ", text)

    # Punctuation spacing — keep single spaces between words
    text = re.sub(r"([.,;:])([A-Za-z0-9])", r"\1 \2", text)
    text = re.sub(r"([A-Za-z0-9])([.,;:])(?=[A-Za-z0-9])", r"\1\2 ", text)
    text = re.sub(r"\s+([.,;:!?])", r"\1", text)

    glued_fixes = [
        (r"Python\s*SQL", "Python, SQL"),
        (r"PythonSQL", "Python, SQL"),
        (r"Lang\s*Chain", "LangChain"),
        (r"Chat\s*GPT", "ChatGPT"),
        (r"GPT\s*-\s*4", "GPT-4"),
        (r"Py\s*Torch", "PyTorch"),
        (r"Fast\s*API", "FastAPI"),
        (r"Chroma\s*DB", "ChromaDB"),
        (r"Open\s*AI", "OpenAI"),
        (r"Generative\s*AI", "Generative AI"),
        (r"Vector\s*DB", "Vector DB"),
        (r"Machine\s*Learning", "Machine Learning"),
        (r"Prompt\s*Engineering", "Prompt Engineering"),
        (r"AI\s*Automation", "AI Automation"),
        (r"Gemini\s*API", "Gemini"),
        (r"Java\s*Script", "JavaScript"),
        (r"REST\s*APIs?", "REST APIs"),
        (r"n\s*8\s*n", "n8n"),
    ]
    for pattern, replacement in glued_fixes:
        text = re.sub(pattern, replacement, text, flags=re.I)

    text = _split_embedded_phrases(text)
    text = apply_normalization_map(text)
    text = re.sub(r"[•●▪◦‣⁃]", ", ", text)

    lines: list[str] = []
    for raw_line in text.split("\n"):
        # Collapse horizontal whitespace to single space — never remove spaces between words
        line = re.sub(r"[ \t]+", " ", raw_line).strip()
        line = re.sub(r",\s*,", ", ", line)
        if line:
            lines.append(line)
        elif lines and lines[-1] != "":
            lines.append("")

    return "\n".join(lines).strip()


def _split_embedded_phrases(text: str) -> str:
    lower = text.lower()
    for phrase in _KNOWN_PHRASES:
        start = 0
        while True:
            idx = lower.find(phrase, start)
            if idx == -1:
                break
            end = idx + len(phrase)
            before = lower[idx - 1] if idx > 0 else " "
            after = lower[end] if end < len(lower) else " "
            if not before.isalnum() and not after.isalnum():
                original = text[idx:end]
                text = text[:idx] + f" {original} " + text[end:]
                lower = text.lower()
                start = idx + len(original) + 2
            else:
                start = idx + 1
    return re.sub(r" {2,}", " ", text)
