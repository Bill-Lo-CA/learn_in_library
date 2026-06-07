from __future__ import annotations

import argparse
import sys

from .pipeline import ask, ingest, retrieve


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rag-workspace")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ingest_parser = subparsers.add_parser("ingest", help="Build chunks for a corpus")
    ingest_parser.add_argument("corpus_id")

    retrieve_parser = subparsers.add_parser("retrieve", help="Show retrieved chunks for a question")
    retrieve_parser.add_argument("corpus_id")
    retrieve_parser.add_argument("question")
    retrieve_parser.add_argument("--top-k", type=int, default=None)

    ask_parser = subparsers.add_parser("ask", help="Ask a question with Ollama")
    ask_parser.add_argument("corpus_id")
    ask_parser.add_argument("question")

    args = parser.parse_args(argv)

    if args.command == "ingest":
        chunks = ingest(args.corpus_id)
        print(f"Ingested {len(chunks)} chunks for corpus {args.corpus_id}.")
        return 0

    if args.command == "retrieve":
        results = retrieve(args.corpus_id, args.question, args.top_k)
        for idx, item in enumerate(results, start=1):
            chunk = item.chunk
            print(f"[{idx}] score={item.score:.4f} {chunk.source} pages {chunk.page_start}-{chunk.page_end}")
            print(_preview(chunk.text))
            print()
        return 0

    if args.command == "ask":
        print(ask(args.corpus_id, args.question))
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2


def _preview(text: str, limit: int = 650) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


if __name__ == "__main__":
    sys.exit(main())
