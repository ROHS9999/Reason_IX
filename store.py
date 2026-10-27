"""State of ONE user session: sources, chunks, claims, verdicts, vectors.
Saved as JSON (data/sessions/<id>.json) + vectors in Chroma, so a refresh or a server restart loses nothing."""
import json
import os
import threading

import config
import retrieval
import utils
import vectorstore


def _path(sid: str) -> str:
    return os.path.join(config.DATA_DIR, "sessions", f"{sid}.json")


class Store:
    def __init__(self, sid: str):
        self.sid = sid
        self.generation = 0
        self._io_lock = threading.Lock()
        self.vectors = vectorstore.make(f"s_{sid}")
        self._init_state()

    def _init_state(self):
        self.generation += 1                   # lets a running background job notice a /clear
        self.status = {"state": "idle", "stage": ""}
        self.pairs = []
        self.combined_points = []
        self.sources = []     # {id, type, name, chunk_ids, summary}
        self.chunks = []      # {id, source_id, source_name, type, page, text}
        self.claims = []      # {id, text, source_id, source_name, chunk_id, page, evidence, evidence_verified}
        self.verdicts = {}    # (claim_id_a, claim_id_b) -> verdict dict, so re-analysis never repeats an LLM call
        self.web_checks = {}  # claim_id -> web verification result (cached, so no repeated searches)
        self.candidates = []  # [(claim_id_a, claim_id_b, similarity)] chosen for the last comparison
        self._next_id = 0
        self._unindexed = []  # chunks not yet in the vector DB
        self._bm25 = None

    def reset(self):
        self._init_state()
        self.vectors.reset()
        try:
            os.remove(_path(self.sid))
        except FileNotFoundError:
            pass

    # -- persistence ---------------------------------------------------------------
    def save(self):
        # The background analysis thread may be adding claims / verdicts right now, so work on copies:
        # iterating a dict that another thread is growing raises "dictionary changed size during iteration".
        data = {"sources": list(self.sources), "chunks": list(self.chunks), "claims": list(self.claims),
                "verdicts": {f"{a}|{b}": v for (a, b), v in list(self.verdicts.items())},
                "pairs": list(self.pairs), "combined_points": list(self.combined_points), "next_id": self._next_id,
                "web_checks": dict(self.web_checks)}
        os.makedirs(os.path.dirname(_path(self.sid)), exist_ok=True)
        with self._io_lock:
            tmp = _path(self.sid) + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f)
            os.replace(tmp, _path(self.sid))   # atomic: a crash can never leave a half-written file

    @classmethod
    def load(cls, sid: str):
        try:
            with open(_path(sid), encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, ValueError):
            return None
        st = cls(sid)
        st.sources, st.chunks, st.claims = data["sources"], data["chunks"], data["claims"]
        st.verdicts = {tuple(k.split("|")): v for k, v in data["verdicts"].items()}
        st.pairs, st.combined_points, st._next_id = data["pairs"], data["combined_points"], data["next_id"]
        st.web_checks = data.get("web_checks", {})        # sessions saved by older versions have no such key
        for src in st.sources:                       # server was restarted while a background job was running
            if src["summary"] == ["Analyzing…"]:
                src["summary"] = ["Analysis was interrupted by a restart - clear and upload again."]
        if st.vectors.count() != len(st.chunks):     # vectors missing (e.g. fallback store after a restart)
            st.vectors.reset()
            st._unindexed = list(st.chunks)
            st.sync_vectors()
        return st

    # -- sources ---------------------------------------------------------------------
    def add_source(self, type_: str, name: str, pages):
        """pages = [(page_or_None, text)]. Returns the new source, or None if there was no usable text."""
        pieces = utils.chunk_pages(pages)
        if not pieces:
            return None
        sid = self._next_id
        self._next_id += 1
        source = {"id": sid, "type": type_, "name": name, "chunk_ids": [], "summary": ["Analyzing…"]}
        for n, (page, text) in enumerate(pieces):
            chunk = {"id": f"s{sid}-c{n}", "source_id": sid, "source_name": name,
                     "type": type_, "page": page, "text": text}
            self.chunks.append(chunk)
            self._unindexed.append(chunk)
            source["chunk_ids"].append(chunk["id"])
        self.sources.append(source)
        self._bm25 = None
        return source

    def get_chunk(self, chunk_id: str):
        return next((c for c in self.chunks if c["id"] == chunk_id), None)

    # -- retrieval (used by /compare) ----------------------------------------------
    def sync_vectors(self):
        """Embed ONLY the new chunks and add them to the vector DB (the old code re-embedded everything)."""
        if not self._unindexed:
            return
        embs = utils.embed([c["text"] for c in self._unindexed])
        self.vectors.add([c["id"] for c in self._unindexed], embs, [c["source_id"] for c in self._unindexed])
        self._unindexed = []

    def get_bm25(self):
        if self._bm25 is None and self.chunks:
            self._bm25 = retrieval.BM25([retrieval.tokenize(c["text"]) for c in self.chunks])
        return self._bm25

    def search(self, query: str, k: int = 4, source_id=None):
        return retrieval.hybrid_search(self, query, k, source_id)
