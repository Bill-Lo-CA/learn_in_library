import json
from pathlib import Path

from rag_workspace.config import CorpusConfig
from rag_workspace.pipeline import retrieve


def test_vector_retrieve_checks_index_embedding_model(monkeypatch, tmp_path: Path):
    root = tmp_path / "demo"
    index_dir = root / "index"
    index_dir.mkdir(parents=True)
    (index_dir / "vector_metadata.json").write_text(
        json.dumps(
            {
                "kind": "ollama_embedding_vector_v1",
                "provider": "ollama",
                "model": "override-embed",
                "dimensions": 3,
                "chunk_count": 0,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    config = CorpusConfig(
        corpus_id="demo",
        name="Demo",
        root=root,
        source_files=[],
        cleaner_file=root / "cleaner.py",
        cleaner_function="clean_page",
        chunk_words=300,
        chunk_overlap_words=60,
        answer_model="qwen3:8b",
        ollama_host="http://localhost:11434",
        top_k=3,
        retrieval_backend="vector",
        embedding_provider="ollama",
        embedding_model="configured-embed",
        embedding_batch_size=8,
        vector_dimensions=512,
    )
    checked_models = []

    monkeypatch.setattr("rag_workspace.pipeline.load_corpus_config", lambda corpus_id: config)
    monkeypatch.setattr("rag_workspace.pipeline.read_chunks", lambda path: [])
    monkeypatch.setattr(
        "rag_workspace.pipeline.require_model",
        lambda host, model, purpose: checked_models.append(model),
    )
    monkeypatch.setattr("rag_workspace.pipeline.search_vector_index", lambda *args: [])

    retrieve("demo", "signal reflection", backend="vector")

    assert checked_models == ["override-embed"]
