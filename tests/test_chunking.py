from rag_workspace.chunking import chunk_pages


def test_chunk_pages_preserves_page_range():
    pages = [(1, "alpha beta gamma"), (2, "delta epsilon zeta")]

    chunks = chunk_pages(
        corpus_id="demo",
        source_name="demo.pdf",
        pages=pages,
        chunk_words=4,
        overlap_words=1,
    )

    assert chunks[0].page_start == 1
    assert chunks[0].page_end == 2
    assert chunks[0].text == "alpha beta gamma delta"
