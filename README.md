# RAG Workspace

Local RAG workspace for building searchable corpora from PDFs and asking questions with Ollama.

The first corpus is `high_speed_digital_design`, backed by the local PDF in:

```text
corpora/high_speed_digital_design/source/
```

## Requirements

- Python 3.12+
- `pdftotext` and `pdfinfo`
- Ollama running locally
- `qwen3:8b` available in Ollama
- `bge-m3` available in Ollama for embeddings

## Development Setup

Create and activate a virtual environment before installing development tools:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e ".[dev]"
```

Run tests:

```bash
python3 -m pytest -q
```

Check local models:

```bash
ollama list
```

Install local models:

```bash
ollama pull qwen3:8b
ollama pull bge-m3
```

## First Run

Build chunks:

```bash
PYTHONPATH=src python3 -m rag_workspace.cli ingest high_speed_digital_design
```

Preview retrieval without calling the LLM:

```bash
PYTHONPATH=src python3 -m rag_workspace.cli retrieve high_speed_digital_design "What causes signal reflection?"
```

Ask with Ollama:

```bash
PYTHONPATH=src python3 -m rag_workspace.cli ask high_speed_digital_design "What causes signal reflection?" --backend vector
```

Commands that need Ollama check the configured models before running. If a required model is missing, the CLI prints an `ollama pull <model>` suggestion.

## Smoke Test

Run retrieval-only smoke test without calling Ollama:

```bash
python3 scripts/smoke_test.py
```

Rebuild chunks first:

```bash
python3 scripts/smoke_test.py --ingest
```

Call Ollama after retrieval:

```bash
python3 scripts/smoke_test.py --ask
python3 scripts/smoke_test.py --ask --backend lexical
```

Short flags are also available:

```bash
python3 scripts/smoke_test.py -c high_speed_digital_design -q "What causes signal reflection?" -i
python3 scripts/smoke_test.py -a
```

Choose a retrieval backend:

```bash
python3 scripts/smoke_test.py --backend vector
python3 scripts/smoke_test.py --backend lexical
```

## Retrieval Eval

Run retrieval regression checks against the corpus eval set:

```bash
rag-workspace eval high_speed_digital_design --backend lexical
```

Without installing the package entry point, use:

```bash
PYTHONPATH=src python3 -m rag_workspace.cli eval high_speed_digital_design --backend lexical
```

## Quiz Generation

Generate exam-style multiple-choice questions from retrieved context:

```bash
rag-workspace quiz high_speed_digital_design "signal reflection" --count 3 --difficulty intermediate
```

By default, quiz output language is `auto`: English topics produce English questions, and Chinese topics produce Traditional Chinese questions. Use `--language "Traditional Chinese"` or `--language English` to force the output language.

The first version uses the configured `answer_model` for quiz generation. It asks the model to include one correct answer, wrong-option analysis, explanations, and source citations.

## Retrieval Backends

The workspace currently supports two local retrieval backends:

- `vector`: default persisted vector index stored under `corpora/*/index/`, using Ollama `bge-m3` embeddings.
- `lexical`: original in-memory lexical scorer kept as a fallback and debug baseline.

The vector backend also keeps a local `hashed_tfidf` embedding provider for tests and fallback, but the configured corpus uses `bge-m3` through Ollama.
