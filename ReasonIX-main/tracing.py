"""Optional Langfuse tracing. Set LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY (and LANGFUSE_HOST) in .env and every
LLM call (prompt, output, latency, tokens, errors) shows up in the Langfuse dashboard. No keys = no tracing, no errors."""
import os

_handler_cls = None
_tried = False


def callbacks() -> list:
    global _handler_cls, _tried
    if not (os.getenv("LANGFUSE_PUBLIC_KEY") and os.getenv("LANGFUSE_SECRET_KEY")):
        return []
    if not _tried:
        _tried = True
        try:
            from langfuse.langchain import CallbackHandler      # langfuse >= 3
            _handler_cls = CallbackHandler
        except Exception:  # noqa: BLE001
            try:
                from langfuse.callback import CallbackHandler   # langfuse 2.x
                _handler_cls = CallbackHandler
            except Exception as e:  # noqa: BLE001
                print(f"[TRACING] langfuse not usable: {e}")
    try:
        return [_handler_cls()] if _handler_cls else []         # one handler per call = one trace per call
    except Exception as e:  # noqa: BLE001
        print(f"[TRACING] could not create handler: {e}")
        return []
