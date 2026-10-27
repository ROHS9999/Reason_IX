import utils


def test_chunks_respect_size_and_sentences():
    text = " ".join(f"Sentence number {i} is about topic {i % 5}." for i in range(200))
    chunks = utils.chunk_text(text, 1000, 100)
    assert len(chunks) > 3
    assert all(len(c) <= 1100 for c in chunks)
    assert all(c.endswith(".") for c in chunks)          # never cut mid-sentence


def test_chunks_overlap():
    text = " ".join(f"Sentence number {i} is about topic {i % 5}." for i in range(100))
    chunks = utils.chunk_text(text, 600, 150)
    last_sentence_of_first = chunks[0].split(". ")[-1]
    assert last_sentence_of_first in chunks[1]


def test_giant_sentence_without_punctuation_is_split():
    chunks = utils.chunk_text("x" * 5000, 2000, 200)
    assert len(chunks) == 3 and all(len(c) <= 2000 for c in chunks)


def test_pages_keep_their_page_number():
    pages = [(1, "First page has enough words to be kept here."), (2, "Second page also has enough words here.")]
    out = utils.chunk_pages(pages)
    assert [p for p, _ in out] == [1, 2]


def test_tiny_chunks_are_dropped():
    assert utils.chunk_pages([(1, "Too short")]) == []


def test_clean_text_joins_hyphenated_words():
    assert utils.clean_text("inter-\nnational  trade") == "international trade"
