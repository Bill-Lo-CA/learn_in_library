from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
CORPORA_DIR = REPO_ROOT / "corpora"
CORPORA_DIR_ENV = "RAG_WORKSPACE_CORPORA_DIR"


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


def load_corpus_config(corpus_ref: str) -> CorpusConfig:
    config_path = resolve_corpus_config_path(corpus_ref)
    root = config_path.parent

    raw = _load_yaml(config_path)
    source_files = [root / value for value in raw.get("source_files", [])]

    return CorpusConfig(
        corpus_id=str(raw.get("id", config_path.parent.name)),
        name=str(raw.get("name", config_path.parent.name)),
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


def resolve_corpus_config_path(corpus_ref: str) -> Path:
    ref_path = Path(corpus_ref).expanduser()
    if ref_path.exists():
        if ref_path.is_file():
            if ref_path.name != "corpus.yaml":
                raise FileNotFoundError(f"Expected corpus.yaml config file, got: {ref_path}")
            return ref_path.resolve()
        config_path = ref_path / "corpus.yaml"
        if config_path.exists():
            return config_path.resolve()
        raise FileNotFoundError(f"Missing corpus config: {config_path}")

    for config_path in _candidate_config_paths(corpus_ref):
        if config_path.exists():
            return config_path.resolve()

    scanned_match = _find_config_by_yaml_id(corpus_ref)
    if scanned_match is not None:
        return scanned_match.resolve()

    searched = "\n".join(f"  - {path}" for path in _candidate_config_paths(corpus_ref))
    external_dirs = os.environ.get(CORPORA_DIR_ENV)
    env_hint = f"\n{CORPORA_DIR_ENV}={external_dirs}" if external_dirs else ""
    raise FileNotFoundError(f"Missing corpus config for '{corpus_ref}'. Searched:\n{searched}{env_hint}")


def _candidate_config_paths(corpus_ref: str) -> list[Path]:
    candidates: list[Path] = []
    for corpora_dir in _corpora_search_dirs():
        candidates.append(corpora_dir / corpus_ref / "corpus.yaml")
    return candidates


def _corpora_search_dirs() -> list[Path]:
    dirs: list[Path] = []
    external_dirs = os.environ.get(CORPORA_DIR_ENV, "")
    for value in external_dirs.split(os.pathsep):
        if value:
            dirs.append(Path(value).expanduser())
    dirs.append(CORPORA_DIR)
    return dirs


def _find_config_by_yaml_id(corpus_id: str) -> Path | None:
    for corpora_dir in _corpora_search_dirs():
        if not corpora_dir.exists() or not corpora_dir.is_dir():
            continue
        for config_path in sorted(corpora_dir.glob("*/corpus.yaml")):
            try:
                raw = _load_yaml(config_path)
            except (OSError, RuntimeError, ValueError):
                continue
            if str(raw.get("id", config_path.parent.name)) == corpus_id:
                return config_path
    return None


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
