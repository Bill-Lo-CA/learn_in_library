from __future__ import annotations

import argparse
import json
import sys

from .pipeline import ask, ingest, retrieve
from .config import load_corpus_config
from .evaluation import parse_chunk_size_candidates, run_chunk_size_eval, run_retrieval_eval
from .quiz import generate_quiz
from .retrieval import RetrievedChunk


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rag-workspace")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_parser = subparsers.add_parser("ingest", help="Build chunks for a corpus")
    ingest_parser.add_argument("corpus_id")

    retrieve_parser = subparsers.add_parser("retrieve", help="Show retrieved chunks for a question")
    retrieve_parser.add_argument("corpus_id")
    retrieve_parser.add_argument("question")
    retrieve_parser.add_argument("--top-k", type=int, default=None)
    retrieve_parser.add_argument("--backend", choices=["vector", "lexical"], default=None)

    debug_parser = subparsers.add_parser("debug-retrieve", help="Show detailed retrieval diagnostics")
    debug_parser.add_argument("corpus_id")
    debug_parser.add_argument("question")
    debug_parser.add_argument("--top-k", type=int, default=None)
    debug_parser.add_argument("--backend", choices=["vector", "lexical"], default=None)
    debug_parser.add_argument("--preview-chars", type=int, default=320)
    debug_parser.add_argument("--json", action="store_true", dest="json_output")

    ask_parser = subparsers.add_parser("ask", help="Ask a question with Ollama")
    ask_parser.add_argument("corpus_id")
    ask_parser.add_argument("question")
    ask_parser.add_argument("--backend", choices=["vector", "lexical"], default=None)

    eval_parser = subparsers.add_parser("eval", help="Run retrieval evaluation cases")
    eval_parser.add_argument("corpus_id")
    eval_parser.add_argument("--backend", choices=["vector", "lexical"], default=None)
    eval_parser.add_argument("--top-k", type=int, default=None)

    chunk_eval_parser = subparsers.add_parser("chunk-size-eval", help="Compare chunk sizes against retrieval eval cases")
    chunk_eval_parser.add_argument("corpus_id")
    chunk_eval_parser.add_argument(
        "--candidate",
        action="append",
        default=[],
        metavar="WORDS:OVERLAP",
        help="Chunk size candidate, for example 300:60. Repeat to compare multiple candidates.",
    )
    chunk_eval_parser.add_argument("--top-k", type=int, default=None)

    quiz_parser = subparsers.add_parser("quiz", help="Generate exam-style questions from retrieved context")
    quiz_parser.add_argument("corpus_id")
    quiz_parser.add_argument("topic")
    quiz_parser.add_argument("--count", type=int, default=5)
    quiz_parser.add_argument("--difficulty", choices=["beginner", "intermediate", "advanced"], default="intermediate")
    quiz_parser.add_argument("--language", default="auto")
    quiz_parser.add_argument("--backend", choices=["vector", "lexical"], default=None)

    args = parser.parse_args(argv)

    try:
        if args.command == "ingest":
            chunks = ingest(args.corpus_id)
            print(f"Ingested {len(chunks)} chunks for corpus {args.corpus_id}.")
            return 0

        if args.command == "retrieve":
            results = retrieve(args.corpus_id, args.question, args.top_k, args.backend)
            for idx, item in enumerate(results, start=1):
                chunk = item.chunk
                print(f"[{idx}] score={item.score:.4f} {chunk.source} pages {chunk.page_start}-{chunk.page_end}")
                print(_preview(chunk.text))
                print()
            return 0

        if args.command == "debug-retrieve":
            config = load_corpus_config(args.corpus_id)
            selected_backend = args.backend or config.retrieval_backend
            selected_top_k = args.top_k or config.top_k
            results = retrieve(args.corpus_id, args.question, selected_top_k, selected_backend)
            if args.json_output:
                print(
                    json.dumps(
                        _debug_retrieval_payload(
                            corpus_id=config.corpus_id,
                            question=args.question,
                            backend=selected_backend,
                            top_k=selected_top_k,
                            results=results,
                            preview_chars=args.preview_chars,
                        ),
                        ensure_ascii=False,
                        indent=2,
                    )
                )
                return 0
            print(f"Retrieval debug for corpus {config.corpus_id}")
            print(f"query: {args.question}")
            print(f"backend: {selected_backend}")
            print(f"top_k: {selected_top_k}")
            print(f"results: {len(results)}")
            for idx, item in enumerate(results, start=1):
                chunk = item.chunk
                print(f"\n[{idx}] score={item.score:.4f}")
                print(f"chunk_id: {chunk.chunk_id}")
                print(f"corpus_id: {chunk.corpus_id}")
                print(f"source: {chunk.source}")
                print(f"pages: {chunk.page_start}-{chunk.page_end}")
                print(f"preview: {_preview(chunk.text, args.preview_chars)}")
            return 0

        if args.command == "ask":
            print(ask(args.corpus_id, args.question, args.backend))
            return 0

        if args.command == "eval":
            summary = run_retrieval_eval(args.corpus_id, args.backend, args.top_k)
            print(
                f"Retrieval eval: {summary.passed}/{summary.total} passed "
                f"for corpus {summary.corpus_id}."
            )
            for result in summary.results:
                status = "PASS" if result.passed else "FAIL"
                rank = result.matched_rank if result.matched_rank is not None else "-"
                print(
                    f"[{status}] {result.case.case_id} "
                    f"backend={result.backend} top_k={result.top_k} matched_rank={rank}"
                )
                print(f"  question: {result.case.question}")
                for idx, item in enumerate(result.retrieved, start=1):
                    chunk = item.chunk
                    print(
                        f"  {idx}. score={item.score:.4f} "
                        f"pages {chunk.page_start}-{chunk.page_end} "
                        f"{_preview(chunk.text, 140)}"
                    )
            return 0 if summary.failed == 0 else 1

        if args.command == "chunk-size-eval":
            candidates = parse_chunk_size_candidates(
                args.candidate or ["250:50", "300:60", "320:64", "420:80"]
            )
            summary = run_chunk_size_eval(args.corpus_id, candidates, args.top_k)
            print(
                f"Chunk-size eval: corpus={summary.corpus_id} "
                f"backend={summary.backend} candidates={len(summary.results)}"
            )
            for result in summary.results:
                avg_rank = (
                    f"{result.average_matched_rank:.2f}"
                    if result.average_matched_rank is not None
                    else "-"
                )
                candidate = result.candidate
                print(
                    f"{candidate.chunk_words}:{candidate.overlap_words} "
                    f"chunks={result.chunk_count} "
                    f"passed={result.passed}/{result.total} "
                    f"avg_rank={avg_rank}"
                )
                for case_result in result.results:
                    status = "PASS" if case_result.passed else "FAIL"
                    rank = case_result.matched_rank if case_result.matched_rank is not None else "-"
                    print(f"  [{status}] {case_result.case.case_id} matched_rank={rank}")
            return 0 if all(result.failed == 0 for result in summary.results) else 1

        if args.command == "quiz":
            print(
                generate_quiz(
                    corpus_id=args.corpus_id,
                    topic=args.topic,
                    count=args.count,
                    difficulty=args.difficulty,
                    language=args.language,
                    backend=args.backend,
                )
            )
            return 0

    except (FileNotFoundError, RuntimeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    parser.error(f"Unknown command: {args.command}")
    return 2


def _preview(text: str, limit: int = 650) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def _debug_retrieval_payload(
    corpus_id: str,
    question: str,
    backend: str,
    top_k: int,
    results: list[RetrievedChunk],
    preview_chars: int,
) -> dict[str, object]:
    items = []
    for rank, item in enumerate(results, start=1):
        chunk = item.chunk
        items.append(
            {
                "rank": rank,
                "score": item.score,
                "chunk_id": chunk.chunk_id,
                "corpus_id": chunk.corpus_id,
                "source": chunk.source,
                "page_start": chunk.page_start,
                "page_end": chunk.page_end,
                "preview": _preview(chunk.text, preview_chars),
            }
        )
    return {
        "corpus_id": corpus_id,
        "question": question,
        "backend": backend,
        "top_k": top_k,
        "results": items,
    }


if __name__ == "__main__":
    sys.exit(main())
