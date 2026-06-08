from rag_workspace.chunking import Chunk
from rag_workspace.quiz import build_quiz_prompt
from rag_workspace.retrieval import RetrievedChunk


def test_build_quiz_prompt_includes_exam_constraints_and_citations():
    prompt = build_quiz_prompt(
        topic="signal reflection",
        retrieved=[
            RetrievedChunk(
                chunk=Chunk(
                    chunk_id="a",
                    corpus_id="demo",
                    source="demo.pdf",
                    page_start=10,
                    page_end=12,
                    text="Impedance discontinuities cause reflections on transmission lines.",
                ),
                score=0.9,
            )
        ],
        count=3,
        difficulty="intermediate",
        question_type="multiple-choice",
        language="Traditional Chinese",
    )

    assert "Create exactly 3 intermediate multiple-choice questions." in prompt
    assert "four options labeled A, B, C, and D" in prompt
    assert "Include exactly one correct answer" in prompt
    assert "why each wrong option is wrong" in prompt
    assert "Do not add a separate bibliography or reference section." in prompt
    assert "[1] demo.pdf, pages 10-12" in prompt
    assert "signal reflection" in prompt
