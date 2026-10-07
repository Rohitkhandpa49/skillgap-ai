"""Text sanitization and conservative normalization for extracted resume text.

Preserves critical technical punctuation:
- C++, C#, .NET, Node.js, React.js, Python 3, ASP.NET, CI/CD, REST/API, PostgreSQL
- Preserves full human-readable sentence structure (does NOT reduce to bag-of-words)
- Normalizes unicode artifacts, non-standard bullets, and excessive whitespace
- Never executes embedded text or evaluates prompt instructions (treats text purely as inert data)
"""

import re
import unicodedata

# Common bullet characters in PDF / Word documents
BULLET_CHARS = r"[\u2022\u2023\u25E6\u2043\u2219\u25CB\u25CF\u25AA\u25AB\u25C6\u25C7\u27A2\u27A4\u2192]"


def clean_resume_text(raw_text: str) -> str:
    """Conservatively clean raw extracted resume text while preserving technical tokens and sentence structure.

    Args:
        raw_text: Raw string extracted from PDF or DOCX parser.

    Returns:
        Sanitized, normalized human-readable text.
    """
    if not raw_text:
        return ""

    # 1. Unicode Normalization (NFKC standardizes weird typography, quotes, and accents)
    text = unicodedata.normalize("NFKC", raw_text)

    # 2. Normalize non-standard space characters (nbsp, zero-width space, thin space)
    text = text.replace("\u00a0", " ").replace("\u200b", "").replace("\ufeff", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 3. Standardize bullet points to a clean dash bullet
    text = re.sub(rf"(?:^|\n)\s*{BULLET_CHARS}+\s*", r"\n- ", text)

    # 4. Clean line by line
    cleaned_lines = []
    for line in text.split("\n"):
        # Strip trailing and leading whitespace for each line
        stripped_line = line.strip()

        # Collapse repeated horizontal whitespace inside line (e.g. multiple spaces or tabs)
        collapsed_line = re.sub(r"[ \t]+", " ", stripped_line)

        # Drop lines that are purely repeated decorative characters (e.g. "------" or "========")
        if re.match(r"^[\-_=*~#]{4,}$", collapsed_line):
            continue

        cleaned_lines.append(collapsed_line)

    # 5. Join lines and normalize vertical whitespace (max 2 consecutive newlines)
    full_text = "\n".join(cleaned_lines)
    full_text = re.sub(r"\n{3,}", "\n\n", full_text)

    return full_text.strip()
