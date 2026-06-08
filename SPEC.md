# RAG Workspace Specification

## Purpose

`RAG_workspace` is a local, reusable RAG workspace for building searchable knowledge corpora from PDF documents and querying them with local Ollama models.

The first corpus is based on:

- `HighSpeed_Digital_System_Design_A_Handbook_of_Interconnect_Theory_and_Design_Practices.pdf`

The workspace should stay general enough to support additional corpora later without turning each corpus into a separate software project.

## Current State

The repository currently contains:

- A git repository initialized in `RAG_workspace`
- A Python package under `src/rag_workspace`
- One configured corpus under `corpora/high_speed_digital_design`
- A corpus-specific PDF cleaner at `corpora/high_speed_digital_design/cleaner.py`
- A CLI entry point exposed by `rag_workspace.cli`
- A smoke test script at `scripts/smoke_test.py`
- A retrieval eval seed set at `corpora/high_speed_digital_design/eval.yaml`
- Optional development dependencies exposed through `pyproject.toml` as `.[dev]`
- A generated local vector index for the first corpus after ingest using Ollama `bge-m3` embeddings
- The original lexical retrieval backend retained as a fallback
- Ollama availability and model checks before commands that require local models

Available local Ollama models observed during setup:

- `qwen3:8b`
- `qwen2.5-coder:7b`
- `bge-m3`

The intended answer-generation model is `qwen3:8b`.

## Target Architecture

The workspace should separate reusable RAG code from corpus-specific files.

```text
RAG_workspace/
  SPEC.md
  FUTURE.md
  README.md
  pyproject.toml

  src/
    rag_workspace/
      __init__.py
      answer.py
      chunking.py
      cleaning.py
      cli.py
      config.py
      ollama_client.py
      pdf_extract.py
      pipeline.py
      quiz.py
      retrieval.py
      storage.py
      vector_store.py

  corpora/
    high_speed_digital_design/
      corpus.yaml
      eval.yaml
      source/
      index/
      chunks.jsonl

  examples/
    corpus.example.yaml

  scripts/
    smoke_test.py

  tests/
```

## Corpus Model

A corpus is a single searchable knowledge collection. It may contain one or more source documents, but should have one config file and one generated index.

For the first corpus, retrieval is configured with:

```yaml
retrieval_backend: vector
embedding_provider: ollama
embedding_model: bge-m3
answer_model: qwen3:8b
```

For the first corpus:

```text
corpora/high_speed_digital_design/
  corpus.yaml
  eval.yaml
  source/
    HighSpeed_Digital_System_Design_A_Handbook_of_Interconnect_Theory_and_Design_Practices.pdf
  index/
  chunks.jsonl
```

The PDF source and generated indexes should be treated as local data. They should not be committed to GitHub unless their license and size are explicitly acceptable.

## Implemented RAG Flow

The current version has both a local vector backend and the original lexical backend:

1. Read corpus configuration.
2. Check Ollama availability and required local models before Ollama-backed commands run.
3. Extract text from PDF pages with `pdfinfo` and `pdftotext`.
4. Load the corpus-specific cleaner from the corpus folder.
5. Clean repeated headers, footers, broken whitespace, and low-value fragments.
6. Split extracted text into page-aware chunks.
7. Store chunks with metadata, including source document and page range.
8. Build an Ollama `bge-m3` embedding index under the corpus `index/` directory.
9. Retrieve top matching chunks with the configured backend: `vector` by default or `lexical` as fallback.
10. Ask `qwen3:8b` through Ollama to answer using only retrieved context.
11. Return the answer with chunk citations and page ranges.

## Quiz Generation

The workspace can generate exam-style multiple-choice questions from retrieved context. The first version:

- Uses the configured `answer_model` as the quiz-generation model.
- Retrieves context for a topic using the configured retrieval backend or a CLI backend override.
- Generates a requested number of multiple-choice questions.
- Uses `--language auto` by default: English topics produce English quizzes, and CJK topics produce Traditional Chinese quizzes.
- Requires one correct answer, wrong-option analysis, a brief explanation, and citations to retrieved context.
- Does not yet persist quizzes or grade user answers.

Future versions may split quiz generation and quiz review into separate model roles, but the current implementation keeps one model and one reviewed prompt path for simplicity.

## Retrieval Evaluation

Each corpus may include a `eval.yaml` file with retrieval regression cases. The current schema is:

```yaml
retrieval_eval:
  - id: short_case_id
    question: "Question text"
    expected_pages:
      - start: 10
        end: 12
    top_k: 5
```

The eval runner checks whether any retrieved chunk in the configured `top_k` overlaps an expected page range. This is intended to catch retrieval regressions when chunking, cleaning, embedding models, or ranking behavior changes. It does not evaluate generated answer quality.

## Model Responsibilities

The workspace should separate embedding and answer generation:

- Embedding model: creates vectors for search.
- Answer model: generates final answers from retrieved context.

`qwen3:8b` is the initial answer model. The current vector backend uses Ollama `bge-m3` embeddings for multilingual retrieval. A local hashed TF-IDF provider remains available for tests and fallback. The answer model remains `qwen3:8b`.

Commands that require Ollama validate model availability through the local Ollama API before doing the expensive work:

- `ingest` checks the configured `embedding_model` when `embedding_provider` is `ollama`.
- `retrieve` checks the configured `embedding_model` when using the `vector` backend.
- `ask` checks the configured `answer_model` before generating the final answer.

If Ollama is not reachable or a model is missing, the CLI should print a concise error and, for missing models, suggest `ollama pull <model>`.

## Public Interface

The workspace should eventually expose two stable interfaces:

- CLI for shell use from this and other local projects.
- Python package API for import from sibling projects.

Current CLI shape:

```bash
PYTHONPATH=src python3 -m rag_workspace.cli ingest high_speed_digital_design
PYTHONPATH=src python3 -m rag_workspace.cli retrieve high_speed_digital_design "What causes signal reflections?" --backend vector
PYTHONPATH=src python3 -m rag_workspace.cli ask high_speed_digital_design "What causes signal reflections?" --backend vector
PYTHONPATH=src python3 -m rag_workspace.cli eval high_speed_digital_design --backend lexical
PYTHONPATH=src python3 -m rag_workspace.cli quiz high_speed_digital_design "signal reflection" --count 3
```

Example target Python API shape:

```python
from rag_workspace import ask

answer = ask("high_speed_digital_design", "What causes signal reflections?")
```

## GitHub Rules

The repository should be safe to publish if private data and large generated files are excluded.

Do not commit by default:

- Source PDFs with unclear license status
- Generated vector indexes
- Generated chunk files that contain large portions of source text
- Local cache directories
- Machine-specific absolute paths

Commit by default:

- Source code
- Specs and documentation
- Example configs
- Tests
- Small fixtures created specifically for testing

## Documentation Rule

This spec should be updated whenever the code changes in a way that affects:

- Project layout
- Corpus configuration
- CLI or Python API
- Ingestion flow
- Retrieval behavior
- Model configuration
- GitHub publishing assumptions
