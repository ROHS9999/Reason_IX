# ReasonIX - ZIP 4 (hallucination guard, claim graph, web verification)

## How to apply
1. Copy every file over your project (same paths).
2. `pip install -r requirements.txt -r requirements-extras.txt -r requirements-dev.txt`   (new: `ddgs` for web search)
3. Restart the backend (`uvicorn main:app`, no --reload). The first start loads the NLI model (the same ~740 MB DeBERTa you
   already downloaded for the evaluation, so no new download).
4. Optional in `.env`: `TAVILY_API_KEY=...` (better web search than the keyless default), `GUARD_MODE=filter|flag|off`.
5. Clear and upload 2+ sources again (old claims have no guard data). Then `pytest -q`.

## What you get (and the why for interviews)

**Hallucination guard** (`guard.py`, new graph node between extract and compare)
- Problem: an LLM can invent a "fact" that is not in the document; compared with another source it would produce a
  contradiction that does not exist. Fix: each claim is checked against the 1-2 sentences of its own chunk that overlap most
  with it, using an NLI model (premise = source sentences, hypothesis = claim). Grounded = entailment >= 0.5, OR the quoted
  evidence is verbatim in the chunk AND the source does not contradict the claim. Unsupported claims are removed before
  comparison and counted ("N of M claims removed" banner). Each claim also shows a "source support %" badge.
- Interview line: "I gate the comparison step with an entailment check, so hallucinated claims can't produce false conflicts."
- `GUARD_MODE=flag` keeps everything and only labels; `off` disables it.

**Claim graph** (`pipeline.build_graph_data`, `ClaimGraph` in Dashboard.jsx, "All Sources" tab)
- Nodes = claims that passed the guard, one column per source; edges = contradicts (orange) / supports (green), thicker =
  more confident. Click a dot to read the claim and everything it is linked to. No extra library: plain SVG.
- Interview line: "The graph is built from the pair verdicts, so it is a second view of the same data, not a second pipeline."

**Web verification** (`websearch.py`, `pipeline.verify_claim_web`, `POST /verify/`, "Verify on the web" button on every claim)
- On demand (not automatic: it is slow and uses the web). Search -> the LLM may use ONLY the returned snippets -> verdict
  supported / contradicted / unverified + sources. A supported/contradicted verdict that cites no real result is downgraded to
  "unverified" (so the model cannot answer from memory and pretend it searched). Results are cached per claim, max 30 per
  session. We only read snippets, never fetch result URLs (no SSRF). Request body validated with Pydantic (422 on bad input).

## Honest limits
- Tested here: 37 tests pass (guard rules, gating before comparison, web-verification rules, graph data, caching,
  persistence). NOT tested here: the real NLI model on real claims, real web search (ddgs / Tavily), the LangGraph path,
  Chroma, the dashboard in a browser, and the 6 API tests (they need fastapi, which my sandbox lacks).
- The guard thresholds (0.5 / 0.5) are my defaults, not tuned on data. If it removes too many good claims, set
  `GUARD_MODE=flag` or tell me and I will tune it with you. `ddgs` is an unofficial scraper and can be rate-limited:
  use `TAVILY_API_KEY` for something steadier.
- Web verification is a helper, not ground truth: snippets can be wrong or outdated.
