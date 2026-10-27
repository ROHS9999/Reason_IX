"""The three kinds of judge we compare. Each takes [(text_a, text_b), ...] and returns one label per pair."""
import time


def majority_baseline(y_true):
    """What you get by always answering the most common label - the number any real model must beat."""
    top = max(set(y_true), key=y_true.count)
    return [top] * len(y_true)


def llm_judge(model: str, pairs, batch_size: int = 15):
    """Uses the EXACT production prompt (llm.judge_pairs), in batches of 15 like the app does.
    Returns (labels, number_of_pairs_the_model_failed_to_answer)."""
    import llm
    labels, missing = [], 0
    for i in range(0, len(pairs), batch_size):
        batch = [({"source_name": "A", "text": a}, {"source_name": "B", "text": b}) for a, b in pairs[i:i + batch_size]]
        result = llm.judge_pairs(batch, model=model)
        for k in range(len(batch)):
            v = result.get(k)
            if v is None:
                missing += 1
                labels.append("neutral")      # no answer counts as 'neutral' (and is reported separately)
            else:
                labels.append(v.relation)
    return labels, missing


def nli_judge(pairs, model_name: str = "cross-encoder/nli-deberta-v3-base"):
    """A small NLI classifier (no LLM, runs locally). NLI is directional (A->B), so we score both directions and
    average. NLI 'entailment' means one statement supports the other = our 'agreement'."""
    import numpy as np
    from sentence_transformers import CrossEncoder

    model = CrossEncoder(model_name)
    id2label = getattr(model.model.config, "id2label", None) or {}
    names = [str(id2label.get(i, "")).lower() for i in range(3)]
    if sorted(names) != ["contradiction", "entailment", "neutral"]:
        names = ["contradiction", "entailment", "neutral"]   # documented order of this model family

    def softmax(x):
        e = np.exp(x - x.max(axis=1, keepdims=True))
        return e / e.sum(axis=1, keepdims=True)

    fwd = softmax(np.asarray(model.predict([(a, b) for a, b in pairs])))
    bwd = softmax(np.asarray(model.predict([(b, a) for a, b in pairs])))
    to_ours = {"contradiction": "contradiction", "entailment": "agreement", "neutral": "neutral"}
    return [to_ours[names[int(row.argmax())]] for row in (fwd + bwd) / 2]


def timed(fn, *args, **kwargs):
    t0 = time.time()
    out = fn(*args, **kwargs)
    return out, time.time() - t0
