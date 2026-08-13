"""
tests/test_ea2_6_orchestration.py — Acceptance tests for WO-EA2-6.

Orchestration Faculty: multi-seat WO chains (dependency sequencing + hand-offs).
Read-only faculty — these tests build small SYNTHETIC boards in /tmp and never
touch the real DISPATCH_BOARD.md.

Cases:
  AT-1  next_actionable returns only WOs with all deps met + READY; excludes unmet.
  AT-2  leverage ranking: a WO that unblocks more downstream ranks higher.
  AT-3  blocked_by returns the correct unmet deps.
  AT-4  handoffs identifies a cross-seat dependency.
  AT-5  a dependency cycle is detected + reported, no hang.
  AT-6  malformed / empty board → graceful empty result, no crash.
  AT-7  (bonus) build_chains gives topological prereqs grouped by seat.

Run: python3 tests/test_ea2_6_orchestration.py
"""
import os
import sys
import textwrap
import tempfile

sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")

from company_runtime.orchestration_faculty import (
    build_chains, next_actionable, blocked_by, handoffs, detect_cycles,
)


def _write_board(tmpdir, text):
    path = os.path.join(tmpdir, "DISPATCH_BOARD.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(textwrap.dedent(text))
    return path


_HEADER = "| WO | Title | Agent | Pri | Status | Depends on | Spec |\n|----|--|--|--|--|--|--|\n"


# ── AT-1: next_actionable = deps met + READY only ─────────────────────────────
with tempfile.TemporaryDirectory() as tmp:
    board = _write_board(tmp, _HEADER + textwrap.dedent("""\
        | WO-A1 | root done | Builder | P1 | DONE ✅ David | — | s |
        | WO-A2 | ready, dep met | Builder | P1 | READY | WO-A1 | s |
        | WO-A3 | blocked, dep not done | Builder | P2 | READY | WO-A4 | s |
        | WO-A4 | prerequisite still open | Design | P2 | READY | — | s |
    """))
    na = next_actionable(board_path=board)
    ids = {x["id"] for x in na}
    try:
        assert "WO-A2" in ids, "WO-A2 (dep WO-A1 done) should be actionable"
        assert "WO-A4" in ids, "WO-A4 (no deps, READY) should be actionable"
        assert "WO-A3" not in ids, "WO-A3 depends on open WO-A4 → must be excluded"
        assert "WO-A1" not in ids, "WO-A1 is DONE → not actionable"
        ok(f"AT-1: next_actionable = {sorted(ids)} (excludes unmet WO-A3, done WO-A1)")
    except AssertionError as e: fail("AT-1", e)


# ── AT-2: leverage ranking (more downstream → higher) ─────────────────────────
with tempfile.TemporaryDirectory() as tmp:
    # WO-HUB unblocks D1,D2,D3 (and D2->D2b transitively). WO-LEAF unblocks nothing.
    board = _write_board(tmp, _HEADER + textwrap.dedent("""\
        | WO-HUB | high leverage | Builder | P2 | READY | — | s |
        | WO-LEAF | low leverage | Builder | P2 | READY | — | s |
        | WO-D1 | dep1 | Design | P3 | READY | WO-HUB | s |
        | WO-D2 | dep2 | Design | P3 | READY | WO-HUB | s |
        | WO-D3 | dep3 | Design | P3 | READY | WO-HUB | s |
        | WO-D2B | dep2b | Design | P3 | READY | WO-D2 | s |
    """))
    na = next_actionable(board_path=board)
    lev = {x["id"]: x["leverage"] for x in na}
    order = [x["id"] for x in na]
    try:
        assert lev.get("WO-HUB", 0) >= 4, f"WO-HUB should unblock >=4 downstream, got {lev.get('WO-HUB')}"
        assert lev.get("WO-LEAF", 0) == 0, f"WO-LEAF unblocks nothing, got {lev.get('WO-LEAF')}"
        assert order.index("WO-HUB") < order.index("WO-LEAF"), "WO-HUB must rank above WO-LEAF"
        ok(f"AT-2: leverage HUB={lev['WO-HUB']} > LEAF={lev['WO-LEAF']}; HUB ranked first")
    except AssertionError as e: fail("AT-2", e)


# ── AT-3: blocked_by returns correct unmet deps ───────────────────────────────
with tempfile.TemporaryDirectory() as tmp:
    board = _write_board(tmp, _HEADER + textwrap.dedent("""\
        | WO-B1 | done dep | Builder | P1 | DONE ✅ David | — | s |
        | WO-B2 | open dep | Design | P2 | READY | — | s |
        | WO-B3 | target | Builder | P1 | READY | WO-B1 · WO-B2 | s |
    """))
    res = blocked_by("WO-B3", board_path=board)
    try:
        assert res["found"], "WO-B3 should be found"
        assert res["ready"] is False, "WO-B3 has an unmet dep → not ready"
        unmet_ids = {d["id"] for d in res["blocked_by"]}
        assert unmet_ids == {"WO-B2"}, f"only WO-B2 unmet, got {unmet_ids}"
        assert "WO-B1" in res["met"], "WO-B1 (done) should be in met"
        ok(f"AT-3: blocked_by(WO-B3) unmet={sorted(unmet_ids)}, met={res['met']}")
    except AssertionError as e: fail("AT-3", e)


# ── AT-4: handoffs identify cross-seat dependency ─────────────────────────────
with tempfile.TemporaryDirectory() as tmp:
    board = _write_board(tmp, _HEADER + textwrap.dedent("""\
        | WO-C1 | design prereq | Design | P2 | READY | — | s |
        | WO-C2 | builder waits on design | Builder | P1 | READY | WO-C1 | s |
        | WO-C3 | same-seat dep (not a handoff) | Builder | P2 | READY | WO-C2 | s |
    """))
    ho = handoffs(board_path=board)
    pairs = {(h["wo"], h["depends_on"]) for h in ho}
    try:
        assert ("WO-C2", "WO-C1") in pairs, "cross-seat Builder->Design hand-off missing"
        assert ("WO-C3", "WO-C2") not in pairs, "same-seat dep must NOT be a hand-off"
        h = next(x for x in ho if x["wo"] == "WO-C2")
        assert h["wo_seat"] == "Builder" and h["dep_seat"] == "Design", "seats mislabelled"
        ok(f"AT-4: hand-off WO-C2(Builder) -> WO-C1(Design) detected; same-seat excluded")
    except AssertionError as e: fail("AT-4", e)


# ── AT-5: cycle detected + reported, no hang ──────────────────────────────────
with tempfile.TemporaryDirectory() as tmp:
    board = _write_board(tmp, _HEADER + textwrap.dedent("""\
        | WO-X1 | cyc a | Builder | P2 | READY | WO-X3 | s |
        | WO-X2 | cyc b | Builder | P2 | READY | WO-X1 | s |
        | WO-X3 | cyc c | Builder | P2 | READY | WO-X2 | s |
        | WO-X4 | acyclic | Design | P3 | READY | — | s |
    """))
    cycles = detect_cycles(board_path=board)          # must terminate
    bc = build_chains(board_path=board)               # must terminate too
    try:
        assert len(cycles) >= 1, "the X1->X3->X2->X1 cycle should be detected"
        nodes = set().union(*[set(c) for c in cycles])
        assert {"WO-X1", "WO-X2", "WO-X3"} <= nodes, f"cycle nodes wrong: {nodes}"
        assert bc["counts"]["cycles"] >= 1, "build_chains should report the cycle in counts"
        ok(f"AT-5: cycle detected {cycles[0]} — no hang")
    except AssertionError as e: fail("AT-5", e)


# ── AT-6: malformed / empty board → graceful empty ────────────────────────────
try:
    # (a) nonexistent path
    p_missing = "/tmp/__ea2_6_does_not_exist__.md"
    r_missing = build_chains(board_path=p_missing)
    assert r_missing["chains"] == {} and r_missing["cycles"] == [], "missing board not empty"
    assert next_actionable(board_path=p_missing) == [], "missing board actionable not empty"
    assert handoffs(board_path=p_missing) == [], "missing board handoffs not empty"
    assert detect_cycles(board_path=p_missing) == [], "missing board cycles not empty"
    assert blocked_by("WO-ANY", board_path=p_missing)["found"] is False, "ghost WO found?"

    # (b) garbage / empty content
    with tempfile.TemporaryDirectory() as tmp:
        p_junk = _write_board(tmp, "not a table\n\n### heading only\nrandom text | | |\n")
        assert build_chains(board_path=p_junk)["chains"] == {}, "junk board produced chains"
        assert next_actionable(board_path=p_junk) == [], "junk board produced actionable"
        p_empty = _write_board(tmp, "")
        assert build_chains(board_path=p_empty)["chains"] == {}, "empty board produced chains"
    ok("AT-6: missing / junk / empty boards → graceful empty results, no crash")
except Exception as e: fail("AT-6", f"crashed or wrong: {e!r}")


# ── AT-7: build_chains topological prereqs grouped by seat ────────────────────
with tempfile.TemporaryDirectory() as tmp:
    board = _write_board(tmp, _HEADER + textwrap.dedent("""\
        | WO-P1 | base (design) | Design | P2 | READY | — | s |
        | WO-P2 | mid (builder) | Builder | P2 | READY | WO-P1 | s |
        | WO-P3 | top (builder) | Builder | P1 | READY | WO-P2 | s |
    """))
    bc = build_chains(board_path=board)
    try:
        chain = bc["chains"]["WO-P3"]
        prereqs = chain["prerequisites"]
        assert prereqs == ["WO-P1", "WO-P2"], f"topo order wrong: {prereqs}"
        assert chain["by_seat"].get("Design") == ["WO-P1"], "Design prereq grouping wrong"
        assert chain["by_seat"].get("Builder") == ["WO-P2"], "Builder prereq grouping wrong"
        assert any(h["depends_on"] == "WO-P1" for h in bc["chains"]["WO-P2"]["handoffs"]), \
            "WO-P2 -> WO-P1 cross-seat hand-off missing in chain"
        ok(f"AT-7: build_chains topo prereqs {prereqs}, grouped by seat, hand-off tracked")
    except (AssertionError, KeyError) as e: fail("AT-7", e)


N = PASS + FAIL
print(f"\n{PASS}/{N} passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
