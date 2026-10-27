# ReasonIX upgrade - ZIP 1 (steps 1-5)

## How to apply
1. Copy every file from this zip over your project (same paths). Backend files go in the folder with `main.py`.
2. Delete the files listed in `DELETE_THESE.txt`.
3. `pip install -r requirements.txt` (new: langchain-core, langchain-groq, pydantic).
4. Keep your `.env` with `GROQ_API_KEY`. Frontend: create `FrontWork/frontend/.env` from `.env.example`
   (for your live Railway backend set `VITE_API_URL=https://reasonix-production.up.railway.app`).
5. Run backend `uvicorn main:app --reload`, frontend `npm run dev`, upload 2+ sources on the same topic.

## What changed and why (say these in interviews)

**Step 1 - claim extraction (`llm.py`, `schemas.py`, `pipeline.py`)**
- Old: one big prompt asked for "contradictions", so the model always invented 3 (usually limitations).
- New: each source is turned into atomic, self-contained claims, each with a verbatim evidence sentence.
- Why: you can only compare things that are comparable. Claims are the unit of comparison.
- LangChain + Pydantic (`with_structured_output`) forces the LLM to fill a typed schema, so no regex/json.loads hacks.
- Interview line: "I turned free-text generation into structured extraction with schema validation."

**Step 2 - pairing + judging (`pipeline.candidate_pairs`, `llm.check_pair`)**
- Comparing every claim with every other = N x M LLM calls. Contradictions only exist between claims on the SAME
  topic, so I embed claims and compare only the top-2 most similar claims per other source (cosine >= 0.45), max 20 pairs.
- Each pair gets Contradiction / Agreement / Neutral + confidence + one-line reason. "If unsure -> neutral" avoids false alarms.
- Verdicts are cached in the store, so "Add & Re-analyze" never repeats a call.
- Interview line: "Retrieval narrows the search space, the LLM only judges likely candidates."

**Step 3 - UI (`Dashboard.jsx`)**
- Side-by-side conflicting claims, filter Conflicts / Agreements / All, honest "no contradictions found" message.
- The meter now uses real judged pairs (the old one counted list items, i.e. fake). Bars show model confidence.

**Step 4 - citations**
- PDF text is extracted page by page; chunks never cross a page, so every chunk, claim and answer carries its page number.
- `/chunk/{id}` returns the exact passage; "View source passage" in the UI uses it. `/compare` answers cite `[1] [2]`
  and return a Sources list.
- Bonus: `evidence_verified` checks the quoted evidence really appears in the chunk (first small hallucination guard).

**Step 5 - clean-up**
- Deleted dead files, removed the duplicate URL extractor, removed the hardcoded verb-list/regex sentence filter.
- `main.py` is now only endpoints; logic split into `config / schemas / utils / store / llm / pipeline`.
- State is one `Store` object instead of loose globals (step 6 makes it per-session + Chroma).
- Upload is a plain `def` so FastAPI runs the slow LLM calls in a worker thread and doesn't freeze the server.
- One `config.js` for the API URL (the Input page and Dashboard used different hardcoded URLs).

## Honest limits (we fix these in later zips)
- Not yet per-session: two users share one Store (zip 2). FAISS is still in memory (zip 2).
- Llama 8B can misjudge; zip 3 measures accuracy against a labeled set and compares 70B / NLI.
- Upload now answers in ~1-2 s (no LLM); claims + contradictions fill in over the next few seconds (dashboard polls /status/). LLM calls: 1 per source + 1 for all pairs + 1 per question. Model: openai/gpt-oss-20b (Groq retired Llama 3.1 8B on 16 Aug 2026).
- I could not run this against Groq here. Run it and send me any error text.
