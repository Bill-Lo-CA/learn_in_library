from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .chunking import Chunk
from .ollama_client import embed
from .retrieval import RetrievedChunk, tokenize


@dataclass(frozen=True)
class VectorIndexPaths:
    metadata: Path
    records: Path


def build_vector_index(
    chunks: list[Chunk],
    index_dir: Path,
    dimensions: int,
    embedding_provider: str,
    embedding_model: str,
    ollama_host: str,
    batch_size: int,
) -> None:
    index_dir.mkdir(parents=True, exist_ok=True)
    paths = vector_index_paths(index_dir)

    if embedding_provider == "ollama":
        _build_ollama_index(
            chunks=chunks,
            paths=paths,
            model=embedding_model,
            host=ollama_host,
            batch_size=batch_size,
        )
        return

    if embedding_provider == "hashed_tfidf":
        _build_hashed_tfidf_index(chunks, paths, dimensions)
        return

    raise ValueError(f"Unsupported embedding_provider: {embedding_provider}")


def search_vector_index(
    chunks: list[Chunk],
    index_dir: Path,
    question: str,
    top_k: int,
    ollama_host: str,
) -> list[RetrievedChunk]:
    paths = vector_index_paths(index_dir)
    if not paths.metadata.exists() or not paths.records.exists():
        raise FileNotFoundError(f"Missing vector index in {index_dir}. Run ingest first.")

    metadata = read_vector_index_metadata(index_dir)
    kind = str(metadata.get("kind", ""))
    if kind == "ollama_embedding_vector_v1":
        query_vector = _normalize_dense(embed(ollama_host, str(metadata["model"]), [question])[0])
        return _search_dense_records(chunks, paths.records, query_vector, top_k)

    if kind == "hashed_tfidf_vector_v1":
        dimensions = int(metadata["dimensions"])
        idf = {str(term): float(value) for term, value in metadata.get("idf", {}).items()}
        query_vector = _vectorize_counts(Counter(tokenize(question)), idf, dimensions)
        return _search_sparse_records(chunks, paths.records, query_vector, top_k)

    raise ValueError(f"Unsupported vector index kind: {kind}")


def read_vector_index_metadata(index_dir: Path) -> dict[str, Any]:
    paths = vector_index_paths(index_dir)
    if not paths.metadata.exists():
        raise FileNotFoundError(f"Missing vector index metadata in {index_dir}. Run ingest first.")
    metadata = json.loads(paths.metadata.read_text(encoding="utf-8"))
    if not isinstance(metadata, dict):
        raise ValueError(f"Expected mapping in vector index metadata: {paths.metadata}")
    return metadata


def vector_index_paths(index_dir: Path) -> VectorIndexPaths:
    return VectorIndexPaths(
        metadata=index_dir / "vector_metadata.json",
        records=index_dir / "vectors.jsonl",
    )


def _build_ollama_index(
    chunks: list[Chunk],
    paths: VectorIndexPaths,
    model: str,
    host: str,
    batch_size: int,
) -> None:
    if batch_size <= 0:
        raise ValueError("embedding_batch_size must be positive")

    vector_count = 0
    vector_dimensions: int | None = None
    with paths.records.open("w", encoding="utf-8") as handle:
        for start in range(0, len(chunks), batch_size):
            batch = chunks[start : start + batch_size]
            vectors = embed(host, model, [chunk.text for chunk in batch])
            if len(vectors) != len(batch):
                raise RuntimeError("Ollama returned a different number of embeddings than requested")
            for chunk, vector in zip(batch, vectors, strict=True):
                normalized = _normalize_dense(vector)
                vector_dimensions = vector_dimensions or len(normalized)
                handle.write(_json_record(chunk.chunk_id, normalized))
                vector_count += 1

    paths.metadata.write_text(
        json.dumps(
            {
                "kind": "ollama_embedding_vector_v1",
                "provider": "ollama",
                "model": model,
                "dimensions": vector_dimensions or 0,
                "chunk_count": vector_count,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _build_hashed_tfidf_index(chunks: list[Chunk], paths: VectorIndexPaths, dimensions: int) -> None:
    if dimensions <= 0:
        raise ValueError("vector_dimensions must be positive")

    tokenized = [Counter(tokenize(chunk.text)) for chunk in chunks]
    doc_freq: Counter[str] = Counter()
    for terms in tokenized:
        doc_freq.update(terms.keys())

    total_docs = max(len(chunks), 1)
    idf = {
        term: math.log((1 + total_docs) / (1 + freq)) + 1
        for term, freq in doc_freq.items()
    }

    with paths.records.open("w", encoding="utf-8") as handle:
        for chunk, terms in zip(chunks, tokenized, strict=True):
            vector = _vectorize_counts(terms, idf, dimensions)
            handle.write(_json_record(chunk.chunk_id, vector))

    paths.metadata.write_text(
        json.dumps(
            {
                "kind": "hashed_tfidf_vector_v1",
                "provider": "local",
                "dimensions": dimensions,
                "chunk_count": len(chunks),
                "idf": idf,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _search_dense_records(
    chunks: list[Chunk],
    records_path: Path,
    query_vector: list[float],
    top_k: int,
) -> list[RetrievedChunk]:
    chunks_by_id = {chunk.chunk_id: chunk for chunk in chunks}
    results: list[RetrievedChunk] = []
    with records_path.open("r", encoding="utf-8") as handle:
        for record in _read_records(handle):
            chunk = chunks_by_id.get(str(record["chunk_id"]))
            if chunk is None:
                continue
            score = _dense_dot(query_vector, record["vector"])
            if score > 0:
                results.append(RetrievedChunk(chunk=chunk, score=score))
    results.sort(key=lambda item: item.score, reverse=True)
    return results[:top_k]


def _search_sparse_records(
    chunks: list[Chunk],
    records_path: Path,
    query_vector: dict[str, float],
    top_k: int,
) -> list[RetrievedChunk]:
    if not query_vector:
        return []

    chunks_by_id = {chunk.chunk_id: chunk for chunk in chunks}
    results: list[RetrievedChunk] = []
    with records_path.open("r", encoding="utf-8") as handle:
        for record in _read_records(handle):
            chunk = chunks_by_id.get(str(record["chunk_id"]))
            if chunk is None:
                continue
            score = _sparse_dot(query_vector, record["vector"])
            if score > 0:
                results.append(RetrievedChunk(chunk=chunk, score=score))
    results.sort(key=lambda item: item.score, reverse=True)
    return results[:top_k]


def _read_records(handle: Any) -> list[dict[str, Any]]:
    return [json.loads(line) for line in handle if line.strip()]


def _json_record(chunk_id: str, vector: list[float] | dict[str, float]) -> str:
    return json.dumps({"chunk_id": chunk_id, "vector": vector}, ensure_ascii=False) + "\n"


def _normalize_dense(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if not norm:
        return vector
    return [value / norm for value in vector]


def _vectorize_counts(
    counts: Counter[str],
    idf: dict[str, float],
    dimensions: int,
) -> dict[str, float]:
    vector: dict[int, float] = {}
    for term, count in counts.items():
        weight = count * idf.get(term, 1.0)
        index, sign = _hash_term(term, dimensions)
        vector[index] = vector.get(index, 0.0) + sign * weight

    norm = math.sqrt(sum(value * value for value in vector.values()))
    if not norm:
        return {}
    return {str(index): value / norm for index, value in sorted(vector.items())}


def _hash_term(term: str, dimensions: int) -> tuple[int, int]:
    digest = hashlib.blake2b(term.encode("utf-8"), digest_size=8).digest()
    value = int.from_bytes(digest, byteorder="big", signed=False)
    index = value % dimensions
    sign = 1 if (value >> 63) == 0 else -1
    return index, sign


def _dense_dot(left: list[float], right: list[float]) -> float:
    return sum(left_value * float(right_value) for left_value, right_value in zip(left, right, strict=False))


def _sparse_dot(left: dict[str, float], right: dict[str, float]) -> float:
    if len(left) > len(right):
        left, right = right, left
    return sum(value * float(right.get(index, 0.0)) for index, value in left.items())
