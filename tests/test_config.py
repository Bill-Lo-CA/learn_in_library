from pathlib import Path

from rag_workspace.config import load_corpus_config, resolve_corpus_config_path


def write_corpus_config(root: Path, corpus_id: str = "demo") -> Path:
    root.mkdir(parents=True)
    config_path = root / "corpus.yaml"
    config_path.write_text(
        "\n".join(
            [
                f"id: {corpus_id}",
                "name: Demo Corpus",
                "source_files:",
                "  - source/demo.pdf",
                "cleaner_file: cleaner.py",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return config_path


def test_load_corpus_config_from_yaml_path(tmp_path: Path):
    config_path = write_corpus_config(tmp_path / "external_demo")

    config = load_corpus_config(str(config_path))

    assert config.corpus_id == "demo"
    assert config.root == config_path.parent
    assert config.source_files == [config.root / "source/demo.pdf"]
    assert config.cleaner_file == config.root / "cleaner.py"


def test_resolve_corpus_config_from_directory_path(tmp_path: Path):
    config_path = write_corpus_config(tmp_path / "external_demo")

    assert resolve_corpus_config_path(str(config_path.parent)) == config_path


def test_resolve_corpus_config_from_external_corpora_dir(monkeypatch, tmp_path: Path):
    config_path = write_corpus_config(tmp_path / "external_demo")
    monkeypatch.setenv("RAG_WORKSPACE_CORPORA_DIR", str(tmp_path))

    assert resolve_corpus_config_path("external_demo") == config_path


def test_resolve_corpus_config_by_yaml_id_in_external_corpora_dir(monkeypatch, tmp_path: Path):
    config_path = write_corpus_config(tmp_path / "external_demo_rag", "demo")
    monkeypatch.setenv("RAG_WORKSPACE_CORPORA_DIR", str(tmp_path))

    assert resolve_corpus_config_path("demo") == config_path
