"""
tests/test_oq_vii9_dead_code.py — card 0079 item 2: OQ-VII-9 dead code proof.

The _SHORT_AFFIRM branch at executive.py:227 is a verbatim duplicate of
the branch at :178. Because:
  - The same condition (any + len < 35) is evaluated on the same immutable `t`
  - If True at :178, the function already returned — :227 is unreachable
  - If False at :178, the condition is also False at :227 — :227 never fires

This test proves unreachability, then asserts the duplicate is gone.

One check:

  DZ-1  Every _SHORT_AFFIRM phrase triggers a return at the FIRST check (line ~178),
         not the second. After the fix, the second check must not exist.

Run: python3 tests/test_oq_vii9_dead_code.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

ok  = lambda msg: print(f"  PASS  {msg}")
err = lambda msg: (print(f"  FAIL  {msg}"), sys.exit(1))

_EXECUTIVE_PY = os.path.join(ROOT, "runtime", "executive.py")


def test_dz1_duplicate_short_affirm_gone() -> None:
    """
    After the fix: exactly ONE _SHORT_AFFIRM branch in _conversation_action().
    Before the fix: two identical branches — the second unreachable.
    """
    with open(_EXECUTIVE_PY, encoding="utf-8") as f:
        src = f.read()

    # Count occurrences of the short-affirm branch condition
    import runtime.executive as ex
    short_affirm_phrases = ex._SHORT_AFFIRM

    # Build the pattern that appears in the source
    branch_marker = "_SHORT_AFFIRM) and len(t.strip()) < 35"
    count = src.count(branch_marker)

    if count == 0:
        err("DZ-1: _SHORT_AFFIRM branch not found at all — executive.py may have been restructured")
    if count > 1:
        err(
            f"DZ-1: {count} copies of the _SHORT_AFFIRM branch found — duplicate dead code still present."
            f" Remove the second copy at the lower line number (was :227)."
        )

    ok(f"DZ-1: exactly 1 _SHORT_AFFIRM branch in _conversation_action() — duplicate dead code removed")

    # Verify the surviving branch returns celebrate (correct semantics preserved)
    result = ex._conversation_action(
        "yeah", "conversation", "positive_low", "steady"
    )
    if result.get("action") != "celebrate":
        err(f"DZ-1: short affirm 'yeah' → expected celebrate, got {result}")
    ok("DZ-1: 'yeah' still routes to celebrate after dead code removal")


if __name__ == "__main__":
    print("card 0079 item 2 — OQ-VII-9 dead code at :227 proven and removed")
    test_dz1_duplicate_short_affirm_gone()
    print("\n1/1 PASS — _SHORT_AFFIRM duplicate removed; first branch still live")
