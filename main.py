import os
import threading
from typing import List
from urllib.parse import urlparse
import traceback

from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import config
import graph
import llm
import pipeline
import ratelimit
import security
import utils
import websearch
from sessions import get_store
from store import Store

app = FastAPI(title="ReasonIX")

# Only the frontend origins listed in ALLOWED_ORIGINS (.env) may call the API from a browser.
app.add_middleware(CORSMiddleware, allow_origins=config.ALLOWED_ORIGINS, allow_credentials=False,
                   allow_methods=["GET", "POST"], allow_headers=["X-Session-Id", "Content-Type"])


# Load the embedding + reranker models in the background at startup so the first upload/question doesn't pay for it.
if os.getenv("PRELOAD_MODELS", "1") == "1":
    threading.Thread(target=lambda: (utils.get_model(), utils.get_reranker(), utils.get_nli()), daemon=True).start()


@app.get("/")
def home():
    return {"message": "Backend running"}


@app.post("/clear/")
def clear_all(store: Store = Depends(get_store)):
    store.reset()
    return {"message": "Cleared."}


# NOTE: plain `def` (not `async def`): FastAPI runs it in a worker thread, so the slow, blocking LLM calls
# don't freeze the whole server.
@app.post("/upload/", dependencies=[Depends(ratelimit.limit("upload", lambda: config.RATE_UPLOADS_PER_HOUR))])
def upload_data(
    files: List[UploadFile] = File([]),
    text_input: str = Form(""),
    url_input: str = Form(""),
    store: Store = Depends(get_store),
):
    if store.status.get("state") == "processing":
        return {"error": "Still analyzing the previous upload - wait a few seconds and try again."}
    if len(files) > config.MAX_FILES:
        return {"error": f"Too many files (max {config.MAX_FILES})."}
    if len(text_input) > config.MAX_TEXT_CHARS:
        return {"error": f"Text is too long (max {config.MAX_TEXT_CHARS:,} characters)."}
    urls = [u.strip() for u in url_input.split(",") if u.strip()]
    if len(urls) > config.MAX_URLS:
        return {"error": f"Too many URLs (max {config.MAX_URLS})."}

    new_sources, warnings = [], []

    for file in files:
        name = file.filename or "upload.pdf"
        if not name.lower().endswith(".pdf"):
            warnings.append(f"{name}: only PDF files are supported")
            continue
        try:
            limit = config.MAX_FILE_MB * 1024 * 1024
            data = file.file.read(limit + 1)
            if len(data) > limit:
                warnings.append(f"{name} is larger than {config.MAX_FILE_MB} MB")
                continue
            src = store.add_source("pdf", name, utils.extract_pdf_pages(data))
            (new_sources.append(src) if src else warnings.append(f"No text found in {name}"))
        except Exception:  # noqa: BLE001
            traceback.print_exc()
            warnings.append(f"Could not read {name}")

    if text_input.strip():
        label = text_input.strip()[:50].replace("\n", " ") + ("…" if len(text_input) > 50 else "")
        src = store.add_source("text", label, [(None, text_input)])
        if src:
            new_sources.append(src)

    for url in urls:
        try:
            security.validate_url(url)
        except ValueError as e:
            warnings.append(f"Blocked {url}: {e}")
            continue
        text = utils.extract_text_from_url(url)
        if not text:
            warnings.append(f"Could not fetch {url}")
            continue
        parsed = urlparse(url)
        label = parsed.netloc + (parsed.path[:40] if parsed.path != "/" else "")
        src = store.add_source("url", label, [(None, text)])
        if src:
            new_sources.append(src)

    if not new_sources:
        return {"error": "No valid data found. " + " ".join(warnings)}

    # Embed + store the NEW chunks in the vector DB now (fast, no LLM) so Q&A works immediately...
    store.sync_vectors()
    store.save()

    # ...and run the slow part (claims + comparison) in a background thread. We answer RIGHT NOW with the
    # sources; the dashboard polls /status/ and fills in claims and contradictions as they finish.
    store.status = {"state": "processing", "stage": "Extracting claims…"}
    threading.Thread(target=graph.run_job, args=(store, new_sources), daemon=True).start()

    out = pipeline.build_response(store)
    out["warnings"] = warnings
    return out


@app.get("/status/")
def status(store: Store = Depends(get_store)):
    """Polled by the dashboard while the background analysis runs."""
    return pipeline.build_response(store)


@app.get("/compare/", dependencies=[Depends(ratelimit.limit("ask", lambda: config.RATE_QUESTIONS_PER_HOUR))])
def compare(
    query: str = Query(..., min_length=2, max_length=500),
    source_name: str = Query("", max_length=300),
    store: Store = Depends(get_store),
):
    """Question answering over retrieved chunks. Every answer comes with numbered citations."""
    if not store.chunks:
        return {"answer": "No data uploaded yet.", "citations": []}
    source_id = None
    if source_name:
        src = next((s for s in store.sources if s["name"] == source_name), None)
        source_id = src["id"] if src else None
    try:
        hits = store.search(query, k=4, source_id=source_id)  # hybrid (vectors + BM25) -> rerank
        if not hits:
            return {"answer": "Could not find relevant content.", "citations": []}
        context = "\n\n".join(
            f"[{n}] ({c['source_name']}{', page ' + str(c['page']) if c['page'] else ''})\n{c['text']}"
            for n, c in enumerate(hits, 1)
        )
        citations = [{"n": n, "source": c["source_name"], "page": c["page"], "chunk_id": c["id"]}
                     for n, c in enumerate(hits, 1)]
        return {"answer": llm.answer_query(query, context), "citations": citations}
    except Exception as e:  # noqa: BLE001
        traceback.print_exc()
        return {"answer": f"Error: {e}", "citations": []}


class VerifyRequest(BaseModel):
    """Validated request body (Pydantic): a 422 is returned automatically if the id is missing or malformed."""
    claim_id: str = Field(min_length=1, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")


@app.post("/verify/", dependencies=[Depends(ratelimit.limit("web", lambda: config.RATE_WEB_CHECKS_PER_HOUR))])
def verify(req: VerifyRequest, store: Store = Depends(get_store)):
    """Check ONE claim against the live web: supported / contradicted / unverified, with the sources used."""
    try:
        return pipeline.verify_claim_web(store, req.claim_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Claim not found")
    except websearch.WebSearchUnavailable as e:
        return {"error": str(e)}
    except Exception as e:  # noqa: BLE001
        traceback.print_exc()
        return {"error": f"Verification failed: {e}"}


@app.get("/chunk/{chunk_id}")
def get_chunk(chunk_id: str, store: Store = Depends(get_store)):
    """Lets the UI show the exact source passage behind a claim or citation."""
    c = store.get_chunk(chunk_id)
    if not c:
        raise HTTPException(status_code=404, detail="Chunk not found")
    return {"id": c["id"], "source_name": c["source_name"], "page": c["page"], "text": c["text"]}
