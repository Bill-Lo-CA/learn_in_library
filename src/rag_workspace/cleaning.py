from __future__ import annotations

import importlib.util
from collections.abc import Callable
from pathlib import Path


PageCleaner = Callable[[str, int], str]


def load_cleaner(cleaner_file: Path, function_name: str) -> PageCleaner:
    if not cleaner_file.exists():
        raise FileNotFoundError(f"Missing cleaner file: {cleaner_file}")

    spec = importlib.util.spec_from_file_location("corpus_cleaner", cleaner_file)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load cleaner module: {cleaner_file}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    cleaner = getattr(module, function_name, None)
    if not callable(cleaner):
        raise AttributeError(f"Cleaner function {function_name!r} not found in {cleaner_file}")
    return cleaner
