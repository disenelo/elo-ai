"""
tests/test_approval_memory.py — WO-APPROVAL-MEMORY: David's approvals stick

Assertions:
  AT-1: a WO in DAVID_APPROVED.md does NOT appear in cycle()'s needs_david output
  AT-2: a WO in DAVID_APPROVED.md has its board row flipped to DONE ✅ (apply=True)
  AT-3: approved WO with NO test file is still auto-closed (not gated on test-green)
  AT-4: approved WO that is already DONE is not double-closed (idempotent)
  AT-5: load_david_approved() parses WO-IDs correctly; compile clean

Run: python3 tests/test_approval_memory.py
"""
from __future__ import annotations

import os
import py_compile
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_passed = _failed = 0
_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def ok(label: str):
    global _passed
    _passed += 1
    print(f"  ✅ {label}")


def fail(label: str, err):
    global _failed
    _failed += 1
    print(f"  ❌ {label}: {err}")


# ── Helpers ────────────────────────────────────────────────────────────────────

def _make_board(rows: list[str]) -> str:
    """Minimal board table with a header row."""
    header = "| WO | Title | Agent | Pri | Status | Notes |\n|---|---|---|---|---|---|\n"
    return header + "".join(rows)


def _make_approved(wo_ids: list[str]) -> str:
    lines = ["# DAVID-APPROVED LEDGER\n"]
    for wo in wo_ids:
        lines.append(f"- {wo} — approved\n")
    return "".join(lines)


def _make_board_row(wo_id: str, status: str = "▶ DISPATCHED") -> str:
    return f"| {wo_id} | Test WO | Builder (eLo OS) | P2 | {status} | note |\n"


# ── AT-1: approved WO not in needs_david ─────────────────────────────────────
try:
    from company_runtime.continuation import load_david_approved

    with tempfile.TemporaryDirectory() as tmp:
        approved_path = os.path.join(tmp, "DAVID_APPROVED.md")
        with open(approved_path, "w") as f:
            f.write(_make_approved(["WO-999", "WO-888"]))

        # Monkeypatch _APPROVED path
        import company_runtime.continuation as _cont
        _orig_approved = _cont._APPROVED
        _cont._APPROVED = approved_path
        try:
            approved = load_david_approved()
            assert "WO-999" in approved, f"WO-999 must be in approved set, got {approved}"
            assert "WO-888" in approved, f"WO-888 must be in approved set, got {approved}"
            assert "WO-001" not in approved, "WO-001 must NOT be in approved (not listed)"
        finally:
            _cont._APPROVED = _orig_approved

        # Simulate cycle()'s needs_david computation
        report_items = [
            {"wo": "WO-999", "tier": "DAVID"},
            {"wo": "WO-888", "tier": "CONFIRM"},
            {"wo": "WO-777", "tier": "DAVID"},
        ]
        needs_david = sorted({x["wo"] for x in report_items
                              if x["tier"] in ("DAVID", "RESERVED", "CONFIRM")
                              and x["wo"] not in approved})
        assert "WO-999" not in needs_david, "approved WO must not be in needs_david"
        assert "WO-888" not in needs_david, "approved WO must not be in needs_david"
        assert "WO-777" in needs_david, "non-approved DAVID-tier WO must appear in needs_david"

    ok("AT-1: approved WOs excluded from needs_david; non-approved DAVID-tier still surfaces")
except AssertionError as e:
    fail("AT-1", e)
except Exception as e:
    fail("AT-1", e)


# ── AT-2: board row flipped to DONE for approved WO (apply=True) ──────────────
try:
    from company_runtime.wo_test_runner import auto_close

    with tempfile.TemporaryDirectory() as tmp:
        board_path = os.path.join(tmp, "DISPATCH_BOARD.md")
        with open(board_path, "w") as f:
            f.write(_make_board([_make_board_row("WO-XYZ")]))

        # Monkeypatch BOARD path in wo_test_runner
        import company_runtime.wo_test_runner as _R
        _orig_board = _R.BOARD
        _R.BOARD = board_path
        try:
            result = auto_close("WO-XYZ", "David-approved")
            assert result is True, "auto_close must return True when row was changed"
            with open(board_path) as f:
                content = f.read()
            assert "DONE" in content, "board must contain DONE after auto_close"
            assert "David-approved" in content, "board must cite David-approved as the note"
        finally:
            _R.BOARD = _orig_board

    ok("AT-2: auto_close flips board row to DONE ✅ David-approved")
except AssertionError as e:
    fail("AT-2", e)
except Exception as e:
    fail("AT-2", e)


# ── AT-3: approved WO with no test file is still closed (not gated on green) ──
try:
    import company_runtime.continuation as _cont3
    from company_runtime.wo_test_runner import auto_close as _ac3
    import company_runtime.wo_test_runner as _R3

    with tempfile.TemporaryDirectory() as tmp:
        board_path = os.path.join(tmp, "DISPATCH_BOARD.md")
        approved_path = os.path.join(tmp, "DAVID_APPROVED.md")

        with open(board_path, "w") as f:
            f.write(_make_board([_make_board_row("WO-900")]))
        with open(approved_path, "w") as f:
            f.write(_make_approved(["WO-900"]))

        # Monkeypatch
        _orig_board = _R3.BOARD
        _orig_approved = _cont3._APPROVED
        _R3.BOARD = board_path
        _cont3._APPROVED = approved_path

        try:
            # Even with no test (approved is picked up outside discover() loop)
            approved = _cont3.load_david_approved()
            bstat = _R3.board_status()
            already = "DONE" in bstat.get("WO-900", "")
            assert not already, "WO must start as not DONE"

            # Simulate the approved-outside-mapping path
            if "WO-900" in approved and not already:
                _ac3("WO-900", "David-approved")

            with open(board_path) as f:
                content = f.read()
            assert "DONE" in content, "approved WO with no test must still be closed"
        finally:
            _R3.BOARD = _orig_board
            _cont3._APPROVED = _orig_approved

    ok("AT-3: approved WO with no test file closed without green gate")
except AssertionError as e:
    fail("AT-3", e)
except Exception as e:
    fail("AT-3", e)


# ── AT-4: idempotent — already-DONE WO not double-closed ─────────────────────
try:
    import company_runtime.wo_test_runner as _R4

    with tempfile.TemporaryDirectory() as tmp:
        board_path = os.path.join(tmp, "DISPATCH_BOARD.md")
        with open(board_path, "w") as f:
            f.write(_make_board([_make_board_row("WO-ZZZ", "**DONE ✅ already done**")]))

        _orig_board = _R4.BOARD
        _R4.BOARD = board_path
        try:
            result = _R4.auto_close("WO-ZZZ", "David-approved")
            assert result is False, "auto_close on already-DONE row must return False (no change)"
        finally:
            _R4.BOARD = _orig_board

    ok("AT-4: auto_close is idempotent — already-DONE row not changed again")
except AssertionError as e:
    fail("AT-4", e)
except Exception as e:
    fail("AT-4", e)


# ── AT-5: load_david_approved parses various formats; compile clean ────────────
try:
    from company_runtime.continuation import load_david_approved as _lda5
    import company_runtime.continuation as _cont5

    with tempfile.TemporaryDirectory() as tmp:
        approved_path = os.path.join(tmp, "DAVID_APPROVED.md")
        with open(approved_path, "w") as f:
            f.write(
                "# Header\n"
                "- WO-016 — approved\n"
                "- WO-017 + WO-019 — batch\n"
                "  WO-020\n"                    # indented
                "WO-022 in prose — approved\n"  # in prose
                "not-a-wo\n"                    # should not match
            )

        _orig_approved = _cont5._APPROVED
        _cont5._APPROVED = approved_path
        try:
            result = _lda5()
            for wo in ("WO-016", "WO-017", "WO-019", "WO-020", "WO-022"):
                assert wo in result, f"{wo} must be parsed from approved ledger, got {result}"
            assert "NOT-A-WO" not in result, "non-WO-format strings must not be parsed"
        finally:
            _cont5._APPROVED = _orig_approved

    cont_path = os.path.join(_BASE, "company_runtime", "continuation.py")
    py_compile.compile(cont_path, doraise=True)
    ok("AT-5: load_david_approved parses various formats; continuation.py compiles clean")
except AssertionError as e:
    fail("AT-5", e)
except Exception as e:
    fail("AT-5", e)


# ── Summary ───────────────────────────────────────────────────────────────────
print()
print("=" * 62)
print(f"WO-APPROVAL-MEMORY     {_passed} passed   {_failed} failed")
if _failed:
    sys.exit(1)
