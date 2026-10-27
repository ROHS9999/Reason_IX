"""Every LLM call lives here. LangChain gives us: prompt template | model | typed (Pydantic) output.
Only THREE kinds of LLM call exist, on purpose (each call costs ~1-2 s):
  analyze_source -> 1 call per source  (summary + claims together)
  judge_pairs    -> 1 call for ALL claim pairs together
  answer_query   -> 1 call per question"""
import time

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

import config
import tracing
from schemas import BatchVerdicts, SourceAnalysis, WebVerdict

_llms = {}


def get_llm(model: str = None) -> ChatGroq:
    """One client per model name (the verifier and the evaluation use other models than the default)."""
    model = model or config.LLM_MODEL
    if model not in _llms:
        kwargs = {}
        if "gpt-oss" in model:
            kwargs["reasoning_effort"] = "low"  # gpt-oss "thinks" first; low = much faster, enough for our tasks
        # temperature 0 = same input gives (nearly) the same output; we want repeatable judgements
        _llms[model] = ChatGroq(model=model, temperature=0, max_tokens=2500, **kwargs)
    return _llms[model]


def _structured_chain(system: str, human: str, schema, method: str, model: str = None):
    prompt = ChatPromptTemplate.from_messages([("system", system), ("human", human)])
    # the model must fill OUR schema instead of free text we would have to regex
    return prompt | get_llm(model).with_structured_output(schema, method=method)


_RETRY_WAIT_CODES = (429, 500, 502, 503, 504)


def _call(chain, inputs: dict):
    """Retry only what can go away: rate limits / server errors (wait), bad model output (one quick retry).
    Wrong model name, bad key, or a 400 are raised at once - the caller decides what to do."""
    last, bad_output_tries = None, 0
    for attempt in range(1, config.LLM_RETRIES + 1):
        try:
            cb = tracing.callbacks()                      # [] unless Langfuse keys are set
            return chain.invoke(inputs, config={"callbacks": cb}) if cb else chain.invoke(inputs)
        except Exception as e:  # noqa: BLE001
            code = getattr(e, "status_code", None)
            if code in (400, 401, 403, 404):
                raise
            last = e
            if code in _RETRY_WAIT_CODES:
                if attempt < config.LLM_RETRIES:
                    time.sleep(config.LLM_RETRY_WAIT * attempt)
            else:
                bad_output_tries += 1
                if bad_output_tries >= 2:
                    break
    raise last


# Small models sometimes emit broken JSON in a tool call (Groq: 400 "tool_use_failed"). So we try the
# function-calling method, then JSON-schema mode (constrained decoding), then function calling once more.
_METHODS = ("function_calling", "json_schema", "function_calling")


def _structured_call(system: str, human: str, schema, inputs: dict, model: str = None):
    last = None
    for method in _METHODS:
        try:
            return _call(_structured_chain(system, human, schema, method, model), inputs)
        except Exception as e:  # noqa: BLE001
            if getattr(e, "status_code", None) in (401, 403, 404, 429):
                raise  # not fixable by switching method
            last = e
            print(f"[LLM] {method} failed: {str(e)[:150]} -> trying next method")
    raise last


# ── Steps 1: summary + claims in ONE call per source ──────────────────────────
def analyze_source(source_name: str, passages: str, max_claims: int):
    return _structured_call(
        "You analyse a source for a system that compares sources. Only use what the text itself asserts.",
        'Source: "{source_name}"\n\nPASSAGES:\n{passages}\n\n'
        "Do two things:\n"
        "1. summary: exactly 3 one-sentence points (what it is about, the main question/problem, the main finding/approach).\n"
        "2. claims: up to {max_claims} important factual claims.\n"
        "Claim rules:\n"
        "- ONE self-contained statement that makes sense without the text "
        "(name the subject; never write 'it', 'this study', 'the authors').\n"
        "- Keep numbers, dates, names and conditions exactly as written.\n"
        "- Skip opinions, background, definitions, references, author names and boilerplate.\n"
        "- chunk = the passage number [n] it came from.\n"
        "- evidence = a SHORT snippet (8-15 words) copied word-for-word from that passage. "
        "Never put double quotes inside any field.",
        SourceAnalysis,
        {"source_name": source_name, "passages": passages, "max_claims": max_claims},
    )


# ── Step 2: ALL pairs judged in ONE call ──────────────────────────────────────
def judge_pairs(pairs, model: str = None):
    """pairs = [(claim_a, claim_b), ...]. Returns {index_in_pairs: PairItem}. `model` lets the verifier and the
    evaluation use a different model than the default."""
    if not pairs:
        return {}
    text = "\n\n".join(
        f'Pair {n}\nA (from "{a["source_name"]}"): {a["text"]}\nB (from "{b["source_name"]}"): {b["text"]}'
        for n, (a, b) in enumerate(pairs, 1)
    )
    out = _structured_call(
        "You are a careful fact-checking judge. Judge ONLY the statements given; "
        "do not use outside knowledge about which one is true.",
        "{pairs}\n\nFor EVERY pair above decide the relationship:\n"
        "- contradiction: both cannot be true at the same time about the same subject "
        "(opposite conclusions, or different values for the same measurement).\n"
        "- agreement: they state the same thing, or one supports the other.\n"
        "- neutral: different topics or different aspects; neither supports nor opposes the other.\n"
        "If unsure choose neutral. Return one verdict per pair with its pair number as id.",
        BatchVerdicts,
        {"pairs": text},
        model,
    )
    return {v.id - 1: v for v in out.verdicts if 1 <= v.id <= len(pairs)} if out else {}


# ── Web verification of ONE claim ──────────────────────────────────────────────
def verify_claim(claim: str, results: list):
    """results = [{title, url, snippet}, ...] from a web search. The model may only use these snippets."""
    text = "\n\n".join(f'[{n}] {r["title"]} ({r["url"]})\n{r["snippet"]}' for n, r in enumerate(results, 1))
    return _structured_call(
        "You are a careful fact-checker. Use ONLY the numbered search results given. "
        "Never rely on your own memory of the facts.",
        "CLAIM: {claim}\n\nSEARCH RESULTS:\n{results}\n\n"
        "Decide: supported (results clearly back the claim), contradicted (results clearly say otherwise), "
        "unverified (results are missing, off-topic or unclear). If unsure choose unverified. "
        "List the numbers of the results you relied on in source_numbers.",
        WebVerdict,
        {"claim": claim, "results": text},
    )


# ── /compare: question answering with citations ───────────────────────────────
def answer_query(query: str, context: str) -> str:
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a research analyst. Answer ONLY from the numbered context passages. "
                   "If the passages do not contain the answer, say so."),
        ("human", "QUESTION: {query}\n\nCONTEXT:\n{context}\n\n"
                  "Answer in 2-3 sentences, then 'Key Points:' with 2-3 short bullets. "
                  "After every statement add the passage number it came from, like [1] or [2]. "
                  "Plain English, be brief."),
    ])
    chain = prompt | get_llm() | StrOutputParser()
    return _call(chain, {"query": query, "context": context}).strip()
