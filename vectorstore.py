"""Vector database layer. Chroma = persistent (survives restarts). If chromadb can't be installed
(e.g. no wheel for your Python version) we fall back to a small in-memory numpy store with the SAME interface,
so the app still runs."""
import numpy as np

import config

try:
    import chromadb
    from chromadb.config import Settings
    _client = chromadb.PersistentClient(path=config.CHROMA_DIR, settings=Settings(anonymized_telemetry=False))
    HAVE_CHROMA = True
except Exception as e:  # noqa: BLE001
    print(f"[VECTORS] chromadb unavailable ({e}); using the in-memory numpy fallback")
    _client = None
    HAVE_CHROMA = False


class ChromaVectors:
    def __init__(self, name: str):
        self.name = name
        self.col = _client.get_or_create_collection(name, metadata={"hnsw:space": "cosine"})

    def add(self, ids, embeddings, source_ids):
        self.col.add(ids=list(ids), embeddings=np.asarray(embeddings).tolist(),
                     metadatas=[{"source_id": int(s)} for s in source_ids])

    def query(self, embedding, n: int, source_id=None):
        total = self.col.count()
        if total == 0:
            return []
        res = self.col.query(query_embeddings=[np.asarray(embedding).tolist()], n_results=min(n, total),
                             where={"source_id": int(source_id)} if source_id is not None else None)
        return res["ids"][0]

    def count(self):
        return self.col.count()

    def reset(self):
        _client.delete_collection(self.name)
        self.col = _client.get_or_create_collection(self.name, metadata={"hnsw:space": "cosine"})


class NumpyVectors:
    def __init__(self, name: str):
        self.name = name
        self.ids, self.src, self.mat = [], [], None

    def add(self, ids, embeddings, source_ids):
        emb = np.asarray(embeddings, dtype="float32")
        self.mat = emb if self.mat is None else np.vstack([self.mat, emb])
        self.ids += list(ids)
        self.src += [int(s) for s in source_ids]

    def query(self, embedding, n: int, source_id=None):
        if self.mat is None:
            return []
        scores = self.mat @ np.asarray(embedding, dtype="float32")
        order = np.argsort(-scores)
        return [self.ids[i] for i in order if source_id is None or self.src[i] == source_id][:n]

    def count(self):
        return len(self.ids)

    def reset(self):
        self.ids, self.src, self.mat = [], [], None


def make(name: str):
    return ChromaVectors(name) if HAVE_CHROMA else NumpyVectors(name)
