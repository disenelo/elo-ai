"""tests/test_card_0020_d7_company_state_freshness.py — Card 0020 · D-7.

David L3 retired the "Presentable v1" milestone on 2026-08-10. The 2026-08-19
live test still had eLo announcing it as the CURRENT milestone. Two guards in
this test:

  D-7.a — the DISPATCH_BOARD.md COMPANY_FOCUS marker no longer names "Presentable v1"
  D-7.b — even if a stale state file still says "Presentable v1", the reader
           replaces that milestone with an honest post-Presentable label

Run: python3 tests/test_card_0020_d7_company_state_freshness.py
"""
import sys, os
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


BOARD = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "engineering", "work_orders", "DISPATCH_BOARD.md",
)


# D-7.a — the board marker no longer names Presentable v1 as the milestone
try:
    with open(BOARD, encoding="utf-8") as f:
        text = f.read()
    import re
    m = re.search(r"COMPANY_FOCUS:\s*([^|]+)", text)
    assert m, "COMPANY_FOCUS marker missing from board"
    milestone = m.group(1).strip().lower()
    assert "presentable v1" not in milestone, (
        f"marker still names retired milestone: {milestone!r}"
    )
    ok(f"D-7.a: COMPANY_FOCUS marker milestone is now {m.group(1).strip()!r}")
except Exception as e:
    fail("D-7.a", e)


# D-7.b — retirement guard: reader replaces a lingering "Presentable v1" state
try:
    from company_runtime.company_state_writer import (
        _milestone_label,
        _build_briefing,
        _build_board_reply,
    )
    label = _milestone_label({"milestone": "Presentable v1"})
    assert "retired" in label.lower(), \
        f"retirement label missing: {label!r}"
    assert "2026-08-10" in label, \
        f"retirement date missing: {label!r}"

    stale_state = {
        "company_focus": {"milestone": "Presentable v1", "items": []},
        "today_priorities": [],
        "waiting_for_approval": [],
        "board": [],
        "roadmap": [],
        "engineering": {},
    }
    briefing = _build_briefing(stale_state).lower()
    board    = _build_board_reply(stale_state).lower()
    for out, label in [(briefing, "briefing"), (board, "board reply")]:
        assert "retired" in out, f"{label} did not surface the retirement: {out!r}"
        assert "2026-08-10" in out, f"{label} missing retirement date: {out!r}"
    ok("D-7.b: retirement guard converts stale 'Presentable v1' into an honest label")
except Exception as e:
    fail("D-7.b", e)


print()
print("=" * 52)
print(f"Card 0020 · D-7 company-state freshness  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
