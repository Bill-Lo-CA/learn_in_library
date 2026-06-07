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
- A generated lexical retrieval index for the first corpus after ingest

Available local Ollama models observed during setup:

- `qwen3:8b`
- `qwen2.5-coder:7b`

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
      retrieval.py
      storage.py

  corpora/
    high_speed_digital_design/
      corpus.yaml
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

For the first corpus:

```text
corpora/high_speed_digital_design/
  corpus.yaml
  source/
    HighSpeed_Digital_System_Design_A_Handbook_of_Interconnect_Theory_and_Design_Practices.pdf
  index/
  chunks.jsonl
```

The PDF source and generated indexes should be treated as local data. They should not be committed to GitHub unless their license and size are explicitly acceptable.

## Implemented RAG Flow

The current first version uses a zero-vector-DB baseline:

1. Read corpus configuration.
2. Extract text from PDF pages with `pdfinfo` and `pdftotext`.
3. Load the corpus-specific cleaner from the corpus folder.
4. Clean repeated headers, footers, broken whitespace, and low-value fragments.
5. Split extracted text into page-aware chunks.
6. Store chunks with metadata, including source document and page range.
7. Retrieve top matching chunks with local lexical TF-IDF-style scoring.
8. Ask `qwen3:8b` through Ollama to answer using only retrieved context.
9. Return the answer with chunk citations and page ranges.

## Model Responsibilities

The workspace should separate embedding and answer generation:

- Embedding model: creates vectors for search.
- Answer model: generates final answers from retrieved context.

`qwen3:8b` is the initial answer model. The first version uses lexical retrieval so the project can run without downloading extra dependencies. A dedicated embedding model should be added later for better semantic retrieval quality.

## Public Interface

The workspace should eventually expose two stable interfaces:

- CLI for shell use from this and other local projects.
- Python package API for import from sibling projects.

Current CLI shape:

```bash
PYTHONPATH=src python3 -m rag_workspace.cli ingest high_speed_digital_design
PYTHONPATH=src python3 -m rag_workspace.cli retrieve high_speed_digital_design "What causes signal reflections?"
PYTHONPATH=src python3 -m rag_workspace.cli ask high_speed_digital_design "What causes signal reflections?"
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
