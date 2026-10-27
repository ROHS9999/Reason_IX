# ReasonIX upgrade - ZIP 2 (steps 6-7: storage + retrieval)

## How to apply
1. Copy every file over your project (same paths). Backend files next to `main.py`; 3 frontend files in `FrontWork/frontend/src/`.
2. `pip install -r requirements.txt`  (adds `chromadb`; `faiss-cpu` is no longer used).
   If chromadb fails to install on your Python version, delete that line and install the rest: the app falls back to an
   in-memory numpy vector store automatically (it prints a warning). Tell me and I will switch you to Qdrant.
3. Restart the backend WITHOUT --reload: `uvicorn main:app`  (it now writes a `data/` folder, which would trigger reloads).
   First start downloads the reranker model (~90 MB) once.
4. Clear browser data for localhost or just upload again: old data from zip 1 is not carried over.

## What changed and why (interview lines)

**Per-session storage (`sessions.py`, `store.py`, `config.js`)**
- Old: ONE global state for every visitor - two users would see and overwrite each other's documents.
- New: the browser makes a random id (localStorage) and sends it as `X-Session-Id`; FastAPI's `Depends(get_store)` gives each
  request ITS user's `Store`. LRU cap of 50 sessions in memory; the id is regex-validated (it becomes a file name).
- Interview: "I isolated tenants with a session id and dependency injection."

**Persistence (`store.py`) + Chroma (`vectorstore.py`)**
- Vectors live in a persistent Chroma collection per session (cosine distance); everything else is saved as JSON
  (atomic write: temp file then rename). Refresh or server restart loses nothing.
- Only NEW chunks are embedded when you add sources (old code re-embedded everything every time).
- Interview: "FAISS in RAM was a prototype; I moved to a persistent vector DB behind a small interface, with a fallback."

**Better chunking (`utils.chunk_text`)**
- Old: cut every 500 words, often mid-sentence. New: split into sentences, pack whole sentences up to ~2000 chars,
  repeat the last ~200 chars as overlap; chunks still never cross a PDF page (page citations stay exact).
- Interview: "Sentence-aware chunking with overlap keeps each idea intact for both retrieval and claim extraction."

**Hybrid search + reranker (`retrieval.py`, used by /compare)**
- Vectors understand meaning but can miss exact names/numbers; BM25 (written from scratch, ~20 lines) nails exact words
  but is blind to meaning. Reciprocal Rank Fusion merges both rankings, then a cross-encoder reranker
  (ms-marco-MiniLM) reads question+passage together and picks the best 4.
- Interview: "Retrieve wide and cheap, rerank narrow and accurate."

## Honest limits
- The Chroma code path could not be run here (no network); the logic was tested with the numpy fallback.
  If Chroma throws an error, paste it and I fix it.
- No automatic cleanup of old session files on disk yet (zip 3 adds tests + CI, zip 4 deployment).
