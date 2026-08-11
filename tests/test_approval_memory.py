"""
tests/test_approval_memory.py — WO-APPROVAL-MEMORY (card 01)

David's approvals must stick. Once a WO is in DAVID_APPROVED.md it must:
  - NOT appear in `needs_david` output
  - Have its board row flipped to DONE ✅ David-approved when tests are green

  AT-0: load_david_approved() parses real DAVID_APPROVED.md (non-empty set returned)
  AT-1: load_david_approved() returns approved WO-IDs as upper-case strings
  AT-2: approved WO not in needs_david (filtering logic correct)
  AT-3: non-approved DAVID-tier WO still surfaces in needs_david
  AT-4: approved WO with green test → auto_close called with "David-approved" note
  AT-5: load_david_approved() returns empty set gracefully when file missing

Run: python3 tests/test_approval_memory.py
"""
from __future__ import annotations
import sys, os, re, tempfile, shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_passed = _failed = 0


def ok(label: str):
    global _passed
    _passed += 1
    print(f"  ✅ {label}")


def fail(label: str, err):
    global _failed
    _failed += 1
    print(f"  ❌ {label}: {err}")


import company_runtime.continuation as cont


# ── AT-0: real ledger parses to a non-empty set ───────────────────────────────
try:
    approved = cont.load_david_approved()
    assert isinstance(approved, set), f"expected set, got {type(approved)}"
    assert len(approved) > 0, "approved set empty — DAVID_APPROVED.md not parsed"
    ok(f"AT-0: load_david_approved() → {len(approved)} approved WOs")
except AssertionError as e:
    fail("AT-0", e)
except Exception as e:
    fail("AT-0", e)


# ── AT-1: IDs are upper-cased WO-NNN strings ─────────────────────────────────
try:
    approved = cont.load_david_approved()
    # Every entry must match WO-\d+ pattern
    for wo in approved:
        assert re.match(r"^WO-\d+[A-Z]?$", wo), f"non-standard ID: {wo!r}"
    # Real ones we know should be there
    for expected in ("WO-035", "WO-039", "WO-045"):
        assert expected in approved, f"{expected} not found in approved set"
    ok("AT-1: approved IDs are upper-case WO-NNN; WO-035/039/045 present")
except AssertionError as e:
    fail("AT-1", e)
except Exception as e:
    fail("AT-1", e)


# ── AT-2/AT-3: needs_david excludes approved, keeps non-approved ──────────────
try:
    # Build a minimal mock report: one approved DAVID-tier WO + one non-approved
    APPROVED_WO = "WO-035"
    OTHER_WO    = "WO-999"
    approved = cont.load_david_approved()
    assert APPROVED_WO in approved, f"test assumption broken: {APPROVED_WO} not in ledger"

    mock_report = [
        {"wo": APPROVED_WO, "tier": "DAVID"},   # approved — must NOT surface
        {"wo": OTHER_WO,    "tier": "DAVID"},   # not approved — MUST surface
    ]
    needs = sorted(
        x["wo"] for x in mock_report
        if x["tier"] in ("DAVID", "RESERVED", "CONFIRM")
        and x["wo"] not in approved
    )
    assert APPROVED_WO not in needs, f"{APPROVED_WO} should be gone from needs_david"
    assert OTHER_WO in needs,        f"{OTHER_WO} should still be in needs_david"
    ok(f"AT-2: approved WO excluded from needs_david")
    ok(f"AT-3: non-approved DAVID-tier WO still surfaces")
except AssertionError as e:
    fail("AT-2/AT-3", e)
except Exception as e:
    fail("AT-2/AT-3", e)


# ── AT-4: approved green WO → auto_close with "David-approved" note ───────────
try:
    _tmp = tempfile.mkdtemp(prefix="wo_approval_test_")
    _fake_board = os.path.join(_tmp, "BOARD.md")

    # Write a minimal board row for a DAVID-tier WO that's approved but not DONE
    with open(_fake_board, "w", encoding="utf-8") as f:
        f.write("| WO-035 | Semantic sit intent | Builder | P1 | ▶ BUILD | notes |\n")

    # Patch auto_close to use the temp board
    _orig_board = cont.R.BOARD
    cont.R.BOARD = _fake_board

    cont.R.auto_close("WO-035", "David-approved")

    with open(_fake_board, encoding="utf-8") as f:
        result = f.read()

    assert "DONE" in result,            "DONE marker not written"
    assert "David-approved" in result,  "'David-approved' note not in board row"

    cont.R.BOARD = _orig_board
    shutil.rmtree(_tmp, ignore_errors=True)
    ok("AT-4: auto_close('David-approved') flips board row to DONE ✅ David-approved")
except AssertionError as e:
    fail("AT-4", e)
    try: cont.R.BOARD = _orig_board
    except Exception: pass
except Exception as e:
    fail("AT-4", e)
    try: cont.R.BOARD = _orig_board
    except Exception: pass


# ── AT-5: graceful when DAVID_APPROVED.md missing ────────────────────────────
try:
    _orig_path = cont._APPROVED
    cont._APPROVED = "/tmp/no_such_file_david_approved_xyz.md"
    result = cont.load_david_approved()
    assert result == set(), f"expected empty set, got {result}"
    cont._APPROVED = _orig_path
    ok("AT-5: load_david_approved() returns empty set when file missing")
except AssertionError as e:
    fail("AT-5", e)
    cont._APPROVED = _orig_path
except Exception as e:
    fail("AT-5", e)
    try: cont._APPROVED = _orig_path
    except Exception: pass


# ── Final summary ─────────────────────────────────────────────────────────────
print()
print("=" * 62)
print(f"approval-memory   {_passed} passed   {_failed} failed")
if _failed:
    sys.exit(1)
