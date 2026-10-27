from types import SimpleNamespace as NS

import config
import graph
import llm
import pipeline
from store import Store


def _claims_for(name):
    # one claim per "topic"; the evidence is a real snippet of the passage so evidence_verified is True
    return NS(summary=["s1", "s2", "s3"], claims=[
        NS(chunk=1, claim=f"{name} says topic {i} has a measurable effect here", evidence="Alpha document text") for i in range(3)])


def _fake_llm(monkeypatch, confidence=60):
    monkeypatch.setattr(llm, "analyze_source", lambda name, passages, n: _claims_for(name))

    def judge(pairs, model=None):
        rel = "contradiction"
        conf = 95 if model == config.VERIFY_MODEL else confidence
        rel = "agreement" if model == config.VERIFY_MODEL else rel   # the bigger model disagrees with the first judge
        return {k: NS(relation=rel, confidence=conf, explanation="x") for k in range(len(pairs))}
    monkeypatch.setattr(llm, "judge_pairs", judge)


def _two_sources(embed_patch):
    s = Store("test_pipe_0001")
    s.reset()
    for name in ("docA", "docB"):
        s.add_source("text", name, [(None, "Alpha document text that has enough words to count as a chunk.")])
    return s


def test_candidate_pairs_only_cross_source():
    import numpy as np
    claims = [{"source_id": 0}, {"source_id": 0}, {"source_id": 1}]
    embs = np.array([[1, 0], [1, 0], [1, 0]], dtype="float32")
    pairs = pipeline.candidate_pairs(claims, embs, top_k=2, min_sim=0.1, max_pairs=10)
    assert all(claims[i]["source_id"] != claims[j]["source_id"] for i, j, _ in pairs)
    assert len(pairs) == 2


def test_full_job_with_second_opinion(monkeypatch, embed_patch):
    _fake_llm(monkeypatch, confidence=60)             # shaky conflicts -> the verify node must run
    s = _two_sources(embed_patch)
    graph.run_job(s, list(s.sources))
    assert s.status["state"] == "done"
    assert s.pairs, "expected claim pairs"
    # the larger model changed every shaky 'contradiction' into 'agreement'
    assert all(p["relation"] == "agreement" and p["verified"] and p["first_opinion"] == "contradiction" for p in s.pairs)
    s.reset()


def test_confident_conflicts_skip_verification(monkeypatch, embed_patch):
    _fake_llm(monkeypatch, confidence=95)             # confident -> no second opinion needed
    s = _two_sources(embed_patch)
    graph.run_job(s, list(s.sources))
    assert s.pairs and all(p["relation"] == "contradiction" and not p["verified"] for p in s.pairs)
    s.reset()


def test_failed_analysis_sets_error_status(monkeypatch, embed_patch):
    def boom(*a, **k):
        raise RuntimeError("model_not_found")
    monkeypatch.setattr(llm, "analyze_source", boom)
    s = _two_sources(embed_patch)
    graph.run_job(s, list(s.sources))
    assert s.status["state"] == "error" and "model_not_found" in s.status["stage"]
    s.reset()


def test_clear_during_job_cancels(monkeypatch, embed_patch):
    _fake_llm(monkeypatch)
    s = _two_sources(embed_patch)
    original = llm.analyze_source

    def analyze_then_clear(name, passages, n):
        s.generation += 1                              # simulate the user pressing Clear mid-job
        return original(name, passages, n)
    monkeypatch.setattr(llm, "analyze_source", analyze_then_clear)
    graph.run_job(s, list(s.sources))
    assert s.pairs == [] and s.status["state"] != "done"
    s.reset()


def test_graph_data_has_nodes_edges_and_connected_flags(monkeypatch, embed_patch):
    _fake_llm(monkeypatch, confidence=95)
    s = _two_sources(embed_patch)
    graph.run_job(s, list(s.sources))
    data = pipeline.build_graph_data(s, s.pairs)
    assert data["edges"] and all(e["relation"] == "contradicts" for e in data["edges"])
    ids = {n["id"] for n in data["nodes"]}
    assert all(e["source"] in ids and e["target"] in ids for e in data["edges"])
    assert any(n["connected"] for n in data["nodes"])
    s.reset()
