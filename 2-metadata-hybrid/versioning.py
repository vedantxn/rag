"""Resolve doc version from explicit arg and/or question text."""

from __future__ import annotations

import re

# Matches v1 / v2 as a version token (not inside longer words)
VERSION_RE = re.compile(r"\b(v[12])\b", re.IGNORECASE)
# "version 2" / "version 1"
VERSION_WORD_RE = re.compile(r"\bversion\s*([12])\b", re.IGNORECASE)


def parse_version_from_question(question: str) -> str | None:
    """Return 'v1' / 'v2' if mentioned in the question, else None."""
    m = VERSION_RE.search(question)
    if m:
        return m.group(1).lower()
    m = VERSION_WORD_RE.search(question)
    if m:
        return f"v{m.group(1)}"
    return None


def resolve_version(explicit: str | None, question: str) -> str | None:
    """
    Explicit CLI/API version wins; otherwise parse from question.
    Returns None if neither provides a version (search all).
    """
    if explicit:
        v = explicit.strip().lower()
        if not re.fullmatch(r"v[12]", v):
            raise ValueError(f"version must be v1 or v2, got {explicit!r}")
        return v
    return parse_version_from_question(question)


def strip_version_phrases(question: str) -> str:
    """Optional: remove 'in v2' style phrases so search focuses on the topic."""
    q = VERSION_WORD_RE.sub(" ", question)
    q = re.sub(r"\bin\s+v[12]\b", " ", q, flags=re.IGNORECASE)
    q = VERSION_RE.sub(" ", q)
    return re.sub(r"\s+", " ", q).strip()
