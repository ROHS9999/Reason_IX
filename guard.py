"""Hallucination guard: an LLM can invent a 'fact' that is not in the document. If that invented claim is then compared
with another source, we would report a contradiction that does not exist. So every claim is checked against the text
it supposedly came from, with a small NLI model (no LLM, runs locally):

    premise    = the 1-2 sentences of the source chunk that best overlap with the claim
    hypothesis = the claim

    grounded  =  NLI says 'entailment' >= 0.5
              OR the quoted evidence really appears word-for-word in the chunk AND NLI does not say 'contradiction'

Ungrounded claims are dropped before comparison (GUARD_MODE=filter) and counted, so the UI can show how many were removed."""
import re

import config
import utils

_WORD = re.compile(r"\w+")


def best_sentences(chunk_text: str, claim: str, k: int = 2) -> str:
    """The k sentences of the chunk sharing the most (longer) words with the claim, in their original order."""
    claim_words = {w for w in _WORD.findall(claim.lower()) if len(w) > 3}
    sents = utils.split_sentences(chunk_text)
    if not sents:
        return chunk_text[:500]
    scored = sorted(range(len(sents)),
                    key=lambda i: -len(claim_words & {w for w in _WORD.findall(sents[i].lower()) if len(w) > 3}))
    return " ".join(sents[i] for i in sorted(scored[:k]))


def check_claims(store, claims) -> None:
    """Sets claim['support'] (entailment probability or None), claim['source_contradiction'], claim['grounded']."""
    if not claims:
        return
    if config.GUARD_MODE == "off":
        for c in claims:
            c["support"], c["grounded"] = None, True
        return
    chunk_text = {ch["id"]: ch["text"] for ch in store.chunks}
    pairs = [(best_sentences(chunk_text[c["chunk_id"]], c["text"]), c["text"]) for c in claims]
    try:
        probs = utils.nli_probs(pairs)
    except Exception as e:  # noqa: BLE001 - if the NLI model cannot load, do not block the whole analysis
        print(f"[GUARD] NLI unavailable ({e}); falling back to the verbatim-quote check only")
        probs = [None] * len(claims)
    for c, p in zip(claims, probs):
        if p is None:
            c["support"], c["grounded"] = None, bool(c["evidence_verified"])
            continue
        c["support"] = round(p["entailment"], 3)
        c["source_contradiction"] = round(p["contradiction"], 3)
        c["grounded"] = (p["entailment"] >= config.GUARD_ENTAIL
                         or (bool(c["evidence_verified"]) and p["contradiction"] < config.GUARD_CONTRADICT))
