from __future__ import annotations

from .ollama_client import generate, require_model
from .pipeline import retrieve
from .retrieval import RetrievedChunk


def generate_quiz(
    corpus_id: str,
    topic: str,
    count: int = 5,
    difficulty: str = "intermediate",
    question_type: str = "multiple-choice",
    language: str = "auto",
    backend: str | None = None,
) -> str:
    from .config import load_corpus_config

    if count <= 0:
        raise ValueError("count must be positive")
    if question_type != "multiple-choice":
        raise ValueError("Only multiple-choice quizzes are currently supported.")

    config = load_corpus_config(corpus_id)
    require_model(config.ollama_host, config.answer_model, "quiz generation")
    retrieved = retrieve(corpus_id, topic, config.top_k, backend or config.retrieval_backend)
    if not retrieved:
        return "No relevant chunks were found. Try ingesting the corpus or using a different topic."

    prompt = build_quiz_prompt(
        topic=topic,
        retrieved=retrieved,
        count=count,
        difficulty=difficulty,
        question_type=question_type,
        language=language,
    )
    return generate(config.ollama_host, config.answer_model, prompt)


def build_quiz_prompt(
    topic: str,
    retrieved: list[RetrievedChunk],
    count: int,
    difficulty: str,
    question_type: str,
    language: str,
) -> str:
    output_language = resolve_quiz_language(topic, language)
    context_blocks = []
    for idx, item in enumerate(retrieved, start=1):
        chunk = item.chunk
        citation = f"{chunk.source}, pages {chunk.page_start}-{chunk.page_end}"
        context_blocks.append(f"[{idx}] {citation}\n{chunk.text}")

    context = "\n\n".join(context_blocks)
    return f"""You are creating exam-style study questions from a retrieved technical book context.

Rules:
- Use only the context below.
- Write in {output_language}.
- Create exactly {count} {difficulty} {question_type} questions.
- Each question must have four options labeled A, B, C, and D.
- Include exactly one correct answer for each question.
- Include a short explanation for why the correct answer is right.
- Include a short note for why each wrong option is wrong.
- Cite the supporting context in each explanation with bracket numbers like [1] and page ranges.
- Do not add a separate bibliography or reference section.
- If the context is insufficient for a good question, say what is missing instead of inventing facts.
- Prefer questions that test understanding, comparison, or application, not memorization of wording.

Context:
{context}

Topic:
{topic}

Quiz:
"""


def resolve_quiz_language(topic: str, language: str) -> str:
    if language.strip().lower() != "auto":
        return language
    if _contains_cjk(topic):
        return "Traditional Chinese"
    return "English"


def _contains_cjk(text: str) -> bool:
    return any(
        "\u3400" <= char <= "\u4dbf"
        or "\u4e00" <= char <= "\u9fff"
        or "\uf900" <= char <= "\ufaff"
        for char in text
    )
