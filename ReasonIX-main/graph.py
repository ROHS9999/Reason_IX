"""The analysis pipeline as a LangGraph state machine:

    extract claims --> guard (drop unsupported claims) --> compare --(shaky conflicts?)--> verify --> finalize
                                                               \\-------------- no ------------------>/

Why a graph and not a plain function: every step is a named node with a clear job, the 'verify' step only runs when
it is needed (a conditional edge), and the same structure is easy to extend (web-search verification, retries).
If langgraph is not installed we run the SAME nodes in the same order with plain Python, so nothing breaks."""
from typing import TypedDict

import pipeline

try:
    from langgraph.graph import END, StateGraph
    HAVE_LANGGRAPH = True
except Exception:  # noqa: BLE001
    HAVE_LANGGRAPH = False


class JobState(TypedDict, total=False):
    stage: str
    abort: bool
    to_verify: list


def make_nodes(store, new_sources):
    gen = store.generation

    def cancelled():
        return store.generation != gen          # the user pressed Clear while we were working

    def extract(state):
        store.status = {"state": "processing", "stage": "Extracting claims…"}
        pipeline.analyze_sources(store, new_sources)
        if cancelled():
            return {"stage": "cancelled", "abort": True}
        if not store.claims:
            store.status = {"state": "error", "stage": new_sources[0]["summary"][0]}
            return {"stage": "no_claims", "abort": True}
        return {"stage": "extracted"}

    def guard(state):
        store.status = {"state": "processing", "stage": "Checking every claim against its source text…"}
        pipeline.guard_new_claims(store)
        if cancelled():
            return {"stage": "cancelled", "abort": True}
        return {"stage": "guarded"}

    def compare(state):
        store.status = {"state": "processing", "stage": "Comparing claims across sources…"}
        pipeline.judge_candidates(store)
        if cancelled():
            return {"stage": "cancelled", "abort": True}
        return {"stage": "compared", "to_verify": pipeline.needs_verification(store)}

    def verify(state):
        store.status = {"state": "processing", "stage": "Double-checking uncertain conflicts with a larger model…"}
        pipeline.verify_pairs(store, state.get("to_verify", []))
        return {"stage": "verified"}

    def finalize(state):
        if cancelled():
            return {"stage": "cancelled", "abort": True}
        store.pairs = pipeline.assemble_pairs(store)
        store.combined_points = pipeline.combined_summary(store)
        store.status = {"state": "done", "stage": ""}
        return {"stage": "done"}

    return {"extract": extract, "guard": guard, "compare": compare, "verify": verify, "finalize": finalize}


def after_extract(state) -> str:
    return "end" if state.get("abort") else "guard"


def after_guard(state) -> str:
    return "end" if state.get("abort") else "compare"


def after_compare(state) -> str:
    if state.get("abort"):
        return "end"
    return "verify" if state.get("to_verify") else "finalize"


def build_graph(nodes):
    g = StateGraph(JobState)
    for name, fn in nodes.items():
        g.add_node(name, fn)
    g.set_entry_point("extract")
    g.add_conditional_edges("extract", after_extract, {"guard": "guard", "end": END})
    g.add_conditional_edges("guard", after_guard, {"compare": "compare", "end": END})
    g.add_conditional_edges("compare", after_compare, {"verify": "verify", "finalize": "finalize", "end": END})
    g.add_edge("verify", "finalize")
    g.add_edge("finalize", END)
    return g.compile()


def run_linear(nodes):
    """Same nodes, same routing, no langgraph."""
    state = {}
    state.update(nodes["extract"](state))
    if after_extract(state) == "end":
        return state
    state.update(nodes["guard"](state))
    if after_guard(state) == "end":
        return state
    state.update(nodes["compare"](state))
    route = after_compare(state)
    if route == "end":
        return state
    if route == "verify":
        state.update(nodes["verify"](state))
    state.update(nodes["finalize"](state))
    return state


def run_job(store, new_sources):
    """Runs in a background thread after /upload/ has already answered."""
    gen = store.generation
    try:
        nodes = make_nodes(store, new_sources)
        if HAVE_LANGGRAPH:
            build_graph(nodes).invoke({"stage": "start"})
        else:
            run_linear(nodes)
    except Exception as e:  # noqa: BLE001
        print(f"[JOB] failed: {e}")
        if store.generation == gen:
            store.status = {"state": "error", "stage": str(e)[:300]}
    if store.generation == gen:
        store.save()
