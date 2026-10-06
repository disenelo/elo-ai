"""
faculties/metacognition/correction_capture.py — a correction has to leave a
mark.

Builder 2 brief, three NO verdicts sharing one cause:

    capable of changing future behaviour after correction?   NO
        "No mechanism writes a correction back to vault or WKG.
         'Got it' with no action demonstrates this."
    capable of learning from self-correction?                NO
        "Nothing is stored from a self-correction event."
    capable of learning from feedback?                       NO
        "Feedback not captured as typed events."

MEASURED 2026-10-06. self/corrections_ledger.jsonl holds 47,009 rows, so
corrections ARE recorded — the brief is wrong that nothing stores them. What
is missing is that none of it is a MEMORY. The ledger is an append-only log
nothing retrieves from; the vault is what eLo recalls. A correction that never
reaches the vault cannot change a later turn, which is exactly what "Got it"
with no action looks like from the outside.

WHAT IS WORTH KEEPING, and it is not all of it. Of those 47,009:

    45,934  scrub: raw generation differed from final output     97.7%
       774  identity drift: core value '<trait>' absent
       157  character identity clarification
       137  arithmetic

A scrub is the verify layer catching a slip before it shipped — the guard
WORKING. Writing 45,934 of those into the vault would bury everything eLo
actually knows under its own telemetry, and he would "learn" that he
frequently rephrases. memory/spg_failure.py already draws this line and
scores it; this reuses that rather than inventing a second judgement.

TYPED, so it is answerable. Each record carries source_type="CORRECTION" and
the failure kind, so "what have I been corrected on" is a query rather than a
grep.

Deliberately not writing WKG. A correction is an event eLo experienced, not a
claim about the world, and record_claim's epistemic classes do not have an
honest slot for "I was wrong about this once".
"""
from __future__ import annotations

import json
import logging
import os
import tempfile
import time
from typing import Any, Mapping

_log = logging.getLogger("elo.correction_capture")

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))

# Below this, a correction is noise and stays in the ledger. The scrub band
# sits at 0.05 and everything that matters sits at 0.55 or above, so this
# separates them with room on both sides.
KEEP_THRESHOLD: float = 0.40

# [BUILDER CHOICE] Vault weight by how much the correction should bend later
# behaviour. Identity drift is the one David cares about most and the one eLo
# repeats most — 774 of 1,072 real corrections.
_WEIGHT: dict[str, int] = {
    "arithmetic": 8,
    "identity_drift": 8,
    "character_clarification": 6,
    "other": 5,
    "scrub": 1,
}


def should_keep(row: Mapping[str, Any]) -> bool:
    """Is this correction worth remembering, or is it the guard working?"""
    if not isinstance(row, Mapping):
        return False

    # A correction with no stated reason is not learnable, and without this
    # it slipped through: an empty row classifies as "other", which scores
    # exactly 0.40 and cleared a 0.40 threshold. Caught by its own test, not
    # in production.
    if not str(row.get("why", "") or "").strip():
        return False
    if not str(row.get("corrected_response", "") or "").strip():
        return False

    try:
        from memory.spg_failure import score_correction
        return score_correction(row) >= KEEP_THRESHOLD
    except Exception:
        return False


def _summary(kind: str, row: Mapping[str, Any]) -> str:
    what = str(row.get("why", "") or "").strip() or kind
    return f"Corrected — {what}"[:220]


def capture(row: Mapping[str, Any], *, apply: bool = True) -> dict | None:
    """
    Write one correction to the vault as a typed memory.

    Returns the record written, or None when the correction is noise, the
    write fails, or apply is False. Never raises: failing to remember a
    correction must not also break the turn it happened in.
    """
    if not isinstance(row, Mapping):
        return None
    if not should_keep(row):
        return None

    try:
        from memory.spg_failure import classify, signature
        kind = classify(row.get("why", ""))
        sig = signature(row.get("why", ""))
    except Exception:
        kind, sig = "other", "other"

    # The metacognitive half: a correction IS eLo finding out a response of
    # his was poor. Carried on the record so "was that response poor, and
    # why" is answerable from the memory rather than re-derived from the
    # reason string every time something wants to know.
    try:
        from faculties.metacognition.response_assessment import assess_correction
        verdict = assess_correction(row)
    except Exception:
        verdict = {}

    record = {
        "kind": kind,
        "signature": sig,
        "verdict": verdict.get("verdict", ""),
        "cause": verdict.get("cause", ""),
        "severity": verdict.get("severity", 0.0),
        "summary": _summary(kind, row),
        "weight": _WEIGHT.get(kind, 5),
        "input": str(row.get("input", "") or "")[:600],
        "corrected": str(row.get("corrected_response", "") or "")[:600],
        "why": str(row.get("why", "") or "")[:300],
    }

    if not apply:
        return record

    try:
        from memory.vault_layer import write_memory
        spot = write_memory(
            project="elo-os",
            memory_type="fix",
            summary=record["summary"],
            deep_text=(
                f"What was said: {record['input']}\n\n"
                f"What it became: {record['corrected']}\n\n"
                f"Why: {record['why']}"
            ),
            weight=record["weight"],
            tags=["correction", kind, sig,
                  f"cause:{record['cause']}"] if record.get("cause")
                 else ["correction", kind, sig],
            # INFERRED, not VERIFIED: that a correction happened is certain,
            # that eLo was wrong in the way the reason says is a judgement the
            # verify layer made.
            epistemic_class="inferred",
            source_ref=str(row.get("id", "") or ""),
            source_type="CORRECTION",
            content_type="correction",
        )
        record["spot"] = spot
        _log.info("correction kept (%s): %s", sig, record["summary"][:70])
    except Exception as e:
        _log.warning("correction not written to vault (non-fatal): %s", e)
        return None

    return record


# Where the ledger has been read up to. Without it, every tick would rewrite
# the same corrections into the vault forever — 1,262 keepable rows becoming
# millions of duplicate memories, which is a worse failure than not keeping
# them at all.
_CURSOR_PATH = os.path.join(_ROOT, "self", "state", "correction_cursor.json")

# A ceiling per pass. The first run has 47,238 rows behind it and writing all
# of them in one ambient tick would stall the loop and flood the vault in a
# single second.
MAX_PER_PASS: int = 25


def _read_cursor() -> int:
    try:
        with open(_CURSOR_PATH, encoding="utf-8") as f:
            return int((json.load(f) or {}).get("rows_read", 0))
    except Exception:
        return 0


def _write_cursor(n: int) -> None:
    try:
        os.makedirs(os.path.dirname(_CURSOR_PATH), exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(_CURSOR_PATH))
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump({"rows_read": int(n), "_ts": time.time()}, f)
        os.replace(tmp, _CURSOR_PATH)
    except Exception as e:
        _log.debug("correction cursor not written (non-fatal): %s", e)


def capture_new(*, apply: bool = True, max_rows: int | None = None) -> dict:
    """
    Keep the corrections that have appeared since the last pass.

    Returns counts, so a caller sees the ratio rather than assuming it.
    """
    try:
        from memory.spg_failure import load_corrections
        rows = load_corrections()
    except Exception as e:
        _log.debug("correction ledger unreadable (non-fatal): %s", e)
        return {"seen": 0, "kept": 0, "skipped": 0, "rows_read": 0}

    start = _read_cursor()
    if start > len(rows):
        # The ledger was rotated or truncated under us. Starting again from
        # the end rather than the beginning: re-reading 47,000 rows would
        # duplicate everything already kept.
        _log.info("correction ledger shrank (%d -> %d) — resuming from the end",
                  start, len(rows))
        start = len(rows)

    cap = MAX_PER_PASS if max_rows is None else int(max_rows)
    batch = rows[start:start + cap]

    kept = 0
    for row in batch:
        if capture(row, apply=apply):
            kept += 1

    end = start + len(batch)
    if apply and end > start:
        _write_cursor(end)

    return {"seen": len(batch), "kept": kept,
            "skipped": len(batch) - kept, "rows_read": end}


def capture_recent(limit: int = 50, *, apply: bool = True) -> dict:
    """The tail of the ledger, ignoring the cursor. For inspection."""
    try:
        from memory.spg_failure import load_corrections
        rows = load_corrections()[-max(1, int(limit)):]
    except Exception as e:
        _log.debug("correction ledger unreadable (non-fatal): %s", e)
        return {"seen": 0, "kept": 0, "skipped": 0}

    kept = 0
    for row in rows:
        if capture(row, apply=apply):
            kept += 1
    return {"seen": len(rows), "kept": kept, "skipped": len(rows) - kept}
