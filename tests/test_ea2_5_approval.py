"""
tests/test_ea2_5_approval.py — Acceptance tests for WO-EA2-5 (Approval Faculty)

Spec: formalize the L3 approval gate as a clean, testable decision + record faculty
(company_runtime/approval_faculty.py). This faculty DECIDES whether an approval is
allowed and RECORDS it to an append-only JSONL ledger. It does NOT edit the board.

Tests run against a TEMP ledger in /tmp — the real blender/approval_ledger.jsonl is
never touched.

    AT-1  L3 actor ("david") approving a normal WO           → ok:True
    AT-2  Non-L3 actor                                        → refused
    AT-3a RESERVED WO (money/legal/safety) w/o human_flag     → refused
    AT-3b same RESERVED WO WITH human_flag                    → allowed
    AT-4  AUTO WO by david                                    → allowed
    AT-5  every decision writes a ledger line (grows + parses)
    AT-6  malformed input (missing wo/actor)                  → graceful {ok:False}, no crash

Run: python3 tests/test_ea2_5_approval.py
"""
import sys
import os
import json
import tempfile

sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


from company_runtime.approval_faculty import ApprovalFaculty, request, L3_ACTORS


# Temp ledger — NEVER the real blender/ path.
_LEDGER = os.path.join(tempfile.gettempdir(), "ea2_5_approval_ledger_test.jsonl")
if os.path.exists(_LEDGER):
    os.remove(_LEDGER)
fac = ApprovalFaculty(_LEDGER)


def _ledger_lines():
    if not os.path.exists(_LEDGER):
        return []
    with open(_LEDGER, encoding="utf-8") as f:
        return [ln for ln in f.read().splitlines() if ln.strip()]


# ── AT-1: L3 actor approving a normal WO → ok:True ────────────────────────────
try:
    r = fac.request("WO-500", "david", title="engineering task", status="READY")
    assert r["ok"] is True, f"expected ok:True, got {r}"
    assert r["decision"] == "allowed", f"expected decision allowed, got {r['decision']!r}"
    ok(f"AT-1: L3 david/WO-500 allowed — {r['reason']!r}")
except AssertionError as e: fail("AT-1", e)


# ── AT-2: non-L3 actor → refused ──────────────────────────────────────────────
try:
    r = fac.request("WO-500", "random_intern", title="engineering task")
    assert r["ok"] is False, f"non-L3 actor should be refused, got {r}"
    assert r["decision"] == "refused", f"expected refused, got {r['decision']!r}"
    assert "l3" in r["reason"].lower(), f"reason should mention L3: {r['reason']!r}"
    ok(f"AT-2: non-L3 actor refused — {r['reason']!r}")
except AssertionError as e: fail("AT-2", e)


# ── AT-3: RESERVED WO — refused without human_flag, allowed with ──────────────
# BO-2 → money (reserved prefix); "LG-2" safety/legal prefix. Test both money + safety.
try:
    r_money = fac.request("BO-2", "david", human_flag=False, title="funding model")
    assert r_money["ok"] is False, f"RESERVED money w/o human_flag should refuse: {r_money}"
    assert "reserved" in r_money["reason"].lower() or "human_flag" in r_money["reason"].lower(), \
        f"reason should cite reserved/human_flag: {r_money['reason']!r}"

    r_safety = fac.request("LG-2", "david", human_flag=False, title="compliance / legal review")
    assert r_safety["ok"] is False, f"RESERVED legal/safety w/o human_flag should refuse: {r_safety}"

    ok(f"AT-3a: RESERVED BO-2 + LG-2 refused without human_flag — {r_money['reason']!r}")
except AssertionError as e: fail("AT-3a", e)

try:
    r_ok = fac.request("BO-2", "david", human_flag=True, title="funding model")
    assert r_ok["ok"] is True, f"RESERVED WO with human_flag should be allowed: {r_ok}"
    assert r_ok["decision"] == "allowed"
    ok(f"AT-3b: RESERVED BO-2 allowed WITH human_flag — {r_ok['reason']!r}")
except AssertionError as e: fail("AT-3b", e)


# ── AT-4: AUTO WO by david → allowed ─────────────────────────────────────────
try:
    # "cleanup" title → wo_policy classifies AUTO (trivial/mechanical).
    r = fac.request("WO-777", "david", title="cleanup dead code", status="DONE")
    assert r["ok"] is True, f"AUTO WO by david should be allowed: {r}"
    assert r["decision"] == "allowed"
    ok(f"AT-4: AUTO WO by david allowed — {r['reason']!r}")
except AssertionError as e: fail("AT-4", e)


# ── AT-5: every decision writes a ledger line (grows + parses) ────────────────
try:
    before = len(_ledger_lines())
    fac.request("WO-800", "david", title="another task")
    fac.request("WO-801", "not_l3", title="another task")
    after_lines = _ledger_lines()
    assert len(after_lines) == before + 2, \
        f"ledger should grow by 2 (was {before}, now {len(after_lines)})"
    # every line parses as JSON with the expected fields
    for ln in after_lines:
        obj = json.loads(ln)
        for k in ("ts", "wo", "actor", "importance", "decision", "reason"):
            assert k in obj, f"ledger line missing key {k!r}: {obj}"
    # allowed + refused both recorded
    decisions = {json.loads(ln)["decision"] for ln in after_lines}
    assert "allowed" in decisions and "refused" in decisions, \
        f"both allowed + refused decisions should be logged: {decisions}"
    ok(f"AT-5: ledger grew {before}→{len(after_lines)}; all lines parse with required fields")
except AssertionError as e: fail("AT-5", e)


# ── AT-6: malformed input → graceful {ok:False}, no crash ────────────────────
_crashed = False
_all_refused = True
_cases = [
    ("", "david"),          # missing wo
    ("WO-900", ""),         # missing actor
    (None, None),           # both None
    (None, "david"),        # None wo
    ("WO-901", None),       # None actor
]
for wo, actor in _cases:
    try:
        r = fac.request(wo, actor)
        if r.get("ok"):
            _all_refused = False
    except Exception:
        _crashed = True
try:
    assert not _crashed, "request() raised on malformed input"
    assert _all_refused, "a malformed case returned ok=True"
    ok("AT-6: malformed inputs refused gracefully, no crash")
except AssertionError as e: fail("AT-6", e)


# ── bonus: module-level request() convenience against a temp ledger ──────────
try:
    _tmp2 = os.path.join(tempfile.gettempdir(), "ea2_5_approval_ledger_modlevel.jsonl")
    if os.path.exists(_tmp2):
        os.remove(_tmp2)
    r = request("WO-1000", "founder", title="task", ledger_path=_tmp2)
    assert r["ok"] is True, f"founder is L3, should be allowed: {r}"
    assert os.path.exists(_tmp2) and len(open(_tmp2).read().splitlines()) == 1
    ok("AT-7: module-level request() works + logs to supplied temp ledger")
except AssertionError as e: fail("AT-7", e)


# cleanup temp ledgers
for _p in (_LEDGER, os.path.join(tempfile.gettempdir(), "ea2_5_approval_ledger_modlevel.jsonl")):
    try:
        if os.path.exists(_p):
            os.remove(_p)
    except Exception:
        pass


_total = PASS + FAIL
print(f"\nResult: {PASS}/{_total} passed, {FAIL} failed")
sys.exit(1 if FAIL else 0)
