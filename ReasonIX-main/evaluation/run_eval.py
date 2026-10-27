"""Measure how good the contradiction / agreement / neutral judge is.

    python -m evaluation.run_eval                          # gpt-oss-20b, gpt-oss-120b, NLI (DeBERTa), baseline
    python -m evaluation.run_eval --models openai/gpt-oss-20b --no-nli

Writes evaluation/results_pairs.md (paste into your README) and evaluation/results_pairs.json (every prediction,
for error analysis). Needs GROQ_API_KEY in .env for the LLM judges."""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluation import judges, metrics  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def load_dataset(path=None):
    path = path or os.path.join(HERE, "dataset.jsonl")
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="*", default=["openai/gpt-oss-20b", "openai/gpt-oss-120b"])
    ap.add_argument("--no-nli", action="store_true")
    ap.add_argument("--dataset", default=None)
    args = ap.parse_args()

    rows = load_dataset(args.dataset)
    pairs = [(r["a"], r["b"]) for r in rows]
    y_true = [r["label"] for r in rows]
    print(f"{len(rows)} labeled pairs: " + ", ".join(f"{l}={y_true.count(l)}" for l in metrics.LABELS))

    results = {"Majority-class baseline": {"pred": judges.majority_baseline(y_true), "seconds": 0.0, "missing": 0}}

    for model in args.models:
        print(f"-> {model} ...")
        (pred, missing), secs = judges.timed(judges.llm_judge, model, pairs)
        results[model] = {"pred": pred, "seconds": secs, "missing": missing}

    if not args.no_nli:
        print("-> NLI DeBERTa ...")
        pred, secs = judges.timed(judges.nli_judge, pairs)
        results["NLI cross-encoder/nli-deberta-v3-base"] = {"pred": pred, "seconds": secs, "missing": 0}

    report = {}
    for name, r in results.items():
        report[name] = {**metrics.summarize(y_true, r["pred"]), "seconds": r["seconds"], "missing": r["missing"],
                        "sec_per_pair": r["seconds"] / len(rows)}

    # ---- markdown report
    md = ["# Pair-judge evaluation", "",
          f"{len(rows)} hand-labeled claim pairs ({', '.join(f'{y_true.count(l)} {l}' for l in metrics.LABELS)}). "
          "Metrics are macro-averaged over the 3 classes.", "",
          "| Judge | Accuracy | Macro-F1 | Contradiction F1 | Agreement F1 | Neutral F1 | s / pair | No answer |",
          "|---|---|---|---|---|---|---|---|"]
    for name, rep in report.items():
        pc = rep["per_class"]
        md.append(f"| {name} | {rep['accuracy']:.1%} | {rep['macro_f1']:.3f} | {pc['contradiction']['f1']:.2f} | "
                  f"{pc['agreement']['f1']:.2f} | {pc['neutral']['f1']:.2f} | {rep['sec_per_pair']:.2f} | {rep['missing']} |")
    md += ["", "## Confusion matrices (rows = true label, columns = predicted)", ""]
    for name, rep in report.items():
        if name.startswith("Majority"):
            continue
        md += [f"**{name}**", "", "| true \\ pred | " + " | ".join(metrics.LABELS) + " |", "|---|---|---|---|"]
        for t in metrics.LABELS:
            md.append(f"| {t} | " + " | ".join(str(rep["confusion"][t][p]) for p in metrics.LABELS) + " |")
        md.append("")
    with open(os.path.join(HERE, "results_pairs.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    preds = [{"id": r["id"], "label": r["label"], "a": r["a"], "b": r["b"],
              **{name: res["pred"][i] for name, res in results.items()}} for i, r in enumerate(rows)]
    with open(os.path.join(HERE, "results_pairs.json"), "w", encoding="utf-8") as f:
        json.dump({"summary": report, "predictions": preds}, f, indent=1, ensure_ascii=False)

    print("\n".join(md))
    print("\nSaved evaluation/results_pairs.md and results_pairs.json (open the json to see which pairs each judge got wrong).")


if __name__ == "__main__":
    main()
