"""Section-aware chunker (PART2_PLAN Task 2.2): long documents -> sections.

Splits at heading boundaries (markdown #, numbered clauses, ALL-CAPS titles,
"Section N" lines); oversized sections split further at paragraph breaks.
Deterministic, stdlib only. Headings stay attached to their section.
"""

from __future__ import annotations

import re

_HEADING = re.compile(
    r"^(#{1,4}\s+.+|\d+(?:\.\d+)*[.\)]\s+.+|[A-Z][A-Z0-9 \-/&]{3,}|Section\s+\d+.*)$"
)


def split_headings(text: str) -> list:
    """Split text into (heading, body) sections; heading '' when absent."""
    sections, heading, buf = [], "", []
    for line in text.splitlines(keepends=True):
        stripped = line.strip()
        if stripped and _HEADING.match(stripped):
            sections.append((heading, "".join(buf)))
            heading, buf = stripped, []
        else:
            buf.append(line)
    sections.append((heading, "".join(buf)))
    return [(h, b) for h, b in sections if h or b.strip()]


def chunk(text: str, max_chars: int = 4000) -> list:
    """Return [{index, heading, text}] chunks, each <= max_chars when possible."""
    chunks = []
    for heading, body in split_headings(text):
        section = (heading + "\n" + body) if heading else body
        if len(section) <= max_chars:
            chunks.append({"heading": heading, "text": section})
            continue
        for para in _split_paragraphs(section, max_chars):
            chunks.append({"heading": heading, "text": para})
    for i, entry in enumerate(chunks):
        entry["index"] = i
    return chunks


def _split_paragraphs(section: str, max_chars: int) -> list:
    parts, current = [], ""
    for para in re.split(r"\n\s*\n", section):
        candidate = (current + "\n\n" + para).strip() if current else para.strip()
        if len(candidate) <= max_chars or not current:
            current = candidate
        else:
            parts.append(current)
            current = para.strip()
    if current:
        parts.append(current)
    return parts or [section]
