from __future__ import annotations

import re
import subprocess
from pathlib import Path


def pdf_page_count(pdf_path: Path) -> int:
    result = subprocess.run(
        ["pdfinfo", str(pdf_path)],
        check=True,
        capture_output=True,
        text=True,
    )
    match = re.search(r"^Pages:\s+(\d+)$", result.stdout, flags=re.MULTILINE)
    if not match:
        raise RuntimeError(f"Could not read page count from pdfinfo output for {pdf_path}")
    return int(match.group(1))


def extract_pdf_pages(pdf_path: Path) -> list[tuple[int, str]]:
    page_count = pdf_page_count(pdf_path)
    pages: list[tuple[int, str]] = []
    for page_number in range(1, page_count + 1):
        result = subprocess.run(
            ["pdftotext", "-layout", "-f", str(page_number), "-l", str(page_number), str(pdf_path), "-"],
            check=True,
            capture_output=True,
            text=True,
            errors="replace",
        )
        pages.append((page_number, result.stdout))
    return pages
