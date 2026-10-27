import retrieval
from store import Store


def test_bm25_prefers_exact_word():
    docs = ["the red fox jumps", "spider man is a hero", "bm25 ranks exact words like zebra", "quantum zebra mechanics"]
    bm = retrieval.BM25([retrieval.tokenize(d) for d in docs])
    scores = bm.scores(retrieval.tokenize("zebra"))
    assert scores[0] == 0 and scores[1] == 0 and scores[3] > scores[2] > 0   # shorter doc scores higher


def test_rrf_rewards_items_in_both_lists():
    assert retrieval.rrf([["a", "b", "c"], ["c", "a", "d"]])[:2] == ["a", "c"]


def test_hybrid_search_finds_right_source(embed_patch):
    s = Store("test_retrieval_01")
    s.reset()
    s.add_source("text", "animals", [(None, "Zebras live in Africa and eat grass. Lions hunt zebras at night.")])
    s.add_source("text", "coding", [(None, "Python is a programming language that is popular for machine learning.")])
    s.sync_vectors()
    assert s.search("what do zebras eat", k=1)[0]["source_name"] == "animals"
    assert s.search("python programming", k=1)[0]["source_name"] == "coding"
    assert s.search("zebras", k=2, source_id=1)[0]["source_name"] == "coding"   # scoped to one source
    s.reset()
