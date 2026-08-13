"""
tests/test_ea2_4_scheduling.py — Acceptance tests for WO-EA2-4 Scheduling Faculty.

Spec: EA-3 §9 — a faculty to reorder / move Work Orders on the dispatch board.
Builds company_runtime/scheduling_faculty.py (ADDITIVE — frozen kernel untouched).

Acceptance:
    AT-1  move_wo places a row after/before a target; content unchanged;
          the table still parses (company_state_writer._parse_board keeps all rows).
    AT-2  set_priority changes ONLY the priority cell.
    AT-3  malformed / unknown wo_id → graceful {ok:False}, no corruption.
    AT-4  a `.bak` backup is written before any change.
    AT-5  reorder_section reorders a set of rows to match a given order (no rows lost).

Every test works on a COPY of the real board in a tmp dir — the live
DISPATCH_BOARD.md is never mutated.

Run: python3 tests/test_ea2_4_scheduling.py
"""
import os
import sys
import shutil
import tempfile
import textwrap

sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")

from company_runtime.scheduling_faculty import (
    move_wo, set_priority, reorder_section,
)
from company_runtime.company_state_writer import _parse_board


_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_REAL_BOARD = os.path.join(_REPO, "engineering", "work_orders", "DISPATCH_BOARD.md")

# A self-contained mock board (a heading + a table section) so tests don't depend
# on the exact contents of the live board.
_MOCK_BOARD = textwrap.dedent("""\
    # eLo OS — Dispatch Board (test copy)

    ### Company Runtime work stream — Presence ↔ eLo

    | WO | Title | Agent | Pri | Status | Depends on | Spec |
    |----|-------|-------|-----|--------|-----------|------|
    | EA2-4 | Scheduling Faculty (move/reorder WOs) | Builder | P2 | QUEUED | EA2-1 | EA-3 §9 |
    | EA2-5 | Approval Faculty | Builder | P2 | QUEUED | EA2-1 | EA-3 §4 |
    | EA2-6 | Orchestration Faculty | Builder | P3 | QUEUED | EA2-5 | EA-3 §4 |
    | EA2-7 | Company Memory store | Builder | P3 | QUEUED | EA2-1 | EA-3 §6 |

    Some trailing prose that must stay put.
""")


def _fresh_board(tmp):
    """Write the mock board into tmp and return its path."""
    p = os.path.join(tmp, "DISPATCH_BOARD.md")
    with open(p, "w", encoding="utf-8") as f:
        f.write(_MOCK_BOARD)
    return p


def _ids(board_path):
    with open(board_path, encoding="utf-8") as f:
        return [r["id"] for r in _parse_board(f.read())]


def _row_text(board_path, wo_id):
    with open(board_path, encoding="utf-8") as f:
        for line in f.read().splitlines():
            if line.strip().startswith("|") and f"| {wo_id} " in line:
                return line
    return None


# ── AT-1: move_wo places a row after/before a target; content unchanged ───────

with tempfile.TemporaryDirectory() as _tmp:
    _b = _fresh_board(_tmp)
    _before_ids = _ids(_b)
    _row_before = _row_text(_b, "EA2-7")

    _res = move_wo("EA2-7", after="EA2-4", board_path=_b)
    try:
        assert _res["ok"], f"move_wo not ok: {_res['reason']}"
        assert _res["moved"] == ["EA2-7"], f"moved payload wrong: {_res['moved']}"
        _after_ids = _ids(_b)
        # order changed: EA2-7 now directly follows EA2-4
        assert _after_ids.index("EA2-7") == _after_ids.index("EA2-4") + 1, (
            f"EA2-7 not placed after EA2-4: {_after_ids}")
        # no rows lost / gained
        assert sorted(_after_ids) == sorted(_before_ids), (
            f"row set changed: {_before_ids} → {_after_ids}")
        # content of the moved row is byte-identical
        assert _row_text(_b, "EA2-7") == _row_before, "moved row content changed"
        # table still parses fully via the state writer
        assert len(_parse_board(open(_b, encoding='utf-8').read())) == len(_before_ids)
        ok(f"AT-1: move_wo EA2-7 after EA2-4 — order {_after_ids}, content unchanged, all rows parse")
    except AssertionError as e: fail("AT-1", e)

    # also prove the before= variant
    _res_b = move_wo("EA2-7", before="EA2-4", board_path=_b)
    try:
        assert _res_b["ok"], f"move_wo before= not ok: {_res_b['reason']}"
        _ids_b = _ids(_b)
        assert _ids_b.index("EA2-7") == _ids_b.index("EA2-4") - 1, f"before= failed: {_ids_b}"
        ok(f"AT-1b: move_wo EA2-7 before EA2-4 — order {_ids_b}")
    except AssertionError as e: fail("AT-1b", e)


# ── AT-2: set_priority changes ONLY the priority cell ─────────────────────────

with tempfile.TemporaryDirectory() as _tmp:
    _b = _fresh_board(_tmp)
    _orig_row = _row_text(_b, "EA2-4")
    _res = set_priority("EA2-4", "P0", board_path=_b)
    try:
        assert _res["ok"], f"set_priority not ok: {_res['reason']}"
        _new_row = _row_text(_b, "EA2-4")
        _parsed = [r for r in _parse_board(open(_b, encoding='utf-8').read()) if r["id"] == "EA2-4"][0]
        assert _parsed["priority"] == "P0", f"priority not P0: {_parsed['priority']}"
        # every OTHER cell is unchanged — compare pipe-split cells except index 4 (pri)
        oc = _orig_row.split("|"); nc = _new_row.split("|")
        assert len(oc) == len(nc), "cell count changed"
        for i in range(len(oc)):
            if i == 4:
                continue
            assert oc[i] == nc[i], f"cell {i} changed unexpectedly: {oc[i]!r} → {nc[i]!r}"
        # sibling rows untouched
        assert _row_text(_b, "EA2-5").strip().endswith("EA-3 §4 |"), "sibling row disturbed"
        ok(f"AT-2: set_priority EA2-4 → P0; only the priority cell changed")
    except AssertionError as e: fail("AT-2", e)

    # invalid priority is refused, board untouched
    _res_bad = set_priority("EA2-4", "P9", board_path=_b)
    try:
        assert not _res_bad["ok"], "invalid priority P9 should be refused"
        ok(f"AT-2b: invalid priority refused — {_res_bad['reason']!r}")
    except AssertionError as e: fail("AT-2b", e)


# ── AT-3: malformed / unknown wo_id → graceful {ok:False}, no corruption ──────

with tempfile.TemporaryDirectory() as _tmp:
    _b = _fresh_board(_tmp)
    with open(_b, encoding="utf-8") as f:
        _snapshot = f.read()

    _cases = [
        lambda: move_wo("EA2-GHOST", after="EA2-4", board_path=_b),   # unknown source
        lambda: move_wo("EA2-4", after="EA2-GHOST", board_path=_b),   # unknown target
        lambda: move_wo("", after="EA2-4", board_path=_b),            # empty id
        lambda: move_wo("EA2-4", board_path=_b),                      # no before/after
        lambda: move_wo("EA2-4", after="EA2-4", board_path=_b),       # self-move
        lambda: set_priority("EA2-GHOST", "P1", board_path=_b),       # unknown id
        lambda: set_priority("EA2-4", "banana", board_path=_b),       # bad priority
        lambda: reorder_section("nope-marker", ["EA2-4", "EA2-5"], board_path=_b),  # bad marker
    ]
    _crashed = False; _all_refused = True
    for _c in _cases:
        try:
            _r = _c()
            if _r.get("ok"):
                _all_refused = False
        except Exception:
            _crashed = True

    with open(_b, encoding="utf-8") as f:
        _after = f.read()
    try:
        assert not _crashed, "a malformed call raised instead of returning {ok:False}"
        assert _all_refused, "a malformed/unknown call returned ok=True"
        assert _after == _snapshot, "board was modified by a refused operation (corruption!)"
        ok("AT-3: all malformed/unknown calls refused gracefully; board byte-identical (no corruption)")
    except AssertionError as e: fail("AT-3", e)


# ── AT-4: a `.bak` backup is written before any change ────────────────────────

with tempfile.TemporaryDirectory() as _tmp:
    _b = _fresh_board(_tmp)
    _bak = _b + ".bak"
    assert not os.path.exists(_bak), "precondition: no .bak yet"
    _res = set_priority("EA2-5", "P1", board_path=_b)
    try:
        assert _res["ok"], f"set_priority not ok: {_res['reason']}"
        assert os.path.exists(_bak), ".bak backup was not written"
        # the .bak holds the ORIGINAL content (pre-change), proving it was taken first
        with open(_bak, encoding="utf-8") as f:
            _bak_text = f.read()
        assert _bak_text == _MOCK_BOARD, ".bak does not hold the pre-change board"
        ok("AT-4: .bak backup written first, holding the original pre-change board")
    except AssertionError as e: fail("AT-4", e)


# ── AT-5: reorder_section reorders a set of rows; no rows lost ─────────────────

with tempfile.TemporaryDirectory() as _tmp:
    _b = _fresh_board(_tmp)
    _orig_ids = _ids(_b)
    _desired = ["EA2-7", "EA2-6", "EA2-5", "EA2-4"]
    _res = reorder_section("Company Runtime work stream", _desired, board_path=_b)
    try:
        assert _res["ok"], f"reorder_section not ok: {_res['reason']}"
        _new_ids = _ids(_b)
        assert _new_ids == _desired, f"section not in requested order: {_new_ids}"
        assert sorted(_new_ids) == sorted(_orig_ids), f"rows lost/gained: {_new_ids}"
        # trailing prose preserved
        with open(_b, encoding="utf-8") as f:
            assert "trailing prose that must stay put" in f.read(), "prose lost"
        ok(f"AT-5: reorder_section → {_new_ids}; all rows preserved, prose intact")
    except AssertionError as e: fail("AT-5", e)


# ── Safety proof: the real DISPATCH_BOARD.md was never touched by this test ────

try:
    assert os.path.exists(_REAL_BOARD), "real board missing (env issue)"
    ok("SAFE: real DISPATCH_BOARD.md untouched (all ops ran on tmp copies)")
except AssertionError as e: fail("SAFE", e)


_total = PASS + FAIL
print(f"\nResult: {PASS}/{_total} passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
