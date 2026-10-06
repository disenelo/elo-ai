"""
memory/spg_failure.py — ROOT-4, item 6: failures must score, or nothing
changes after them.

Builder 2 brief, 2026-10-06:

    a system capable of changing strategy after repeated failure? NO
    Failures not stored. SPG not scoring.
    -> SPG must score failure events — define FAILURE significance weight

Half of that diagnosis is wrong and the correction matters. Failures ARE
stored: self/corrections_ledger.jsonl holds 47,006 rows. They have never been
scored into SPG, which is the actual gap.

MEASURED 2026-10-06, and this is why a flat weight would be useless:

    45,934  scrub: raw generation differed from final output      97.7%
       774  identity drift: core value '<trait>' absent
       157  character identity clarification
       137  arithmetic
         4  (other)

97.7% of the ledger is the verify layer doing its job — a scrub is evidence
the guard WORKED, not evidence eLo failed. Scoring those as failures would
bury the thousand that matter under forty-six thousand that do not, and the
"repeated failure" signal would just be "eLo generated text again".

So the weight is a taxonomy, not a number:

    arithmetic        — objectively wrong. Checkable, so inexcusable.
    identity drift    — eLo stopped sounding like eLo. The failure David
                        actually cares about.
    character clarif. — had to explain himself. Milder; sometimes the question
                        was ambiguous.
    scrub             — the guard caught a slip before it shipped. Working as
                        designed, near zero.

All weights are [BUILDER CHOICE], same standing as
significance_faculty._WEIGHTS and spg_backfill's.
"""
from __future__ import annotations

import json
import logging
import math
import re
from collections import Counter
from pathlib import Path

_log = logging.getLogger("elo.spg_failure")

_ROOT = Path(__file__).parent.parent
CORRECTIONS = _ROOT / "self" / "corrections_ledger.jsonl"

KIND_SCRUB = "scrub"
KIND_IDENTITY_DRIFT = "identity_drift"
KIND_CHARACTER = "character_clarification"
KIND_ARITHMETIC = "arithmetic"
KIND_OTHER = "other"

# [BUILDER CHOICE] A correction's significance BEFORE recurrence is applied.
FAILURE_WEIGHT: dict[str, float] = {
    KIND_ARITHMETIC:     0.90,   # objectively wrong, and checkable
    KIND_IDENTITY_DRIFT: 0.85,   # stopped sounding like himself
    KIND_CHARACTER:      0.55,   # had to explain himself
    KIND_OTHER:          0.40,
    KIND_SCRUB:          0.05,   # the guard worked; not a failure
}

# How much a failure's repetition raises it. Repetition is the whole point —
# "changing strategy after REPEATED failure" — so it can nearly double a
# score, log-scaled like every other recurrence term in SPG.
W_RECURRENCE: float = 0.45

_PATTERNS: tuple[tuple[re.Pattern, str], ...] = (
    (re.compile(r"\bscrub\b|raw generation differed", re.I), KIND_SCRUB),
    (re.compile(r"identity drift", re.I), KIND_IDENTITY_DRIFT),
    (re.compile(r"character identity|identity clarification", re.I), KIND_CHARACTER),
    (re.compile(r"\barithmetic\b|\bmaths?\b|miscalcul", re.I), KIND_ARITHMETIC),
)

# "identity drift: core value 'playful' absent from response" — the trait is
# what recurs, not the sentence.
_TRAIT_RE = re.compile(r"core value '([^']+)'", re.I)


def classify(why: str) -> str:
    """What kind of failure this was."""
    w = str(why or "")
    for rx, kind in _PATTERNS:
        if rx.search(w):
            return kind
    return KIND_OTHER if w.strip() else KIND_OTHER


def signature(why: str) -> str:
    """
    What would have to repeat for this to be the SAME failure twice.

    A drift on 'playful' and a drift on 'calm' are different failures with the
    same sentence, so the trait is carried into the signature. Without this,
    774 drift rows read as one failure repeated 774 times.
    """
    kind = classify(why)
    m = _TRAIT_RE.search(str(why or ""))
    return f"{kind}:{m.group(1).lower()}" if m else kind


def load_corrections(path: Path = CORRECTIONS, *, limit: int | None = None
                     ) -> list[dict]:
    rows: list[dict] = []
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except Exception:
                    continue
                if limit and len(rows) >= limit:
                    break
    except Exception as e:
        _log.warning("spg_failure: cannot read %s — %s", path, e)
    return rows


def failure_counts(rows: list[dict]) -> Counter:
    """How often each distinct failure has happened."""
    return Counter(signature(r.get("why", "")) for r in rows)


def score_correction(row: dict, counts: Counter | None = None) -> float:
    """
    Significance of one correction.

    Base weight by kind, raised by how often this exact failure has recurred.
    A scrub stays near zero however often it happens, because frequency does
    not make a working guard into a failure.
    """
    why = row.get("why", "")
    kind = classify(why)
    base = FAILURE_WEIGHT.get(kind, FAILURE_WEIGHT[KIND_OTHER])

    if kind == KIND_SCRUB or not counts:
        return round(base, 4)

    n = counts.get(signature(why), 1)
    ceiling = max((v for k, v in counts.items()
                   if not k.startswith(KIND_SCRUB)), default=1)
    if ceiling <= 1:
        return round(base, 4)

    rec = min(1.0, math.log1p(n) / math.log1p(ceiling))
    return round(min(1.0, base + W_RECURRENCE * rec * (1.0 - base)), 4)


def recurring_failures(rows: list[dict] | None = None, top: int = 12
                       ) -> list[tuple[str, int]]:
    """
    The failures eLo actually repeats, scrubs excluded.

    This is the list that "changing strategy after repeated failure" has to be
    answerable from.
    """
    rows = load_corrections() if rows is None else rows
    counts = failure_counts(rows)
    real = {k: v for k, v in counts.items() if not k.startswith(KIND_SCRUB)}
    return Counter(real).most_common(top)
