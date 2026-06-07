from __future__ import annotations

import json

from .answer import build_prompt
from .chunking import Chunk, chunk_pages
from .cleaning import load_cleaner
from .config import load_corpus_config
from .ollama_client import generate
from .pdf_extract import extract_pdf_pages
from .retrieval import RetrievedChunk, retrieve_chunks
from .storage import read_chunks, write_chunks


def ingest(corpus_id: str) -> list[Chunk]:
    config = load_corpus_config(corpus_id)
    cleaner = load_cleaner(config.cleaner_file, config.cleaner_function)

    all_chunks: list[Chunk] = []
    for source_path in config.source_files:
        if not source_path.exists():
            raise FileNotFoundError(f"Missing source PDF: {source_path}")
        pages = []
        for page_number, text in extract_pdf_pages(source_path):
            cleaned = cleaner(text, page_number)
            if cleaned:
                pages.append((page_number, cleaned))
        all_chunks.extend(
            chunk_pages(
                corpus_id=config.corpus_id,
                source_name=source_path.name,
                pages=pages,
                chunk_words=config.chunk_words,
                overlap_words=config.chunk_overlap_words,
            )
        )

    write_chunks(config.chunks_path, all_chunks)
    config.index_dir.mkdir(parents=True, exist_ok=True)
    metadata_path = config.index_dir / "metadata.json"
    metadata_path.write_text(
        json.dumps(
            {
                "corpus_id": config.corpus_id,
                "chunk_count": len(all_chunks),
                "source_files": [path.name for path in config.source_files],
                "retrieval": "lexical_tfidf_v1",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return all_chunks


def retrieve(corpus_id: str, question: str, top_k: int | None = None) -> list[RetrievedChunk]:
    config = load_corpus_config(corpus_id)
    chunks = read_chunks(config.chunks_path)
    return retrieve_chunks(chunks, question, top_k or config.top_k)


def ask(corpus_id: str, question: str) -> str:
    config = load_corpus_config(corpus_id)
    retrieved = retrieve(corpus_id, question, config.top_k)
    if not retrieved:
        return "No relevant chunks were found. Try ingesting the corpus or rephrasing the question."
    prompt = build_prompt(question, retrieved)
    return generate(config.ollama_host, config.answer_model, prompt)
