"""Hybrid retrieval for /compare:  vectors (meaning) + BM25 (exact words) -> fuse -> rerank.
- Vectors find paraphrases ("car" ~ "automobile") but can miss rare exact terms, names, numbers.
- BM25 is the opposite: great on exact words, blind to meaning.
- Reciprocal Rank Fusion (RRF) merges the two ranked lists without needing comparable scores.
- A cross-encoder reranker then re-orders the top candidates properly."""
import math
import re
from collections import Counter

import config
import utils


def tokenize(text: str):
    return re.findall(r"\w+", text.lower())


class BM25:
    """Okapi BM25 from scratch: score = sum over query words of IDF * saturated, length-normalised term frequency."""

    def __init__(self, docs, k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.tf = [Counter(d) for d in docs]
        self.dl = [len(d) for d in docs]
        self.n = len(docs)
        self.avgdl = (sum(self.dl) / self.n) if self.n else 0.0
        df = Counter()
        for d in docs:
            df.update(set(d))
        self.idf = {t: math.log(1 + (self.n - c + 0.5) / (c + 0.5)) for t, c in df.items()}

    def scores(self, query_tokens):
        out = [0.0] * self.n
        for t in set(query_tokens):
            idf = self.idf.get(t)
            if idf is None:
                continue
            for i, tf in enumerate(self.tf):
                f = tf.get(t, 0)
                if f:
                    out[i] += idf * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * self.dl[i] / self.avgdl))
        return out


def rrf(rankings, k: int = 60):
    """Reciprocal Rank Fusion: an item's score = sum of 1/(k+rank) over every list it appears in."""
    score = {}
    for ranking in rankings:
        for rank, item in enumerate(ranking):
            score[item] = score.get(item, 0.0) + 1.0 / (k + rank + 1)
    return sorted(score, key=lambda x: -score[x])


def dense_ids(store, query: str, n: int, source_id=None):
    """Chunk ids ranked by vector similarity (meaning)."""
    return store.vectors.query(utils.embed([query])[0], n, source_id)


def sparse_ids(store, query: str, n: int, source_id=None):
    """Chunk ids ranked by BM25 (exact words). Chunks sharing no word with the query are left out."""
    bm25 = store.get_bm25()
    if bm25 is None:
        return []
    scores = bm25.scores(tokenize(query))
    ranked = sorted(range(len(scores)), key=lambda i: -scores[i])
    return [store.chunks[i]["id"] for i in ranked
            if scores[i] > 0 and (source_id is None or store.chunks[i]["source_id"] == source_id)][:n]


def hybrid_search(store, query: str, k: int = 4, source_id=None):
    """Returns the best k chunk dicts for the query."""
    by_id = {c["id"]: c for c in store.chunks}
    fused_ids = rrf([dense_ids(store, query, config.FETCH_K, source_id),
                     sparse_ids(store, query, config.FETCH_K, source_id)])
    fused = [by_id[i] for i in fused_ids if i in by_id][:config.FETCH_K + 3]
    return utils.rerank(query, fused, k)
