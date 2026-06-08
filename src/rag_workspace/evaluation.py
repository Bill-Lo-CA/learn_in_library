from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .config import load_corpus_config
from .pipeline import retrieve
from .retrieval import RetrievedChunk


@dataclass(frozen=True)
class ExpectedPageRange:
    start: int
    end: int


@dataclass(frozen=True)
class RetrievalEvalCase:
    case_id: str
    question: str
    expected_pages: list[ExpectedPageRange]
    top_k: int | None = None
    backend: str | None = None


@dataclass(frozen=True)
class RetrievalEvalResult:
    case: RetrievalEvalCase
    backend: str
    top_k: int
    passed: bool
    matched_rank: int | None
    retrieved: list[RetrievedChunk]


@dataclass(frozen=True)
class RetrievalEvalSummary:
    corpus_id: str
    backend: str
    total: int
    passed: int
    failed: int
    results: list[RetrievalEvalResult]


def load_retrieval_eval_cases(corpus_id: str) -> list[RetrievalEvalCase]:
    config = load_corpus_config(corpus_id)
    if not config.eval_path.exists():
        raise FileNotFoundError(f"Missing retrieval eval file: {config.eval_path}")

    raw = _load_yaml(config.eval_path)
    cases = raw.get("retrieval_eval", [])
    if not isinstance(cases, list):
        raise ValueError(f"Expected retrieval_eval list in {config.eval_path}")

    return [_parse_case(item, config.eval_path) for item in cases]


def run_retrieval_eval(
    corpus_id: str,
    backend: str | None = None,
    top_k: int | None = None,
) -> RetrievalEvalSummary:
    config = load_corpus_config(corpus_id)
    cases = load_retrieval_eval_cases(corpus_id)
    selected_backend = backend or config.retrieval_backend
    results: list[RetrievalEvalResult] = []

    for case in cases:
        case_backend = case.backend or selected_backend
        case_top_k = top_k or case.top_k or config.top_k
        retrieved = retrieve(corpus_id, case.question, case_top_k, case_backend)
        matched_rank = _first_matching_rank(retrieved, case.expected_pages)
        results.append(
            RetrievalEvalResult(
                case=case,
                backend=case_backend,
                top_k=case_top_k,
                passed=matched_rank is not None,
                matched_rank=matched_rank,
                retrieved=retrieved,
            )
        )

    passed = sum(1 for result in results if result.passed)
    return RetrievalEvalSummary(
        corpus_id=config.corpus_id,
        backend=selected_backend,
        total=len(results),
        passed=passed,
        failed=len(results) - passed,
        results=results,
    )


def _first_matching_rank(
    retrieved: list[RetrievedChunk],
    expected_pages: list[ExpectedPageRange],
) -> int | None:
    for rank, item in enumerate(retrieved, start=1):
        if _matches_any_expected_page(item, expected_pages):
            return rank
    return None


def _matches_any_expected_page(
    retrieved: RetrievedChunk,
    expected_pages: list[ExpectedPageRange],
) -> bool:
    chunk_start = retrieved.chunk.page_start
    chunk_end = retrieved.chunk.page_end
    return any(
        chunk_start <= expected.end and chunk_end >= expected.start
        for expected in expected_pages
    )


def _parse_case(raw: Any, path: object) -> RetrievalEvalCase:
    if not isinstance(raw, dict):
        raise ValueError(f"Expected mapping for retrieval eval case in {path}")

    case_id = str(raw.get("id", "")).strip()
    question = str(raw.get("question", "")).strip()
    if not case_id:
        raise ValueError(f"Retrieval eval case is missing id in {path}")
    if not question:
        raise ValueError(f"Retrieval eval case {case_id!r} is missing question")

    expected_pages = raw.get("expected_pages", [])
    if not isinstance(expected_pages, list) or not expected_pages:
        raise ValueError(f"Retrieval eval case {case_id!r} needs expected_pages")

    return RetrievalEvalCase(
        case_id=case_id,
        question=question,
        expected_pages=[_parse_expected_page_range(item, case_id) for item in expected_pages],
        top_k=_optional_int(raw.get("top_k")),
        backend=_optional_str(raw.get("backend")),
    )


def _parse_expected_page_range(raw: Any, case_id: str) -> ExpectedPageRange:
    if isinstance(raw, int):
        return ExpectedPageRange(start=raw, end=raw)
    if isinstance(raw, dict):
        start = int(raw.get("start", 0))
        end = int(raw.get("end", start))
        if start <= 0 or end < start:
            raise ValueError(f"Invalid expected page range in retrieval eval case {case_id!r}")
        return ExpectedPageRange(start=start, end=end)
    raise ValueError(f"Invalid expected page entry in retrieval eval case {case_id!r}")


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _load_yaml(path: object) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError("PyYAML is required to read retrieval eval files.") from exc

    with open(path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping in {path}")
    return data
