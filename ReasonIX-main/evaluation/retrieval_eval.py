"""Does hybrid search + reranking really beat plain vector search?  No LLM and no API key needed.

    python -m evaluation.retrieval_eval

A small corpus of 12 short documents (several deliberately similar: two metros, two languages, two mountains...) and
24 questions with a known correct document: 12 worded differently from the text ('semantic') and 12 made of exact
terms ('exact'). For each retrieval mode we measure Hit@1, Hit@3 and MRR (mean reciprocal rank = average of 1/rank of
the right document; 1.0 means always first)."""
import json
import os
import sys
import tempfile

os.environ.setdefault("GROQ_API_KEY", "not-needed-for-retrieval-eval")
os.environ["DATA_DIR"] = tempfile.mkdtemp()                      # throw-away vector DB
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config  # noqa: E402
import retrieval  # noqa: E402
import utils  # noqa: E402
from store import Store  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
N = 12


def rank_of(gold_id, ids):
    return ids.index(gold_id) + 1 if gold_id in ids else None


def main():
    with open(os.path.join(HERE, "retrieval_corpus.json"), encoding="utf-8") as f:
        data = json.load(f)

    store = Store("retrieval_eval_session")
    store.reset()
    for d in data["docs"]:
        store.add_source("text", d["name"], [(None, d["text"])])
    store.sync_vectors()
    by_id = {c["id"]: c for c in store.chunks}

    modes = {
        "Vector only": lambda q: retrieval.dense_ids(store, q, N),
        "BM25 only": lambda q: retrieval.sparse_ids(store, q, N),
        "Hybrid (RRF)": lambda q: retrieval.rrf([retrieval.dense_ids(store, q, N), retrieval.sparse_ids(store, q, N)]),
        "Hybrid + rerank": lambda q: [c["id"] for c in utils.rerank(
            q, [by_id[i] for i in retrieval.rrf([retrieval.dense_ids(store, q, N), retrieval.sparse_ids(store, q, N)])], N)],
    }

    table = {}
    for mode, fn in modes.items():
        ranks = {"semantic": [], "exact": []}
        for item in data["questions"]:
            ranks[item["type"]].append(rank_of(f"s{item['gold']}-c0", fn(item["q"])))
        table[mode] = ranks

    def stats(rs):
        n = len(rs)
        hit1 = sum(r == 1 for r in rs) / n
        hit3 = sum(r is not None and r <= 3 for r in rs) / n
        mrr = sum((1 / r) if r else 0 for r in rs) / n
        return hit1, hit3, mrr

    md = ["# Retrieval evaluation", "",
          f"{len(data['docs'])} documents, {len(data['questions'])} questions (12 semantic, 12 exact-term).", "",
          "| Mode | Hit@1 | Hit@3 | MRR | MRR semantic | MRR exact |", "|---|---|---|---|---|---|"]
    for mode, ranks in table.items():
        both = ranks["semantic"] + ranks["exact"]
        h1, h3, mrr = stats(both)
        md.append(f"| {mode} | {h1:.0%} | {h3:.0%} | {mrr:.3f} | {stats(ranks['semantic'])[2]:.3f} | {stats(ranks['exact'])[2]:.3f} |")
    store.reset()
    out = "\n".join(md)
    with open(os.path.join(HERE, "results_retrieval.md"), "w", encoding="utf-8") as f:
        f.write(out)
    print(out)
    print("\nSaved evaluation/results_retrieval.md")


if __name__ == "__main__":
    main()
