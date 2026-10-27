"""End-to-end API tests (FastAPI TestClient). Skipped automatically if fastapi/httpx are not installed."""
import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

import graph  # noqa: E402
import llm  # noqa: E402
import main  # noqa: E402

HEADERS = {"X-Session-Id": "test_api_session_1"}


def test_home_ok():
    assert TestClient(main.app).get("/").json()["message"] == "Backend running"


def test_session_header_is_required():
    assert TestClient(main.app).get("/status/").status_code == 400
    assert TestClient(main.app).get("/status/", headers={"X-Session-Id": "../etc/passwd"}).status_code == 400


def test_upload_text_then_status_and_clear(monkeypatch, embed_patch):
    monkeypatch.setattr(graph, "run_job", lambda store, sources: None)      # skip the LLM pipeline
    c = TestClient(main.app)
    c.post("/clear/", headers=HEADERS)
    r = c.post("/upload/", headers=HEADERS, data={"text_input": "Alpha document with plenty of words in it, really."})
    body = r.json()
    assert body["sources"][0]["chunk_count"] == 1 and body["status"]["state"] == "processing"
    assert len(c.get("/status/", headers=HEADERS).json()["sources"]) == 1
    c.post("/clear/", headers=HEADERS)
    assert c.get("/status/", headers=HEADERS).json()["sources"] == []


def test_limits_and_blocked_url(monkeypatch, embed_patch):
    monkeypatch.setattr(graph, "run_job", lambda store, sources: None)
    c = TestClient(main.app)
    c.post("/clear/", headers=HEADERS)
    r = c.post("/upload/", headers=HEADERS, data={"url_input": "http://127.0.0.1:8000/"})
    assert "Blocked" in r.json()["error"]
    r = c.post("/upload/", headers=HEADERS, data={"text_input": "x" * 200_001})
    assert "too long" in r.json()["error"]


def test_compare_returns_citations(monkeypatch, embed_patch):
    monkeypatch.setattr(graph, "run_job", lambda store, sources: None)
    monkeypatch.setattr(llm, "answer_query", lambda q, ctx: "Zebras eat grass [1].")
    c = TestClient(main.app)
    c.post("/clear/", headers=HEADERS)
    c.post("/upload/", headers=HEADERS, data={"text_input": "Zebras live in Africa and eat grass all day long."})
    r = c.get("/compare/", headers=HEADERS, params={"query": "what do zebras eat"}).json()
    assert r["answer"].startswith("Zebras") and r["citations"][0]["n"] == 1
    assert c.get("/compare/", headers=HEADERS, params={"query": "x"}).status_code == 422   # too short
    c.post("/clear/", headers=HEADERS)


def test_verify_validates_input_and_reports_unknown_claim(monkeypatch, embed_patch):
    c = TestClient(main.app)
    assert c.post("/verify/", headers=HEADERS, json={}).status_code == 422
    assert c.post("/verify/", headers=HEADERS, json={"claim_id": "../x"}).status_code == 422
    assert c.post("/verify/", headers=HEADERS, json={"claim_id": "s9-k9"}).status_code == 404
