from __future__ import annotations

from .retrieval import RetrievedChunk


def build_prompt(question: str, retrieved: list[RetrievedChunk]) -> str:
    context_blocks = []
    for idx, item in enumerate(retrieved, start=1):
        chunk = item.chunk
        citation = f"{chunk.source}, pages {chunk.page_start}-{chunk.page_end}"
        context_blocks.append(f"[{idx}] {citation}\n{chunk.text}")

    context = "\n\n".join(context_blocks)
    return f"""You are answering from a retrieved technical book context.

Rules:
- Answer only from the context below.
- If the context is insufficient, say what is missing.
- Cite sources with bracket numbers like [1] and include page ranges when useful.
- Be concise and technical.

Context:
{context}

Question:
{question}

Answer:
"""
