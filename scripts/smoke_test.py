from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from rag_workspace.config import load_corpus_config
from rag_workspace.pipeline import ask, ingest, retrieve


DEFAULT_QUESTION = "What causes signal reflection?"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a quick end-to-end RAG smoke test.")
    parser.add_argument("-c", "--corpus", default="high_speed_digital_design")
    parser.add_argument("-q", "--question", default=DEFAULT_QUESTION)
    parser.add_argument("-i", "--ingest", action="store_true", help="Rebuild chunks before retrieval.")
    parser.add_argument("-a", "--ask", action="store_true", help="Call Ollama after retrieval.")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--backend", choices=["vector", "lexical"], default=None)
    parser.add_argument("--embedding-model", default=None, help="Override the embedding model when rebuilding with --ingest.")
    args = parser.parse_args(argv)

    config = load_corpus_config(args.corpus)
    print(f"Corpus: {config.corpus_id}")
    print(f"Question: {args.question}")

    if args.ingest:
        chunks = ingest(args.corpus, args.embedding_model)
        print(f"Ingest: ok ({len(chunks)} chunks)")
        if args.embedding_model:
            print(f"Embedding model override: {args.embedding_model}")
    elif not config.chunks_path.exists():
        print(f"Missing chunks: {config.chunks_path}")
        print("Run with --ingest first.")
        return 1

    backend = args.backend or config.retrieval_backend
    print(f"Backend: {backend}")

    results = retrieve(args.corpus, args.question, args.top_k, backend)
    if not results:
        print("Retrieve: no matching chunks")
        return 1

    print(f"Retrieve: ok ({len(results)} chunks)")
    for idx, item in enumerate(results, start=1):
        chunk = item.chunk
        print(
            f"[{idx}] score={item.score:.4f} "
            f"{chunk.source} pages {chunk.page_start}-{chunk.page_end}"
        )
        print(_preview(chunk.text))

    if args.ask:
        print("Ask: calling Ollama")
        print(ask(args.corpus, args.question, backend))
    else:
        print("Ask: skipped (pass -a/--ask to call Ollama)")

    return 0


def _preview(text: str, limit: int = 260) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."


if __name__ == "__main__":
    raise SystemExit(main())
