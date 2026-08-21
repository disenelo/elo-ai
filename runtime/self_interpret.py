"""
runtime/self_interpret.py — WO-117 Self-Interpretation (card 0083).

eLo reads his own accumulated record and says something true about himself
that nobody wrote into him. Assembly, not invention.

Rules (card 0083 §2 — read before changing a line):
  - ADR-Exec-005 D1: language alone is never evidence. Every claim must cite
    a count that exists in the store. No rounding up, no "often" without a number.
  - Falsifiable: reflect:105 vs answer:54 → "I reflect about twice as often as
    I answer." NOT "I am a reflective person."
  - CT4V-03 / CA ruling: narrative must never CREATE identity facts. This module
    reads the record. It does NOT write to EloSelfState.
  - David 2026-08-21: "learns and asses not adopts … there is a reason to why."
    Every interpretation carries the numbers it came from. No traceable source =
    a personality trait someone invented.

Output: SelfInterpretation dataclass — or None if the record is empty.
Caller: runtime/spine/spine.py (card 0083 §3).
"""
from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from self.elo_self_model import EloSelfState

_log = logging.getLogger(__name__)

_ROOT         = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_AUTOBIOGRAPHY = os.path.join(_ROOT, "self", "journals", "autobiography.jsonl")

# Minimum count before a count-based claim is made — prevents single-event claims.
_MIN_COUNT = 2


@dataclass
class SelfInterpretation:
    """A falsifiable self-assessment grounded in counted evidence."""
    text:         str        = ""           # the interpretation sentence(s)
    derived_from: list       = field(default_factory=list)  # [{source, key, count}]
    verified_events: int     = 0            # number of ACK'd autobiography entries seen

    def as_dict(self) -> dict:
        return {
            "text":          self.text,
            "derived_from":  list(self.derived_from),
            "verified_events": self.verified_events,
        }

    def is_empty(self) -> bool:
        return not self.text.strip()


def _load_autobiography(path: str = _AUTOBIOGRAPHY) -> list[dict]:
    """Read verified autobiography entries. Non-fatal on missing file."""
    rows: list[dict] = []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    if obj.get("verified"):
                        rows.append(obj)
                except (json.JSONDecodeError, AttributeError):
                    pass
    except FileNotFoundError:
        pass
    return rows


def interpret(state: "EloSelfState",
              autobiography_path: str | None = None) -> SelfInterpretation | None:
    """
    Produce a self-interpretation grounded in the live accumulated record.

    Returns None — not an empty string — when the record is empty so callers
    can skip silently rather than emitting hollow text.

    No writes to state. Reads:
      state.recent_behavior  — verb → count rolling this session
      state.lifetime_threads — [(topic, count), ...]
      state.last_reflection_lesson — lesson text from last reflection cycle
      autobiography.jsonl    — body-ACK'd lived events (verified=True only)
      identity_meaning.derive_tendencies(state) — pattern phrases
    """
    behavior: dict = dict(getattr(state, "recent_behavior", {}) or {})
    threads:  list = list(getattr(state, "lifetime_threads", []) or [])
    lesson:   str  = str(getattr(state, "last_reflection_lesson", "") or "")

    # Nothing in the record yet — silence, not a guess (card test 1)
    if not behavior and not threads and not lesson:
        return None

    path = autobiography_path or _AUTOBIOGRAPHY
    auto_entries = _load_autobiography(path)

    derived_from: list = []
    claims:       list = []

    # ── Behavior counts ─────────────────────────────────────────────────────────
    # Only cite counts that exist and meet the minimum threshold.
    counted = {v: c for v, c in behavior.items() if isinstance(c, (int, float)) and c >= _MIN_COUNT}
    if counted:
        top = sorted(counted.items(), key=lambda kv: kv[1], reverse=True)
        dominant, dom_count = top[0]
        if len(top) >= 2:
            second, sec_count = top[1]
            ratio = dom_count / sec_count if sec_count else 0
            if ratio >= 1.5:
                claims.append(
                    f"I {dominant} about {ratio:.1f}× as often as I {second} "
                    f"({dom_count} vs {sec_count} this session)"
                )
            else:
                claims.append(
                    f"I {dominant} and {second} roughly equally this session "
                    f"({dom_count} vs {sec_count})"
                )
            derived_from.append({"source": "recent_behavior", "key": dominant, "count": dom_count})
            derived_from.append({"source": "recent_behavior", "key": second,   "count": sec_count})
        else:
            claims.append(f"I {dominant} most ({dom_count} times this session)")
            derived_from.append({"source": "recent_behavior", "key": dominant, "count": dom_count})

    # ── Lifetime threads ─────────────────────────────────────────────────────────
    recurring = [
        (t, c) for t, c in threads
        if isinstance(t, str) and isinstance(c, (int, float)) and c >= _MIN_COUNT
    ]
    if recurring:
        top_thread, top_count = max(recurring, key=lambda x: x[1])
        claims.append(f"I keep returning to {top_thread} ({int(top_count)} times across sessions)")
        derived_from.append({"source": "lifetime_threads", "key": top_thread, "count": int(top_count)})

    # ── Last reflection lesson ────────────────────────────────────────────────────
    if lesson:
        claims.append(f"My last reflection: {lesson}")
        derived_from.append({"source": "last_reflection_lesson", "key": lesson, "count": 1})

    # ── Verified autobiography events ────────────────────────────────────────────
    verified_count = len(auto_entries)
    if verified_count:
        derived_from.append({"source": "autobiography", "key": "verified_events",
                             "count": verified_count})

    # Nothing derived — still no claims despite the record (very thin data)
    if not claims:
        return None

    text = " ".join(claims) + "."

    # Sanity: every number in the text must appear in derived_from counts
    # (the test suite verifies this — card test 4)
    all_counts = {str(int(d["count"])) for d in derived_from if isinstance(d.get("count"), (int, float))}
    for tok in text.split():
        tok_stripped = tok.rstrip("×.(),:;")
        if tok_stripped.isdigit() and tok_stripped not in all_counts:
            _log.warning("self_interpret: emitting number %r not in derived_from — suppressed", tok_stripped)
            return None

    return SelfInterpretation(
        text=text,
        derived_from=derived_from,
        verified_events=verified_count,
    )
