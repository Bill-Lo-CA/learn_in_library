import pytest

from rag_workspace.chunking import Chunk
from rag_workspace.evaluation import (
    ExpectedPageRange,
    _first_matching_rank,
    _parse_case,
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
