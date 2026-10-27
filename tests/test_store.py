from store import Store


def test_sessions_are_isolated(embed_patch):
    a, b = Store("test_store_aaaa"), Store("test_store_bbbb")
    a.reset(); b.reset()
    a.add_source("text", "docA", [(None, "Alpha document with several words inside of it.")])
    b.add_source("text", "docB", [(None, "Beta document with several words inside of it.")])
    assert [c["source_name"] for c in a.chunks] == ["docA"]
    assert [c["source_name"] for c in b.chunks] == ["docB"]
    a.reset(); b.reset()


def test_save_and_load_roundtrip(embed_patch):
    s = Store("test_store_cccc")
    s.reset()
    s.add_source("text", "docC", [(None, "Gamma document with several words inside of it.")])
    s.sync_vectors()
    s.verdicts[("s0-k0", "s0-k1")] = {"relation": "agreement", "confidence": 90, "explanation": "x"}
    s.save()
    loaded = Store.load("test_store_cccc")
    assert len(loaded.chunks) == 1
    assert ("s0-k0", "s0-k1") in loaded.verdicts
    assert loaded.vectors.count() == 1
    loaded.reset()
    assert Store.load("test_store_cccc") is None


def test_clear_bumps_generation(embed_patch):
    s = Store("test_store_dddd")
    g = s.generation
    s.reset()
    assert s.generation == g + 1
