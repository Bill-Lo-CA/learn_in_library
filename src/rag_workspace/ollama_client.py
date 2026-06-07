from __future__ import annotations

import json
import urllib.error
import urllib.request


def generate(host: str, model: str, prompt: str, temperature: float = 0.1) -> str:
    url = host.rstrip("/") + "/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": temperature},
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not reach Ollama at {host}. Is Ollama running?") from exc

    return str(data.get("response", "")).strip()


def embed(host: str, model: str, inputs: list[str]) -> list[list[float]]:
    url = host.rstrip("/") + "/api/embed"
    payload = {"model": model, "input": inputs}
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=300) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not reach Ollama at {host}. Is Ollama running?") from exc

    embeddings = data.get("embeddings")
    if not isinstance(embeddings, list):
        raise RuntimeError(f"Unexpected Ollama embed response for model {model!r}")
    return [[float(value) for value in embedding] for embedding in embeddings]
