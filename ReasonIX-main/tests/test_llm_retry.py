import pytest

import config
import llm


class HttpError(Exception):
    def __init__(self, code, msg=""):
        super().__init__(msg)
        self.status_code = code


def _script(monkeypatch, outcomes):
    calls = []

    class Chain:
        def __init__(self, method):
            self.method = method

        def invoke(self, inputs, **kwargs):
            calls.append(self.method)
            out = outcomes.pop(0)
            if isinstance(out, Exception):
                raise out
            return out

    monkeypatch.setattr(llm, "_structured_chain", lambda sys_, hum, schema, method, model=None: Chain(method))
    monkeypatch.setattr(config, "LLM_RETRY_WAIT", 0)
    return calls


def test_broken_tool_json_falls_back_to_json_schema(monkeypatch):
    calls = _script(monkeypatch, [HttpError(400, "tool_use_failed"), "OK"])
    assert llm._structured_call("s", "h", None, {}) == "OK"
    assert calls == ["function_calling", "json_schema"]


def test_wrong_model_fails_immediately(monkeypatch):
    calls = _script(monkeypatch, [HttpError(404, "model_not_found"), "OK"])
    with pytest.raises(HttpError):
        llm._structured_call("s", "h", None, {})
    assert calls == ["function_calling"]


def test_rate_limit_is_retried_on_same_method(monkeypatch):
    calls = _script(monkeypatch, [HttpError(429), HttpError(429), "OK"])
    assert llm._structured_call("s", "h", None, {}) == "OK"
    assert calls == ["function_calling"] * 3
