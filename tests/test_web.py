from types import SimpleNamespace as NS

import pytest

import llm
import pipeline
import websearch
from store import Store


def _store():
    s = Store("test_web_0001")
    s.reset()
    s.claims = [{"id": "s0-k0", "text": "Water boils at 100 degrees Celsius at sea level."}]
    return s


RESULTS = [{"title": "Boiling point", "url": "https://example.org/water", "snippet": "Water boils at 100 C."},
           {"title": "Bad link", "url": "javascript:alert(1)", "snippet": "x"}]


def test_supported_verdict_with_real_source(monkeypatch):
    s = _store()
    monkeypatch.setattr(websearch, "search", lambda q, n=5: RESULTS)
    monkeypatch.setattr(llm, "verify_claim", lambda c, r: NS(verdict="supported", confidence=90,
                                                             explanation="Matches result 1.", source_numbers=[1, 1, 2, 9]))
    out = pipeline.verify_claim_web(s, "s0-k0")
    assert out["verdict"] == "supported"
    assert out["sources"] == [{"title": "Boiling point", "url": "https://example.org/water"}]   # deduped, non-http dropped
    s.reset()


def test_verdict_without_a_cited_source_is_downgraded(monkeypatch):
    s = _store()
    monkeypatch.setattr(websearch, "search", lambda q, n=5: RESULTS)
    monkeypatch.setattr(llm, "verify_claim", lambda c, r: NS(verdict="contradicted", confidence=99,
                                                             explanation="From memory.", source_numbers=[]))
    assert pipeline.verify_claim_web(s, "s0-k0")["verdict"] == "unverified"
    s.reset()


def test_result_is_cached_and_search_not_repeated(monkeypatch):
    s = _store()
    calls = []
    monkeypatch.setattr(websearch, "search", lambda q, n=5: calls.append(q) or RESULTS)
    monkeypatch.setattr(llm, "verify_claim", lambda c, r: NS(verdict="supported", confidence=80,
                                                             explanation="ok", source_numbers=[1]))
    pipeline.verify_claim_web(s, "s0-k0")
    pipeline.verify_claim_web(s, "s0-k0")
    assert len(calls) == 1
    s.reset()


def test_no_results_means_unverified(monkeypatch):
    s = _store()
    monkeypatch.setattr(websearch, "search", lambda q, n=5: [])
    assert pipeline.verify_claim_web(s, "s0-k0")["verdict"] == "unverified"
    s.reset()


def test_unknown_claim_and_unavailable_search(monkeypatch):
    s = _store()
    with pytest.raises(KeyError):
        pipeline.verify_claim_web(s, "nope")

    def unavailable(q, n=5):
        raise websearch.WebSearchUnavailable("no provider")
    monkeypatch.setattr(websearch, "search", unavailable)
    with pytest.raises(websearch.WebSearchUnavailable):
        pipeline.verify_claim_web(s, "s0-k0")
    s.reset()


def test_web_checks_survive_save_and_load():
    s = _store()
    s.web_checks["s0-k0"] = {"claim_id": "s0-k0", "verdict": "supported", "confidence": 80, "explanation": "x", "sources": []}
    s.save()
    assert Store.load("test_web_0001").web_checks["s0-k0"]["verdict"] == "supported"
    s.reset()
