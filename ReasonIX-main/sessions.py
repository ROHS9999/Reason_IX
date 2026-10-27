"""One Store per browser session. The browser sends a random id in the X-Session-Id header (see config.js),
so two people using the app never see each other's documents (the old code used ONE global for everybody)."""
import re
import threading
from collections import OrderedDict

from fastapi import Header, HTTPException

import config
from store import Store

_SID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{6,62}[A-Za-z0-9]$")   # also a safe file / collection name
_sessions = OrderedDict()
_lock = threading.Lock()


def get_store(x_session_id: str = Header(default="")) -> Store:
    """FastAPI dependency: every endpoint that declares `store: Store = Depends(get_store)` gets ITS user's store."""
    sid = x_session_id
    if not _SID.match(sid):
        raise HTTPException(status_code=400, detail="Missing or invalid X-Session-Id header")
    with _lock:
        if sid in _sessions:
            _sessions.move_to_end(sid)
            return _sessions[sid]
        store = Store.load(sid) or Store(sid)
        _sessions[sid] = store
        # keep memory bounded: drop the least recently used sessions (their data stays on disk)
        for old in list(_sessions):
            if len(_sessions) <= config.MAX_SESSIONS_IN_MEMORY:
                break
            if old != sid and _sessions[old].status.get("state") != "processing":
                del _sessions[old]
        return store
