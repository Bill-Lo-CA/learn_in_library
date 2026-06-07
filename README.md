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

Check local models:

```bash
ollama list
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
PYTHONPATH=src python3 -m rag_workspace.cli ask high_speed_digital_design "What causes signal reflection?"
```
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
```
