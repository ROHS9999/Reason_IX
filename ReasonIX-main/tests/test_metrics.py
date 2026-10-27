from evaluation import metrics


def test_perfect_predictions():
    y = ["contradiction", "agreement", "neutral", "neutral"]
    s = metrics.summarize(y, y)
    assert s["accuracy"] == 1.0 and s["macro_f1"] == 1.0


def test_known_values():
    y_true = ["contradiction", "contradiction", "agreement", "neutral"]
    y_pred = ["contradiction", "neutral", "agreement", "neutral"]
    assert metrics.accuracy(y_true, y_pred) == 0.75
    pc = metrics.per_class(y_true, y_pred)
    assert pc["contradiction"]["precision"] == 1.0 and pc["contradiction"]["recall"] == 0.5
    assert abs(pc["contradiction"]["f1"] - 2 / 3) < 1e-9
    assert pc["neutral"]["precision"] == 0.5 and pc["neutral"]["recall"] == 1.0
    assert metrics.confusion(y_true, y_pred)["contradiction"]["neutral"] == 1


def test_dataset_is_balanced_and_valid():
    from evaluation.run_eval import load_dataset
    rows = load_dataset()
    labels = [r["label"] for r in rows]
    assert len(rows) >= 45 and all(l in metrics.LABELS for l in labels)
    assert labels.count("contradiction") == labels.count("agreement") == labels.count("neutral")
