# ReasonIX - ZIP 3 (evaluation, LangGraph, tracing, tests, Docker, CI, security)

## How to apply
1. Copy every file over your project (same paths). New folders: `evaluation/`, `tests/`, `.github/`.
2. `pip install -r requirements.txt -r requirements-extras.txt -r requirements-dev.txt`
   (extras = langgraph + langfuse; if one fails to install on Python 3.14 just skip it, the app has fallbacks).
3. Restart the backend: `uvicorn main:app` (no --reload). Add `.env` values if you want (see `.env.example`).
4. Run the tests: `pytest -q`

## Get the numbers for your resume (do this yourself, ~2 minutes)
    python -m evaluation.run_eval            # accuracy / macro-F1: gpt-oss-20b vs gpt-oss-120b vs DeBERTa NLI vs baseline
    python -m evaluation.retrieval_eval      # Hit@1 / MRR: vector vs BM25 vs hybrid vs hybrid+rerank (no API key needed)
Results land in `evaluation/results_*.md`; `results_pairs.json` lists every prediction so you can read the mistakes.

IMPORTANT - be honest on the resume:
- The 45 pairs and 12-doc corpus were written by me (Claude), not collected from real data. READ `evaluation/dataset.jsonl`
  and fix any label you disagree with BEFORE you run it - the labels are only as good as your agreement with them.
- 45 pairs is small: one pair = 2.2 points of accuracy. Say "on a 45-pair hand-labeled set", never "state of the art".
- Llama 3.1 8B / 3.3 70B no longer exist on Groq (retired 16 Aug 2026), so the comparison is gpt-oss-20b vs gpt-oss-120b vs NLI.
- RAGAS is NOT included (I could not verify its API offline). Retrieval is measured with Hit@k / MRR instead. Do not write "RAGAS" on the resume.
- Good resume line (fill with YOUR numbers): "Built a claim-level contradiction detector and evaluated 3 judges on a
  45-pair labeled set (best: <model>, <acc>% accuracy / <F1> macro-F1); hybrid search + reranking raised MRR from <x> to <y>."

## What changed and why (interview lines)
- **Evaluation** (`evaluation/`): accuracy, per-class precision/recall/F1, macro-F1, confusion matrix written by hand.
  Macro-F1 averages the 3 classes so the hard one (contradiction) counts as much as the easy ones. The LLM judges are
  tested with the exact production prompt. NLI (DeBERTa) is directional, so both directions are averaged.
- **LangGraph** (`graph.py`): nodes extract -> compare -> (verify) -> finalize. `verify` only runs when a contradiction has
  confidence < 75: the bigger model (`VERIFY_MODEL`) re-judges it and its verdict wins. Why: a false "contradiction" is the
  worst error, so spend extra compute only on the shaky ones. The UI shows "re-checked by larger model".
- **Langfuse** (`tracing.py`): set the 3 env vars and every LLM call is traced (prompt, output, latency). Optional.
- **Pydantic/limits/CORS** (`main.py`): query length validated (422 otherwise), max files/size/text/URLs, PDF-only, CORS only
  for `ALLOWED_ORIGINS`.
- **SSRF protection** (`security.py`): users could make the server fetch localhost or cloud-metadata addresses through the URL
  box. Now only public http(s) hosts, and every redirect hop is re-checked.
- **Tests** (`tests/`): 30 tests - chunking, BM25/RRF, store persistence + isolation, the whole graph with a fake LLM
  (including the verify path and cancel-on-Clear), retry/fallback logic, SSRF, metrics, API.
- **Docker + CI**: backend image (CPU torch, models baked in), frontend image (build -> nginx), compose file, GitHub Actions
  (pytest, frontend build, docker builds).

## Honest limits
- Tested here: everything in `tests/` except `test_api.py` (needs fastapi, skipped here) - 25 passed. NOT tested here: the
  real LangGraph path (the fallback path was), Chroma, Langfuse, Docker/CI runs, and all real Groq/model calls.
  If `pytest` or a Docker/CI step fails, paste the error and I fix it.
- Evaluation numbers do not exist until YOU run the commands above.
