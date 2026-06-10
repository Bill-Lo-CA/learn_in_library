from pathlib import Path

import pytest

from rag_workspace.chunking import Chunk
from rag_workspace.vector_store import build_vector_index, read_vector_index_metadata, search_vector_index


def test_hashed_vector_index_finds_matching_chunk(tmp_path: Path):
    chunks = [
        Chunk(
            chunk_id="a",
            corpus_id="demo",
            source="demo.pdf",
            page_start=1,
            page_end=1,
            text="impedance discontinuity causes signal reflection",
        ),
        Chunk(
            chunk_id="b",
            corpus_id="demo",
            source="demo.pdf",
            page_start=2,
            page_end=2,
            text="thermal layout copper plane",
        ),
    ]

    build_vector_index(
        chunks=chunks,
        index_dir=tmp_path,
        dimensions=64,
        embedding_provider="hashed_tfidf",
        embedding_model="",
        ollama_host="http://localhost:11434",
        batch_size=2,
    )
    results = search_vector_index(
        chunks=chunks,
        index_dir=tmp_path,
        question="signal reflection",
        top_k=1,
        ollama_host="http://localhost:11434",
    )

    assert results[0].chunk.chunk_id == "a"


def test_read_vector_index_metadata_returns_index_model(tmp_path: Path):
    chunks = [
        Chunk(
            chunk_id="a",
            corpus_id="demo",
            source="demo.pdf",
            page_start=1,
            page_end=1,
            text="signal reflection",
        ),
    ]

    build_vector_index(
        chunks=chunks,
        index_dir=tmp_path,
        dimensions=64,
        embedding_provider="hashed_tfidf",
        embedding_model="",
        ollama_host="http://localhost:11434",
        batch_size=2,
    )

    metadata = read_vector_index_metadata(tmp_path)

    assert metadata["kind"] == "hashed_tfidf_vector_v1"
    assert metadata["provider"] == "local"


def test_read_vector_index_metadata_reports_missing_index(tmp_path: Path):
    with pytest.raises(FileNotFoundError, match="Missing vector index metadata"):
        read_vector_index_metadata(tmp_path)
