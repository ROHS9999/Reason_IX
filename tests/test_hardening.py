"""Tests for: quote matching, the minimum-support rule, honest summaries and the rate limiter."""
import pytest

import config
import pipeline
import ratelimit


# ── quote matching (the "not verbatim" bug) ──────────────────────────────────
def test_norm_ignores_curly_quotes_dashes_and_case():
    passage = "Spider\u2011Man\u2019s villains have no personal motivations.\nNext sentence."
    quote = "Spider-Man's villains have no personal motivations"
    assert pipeline._norm(quote) in pipeline._norm(passage)


def test_norm_still_rejects_invented_quotes():
    passage = "Spider-Man's villains have no personal motivations."
    assert pipeline._norm("Spider-Man villains love Peter") not in pipeline._norm(passage)


def test_norm_handles_ligatures_and_soft_hyphens():
    assert pipeline._norm("e\ufb03cient sys\u00adtem") == "efficient system"


# ── minimum support rule ─────────────────────────────────────────────────────
class _Store:
    def __init__(self, claims):
        self.claims, self.candidates, self.verdicts = claims, [], {}


def _claim(i, sid, text, support):
    return {"id": f"c{i}", "text": text, "source_id": sid, "source_name": f"s{sid}", "grounded": True,
            "support": support}


def test_weakly_supported_claims_are_not_compared(monkeypatch, embed_patch):
    seen = []
    monkeypatch.setattr(pipeline.llm, "judge_pairs", lambda todo, model=None: seen.extend(todo) or {})
    store = _Store([_claim(0, 0, "the tower is 330 metres tall", 0.95),
                    _claim(1, 1, "the tower is 250 metres tall", 0.01),    # almost unsupported -> skipped
                    _claim(2, 1, "the tower is 300 metres tall", 0.90)])
    pipeline.judge_candidates(store)
    ids = {c["id"] for pair in seen for c in pair}
    assert "c1" not in ids and {"c0", "c2"} <= ids


def test_unchecked_claims_are_still_compared(monkeypatch, embed_patch):
    seen = []
    monkeypatch.setattr(pipeline.llm, "judge_pairs", lambda todo, model=None: seen.extend(todo) or {})
    store = _Store([_claim(0, 0, "the tower is 330 metres tall", None),
                    _claim(1, 1, "the tower is 250 metres tall", None)])
    pipeline.judge_candidates(store)
    assert len(seen) == 1


# ── honest summary text ──────────────────────────────────────────────────────
class _SummaryStore:
    def __init__(self, sources, pairs):
        self.sources, self.pairs = sources, pairs


def _pair(rel):
    return {"relation": rel}


def test_summary_pluralises_correctly():
    store = _SummaryStore([], [_pair("agreement"), _pair("contradiction"), _pair("neutral")])
    text = pipeline.combined_summary(store)[-1]
    assert "1 agreement," in text and "1 contradiction," in text and "agreements" not in text


def test_summary_warns_when_a_long_document_was_only_sampled():
    src = {"name": "big.pdf", "summary": ["x"], "chunk_ids": list(range(28)), "chunks_read": 5}
    notes = pipeline.combined_summary(_SummaryStore([src], []))
    assert any("big.pdf (5 of 28 passages)" in n for n in notes)


def test_summary_has_no_warning_when_everything_was_read():
    src = {"name": "small.pdf", "summary": ["x"], "chunk_ids": [1, 2], "chunks_read": 2}
    assert not any("sampled" in n for n in pipeline.combined_summary(_SummaryStore([src], [])))


# ── rate limiter ─────────────────────────────────────────────────────────────
@pytest.fixture
def limited(monkeypatch):
    monkeypatch.setattr(config, "RATE_LIMIT_ENABLED", True)
    ratelimit.reset()
    yield
    ratelimit.reset()


def test_rate_limiter_blocks_after_the_limit(limited):
    from fastapi import FastAPI, Depends
    from fastapi.testclient import TestClient
    app = FastAPI()

    @app.get("/x", dependencies=[Depends(ratelimit.limit("t", lambda: 2))])
    def x():
        return {"ok": True}

    c = TestClient(app)
    assert c.get("/x").status_code == 200
    assert c.get("/x").status_code == 200
    r = c.get("/x")
    assert r.status_code == 429 and "Retry-After" in r.headers


def test_rate_limiter_is_off_when_disabled(monkeypatch):
    monkeypatch.setattr(config, "RATE_LIMIT_ENABLED", False)
    ratelimit.reset()
    from fastapi import FastAPI, Depends
    from fastapi.testclient import TestClient
    app = FastAPI()

    @app.get("/x", dependencies=[Depends(ratelimit.limit("t2", lambda: 1))])
    def x():
        return {}

    c = TestClient(app)
    assert all(c.get("/x").status_code == 200 for _ in range(5))
