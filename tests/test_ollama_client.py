import json
import urllib.error

import pytest

from rag_workspace.ollama_client import list_models, require_model


class FakeResponse:
    def __init__(self, payload: dict):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def test_list_models_reads_ollama_tags(monkeypatch):
    def fake_urlopen(request, timeout):
        assert request.full_url == "http://localhost:11434/api/tags"
        assert timeout == 10
        return FakeResponse(
            {
                "models": [
                    {"name": "qwen3:8b"},
                    {"model": "bge-m3"},
                ]
            }
        )

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    assert list_models("http://localhost:11434") == {"qwen3:8b", "bge-m3"}


def test_require_model_reports_pull_command_for_missing_model(monkeypatch):
    monkeypatch.setattr(
        "rag_workspace.ollama_client.list_models",
        lambda host: {"qwen3:8b"},
    )

    with pytest.raises(RuntimeError, match="ollama pull bge-m3"):
        require_model("http://localhost:11434", "bge-m3", "embedding")


def test_require_model_accepts_implicit_latest_tag(monkeypatch):
    monkeypatch.setattr(
        "rag_workspace.ollama_client.list_models",
        lambda host: {"bge-m3:latest"},
    )

    require_model("http://localhost:11434", "bge-m3", "embedding")


def test_list_models_reports_ollama_connection_error(monkeypatch):
    def fake_urlopen(request, timeout):
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    with pytest.raises(RuntimeError, match="Could not reach Ollama"):
        list_models("http://localhost:11434")
