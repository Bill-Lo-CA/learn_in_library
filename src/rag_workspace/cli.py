from __future__ import annotations

import argparse
import sys

from .pipeline import ask, ingest, retrieve
from .evaluation import run_retrieval_eval


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

    ask_parser = subparsers.add_parser("ask", help="Ask a question with Ollama")
    ask_parser.add_argument("corpus_id")
    ask_parser.add_argument("question")
    ask_parser.add_argument("--backend", choices=["vector", "lexical"], default=None)

    eval_parser = subparsers.add_parser("eval", help="Run retrieval evaluation cases")
    eval_parser.add_argument("corpus_id")
    eval_parser.add_argument("--backend", choices=["vector", "lexical"], default=None)
    eval_parser.add_argument("--top-k", type=int, default=None)

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


if __name__ == "__main__":
    sys.exit(main())
