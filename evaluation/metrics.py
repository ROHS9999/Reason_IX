"""Classification metrics written by hand (no sklearn) so you can explain every number in an interview."""
LABELS = ["contradiction", "agreement", "neutral"]


def accuracy(y_true, y_pred) -> float:
    return sum(t == p for t, p in zip(y_true, y_pred)) / len(y_true)


def confusion(y_true, y_pred) -> dict:
    """matrix[true][pred] = how many."""
    m = {t: {p: 0 for p in LABELS} for t in LABELS}
    for t, p in zip(y_true, y_pred):
        m[t][p] += 1
    return m


def per_class(y_true, y_pred) -> dict:
    """precision = of everything I called X, how much really was X.   recall = of all real X, how many I found.
    F1 = harmonic mean of the two (punishes being good at only one)."""
    out = {}
    for lab in LABELS:
        tp = sum(t == lab and p == lab for t, p in zip(y_true, y_pred))
        fp = sum(t != lab and p == lab for t, p in zip(y_true, y_pred))
        fn = sum(t == lab and p != lab for t, p in zip(y_true, y_pred))
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
        out[lab] = {"precision": prec, "recall": rec, "f1": f1, "support": tp + fn}
    return out


def macro_f1(y_true, y_pred) -> float:
    """Average F1 over the 3 classes, so the rare/hard class counts as much as the easy one."""
    pc = per_class(y_true, y_pred)
    return sum(v["f1"] for v in pc.values()) / len(LABELS)


def summarize(y_true, y_pred) -> dict:
    return {"accuracy": accuracy(y_true, y_pred), "macro_f1": macro_f1(y_true, y_pred),
            "per_class": per_class(y_true, y_pred), "confusion": confusion(y_true, y_pred)}
