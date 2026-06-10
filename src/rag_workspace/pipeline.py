from __future__ import annotations

import json

from .answer import build_prompt
from .chunking import Chunk, chunk_pages
from .cleaning import load_cleaner
from .config import load_corpus_config
from .ollama_client import generate, require_model
from .pdf_extract import extract_pdf_pages
from .retrieval import RetrievedChunk, retrieve_chunks
from .storage import read_chunks, write_chunks
from .vector_store import build_vector_index, read_vector_index_metadata, search_vector_index


def ingest(corpus_id: str, embedding_model: str | None = None) -> list[Chunk]:
    config = load_corpus_config(corpus_id)
    selected_embedding_model = embedding_model or config.embedding_model
    if config.embedding_provider == "ollama":
        require_model(config.ollama_host, selected_embedding_model, "embedding")
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
    build_vector_index(
        chunks=all_chunks,
        index_dir=config.index_dir,
        dimensions=config.vector_dimensions,
        embedding_provider=config.embedding_provider,
        embedding_model=selected_embedding_model,
        ollama_host=config.ollama_host,
        batch_size=config.embedding_batch_size,
    )
    metadata_path = config.index_dir / "metadata.json"
    metadata_path.write_text(
        json.dumps(
            {
                "corpus_id": config.corpus_id,
                "chunk_count": len(all_chunks),
                "source_files": [path.name for path in config.source_files],
                "retrieval": "vector_embedding_v1",
                "fallback_retrieval": "lexical_tfidf_v1",
                "embedding_provider": config.embedding_provider,
                "embedding_model": selected_embedding_model,
                "vector_dimensions": config.vector_dimensions,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return all_chunks


def retrieve(
    corpus_id: str,
    question: str,
    top_k: int | None = None,
    backend: str | None = None,
) -> list[RetrievedChunk]:
    config = load_corpus_config(corpus_id)
    chunks = read_chunks(config.chunks_path)
    selected_backend = backend or config.retrieval_backend
    if selected_backend == "lexical":
        return retrieve_chunks(chunks, question, top_k or config.top_k)
    if selected_backend == "vector":
        if config.embedding_provider == "ollama":
            metadata = read_vector_index_metadata(config.index_dir)
            indexed_model = str(metadata.get("model") or config.embedding_model)
            require_model(config.ollama_host, indexed_model, "embedding")
        return search_vector_index(chunks, config.index_dir, question, top_k or config.top_k, config.ollama_host)
    raise ValueError(f"Unsupported retrieval backend: {selected_backend}")


def ask(corpus_id: str, question: str, backend: str | None = None) -> str:
    config = load_corpus_config(corpus_id)
    require_model(config.ollama_host, config.answer_model, "answer generation")
    retrieved = retrieve(corpus_id, question, config.top_k, backend or config.retrieval_backend)
    if not retrieved:
        return "No relevant chunks were found. Try ingesting the corpus or rephrasing the question."
    prompt = build_prompt(question, retrieved)
    return generate(config.ollama_host, config.answer_model, prompt)
