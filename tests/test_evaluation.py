import pytest

from rag_workspace.chunking import Chunk
from rag_workspace.evaluation import (
    ChunkSizeCandidate,
    ExpectedPageRange,
    RetrievalEvalCase,
    _first_matching_rank,
    _parse_case,
    parse_chunk_size_candidates,
    run_chunk_size_eval_for_pages,
)
from rag_workspace.retrieval import RetrievedChunk


def test_first_matching_rank_accepts_overlapping_page_range():
    retrieved = [
        RetrievedChunk(
            chunk=Chunk(
                chunk_id="a",
                corpus_id="demo",
                source="demo.pdf",
                page_start=1,
                page_end=2,
                text="unrelated",
            ),
            score=0.5,
        ),
        RetrievedChunk(
            chunk=Chunk(
                chunk_id="b",
                corpus_id="demo",
                source="demo.pdf",
                page_start=10,
                page_end=12,
                text="microstrip and stripline",
            ),
            score=0.4,
        ),
    ]

    rank = _first_matching_rank(retrieved, [ExpectedPageRange(start=11, end=11)])

    assert rank == 2


def test_parse_case_requires_expected_pages():
    with pytest.raises(ValueError, match="needs expected_pages"):
        _parse_case({"id": "missing_pages", "question": "demo?"}, "eval.yaml")


def test_parse_case_supports_integer_and_range_pages():
    case = _parse_case(
        {
            "id": "demo",
            "question": "What is demo?",
            "expected_pages": [7, {"start": 10, "end": 12}],
            "backend": "lexical",
            "top_k": 5,
        },
        "eval.yaml",
    )

    assert case.case_id == "demo"
    assert case.backend == "lexical"
    assert case.top_k == 5
    assert case.expected_pages == [
        ExpectedPageRange(start=7, end=7),
        ExpectedPageRange(start=10, end=12),
    ]


def test_parse_chunk_size_candidates_reads_words_and_overlap():
    candidates = parse_chunk_size_candidates(["250:50", "320:64"])

    assert candidates == [
        ChunkSizeCandidate(chunk_words=250, overlap_words=50),
        ChunkSizeCandidate(chunk_words=320, overlap_words=64),
    ]


def test_parse_chunk_size_candidates_rejects_invalid_overlap():
    with pytest.raises(ValueError, match="chunk overlap"):
        parse_chunk_size_candidates(["100:100"])


def test_run_chunk_size_eval_for_pages_scores_candidates():
    cases = [
        RetrievalEvalCase(
            case_id="reflection",
            question="signal reflection",
            expected_pages=[ExpectedPageRange(start=2, end=2)],
            top_k=1,
        )
    ]
    pages_by_source = [
        (
            "demo.pdf",
            [
                (1, "thermal copper plane layout"),
                (2, "impedance discontinuity causes signal reflection"),
            ],
        )
    ]

    summary = run_chunk_size_eval_for_pages(
        corpus_id="demo",
        pages_by_source=pages_by_source,
        cases=cases,
        candidates=[ChunkSizeCandidate(chunk_words=4, overlap_words=0)],
        default_top_k=1,
    )

    assert summary.backend == "lexical"
    assert summary.results[0].chunk_count == 3
    assert summary.results[0].passed == 1
    assert summary.results[0].average_matched_rank == 1
