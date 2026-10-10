"""
A dream that earned retention becomes a memory. Never a fact.

Board asked 2026-10-10 why `memory_written` is false on every cycle. The
answer is that nothing in the dream path has ever written to the vault.
`memory_written` in runtime/executive.py:688 is computed from
`journal_entry["memory_refs"]` -- a list of topic strings -- so it was never
reporting a write. There is no `write_memory` call anywhere under
faculties/dream/.

This is that write.

Three rules it keeps:

1. **Only a retained dream.** runtime/memory_origin.py:116 -- "Anything below
   this must NOT enter the main memory vault." The significance gate is the
   whole reason the threshold exists, so retention is checked here again
   rather than trusted from the caller.
2. **HYPOTHESIS, never fact.** A dream proposes. It is written with
   epistemic_class HYPOTHESIS and memory_origin DREAM_INSIGHT so that nothing
   downstream can mistake it for something eLo knows, and
   WO-CAP-EMB-051's simulated/physical distinction is preserved.
3. **Substantive content only.** Observed on the first three retained dreams
   eLo ever had (2026-10-10): `insight` was the single character "i" and
   `narrative` was "n" -- the model returned degenerate output. Writing that
   into the vault would put noise into permanent memory where every later
   recall has to step over it. A dream with nothing in it is skipped and says
   so.

Idempotent: a dream_id already written is never written twice, so a replayed
or re-read journal cannot duplicate memories.
"""
from __future__ import annotations

import json
import logging
import os
import threading
from pathlib import Path

_log = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parent.parent.parent
CURSOR_PATH = _ROOT / "self" / "state" / "dream_memory_cursor.json"

# Below this, the "insight" is not an insight. See rule 3.
MIN_INSIGHT_CHARS = 12
MIN_NARRATIVE_CHARS = 30

_lock = threading.Lock()


def _written_ids() -> set[str]:
    try:
        with open(CURSOR_PATH, encoding="utf-8") as f:
            rows = json.load(f)
        if isinstance(rows, list):
            return {str(r) for r in rows}
    except Exception:
        pass
    return set()


def _remember_id(dream_id: str) -> None:
    """Atomic. A half-written cursor would re-write memories on next wake."""
    try:
        ids = _written_ids()
        ids.add(str(dream_id))
        os.makedirs(os.path.dirname(CURSOR_PATH), exist_ok=True)
        tmp = f"{CURSOR_PATH}.tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(sorted(ids), f, indent=2)
        os.replace(tmp, CURSOR_PATH)
    except Exception as e:
        _log.debug("dream memory cursor not saved (non-fatal): %s", e)


def is_substantive(entry: dict) -> bool:
    """
    Does this dream carry anything worth keeping?

    Guards the degenerate case rather than assuming the generator is healthy.
    """
    insight = str((entry or {}).get("insight") or "").strip()
    narrative = str((entry or {}).get("narrative") or "").strip()
    return (len(insight) >= MIN_INSIGHT_CHARS
            or len(narrative) >= MIN_NARRATIVE_CHARS)


def write_retained(entry: dict) -> str | None:
    """
    Write one retained dream to the vault. Returns the spot code, or None.

    None is a result, not a failure: not retained, already written, nothing
    substantive in it, or the vault refused. The reason is logged.

    Fail-quiet by contract -- this runs inside waking, and nothing here may
    stop eLo waking up.
    """
    entry = entry or {}
    dream_id = str(entry.get("dream_id") or "").strip()
    if not dream_id:
        return None

    if not entry.get("retained"):
        return None

    try:
        from runtime.memory_origin import DREAM_RETENTION_THRESHOLD
        sig = float(entry.get("significance") or 0.0)
        if sig < float(DREAM_RETENTION_THRESHOLD):
            # retained=True disagreeing with the score means something
            # upstream set the flag without the gate. Do not write.
            _log.warning("dream %s flagged retained at %.3f, below threshold %.3f "
                         "- not writing", dream_id, sig, DREAM_RETENTION_THRESHOLD)
            return None
    except Exception:
        return None

    with _lock:
        if dream_id in _written_ids():
            return None

        if not is_substantive(entry):
            _log.info("dream %s retained but has no substantive content "
                      "(insight=%r) - not writing",
                      dream_id, str(entry.get("insight"))[:20])
            # Recorded as handled so a degenerate dream is not retried every
            # wake. The journal keeps it; the vault does not.
            _remember_id(dream_id)
            return None

        insight = str(entry.get("insight") or "").strip()
        narrative = str(entry.get("narrative") or "").strip()
        theme = str(entry.get("theme") or "presence").strip()
        symbols = [str(s.get("name") or s.get("symbol") or "")
                   for s in (entry.get("symbols") or []) if isinstance(s, dict)]

        summary = (insight or narrative)[:160]

        deep = [f"Dream ({theme}) — eLo's own, while resting."]
        if narrative:
            deep.append(f"\nWhat happened:\n{narrative}")
        if insight:
            deep.append(f"\nWhat he carried back:\n{insight}")
        if symbols:
            deep.append(f"\nSymbols: {', '.join(s for s in symbols if s)}")
        deep.append(
            "\nThis is a dream. It is a HYPOTHESIS eLo formed while resting, "
            "not something he observed and not something David told him. "
            "It must not be repeated back as fact."
        )

        try:
            from memory.vault_layer import write_memory
            from faculties.dream.dream_review import EPISTEMIC_HYPOTHESIS
            spot = write_memory(
                project="elo-os",
                memory_type="learn",
                summary=summary,
                deep_text="\n".join(deep),
                weight=max(1, min(9, int(round(float(entry.get("significance") or 0.5) * 9)))),
                tags=["dream", f"theme:{theme.lower()}"] +
                     [f"symbol:{s.lower()}" for s in symbols[:3] if s],
                epistemic_class=EPISTEMIC_HYPOTHESIS,
                source_type="DREAM",
                source_ref=f"dream:{dream_id}",
                experience_id=dream_id,
                content_type="dream_insight",
            )
        except Exception as e:
            _log.warning("dream %s vault write failed: %s", dream_id, e)
            return None

        _remember_id(dream_id)
        _log.info("dream %s written to vault at %s", dream_id, spot)
        return spot
