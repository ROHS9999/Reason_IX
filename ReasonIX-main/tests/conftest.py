"""Runs before any test: dummy API key + a throw-away data folder, so tests never touch your real data or the network."""
import os
import tempfile

os.environ.setdefault("GROQ_API_KEY", "test-key")
os.environ["DATA_DIR"] = tempfile.mkdtemp()
os.environ["USE_RERANKER"] = "0"            # no model downloads in tests
os.environ["PRELOAD_MODELS"] = "0"

import numpy as np  # noqa: E402
import pytest  # noqa: E402


def fake_embed(texts):
    """Deterministic 'embedding': hashed bag of words. Similar wording -> similar vector. No model needed."""
    import re
    out = []
    for t in texts:
        v = np.zeros(64, dtype="float32")
        for w in re.findall(r"\w+", t.lower()):
            v[sum(map(ord, w)) % 64] += 1
        out.append(v / (np.linalg.norm(v) or 1))
    return np.array(out)


@pytest.fixture
def embed_patch(monkeypatch):
    import utils
    monkeypatch.setattr(utils, "embed", fake_embed)


@pytest.fixture(autouse=True)
def no_model_downloads(monkeypatch):
    """The hallucination guard uses an NLI model; in tests it is replaced by a fake that says 'entailment' for everything."""
    import utils
    monkeypatch.setattr(utils, "nli_probs",
                        lambda pairs: [{"contradiction": 0.05, "entailment": 0.9, "neutral": 0.05}] * len(pairs))
