from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    corpus_id: str
    source: str
    page_start: int
    page_end: int
    text: str


def chunk_pages(
    corpus_id: str,
    source_name: str,
    pages: list[tuple[int, str]],
    chunk_words: int,
    overlap_words: int,
) -> list[Chunk]:
    if chunk_words <= 0:
        raise ValueError("chunk_words must be positive")
    if overlap_words < 0 or overlap_words >= chunk_words:
        raise ValueError("chunk_overlap_words must be >= 0 and smaller than chunk_words")

    chunks: list[Chunk] = []
    current: list[tuple[str, int]] = []

    for page_number, text in pages:
        for word in _words(text):
            current.append((word, page_number))
            if len(current) >= chunk_words:
                chunks.append(_make_chunk(corpus_id, source_name, current))
                current = current[-overlap_words:] if overlap_words else []

    if current:
        chunks.append(_make_chunk(corpus_id, source_name, current))

    return chunks


def _words(text: str) -> list[str]:
    return re.findall(r"\S+", text)


def _make_chunk(corpus_id: str, source_name: str, words: list[tuple[str, int]]) -> Chunk:
    text = " ".join(word for word, _page in words).strip()
    page_start = min(page for _word, page in words)
    page_end = max(page for _word, page in words)
    digest = hashlib.sha1(f"{source_name}:{page_start}:{page_end}:{text}".encode("utf-8")).hexdigest()[:16]
    return Chunk(
        chunk_id=f"{source_name}:{page_start}-{page_end}:{digest}",
        corpus_id=corpus_id,
        source=source_name,
        page_start=page_start,
        page_end=page_end,
        text=text,
    )
