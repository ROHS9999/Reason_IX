"""The ReasonIX pipeline:  chunks -> claims -> cross-source claim pairs -> verdicts -> response.
Runs in a BACKGROUND THREAD after /upload/ has already answered, so the user never waits on the LLM."""
import re
import unicodedata
from concurrent.futures import ThreadPoolExecutor

import config
import guard
import llm
import utils
import websearch


# def _norm(s: str) -> str:
#     return re.sub(r"\s+", " ", s).strip().lower()

def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s)       # ligatures, odd spaces
    s = s.replace("\u00ad", "")                # soft hyphens
    s = re.sub(r"[^\w\s]", " ", s.lower())     # ignore punctuation (curly vs straight quotes, dashes)
    return re.sub(r"\s+", " ", s).strip()


def _spread(items, n):
    """Pick n items evenly spaced across the list (so we sample the whole document, not just the start)."""
    if len(items) <= n:
        return list(items)
    return [items[int(i * len(items) / n)] for i in range(n)]


# ── Step 1: summary + claims per source ───────────────────────────────────────
def _analyze_one(store, source):
    chunks = _spread([store.get_chunk(cid) for cid in source["chunk_ids"]], config.MAX_CHUNKS_PER_SOURCE)
    passages = "\n\n".join(f"[{n}] {c['text']}" for n, c in enumerate(chunks, 1))
    try:
        return source, chunks, llm.analyze_source(source["name"], passages, config.MAX_CLAIMS_PER_SOURCE), None
    except Exception as e:  # noqa: BLE001
        print(f"[ANALYZE] {source['name']} failed: {e}")
        return source, chunks, None, str(e)


def _locate_chunk(item, chunks, norm_texts):
    """Which chunk does a claim come from? Trust the quoted evidence first (checkable), then the model's number."""
    ev = _norm(item.evidence)
    if ev:
        for c, t in zip(chunks, norm_texts):
            if ev in t:
                return c, True
    n = item.chunk
    if isinstance(n, int) and 1 <= n <= len(chunks):
        return chunks[n - 1], False
    return chunks[0], False


def analyze_sources(store, sources):
    """One LLM call per source, all sources in parallel."""
    with ThreadPoolExecutor(config.LLM_WORKERS) as pool:
        results = list(pool.map(lambda s: _analyze_one(store, s), sources))

    for source, chunks, out, err in results:
        if out is None:
            source["summary"] = [f"Analysis failed: {(err or 'no answer from the model')[:200]}"]
            continue
        norm_texts = [_norm(c["text"]) for c in chunks]
        claims, seen = [], set()
        for item in out.claims:
            text = item.claim.strip()
            key = _norm(text)
            if len(text.split()) < 5 or key in seen:
                continue
            seen.add(key)
            chunk, verified = _locate_chunk(item, chunks, norm_texts)
            claims.append({
                "id": f"s{source['id']}-k{len(claims)}",
                "text": text,
                "source_id": source["id"],
                "source_name": source["name"],
                "chunk_id": chunk["id"],
                "page": chunk["page"],
                "evidence": item.evidence.strip(),
                "evidence_verified": verified,   # cheap hallucination check: quote really inside the chunk?
            })
        store.claims.extend(claims)
        source["summary"] = out.summary[:3] or ["No summary produced."]
        print(f"[CLAIMS] {source['name']}: {len(claims)} claims")


# ── Step 2: pairing ───────────────────────────────────────────────────────────
def candidate_pairs(claims, embs, top_k, min_sim, max_pairs):
    """Pick which claim pairs are worth judging.
    Comparing every claim with every other is N*M work. Contradictions only happen between claims about the
    SAME topic, so for each claim we keep its top_k most similar claims in every OTHER source."""
    sims = embs @ embs.T  # cosine similarity matrix (vectors are normalised)
    by_source = {}
    for idx, c in enumerate(claims):
        by_source.setdefault(c["source_id"], []).append(idx)

    best = {}
    for i, c in enumerate(claims):
        for sid, idxs in by_source.items():
            if sid == c["source_id"]:
                continue
            for j in sorted(idxs, key=lambda j: -sims[i][j])[:top_k]:
                s = float(sims[i][j])
                if s >= min_sim:
                    key = (min(i, j), max(i, j))
                    best[key] = max(best.get(key, 0.0), s)

    ordered = sorted(best.items(), key=lambda kv: -kv[1])[:max_pairs]
    return [(i, j, s) for (i, j), s in ordered]


def _claim_out(c):
    out = {k: c[k] for k in ("id", "text", "source_id", "source_name", "page",
                             "chunk_id", "evidence", "evidence_verified")}
    out["support"] = c.get("support")          # NLI probability that the source text backs the claim (None = unchecked)
    return out


def usable_claims(store) -> list:
    """Claims that may be compared. With GUARD_MODE=filter, claims the source text does not support are left out."""
    if config.GUARD_MODE != "filter":
        return list(store.claims)
    return [c for c in store.claims if c.get("grounded", True)]


def guard_new_claims(store):
    """Hallucination guard: check every claim that has not been checked yet (see guard.py)."""
    guard.check_claims(store, [c for c in store.claims if "grounded" not in c])


def judge_candidates(store):
    """Pick candidate pairs (embedding similarity), then judge all NEW ones in ONE batched LLM call.
    Verdicts are cached in the store, so adding a source never repeats old calls."""
    claims = usable_claims(store)
    store.candidates = []
    if len({c["source_id"] for c in claims}) < 2:
        return
    embs = utils.embed([c["text"] for c in claims])
    cands = candidate_pairs(claims, embs, config.PAIR_TOP_K, config.PAIR_MIN_SIMILARITY, config.MAX_PAIRS)
    store.candidates = [(claims[i]["id"], claims[j]["id"], s) for i, j, s in cands]

    todo = [(claims[i], claims[j]) for i, j, _ in cands if (claims[i]["id"], claims[j]["id"]) not in store.verdicts]
    for k, v in llm.judge_pairs(todo).items():
        a, b = todo[k]
        store.verdicts[(a["id"], b["id"])] = {"relation": v.relation, "confidence": v.confidence,
                                              "explanation": v.explanation, "verified": False, "first_opinion": None}


def needs_verification(store) -> list:
    """Shaky conflicts (low confidence) deserve a second opinion from a bigger model.
    A false 'contradiction' is the worst mistake this app can make, so those are the ones we double-check."""
    if config.VERIFY_MODEL == config.LLM_MODEL:
        return []
    keys = [(a, b) for a, b, _ in store.candidates
            if (v := store.verdicts.get((a, b))) and v["relation"] == "contradiction"
            and v["confidence"] < config.VERIFY_BELOW and not v.get("verified")]
    return keys[:config.MAX_VERIFY]


def verify_pairs(store, keys):
    """Second opinion on the given pairs with the stronger model. The stronger model's verdict wins."""
    by_id = {c["id"]: c for c in store.claims}
    items = [(by_id[a], by_id[b]) for a, b in keys]
    try:
        results = llm.judge_pairs(items, model=config.VERIFY_MODEL)
    except Exception as e:  # noqa: BLE001 - verification is a bonus; never fail the job because of it
        print(f"[VERIFY] skipped: {e}")
        return
    for k, v in results.items():
        old = store.verdicts[keys[k]]
        store.verdicts[keys[k]] = {"relation": v.relation, "confidence": v.confidence, "explanation": v.explanation,
                                   "verified": True, "first_opinion": old["relation"]}


def assemble_pairs(store) -> list:
    by_id = {c["id"]: c for c in store.claims}
    pairs = []
    for a_id, b_id, sim in store.candidates:
        verdict = store.verdicts.get((a_id, b_id))
        if verdict is None:
            continue
        pairs.append({"id": f"{a_id}__{b_id}", **verdict, "similarity": round(sim, 3),
                      "claim_a": _claim_out(by_id[a_id]), "claim_b": _claim_out(by_id[b_id])})
    # conflicts first, most confident first
    pairs.sort(key=lambda p: (p["relation"] != "contradiction", -p["confidence"]))
    return pairs


# ── Web verification of one claim (on demand) ─────────────────────────────────
def verify_claim_web(store, claim_id: str) -> dict:
    """Search the web for the claim, then let the LLM judge it using ONLY the returned snippets.
    A 'supported' / 'contradicted' verdict is only accepted if it cites at least one real result; otherwise it is
    downgraded to 'unverified' (the model must not be allowed to answer from memory and pretend it searched)."""
    claim = next((c for c in store.claims if c["id"] == claim_id), None)
    if claim is None:
        raise KeyError(claim_id)
    if claim_id in store.web_checks:
        return store.web_checks[claim_id]
    if len(store.web_checks) >= config.MAX_WEB_CHECKS:
        return {"error": f"Web-check limit reached for this session ({config.MAX_WEB_CHECKS})."}

    results = websearch.search(claim["text"], config.WEB_RESULTS)
    if not results:
        out = {"claim_id": claim_id, "verdict": "unverified", "confidence": 0,
               "explanation": "The web search returned no results for this claim.", "sources": []}
    else:
        v = llm.verify_claim(claim["text"], results)
        if v is None:
            raise RuntimeError("The model gave no answer.")
        sources, seen = [], set()
        for n in v.source_numbers:
            if 1 <= n <= len(results):
                r = results[n - 1]
                if r["url"].startswith(("http://", "https://")) and r["url"] not in seen:
                    seen.add(r["url"])
                    sources.append({"title": (r["title"] or r["url"])[:120], "url": r["url"]})
        verdict, explanation = v.verdict, v.explanation
        if verdict in ("supported", "contradicted") and not sources:
            verdict, explanation = "unverified", explanation + " (no search result was cited, so this is not trusted)"
        out = {"claim_id": claim_id, "verdict": verdict, "confidence": v.confidence,
               "explanation": explanation, "sources": sources}
    store.web_checks[claim_id] = out
    store.save()
    return out


# ── Knowledge graph of claims ─────────────────────────────────────────────────
def build_graph_data(store, pairs) -> dict:
    """Nodes = claims (that passed the guard), edges = 'contradicts' / 'supports' between claims of different sources."""
    edges, connected = [], set()
    for p in pairs:
        if p["relation"] == "neutral":
            continue
        a, b = p["claim_a"]["id"], p["claim_b"]["id"]
        edges.append({"source": a, "target": b, "confidence": p["confidence"],
                      "relation": "contradicts" if p["relation"] == "contradiction" else "supports"})
        connected.update((a, b))
    nodes = [{"id": c["id"], "label": c["text"], "source_id": c["source_id"], "source_name": c["source_name"],
              "page": c["page"], "support": c.get("support"), "connected": c["id"] in connected}
             for c in usable_claims(store)]
    return {"nodes": nodes, "edges": edges}


# ── Response building ─────────────────────────────────────────────────────────
def stats(pairs) -> dict:
    n = lambda rel: sum(1 for p in pairs if p["relation"] == rel)  # noqa: E731
    return {"pairs_checked": len(pairs), "contradictions": n("contradiction"),
            "agreements": n("agreement"), "neutral": n("neutral")}


def _pair_sentence(p) -> str:
    a, b = p["claim_a"], p["claim_b"]
    if p["relation"] == "contradiction":
        return f'{a["source_name"]} says "{a["text"]}" but {b["source_name"]} says "{b["text"]}"'
    return f'{a["source_name"]} and {b["source_name"]} agree: "{a["text"]}"'


def combined_summary(store) -> list:
    """No extra LLM call: built from the per-source summaries and the judged pairs."""
    pts = [f'{s["name"]}: {s["summary"][0]}' for s in store.sources if s["summary"]]
    st = stats(store.pairs)
    pts.append(f'Compared {st["pairs_checked"]} claim pairs across sources: {st["contradictions"]} contradictions, '
               f'{st["agreements"]} agreements, {st["neutral"]} neutral.')
    return pts


def _involves(p, sid) -> bool:
    return sid in (p["claim_a"]["source_id"], p["claim_b"]["source_id"])


def build_response(store) -> dict:
    pairs = store.pairs
    sources_out = []
    for s in store.sources:
        mine = [p for p in pairs if _involves(p, s["id"])]
        sources_out.append({
            "id": s["id"], "type": s["type"], "name": s["name"],
            "chunk_count": len(s["chunk_ids"]),
            "claim_count": sum(1 for c in usable_claims(store) if c["source_id"] == s["id"]),
            "analysis": {
                "summary": s["summary"],
                "agreements": [c["text"] for c in usable_claims(store) if c["source_id"] == s["id"]][:5],  # "Key Findings"
                "contradictions": [_pair_sentence(p) for p in mine if p["relation"] == "contradiction"],
                "stats": stats(mine),
            },
        })

    combined = None
    if len(store.sources) > 1:
        done = store.status.get("state") == "done"
        combined = {
            "summary": store.combined_points if done else ["Comparing sources…"],
            "agreements": [_pair_sentence(p) for p in pairs if p["relation"] == "agreement"][:5],
            "contradictions": [_pair_sentence(p) for p in pairs if p["relation"] == "contradiction"],
            "stats": stats(pairs),
        }
    return {"message": "Upload successful", "status": store.status, "sources": sources_out, "combined": combined,
            "pairs": pairs, "total_chunks": len(store.chunks), "total_claims": len(usable_claims(store)),
            "graph": build_graph_data(store, pairs),
            "guard": {"checked": sum(1 for c in store.claims if "grounded" in c),
                      "removed": sum(1 for c in store.claims if c.get("grounded") is False and config.GUARD_MODE == "filter")}}
