# RAG Workspace

Local RAG workspace for building searchable corpora from PDFs and asking questions with Ollama.

The current implementation is a single-corpus RAG baseline that is intended to grow into a local personal library RAG system. It keeps source PDFs, generated chunks, and generated indexes out of git by default.

The included corpus configuration is `high_speed_digital_design`, backed by a local PDF that should be placed in:

```text
corpora/high_speed_digital_design/source/
```

The PDF itself is not included in this repository.

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

You can also install directly from GitHub after cloning or publishing the repository:

```bash
python3 -m pip install -e "git+ssh://git@github.com/Bill-Lo-CA/learn_in_library.git#egg=rag-workspace"
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

Add your local source PDF at the path configured in `corpora/high_speed_digital_design/corpus.yaml`, then build chunks and the vector index.

Build chunks:

```bash
PYTHONPATH=src python3 -m rag_workspace.cli ingest high_speed_digital_design
```

Rebuild the vector index with a different Ollama embedding model:

```bash
PYTHONPATH=src python3 -m rag_workspace.cli ingest high_speed_digital_design --embedding-model nomic-embed-text
```

Vector retrieval uses the embedding model recorded in the generated index metadata, so queries stay matched to the model used during the latest ingest.

Preview retrieval without calling the LLM:

```bash
PYTHONPATH=src python3 -m rag_workspace.cli retrieve high_speed_digital_design "What causes signal reflection?"
```

Inspect retrieval with chunk ids and structured metadata:

```bash
PYTHONPATH=src python3 -m rag_workspace.cli debug-retrieve high_speed_digital_design "What causes signal reflection?"
PYTHONPATH=src python3 -m rag_workspace.cli debug-retrieve high_speed_digital_design "What causes signal reflection?" --json
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
python3 scripts/smoke_test.py --ingest --embedding-model nomic-embed-text
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

Compare chunk sizes without overwriting the current generated chunks or vector index:

```bash
PYTHONPATH=src python3 -m rag_workspace.cli chunk-size-eval high_speed_digital_design
PYTHONPATH=src python3 -m rag_workspace.cli chunk-size-eval high_speed_digital_design --candidate 250:50 --candidate 320:64
```

The chunk-size evaluator uses lexical retrieval against temporary chunks so it can quickly compare page-range hits before rebuilding Ollama vector indexes.

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

The vector backend also keeps a local `hashed_tfidf` embedding provider for tests and fallback, but the configured corpus uses `bge-m3` through Ollama. Use `ingest --embedding-model <model>` to rebuild the local index with another installed Ollama embedding model.

## Adding A Corpus

Copy `examples/corpus.example.yaml` into a new folder under `corpora/`, then add a corpus-specific cleaner and local PDFs:

```text
corpora/
  my_book/
    corpus.yaml
    cleaner.py
    source/
      my_book.pdf
```

Generated files such as `chunks.jsonl` and `index/` are ignored by git. Keep source PDFs out of the repository unless their license and size are explicitly acceptable.

## GitHub Notes

This repository is designed to publish source code, tests, examples, and documentation without publishing local book data. Before pushing a public repo, verify:

```bash
git status --short
git ls-files
```
