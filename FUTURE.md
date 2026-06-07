# Future Suggestions

## Near Term

- Rename the default git branch from `master` to `main`.
- Add an initial commit once the current shape looks right.
- Consider installing the package in editable mode for easier CLI use.

## RAG Quality

- Keep chunk metadata explicit: corpus id, source filename, page number, chunk id, and text hash.
- Test several chunk sizes before locking defaults, especially 250-320 words for less diluted embeddings.
- Add a retrieval debug command that shows the chunks selected for a question.
- Compare `bge-m3` retrieval against other embedding models such as `qwen3-embedding` or `nomic-embed-text`.
- Add Chinese-to-English technical query rewriting for English source corpora, so casual Chinese questions can map to terms like `impedance discontinuity` and `reflection coefficient`.
- Add hybrid retrieval that combines `bge-m3` vector results with lexical results, then merges or re-scores the candidates.
- Retrieve a larger candidate set first, such as top 10, then rerank down to the final context set.
- Consider a reranker after the first baseline is working.
- Track retrieval quality by ranking correctness rather than treating vector similarity scores as absolute percentages.

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
