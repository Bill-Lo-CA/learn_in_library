from __future__ import annotations

import json
import urllib.error
import urllib.request


def list_models(host: str) -> set[str]:
    url = host.rstrip("/") + "/api/tags"
    request = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not reach Ollama at {host}. Is Ollama running?") from exc

    models = data.get("models")
    if not isinstance(models, list):
        raise RuntimeError("Unexpected Ollama tags response while checking available models.")

    names: set[str] = set()
    for model in models:
        if not isinstance(model, dict):
            continue
        for key in ("name", "model"):
            value = model.get(key)
            if isinstance(value, str) and value:
                names.add(value)
    return names


def require_model(host: str, model: str, purpose: str) -> None:
    available = list_models(host)
    if _has_model(available, model):
        return
    available_text = ", ".join(sorted(available)) or "none"
    raise RuntimeError(
        f"Missing Ollama model for {purpose}: {model!r}. "
        f"Install it with `ollama pull {model}`. "
        f"Available models: {available_text}."
    )


def _has_model(available: set[str], model: str) -> bool:
    if model in available:
        return True
    if ":" not in model and f"{model}:latest" in available:
        return True
    return False


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
