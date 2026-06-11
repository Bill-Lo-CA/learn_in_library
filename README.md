# RAG Workspace

Local RAG framework for building searchable corpora from local documents and asking questions with Ollama.

The repository is intended to stay mostly code, tests, documentation, and examples. Real source documents, generated chunks, and vector indexes should live in data projects that use this framework.

The previous `high_speed_digital_design` corpus has been moved out to `/home/amd2/projects/high_speed_digital_design_rag/` as a local data corpus project.

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

Copy `examples/corpus.example.yaml` into a data project, add source documents there, then build chunks and the vector index in that data project. The CLI accepts a corpus id, a corpus directory path, or a direct `corpus.yaml` path.

Example commands using a direct external config path:

```bash
PYTHONPATH=src python3 -m rag_workspace.cli ingest /home/amd2/projects/high_speed_digital_design_rag/corpus.yaml
PYTHONPATH=src python3 -m rag_workspace.cli retrieve /home/amd2/projects/high_speed_digital_design_rag/corpus.yaml "What causes signal reflection?"
PYTHONPATH=src python3 -m rag_workspace.cli debug-retrieve /home/amd2/projects/high_speed_digital_design_rag/corpus.yaml "What causes signal reflection?" --json
PYTHONPATH=src python3 -m rag_workspace.cli ask /home/amd2/projects/high_speed_digital_design_rag/corpus.yaml "What causes signal reflection?" --backend vector
```

You can also point the framework at external corpus projects and use a corpus id:

```bash
export RAG_WORKSPACE_CORPORA_DIR=/home/amd2/projects
PYTHONPATH=src python3 -m rag_workspace.cli ingest my_book
PYTHONPATH=src python3 -m rag_workspace.cli retrieve my_book "What causes signal reflection?"
PYTHONPATH=src python3 -m rag_workspace.cli debug-retrieve my_book "What causes signal reflection?" --json
PYTHONPATH=src python3 -m rag_workspace.cli ask my_book "What causes signal reflection?" --backend vector
```

When using `RAG_WORKSPACE_CORPORA_DIR`, the CLI first checks `<dir>/<corpus>/corpus.yaml`. It can also find a one-level child project whose `corpus.yaml` has a matching `id`, such as resolving `high_speed_digital_design` to `/home/amd2/projects/high_speed_digital_design_rag/corpus.yaml`.

Vector retrieval uses the embedding model recorded in the generated index metadata, so queries stay matched to the model used during the latest ingest. Commands that need Ollama check the configured models before running. If a required model is missing, the CLI prints an `ollama pull <model>` suggestion.

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
python3 scripts/smoke_test.py -c my_book -q "What causes signal reflection?" -i
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
rag-workspace eval my_book --backend lexical
```

Without installing the package entry point, use:

```bash
PYTHONPATH=src python3 -m rag_workspace.cli eval my_book --backend lexical
```

Compare chunk sizes without overwriting the current generated chunks or vector index:

```bash
PYTHONPATH=src python3 -m rag_workspace.cli chunk-size-eval my_book
PYTHONPATH=src python3 -m rag_workspace.cli chunk-size-eval my_book --candidate 250:50 --candidate 320:64
```

The chunk-size evaluator uses lexical retrieval against temporary chunks so it can quickly compare page-range hits before rebuilding Ollama vector indexes.

## Quiz Generation

Generate exam-style multiple-choice questions from retrieved context:

```bash
rag-workspace quiz my_book "signal reflection" --count 3 --difficulty intermediate
```

By default, quiz output language is `auto`: English topics produce English questions, and Chinese topics produce Traditional Chinese questions. Use `--language "Traditional Chinese"` or `--language English` to force the output language.

The first version uses the configured `answer_model` for quiz generation. It asks the model to include one correct answer, wrong-option analysis, explanations, and source citations.

## Retrieval Backends

The workspace currently supports two local retrieval backends:

- `vector`: default persisted vector index stored under the selected data project's `index/` directory, using Ollama `bge-m3` embeddings.
- `lexical`: original in-memory lexical scorer kept as a fallback and debug baseline.

The vector backend also keeps a local `hashed_tfidf` embedding provider for tests and fallback. Use `ingest --embedding-model <model>` to rebuild the local index with another installed Ollama embedding model.

## Adding A Corpus

Copy `examples/corpus.example.yaml` into a data project outside this framework repository, then add a corpus-specific cleaner and local PDFs:

```text
my_book_rag/
  corpus.yaml
  cleaner.py
  source/
    my_book.pdf
```

Generated files such as `chunks.jsonl` and `index/` should stay in the data project, not in `RAG_workspace`. Keep source PDFs out of the framework repository unless their license and size are explicitly acceptable.

## GitHub Notes

This repository is designed to publish source code, tests, examples, and documentation without publishing local book data. Before pushing a public repo, verify:

```bash
git status --short
git ls-files
```
