from types import SimpleNamespace as NS

import config
import graph
import guard
import llm
import pipeline
import utils
from store import Store


def test_best_sentences_picks_the_matching_ones():
    chunk = ("The weather was mild. The vaccine showed 90 percent efficacy in the trial. "
             "Lunch was served at noon. The committee met twice.")
    out = guard.best_sentences(chunk, "The vaccine had 90 percent efficacy", k=1)
    assert out == "The vaccine showed 90 percent efficacy in the trial."


def _claim(text, verified):
    return {"id": text[:6], "text": text, "chunk_id": "s0-c0", "evidence_verified": verified}


def _store_with_chunk():
    s = Store("test_guard_0001")
    s.reset()
    s.add_source("text", "doc", [(None, "The vaccine showed 90 percent efficacy in the trial. Lunch was served.")])
    return s


def test_guard_rules(monkeypatch):
    s = _store_with_chunk()
    table = {"supported claim": (0.9, 0.0), "quote but unsure": (0.2, 0.1),
             "quote but twisted": (0.1, 0.8), "invented claim": (0.1, 0.1)}
    monkeypatch.setattr(utils, "nli_probs", lambda pairs: [
        {"entailment": table[h][0], "contradiction": table[h][1], "neutral": 0.1} for _, h in pairs])
    claims = [_claim("supported claim", False), _claim("quote but unsure", True),
              _claim("quote but twisted", True), _claim("invented claim", False)]
    guard.check_claims(s, claims)
    assert [c["grounded"] for c in claims] == [True, True, False, False]
    s.reset()


def test_guard_falls_back_when_nli_is_unavailable(monkeypatch):
    s = _store_with_chunk()

    def boom(pairs):
        raise RuntimeError("model could not load")
    monkeypatch.setattr(utils, "nli_probs", boom)
    claims = [_claim("has quote", True), _claim("no quote", False)]
    guard.check_claims(s, claims)
    assert [c["grounded"] for c in claims] == [True, False]
    s.reset()


def test_unsupported_claims_never_reach_the_comparison(monkeypatch, embed_patch):
    def analysis(name, passages, n):
        return NS(summary=["a", "b", "c"], claims=[
            NS(chunk=1, claim=f"{name} real claim number {i} with enough words", evidence="Alpha document text")
            for i in range(2)] + [NS(chunk=1, claim=f"{name} invented claim made up entirely", evidence="NOT IN TEXT")])
    monkeypatch.setattr(llm, "analyze_source", analysis)
    seen = {}

    def judge(pairs, model=None):
        seen["texts"] = [c["text"] for pair in pairs for c in pair]
        return {k: NS(relation="agreement", confidence=90, explanation="x") for k in range(len(pairs))}
    monkeypatch.setattr(llm, "judge_pairs", judge)
    monkeypatch.setattr(utils, "nli_probs", lambda pairs: [
        {"entailment": 0.05 if "invented" in h else 0.9, "contradiction": 0.05, "neutral": 0.05} for _, h in pairs])

    s = Store("test_guard_0002")
    s.reset()
    for name in ("docA", "docB"):
        s.add_source("text", name, [(None, "Alpha document text that has enough words to count as a chunk.")])
    graph.run_job(s, list(s.sources))
    assert s.status["state"] == "done"
    assert not any("invented" in t for t in seen["texts"])               # filtered out before the LLM judged anything
    out = pipeline.build_response(s)
    assert out["guard"]["removed"] == 2 and out["total_claims"] == 4
    assert all("invented" not in n["label"] for n in out["graph"]["nodes"])
    s.reset()


def test_flag_mode_keeps_unsupported_claims(monkeypatch):
    monkeypatch.setattr(config, "GUARD_MODE", "flag")
    s = _store_with_chunk()
    s.claims = [{"id": "k0", "grounded": False}, {"id": "k1", "grounded": True}]
    assert len(pipeline.usable_claims(s)) == 2
    s.reset()
