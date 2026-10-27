"""Tiny in-memory sliding-window rate limiter, per client IP.
Protects your LLM quota on a public deployment. In memory = resets on restart and is per server process,
which is fine for a single-container demo (use Redis or a gateway if you ever scale out)."""
import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

import config

_hits = defaultdict(deque)
_lock = threading.Lock()
WINDOW_SECONDS = 3600


def client_ip(request: Request) -> str:
    if config.TRUST_PROXY:  # only behind a proxy you control; otherwise a client could fake this header
        fwd = request.headers.get("x-forwarded-for", "")
        if fwd:
            return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def limit(name: str, max_calls):
    """FastAPI dependency: at most max_calls() requests per hour per IP. max_calls is a function so that the
    value is read from config on every request (and tests can change it)."""
    def dependency(request: Request):
        if not config.RATE_LIMIT_ENABLED:
            return
        key, now = (name, client_ip(request)), time.monotonic()
        with _lock:
            q = _hits[key]
            while q and now - q[0] > WINDOW_SECONDS:
                q.popleft()
            if len(q) >= max_calls():
                retry = int(WINDOW_SECONDS - (now - q[0])) + 1
                raise HTTPException(status_code=429, headers={"Retry-After": str(retry)},
                                    detail=f"Too many requests. Try again in {max(1, retry // 60)} minute(s).")
            q.append(now)
    return dependency


def reset():
    """Used by tests."""
    with _lock:
        _hits.clear()
