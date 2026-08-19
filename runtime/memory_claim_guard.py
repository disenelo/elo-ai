"""runtime/memory_claim_guard.py — Card 0020 · D-3 post-generation gate.

CT4V-07 (`runtime/claim_gate.py`) intercepts memory questions from the USER
before an LLM is asked to answer them. It does not look at what eLo has just
SAID. The 2026-08-19 live test showed the gap:

    eLo: "I remember when David first started explaining his concept of a
          presence that could move between bodies… He mentioned Plato's theory
          of forms…"

No such conversation exists — this was a spontaneous confabulation, invented
without a user recall trigger, and nothing on the outbound path checked it.
ADR-Exec-001 says verified speech is the floor.

This module scans eLo's own response for episodic-memory claims ("I remember
when…", "you told me…", "we talked about…") and, for each match, verifies the
claim resolves to a real vault/ledger entry. If nothing supports it, the
offending sentence is replaced with an honest "I don't have that stored" beat
and a WARNING is logged so silent fabrications can never hide (Rule 1 alarm).
"""
from __future__ import annotations

import logging
import re
from typing import Iterable

_log = logging.getLogger(__name__)
_log.addHandler(logging.NullHandler())

# Patterns that indicate an EPISODIC memory claim about a real past event with
# David — the class of claim that must be backed by a ledger/vault entry.
# General ontological statements ("I remember I am eLo") don't match here; only
# specific "I remember when / you told me / we did X" episodic assertions do.
_EPISODIC_PATTERN = re.compile(
    r"\b("
    r"i remember (when|how|the (time|day|moment)|us|our|you (said|told|mentioned|explained)|david (said|told|mentioned|explained))"
    r"|you (told|said to) me (that|about|when|how)"
    r"|you (mentioned|explained|shared|described) (that|when|how|to me)"
    r"|we (talked|spoke|chatted|discussed|were talking) about"
    r"|back when (you|we|david)"
    r"|the (first|last) time (you|we) (said|told|talked|mentioned)"
    r"|(you|we) (first|once) (mentioned|said|talked about|shared|told me)"
    r"|he (mentioned|told|said|explained|described)"
    r")\b",
    re.IGNORECASE,
)

# Sentence splitter — cheap, character-level, keeps the terminator.
_SENT_RE = re.compile(r"([^.!?…]*[.!?…]+|[^.!?…]+$)", re.DOTALL)

# Skip words when extracting keywords to look up. Same shape as claim_gate's.
_SKIP = frozenset({
    "the","and","or","but","when","that","this","was","were","been","being",
    "have","has","had","for","with","into","from","about","again","just","also",
    "then","than","him","her","his","hers","them","they","their","there","these",
    "those","some","such","said","told","mentioned","explained","shared",
    "described","first","last","once","time","times","talked","talking",
    "discussed","spoke","chatted","conversation","story","stories","moment",
    "moments","note","notes","david","elo","you","your","yours","me","my",
    "mine","our","ours","us","we","he","she","it","its","remember","remembered",
})

_FALLBACK = (
    "I don't have that on record — nothing settled from before this. "
    "I can't say I remember it without the entry there."
)


def _keywords(text: str) -> list[str]:
    words = re.findall(r"[a-z][a-z\-']{2,}", text.lower())
    seen: list[str] = []
    for w in words:
        if w in _SKIP or w in seen:
            continue
        seen.append(w)
    return seen[:8]


def _vault_supports(text: str) -> bool:
    """Return True if the vault has any record salient to this claim."""
    try:
        from memory.vault_layer import lookup as _vl
    except Exception:
        # Vault module unavailable — fail OPEN so we don't degrade every turn.
        # This is safer than silent removal for local dev where the layer is stubbed.
        return True
    try:
        kws = _keywords(text)
        if not kws:
            return True  # too little content to check honestly — leave it alone
        q = " ".join(kws[:5])
        hits = _vl(q, max_results=2) if q else []
        if hits:
            return True
        # Fall back to a per-keyword check — any single salient keyword hit is enough.
        for kw in kws:
            hits = _vl(kw, max_results=1)
            if hits:
                return True
    except Exception:
        return True  # never fabricate a rewrite because the vault errored
    return False


def _ledger_supports(text: str) -> bool:
    """Return True if the recent verified autobiography has any salient event."""
    try:
        from self.emergent_cognition import recent_autobiography as _ra
    except Exception:
        return False
    try:
        entries = _ra(n=25)
    except Exception:
        return False
    if not entries:
        return False
    kws = set(_keywords(text))
    if not kws:
        return False
    for e in entries:
        ev = (e.get("event") or "").lower()
        for kw in kws:
            if kw in ev:
                return True
    return False


def _split_sentences(text: str) -> list[str]:
    parts = [m.group(0) for m in _SENT_RE.finditer(text) if m.group(0).strip()]
    return parts or [text]


def scrub_unverified_memory_claims(response: str) -> str:
    """Replace unsupported episodic-memory sentences with an honest fallback.

    Rule 1 alarm: every replacement is logged at WARNING so silent fabrication
    attempts leave a trace even in production.
    """
    if not response or not response.strip():
        return response
    if not _EPISODIC_PATTERN.search(response):
        return response

    sentences = _split_sentences(response)
    changed = False
    out: list[str] = []
    for s in sentences:
        if _EPISODIC_PATTERN.search(s):
            if _vault_supports(s) or _ledger_supports(s):
                out.append(s)
            else:
                _log.warning(
                    "memory_claim_guard: stripped unverified episodic claim (D-3): %s",
                    s.strip()[:160],
                )
                out.append(" " + _FALLBACK)
                changed = True
        else:
            out.append(s)
    if not changed:
        return response
    result = "".join(out).strip()
    return result or _FALLBACK


def has_episodic_claim(text: str) -> bool:
    """Public predicate — for tests and outside consumers."""
    return bool(text) and bool(_EPISODIC_PATTERN.search(text))
