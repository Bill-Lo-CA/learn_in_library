# Future Suggestions

## Near Term

- Rename the default git branch from `master` to `main`.
- Add an initial commit once the current shape looks right.
- Consider installing the package in editable mode for easier CLI use.

## RAG Quality

- Keep chunk metadata explicit: corpus id, source filename, page number, chunk id, and text hash.
- Test several chunk sizes before locking defaults.
- Add a retrieval debug command that shows the chunks selected for a question.
- Replace lexical retrieval with embeddings once the baseline behavior is understood.
- Consider a reranker after the first baseline is working.

## Local Model Setup

- Use `qwen3:8b` as the default local answer model.
- Add configuration for model name, Ollama host, temperature, context length, and top-k retrieval.
- Use a dedicated embedding model suitable for semantic retrieval.
- Detect missing Ollama models and show a clear setup message.

## Multi-Project Use

- Expose a CLI that sibling projects can call without knowing internal paths.
- Expose a small Python API for direct import.
- Avoid absolute paths in source code and configs.
- Add example configs that can be copied for new corpora.

## GitHub Readiness

- Keep source PDFs and generated indexes out of git unless explicitly approved.
- Add a license once the project direction is clearer.
- Add install instructions for local use and GitHub-based installation.
- Consider Git LFS only if there is a clear reason to version large non-private files.

## Possible Later Features

- Web UI for asking questions against selected corpora.
- Conversation memory per corpus.
- Multiple document support per corpus.
- Incremental re-indexing when files change.
- Exportable answer logs with citations.
- Evaluation set for checking retrieval and answer quality after changes.
