"""runtime/address_rule_guard.py — Card 0020 · D-4 outbound Ruling G guard.

WO-CANON-I landed the ADDRESS RULE into `living_presence_spec.txt` and
`_PERSONA` (persona side, canonical). Ruling G codifies it: when eLo is
speaking TO David, eLo must not refer to David in the third person. The
2026-08-19 live test shows the rule not holding in generation —

    "I remember when David first started explaining…" — said to David.

The persona says so; the model still slipped. This module is the guardrail
that catches those slips on the outbound path. Every substitution is logged
at WARNING so we can see where the persona is being displaced.
"""
from __future__ import annotations

import logging
import re

_log = logging.getLogger(__name__)
_log.addHandler(logging.NullHandler())

# Ordered substitutions: longer, more-specific forms first so that
# "David's" is caught before the bare-name pass. Each entry is
# (compiled_regex, replacement).
_SUBS = [
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
    (re.compile(r"\bDavid's been\b"),            "you've been"),
    # Third-person pronouns following a David swap — leave them; sentences
    # already-converted may still contain "he" mid-clause. We do not try to
    # rewrite pronouns wholesale (too fragile). Rule 1 alarm below tells us
    # when the guard fires so any remaining slippage is visible.
    # Negative lookahead: do NOT convert bare "David" when immediately followed by " Charles"
    # (name-predicate context — "you're David Charles" must not become "you're you Charles").
    (re.compile(r"\bDavid\b(?! Charles)"),        "you"),
]


def enforce_second_person_to_david(response: str) -> str:
    """Rewrite third-person 'David' references into second-person address.

    Only applied to eLo's OUTBOUND text when the addressee is David (which is
    the whole system in this build — Volume I §Personal_Scope). Every rewrite
    is logged.
    """
    if not has_third_person_david(response):
        return response
    original = response
    hits = 0
    for rx, repl in _SUBS:
        response, n = rx.subn(repl, response)
        hits += n
    if hits:
        _log.warning(
            "address_rule_guard: rewrote %d third-person references to David (D-4). "
            "before=%r after=%r",
            hits, original[:120], response[:120],
        )
    return response


def has_third_person_david(response: str) -> bool:
    return bool(response) and bool(re.search(r"\bDavid\b", response))
