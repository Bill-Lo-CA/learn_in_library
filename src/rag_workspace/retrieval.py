from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass

from .chunking import Chunk


_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "with",
}


@dataclass(frozen=True)
class RetrievedChunk:
    chunk: Chunk
    score: float


def retrieve_chunks(chunks: list[Chunk], question: str, top_k: int) -> list[RetrievedChunk]:
    query_terms = tokenize(question)
    if not query_terms:
        return []

    chunk_terms = [Counter(tokenize(chunk.text)) for chunk in chunks]
    doc_freq = Counter()
    for terms in chunk_terms:
        doc_freq.update(terms.keys())

    query_counts = Counter(query_terms)
    results: list[RetrievedChunk] = []
    total_docs = max(len(chunks), 1)

    for chunk, terms in zip(chunks, chunk_terms, strict=True):
        score = 0.0
        length_norm = math.sqrt(sum(count * count for count in terms.values())) or 1.0
        for term, query_count in query_counts.items():
            if term not in terms:
                continue
            idf = math.log((1 + total_docs) / (1 + doc_freq[term])) + 1
            score += (terms[term] * query_count * idf) / length_norm
        if score > 0:
            results.append(RetrievedChunk(chunk=chunk, score=score))

    results.sort(key=lambda item: item.score, reverse=True)
    return results[:top_k]


def tokenize(text: str) -> list[str]:
    terms = [term.lower() for term in re.findall(r"[A-Za-z][A-Za-z0-9_+-]*", text)]
    return [term for term in terms if term not in _STOPWORDS and len(term) > 1]
