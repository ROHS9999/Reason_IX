"""Extraction, chunking and the embedding / reranker models."""
import re
from urllib.parse import urljoin

import fitz  # PyMuPDF
import numpy as np
import requests
from bs4 import BeautifulSoup

import config
import security

_model = None
_reranker = None
_nli = None


def get_model():
    """Load the embedding model once, on first use (not at import time)."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(config.EMBED_MODEL)
    return _model


def get_nli():
    global _nli
    if _nli is None:
        from sentence_transformers import CrossEncoder
        _nli = CrossEncoder(config.NLI_MODEL)
    return _nli


def get_reranker():
    global _reranker
    if _reranker is None:
        from sentence_transformers import CrossEncoder
        _reranker = CrossEncoder(config.RERANK_MODEL)
    return _reranker


# ── Extraction ────────────────────────────────────────────────────────────────
def extract_pdf_pages(file_bytes: bytes):
    """Return [(page_number, text), ...]. Keeping the page number is what makes citations possible."""
    with fitz.open(stream=file_bytes, filetype="pdf") as pdf:
        return [(i + 1, page.get_text()) for i, page in enumerate(pdf)]


def extract_text_from_url(url: str) -> str:
    """Fetch a page and return its readable text. Redirects are followed by hand so EVERY hop is validated
    (a public site could otherwise redirect us to an internal address)."""
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        r = None
        for _ in range(4):
            security.validate_url(url)
            r = requests.get(url, headers=headers, timeout=15, allow_redirects=False)
            if r.status_code in (301, 302, 303, 307, 308) and r.headers.get("Location"):
                url = urljoin(url, r.headers["Location"])
                continue
            break
        else:
            return ""
        if r is None or r.status_code != 200 or len(r.content) > config.MAX_URL_BYTES:
            return ""
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
            tag.decompose()
        main = soup.find("article") or soup.find("main") or soup.find(id="content") or soup
        tags = main.find_all(["p", "h1", "h2", "h3", "h4", "li", "blockquote", "td"])
        return " ".join(t.get_text(separator=" ", strip=True) for t in tags if len(t.get_text(strip=True)) > 30)
    except Exception as e:  # noqa: BLE001
        print(f"[URL ERROR] {e}")
        return ""


# ── Cleaning + sentence-aware chunking ────────────────────────────────────────
def clean_text(text: str) -> str:
    text = re.sub(r"(?<=[a-z])-\s*\n\s*(?=[a-z])", "", text)  # re-join words hyphenated across lines
    return re.sub(r"\s+", " ", text).strip()


_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def split_sentences(text: str):
    return [s.strip() for s in _SENTENCE_END.split(text) if s.strip()]


def chunk_text(text: str, max_chars: int = config.CHUNK_CHARS, overlap_chars: int = config.CHUNK_OVERLAP):
    """Split into sentences, then pack whole sentences into chunks of ~max_chars.
    Why: the old 500-word cutter sliced sentences in half, which hurts both retrieval and claim extraction.
    The overlap repeats the last sentence(s) so an idea on a chunk border is still seen whole."""
    sents = []
    for s in _SENTENCE_END.split(text):
        s = s.strip()
        while len(s) > max_chars:            # a giant "sentence" (table, code, no punctuation): cut on a space
            cut = s.rfind(" ", 0, max_chars)
            cut = cut if cut > 0 else max_chars
            sents.append(s[:cut])
            s = s[cut:].lstrip()
        if s:
            sents.append(s)

    chunks, cur, cur_len = [], [], 0
    for s in sents:
        if cur and cur_len + len(s) + 1 > max_chars:
            chunks.append(" ".join(cur))
            carry, n = [], 0                 # keep the tail sentences as overlap
            for t in reversed(cur):
                if n + len(t) > overlap_chars:
                    break
                carry.insert(0, t)
                n += len(t) + 1
            cur, cur_len = carry, n
        cur.append(s)
        cur_len += len(s) + 1
    if cur:
        chunks.append(" ".join(cur))
    return chunks


def chunk_pages(pages, min_words: int = 5):
    """pages = [(page_or_None, text)]. Returns [(page_or_None, chunk_text)].
    Chunks never cross a page boundary, so each chunk keeps exactly one page number."""
    out = []
    for page, text in pages:
        for piece in chunk_text(clean_text(text)):
            if len(piece.split()) >= min_words:
                out.append((page, piece))
    return out


# ── Embeddings + reranker ─────────────────────────────────────────────────────
def embed(texts):
    """Normalised vectors, so dot product == cosine similarity."""
    vecs = get_model().encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return np.asarray(vecs, dtype="float32")


def nli_probs(pairs):
    """pairs = [(premise, hypothesis)] -> [{'contradiction': p, 'entailment': p, 'neutral': p}, ...].
    NLI asks: IF the premise is true, must the hypothesis be true (entailment), false (contradiction) or open (neutral)?"""
    if not pairs:
        return []
    model = get_nli()
    id2label = getattr(model.model.config, "id2label", None) or {}
    names = [str(id2label.get(i, "")).lower() for i in range(3)]
    if sorted(names) != ["contradiction", "entailment", "neutral"]:
        names = ["contradiction", "entailment", "neutral"]       # documented label order of this model family
    logits = np.atleast_2d(np.asarray(model.predict(list(pairs)), dtype="float64"))
    e = np.exp(logits - logits.max(axis=1, keepdims=True))
    probs = e / e.sum(axis=1, keepdims=True)
    return [dict(zip(names, map(float, row))) for row in probs]


def rerank(query: str, chunks: list, k: int) -> list:
    """Cross-encoder: reads (question, passage) TOGETHER, so it is far more accurate than comparing two
    separate embeddings - but too slow for the whole corpus, so we only run it on ~15 candidates."""
    if not config.USE_RERANKER or len(chunks) <= 1:
        return chunks[:k]
    try:
        scores = get_reranker().predict([(query, c["text"]) for c in chunks])
        order = sorted(range(len(chunks)), key=lambda i: -float(scores[i]))
        return [chunks[i] for i in order[:k]]
    except Exception as e:  # noqa: BLE001 - never let the reranker break Q&A
        print(f"[RERANK] skipped: {e}")
        return chunks[:k]
