"""runtime/address_rule_guard.py — Card 0020 · D-4 outbound Ruling G guard.

WO-CANON-I landed the ADDRESS RULE into `living_presence_spec.txt` and
`_PERSONA` (persona side, canonical). Ruling G codifies it: when eLo is
speaking TO David, eLo must not refer to David in the third person. The
2026-08-19 live test shows the rule not holding in generation —

    "I remember when David first started explaining…" — said to David.

The persona says so; the model still slipped. This module is the guardrail
that catches those slips on the outbound path. Every substitution is logged
at WARNING so we can see where the persona is being displaced.

B3-2026-10-11 defect: the catch-all `\\bDavid\\b` was rewriting DIRECT ADDRESS
("I'm here, David." → "I'm here, you.") which is semantically wrong.
Fix: mask direct-address spans before substitution, restore after.
"""
from __future__ import annotations

import logging
import re

_log = logging.getLogger(__name__)
_log.addHandler(logging.NullHandler())

# Direct-address patterns — these spans must NOT be rewritten.
# Match the whole span so we can mask it temporarily.
_DIRECT_ADDRESS_RES = [
    # ", David" / ", David." / ", David!" — end-of-clause vocative
    re.compile(r",\s+David\s*[.!?]?", re.IGNORECASE),
    # "David," — start-of-clause vocative
    re.compile(r"\bDavid\s*,", re.IGNORECASE),
    # Greeting word + David: "Hello David" / "Hey David" / "Hi David" etc.
    re.compile(
        r"\b(?:hello|hi|hey|morning|evening|night|wagwan|yo|alright|right)\s+(?:there\s+)?David\b",
        re.IGNORECASE,
    ),
    # "David!" or "David?" alone (direct call)
    re.compile(r"\bDavid\s*[!?]", re.IGNORECASE),
]

_MASK = "\x00DAVID\x00"  # unlikely to appear in real text; stripped before return

# Ordered substitutions: longer, more-specific forms first so that
# "David's" is caught before the bare-name pass. Each entry is
# (compiled_regex, replacement).
_SUBS = [
    (re.compile(r"\bDavid's been\b"),            "you've been"),
    (re.compile(r"\bDavid's\b"),                 "your"),
    (re.compile(r"\bDavid has\b"),               "you have"),
    (re.compile(r"\bDavid have\b"),              "you have"),
    (re.compile(r"\bDavid had\b"),               "you had"),
    (re.compile(r"\bDavid is\b"),                "you are"),
    (re.compile(r"\bDavid was\b"),               "you were"),
    (re.compile(r"\bDavid wants\b"),             "you want"),
    (re.compile(r"\bDavid wanted\b"),            "you wanted"),
    (re.compile(r"\bDavid said\b"),              "you said"),
    (re.compile(r"\bDavid says\b"),              "you say"),
    (re.compile(r"\bDavid told\b"),              "you told"),
    (re.compile(r"\bDavid mentioned\b"),         "you mentioned"),
    (re.compile(r"\bDavid explained\b"),         "you explained"),
    (re.compile(r"\bDavid shared\b"),            "you shared"),
    (re.compile(r"\bDavid described\b"),         "you described"),
    (re.compile(r"\bDavid asked\b"),             "you asked"),
    (re.compile(r"\bDavid decided\b"),           "you decided"),
    (re.compile(r"\bDavid built\b"),             "you built"),
    (re.compile(r"\bDavid made\b"),              "you made"),
    (re.compile(r"\bDavid did\b"),               "you did"),
    (re.compile(r"\bDavid'll\b"),                "you'll"),
    (re.compile(r"\bDavid'd\b"),                 "you'd"),
    # Third-person pronouns following a David swap — leave them; sentences
    # already-converted may still contain "he" mid-clause. We do not try to
    # rewrite pronouns wholesale (too fragile). Rule 1 alarm below tells us
    # when the guard fires so any remaining slippage is visible.
    # Negative lookahead: do NOT convert bare "David" when immediately followed by " Charles"
    # (name-predicate context — "you're David Charles" must not become "you're you Charles").
    (re.compile(r"\bDavid\b(?! Charles)"),        "you"),
]


def _mask_direct_address(text: str) -> tuple[str, list[str]]:
    """Replace direct-address spans with _MASK. Return (masked_text, originals)."""
    originals: list[str] = []
    for pattern in _DIRECT_ADDRESS_RES:
        def _replacer(m: re.Match, _orig: list = originals) -> str:
            _orig.append(m.group(0))
            return _MASK
        text = pattern.sub(_replacer, text)
    return text, originals


def _restore_direct_address(text: str, originals: list[str]) -> str:
    """Re-insert the original direct-address spans in order."""
    for original in originals:
        text = text.replace(_MASK, original, 1)
    return text


def enforce_second_person_to_david(response: str) -> str:
    """Rewrite third-person 'David' references into second-person address.

    Only applied to eLo's OUTBOUND text when the addressee is David (which is
    the whole system in this build — Volume I §Personal_Scope). Every rewrite
    is logged.

    Direct-address uses ("I'm here, David." / "Hello David") are protected
    from substitution — B3 defect filed 2026-10-10.
    """
    if not has_third_person_david(response):
        return response

    # Step 1: protect direct-address spans
    masked, protected = _mask_direct_address(response)

    # Step 2: only proceed if there are still third-person David references after masking
    if not has_third_person_david(masked):
        return response  # only direct-address Davids — nothing to rewrite

    original = response
    hits = 0
    for rx, repl in _SUBS:
        masked, n = rx.subn(repl, masked)
        hits += n

    # Step 3: restore protected spans
    result = _restore_direct_address(masked, protected)

    if hits:
        _log.warning(
            "address_rule_guard: rewrote %d third-person references to David (D-4). "
            "before=%r after=%r",
            hits, original[:120], result[:120],
        )
    return result


def has_third_person_david(response: str) -> bool:
    return bool(response) and bool(re.search(r"\bDavid\b", response))
