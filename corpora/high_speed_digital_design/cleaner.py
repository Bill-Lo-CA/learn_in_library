"""Corpus-specific cleanup for the high-speed digital design PDF."""

from __future__ import annotations

import re


_NOISE_PATTERNS = [
    re.compile(r"^\s*High-Speed Digital System Design\s*$", re.IGNORECASE),
    re.compile(r"^\s*A Handbook of Interconnect Theory and Design Practices\s*$", re.IGNORECASE),
]


def clean_page(text: str, page_number: int) -> str:
    """Clean one extracted PDF page."""

    lines = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            lines.append("")
            continue
        if line.isdigit() and int(line) in {page_number, page_number - 1, page_number + 1}:
            continue
        if any(pattern.match(line) for pattern in _NOISE_PATTERNS):
            continue
        lines.append(line)

    cleaned = "\n".join(lines)
    cleaned = re.sub(r"-\n(?=[a-z])", "", cleaned)
    cleaned = re.sub(r"(?<![.!?:;])\n(?!\n)", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned)
    return cleaned.strip()
