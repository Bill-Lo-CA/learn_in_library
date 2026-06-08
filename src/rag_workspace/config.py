from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
CORPORA_DIR = REPO_ROOT / "corpora"


@dataclass(frozen=True)
class CorpusConfig:
    corpus_id: str
    name: str
    root: Path
    source_files: list[Path]
    cleaner_file: Path
    cleaner_function: str
    chunk_words: int
    chunk_overlap_words: int
    answer_model: str
    ollama_host: str
    top_k: int
    retrieval_backend: str
    embedding_provider: str
    embedding_model: str
    embedding_batch_size: int
    vector_dimensions: int

    @property
    def chunks_path(self) -> Path:
        return self.root / "chunks.jsonl"

    @property
    def index_dir(self) -> Path:
        return self.root / "index"

    @property
    def eval_path(self) -> Path:
        return self.root / "eval.yaml"


def load_corpus_config(corpus_id: str) -> CorpusConfig:
    root = CORPORA_DIR / corpus_id
    config_path = root / "corpus.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Missing corpus config: {config_path}")

    raw = _load_yaml(config_path)
    source_files = [root / value for value in raw.get("source_files", [])]

    return CorpusConfig(
        corpus_id=str(raw.get("id", corpus_id)),
        name=str(raw.get("name", corpus_id)),
        root=root,
        source_files=source_files,
        cleaner_file=root / str(raw.get("cleaner_file", "cleaner.py")),
        cleaner_function=str(raw.get("cleaner_function", "clean_page")),
        chunk_words=int(raw.get("chunk_words", 420)),
        chunk_overlap_words=int(raw.get("chunk_overlap_words", 80)),
        answer_model=str(raw.get("answer_model", "qwen3:8b")),
        ollama_host=str(raw.get("ollama_host", "http://localhost:11434")),
        top_k=int(raw.get("top_k", 6)),
        retrieval_backend=str(raw.get("retrieval_backend", "vector")),
        embedding_provider=str(raw.get("embedding_provider", "ollama")),
        embedding_model=str(raw.get("embedding_model", "bge-m3")),
        embedding_batch_size=int(raw.get("embedding_batch_size", 8)),
        vector_dimensions=int(raw.get("vector_dimensions", 512)),
    )


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("PyYAML is required to read corpus.yaml files.") from exc

    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {path}")
    return data
