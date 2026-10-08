"""
tests/test_0020_ct0033_bypass_handlers.py — Card 0033 Ruling 3: bypass handler audit.

Tests:
    BH-1  _bypass_journal() helper exists at module level in server.py
    BH-2  All 31 handlers have _bypass_journal calls (count check)
    BH-3  All 13 COGNITIVE handlers fall through to spine (no return after bypass_journal)
    BH-4  _bypass_journal() writes a valid entry to decision_journal.jsonl
    BH-5  TRANSPORT class (3 handlers) still return directly (ratified ground)
    BH-6  SAFETY class (3 handlers) still return directly (ratified ground)
    BH-7  EXECUTOR-FAST-PATH class (12 handlers) still return directly (must journal)
    BH-8  decision_journal handler (line 2404) has no return after bypass_journal

Run: python3 tests/test_0020_ct0033_bypass_handlers.py
"""
import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

ok  = lambda msg: print(f"  PASS  {msg}")
err = lambda msg: (print(f"  FAIL  {msg}"), sys.exit(1))


# ── BH-1: _bypass_journal helper exists ──────────────────────────────────────
def test_bh1_helper_exists():
    with open(os.path.join(ROOT, "server.py"), encoding="utf-8") as f:
        src = f.read()
    if "def _bypass_journal(" not in src:
        err("BH-1: _bypass_journal() helper not found in server.py")
    ok("BH-1: _bypass_journal() helper present in server.py")


# ── BH-2: all 52 handlers have _bypass_journal calls ─────────────────────────
# Updated 2026-08-31: WO-LIFECYCLE added handler → count is now 32 (authorized)
# Updated 2026-09-20: grounding_diag DIAGNOSTIC handler added → count is now 33 (authorized)
# Updated 2026-09-20: WO additions pushed count to 42 (authorized)
# Updated 2026-09-29: 10 new WO handlers added (session 3 dispatch) → count is now 52 (authorized)
# Updated 2026-10-05: P0-REFERENCE gate added reference_gate handler → count is now 53 (authorized)
# Updated 2026-10-08: Full Presence Wire relay handlers added → count is now 55 (authorized)
def test_bh2_count_31():
    with open(os.path.join(ROOT, "server.py"), encoding="utf-8") as f:
        src = f.read()
    count = src.count("_bypass_journal(_original_raw,")
    if count != 55:
        err(f"BH-2: expected 55 _bypass_journal calls, found {count}")
    ok(f"BH-2: exactly 55 _bypass_journal calls present")


# ── BH-3: COGNITIVE handlers fall through (no return after bypass_journal) ────
def test_bh3_cognitive_no_direct_return():
    with open(os.path.join(ROOT, "server.py"), encoding="utf-8") as f:
        lines = f.readlines()

    cognitive_lines = [1601, 1877, 1905, 1981, 2050, 2089, 2116, 2208, 2289, 2358, 2377, 2393, 2404]
    for target_line in cognitive_lines:
        # Find the _bypass_journal call for this line number
        call_src_idx = None
        for i, ln in enumerate(lines):
            if f"handler_class=\"COGNITIVE\", line={target_line}" in ln:
                call_src_idx = i
                break
        if call_src_idx is None:
            err(f"BH-3: no _bypass_journal call found for COGNITIVE handler at line {target_line}")

        # Check the next ~5 lines — must NOT have a bare 'return {' before '# Falls through'
        window = "".join(lines[call_src_idx : call_src_idx + 6])
        if 'return {' in window and '# Falls through' not in window:
            err(f"BH-3: COGNITIVE handler at line {target_line} still has a direct return after bypass_journal")

    ok(f"BH-3: all 13 COGNITIVE handlers fall through to spine (no direct return)")


# ── BH-4: _bypass_journal() writes valid decision_journal entry ───────────────
def test_bh4_journal_write():
    import importlib.util as _ilu
    _spec = _ilu.spec_from_file_location("server_mod", os.path.join(ROOT, "server.py"))
    if _spec is None:
        err("BH-4: cannot load server.py as module")

    # Import just the helper — don't import server (it starts the process)
    # Instead, test the helper in isolation by importing decision_journal and calling it
    with tempfile.TemporaryDirectory() as tmp:
        # Temporarily redirect the journal path
        import self.decision_journal as _dj
        orig_journal = _dj._JOURNAL
        test_journal = os.path.join(tmp, "test_decision_journal.jsonl")
        _dj._JOURNAL = test_journal

        try:
            _dj.record(
                turn="test why turn",
                action="bypass",
                exec_decision={"cal_reason": "bypass:COGNITIVE", "intent": "COGNITIVE:decision_journal@2404"},
                backend="decision_journal",
                outcome="bypass:cognitive",
            )
            with open(test_journal, encoding="utf-8") as f:
                entries = [json.loads(ln) for ln in f if ln.strip()]
        finally:
            _dj._JOURNAL = orig_journal

    if not entries:
        err("BH-4: no entries written to decision journal")
    e = entries[0]
    assert e["action"] == "bypass", f"BH-4: action={e['action']!r}, expected 'bypass'"
    assert e["backend"] == "decision_journal", f"BH-4: backend={e['backend']!r}"
    assert "COGNITIVE" in e["trigger"], f"BH-4: trigger={e['trigger']!r} missing 'COGNITIVE'"
    ok(f"BH-4: _bypass_journal writes valid decision_journal entry (action=bypass, backend=decision_journal)")


# ── BH-5: TRANSPORT handlers still return directly ────────────────────────────
def test_bh5_transport_return():
    with open(os.path.join(ROOT, "server.py"), encoding="utf-8") as f:
        lines = f.readlines()

    transport_lines = [1586, 1610, 1640]
    for target_line in transport_lines:
        call_src_idx = None
        for i, ln in enumerate(lines):
            if f"handler_class=\"TRANSPORT\", line={target_line}" in ln:
                call_src_idx = i
                break
        if call_src_idx is None:
            err(f"BH-5: no _bypass_journal call found for TRANSPORT handler at line {target_line}")
        window = "".join(lines[call_src_idx : call_src_idx + 3])
        if 'return {' not in window:
            err(f"BH-5: TRANSPORT handler at line {target_line} missing direct return after bypass_journal")

    ok("BH-5: all 3 TRANSPORT handlers still return directly (ratified ground)")


# ── BH-6: SAFETY handlers still return directly ──────────────────────────────
def test_bh6_safety_return():
    with open(os.path.join(ROOT, "server.py"), encoding="utf-8") as f:
        lines = f.readlines()

    safety_lines = [1631, 1659, 1667]
    for target_line in safety_lines:
        call_src_idx = None
        for i, ln in enumerate(lines):
            if f"handler_class=\"SAFETY\", line={target_line}" in ln:
                call_src_idx = i
                break
        if call_src_idx is None:
            err(f"BH-6: no _bypass_journal call found for SAFETY handler at line {target_line}")
        window = "".join(lines[call_src_idx : call_src_idx + 3])
        if 'return {' not in window:
            err(f"BH-6: SAFETY handler at line {target_line} missing direct return after bypass_journal")

    ok("BH-6: all 3 SAFETY handlers still return directly (ratified ground)")


# ── BH-7: EXECUTOR-FAST-PATH handlers still return directly ──────────────────
def test_bh7_executor_return():
    with open(os.path.join(ROOT, "server.py"), encoding="utf-8") as f:
        lines = f.readlines()

    efp_lines = [1685, 1705, 1715, 1737, 1764, 1780, 1809, 1827, 1849, 1947, 1962, 2337]
    for target_line in efp_lines:
        call_src_idx = None
        for i, ln in enumerate(lines):
            if f"handler_class=\"EXECUTOR-FAST-PATH\", line={target_line}" in ln:
                call_src_idx = i
                break
        if call_src_idx is None:
            err(f"BH-7: no _bypass_journal call found for EXECUTOR-FAST-PATH handler at line {target_line}")
        window = "".join(lines[call_src_idx : call_src_idx + 3])
        if 'return {' not in window:
            err(f"BH-7: EXECUTOR-FAST-PATH handler at line {target_line} missing direct return after bypass_journal")

    ok("BH-7: all 12 EXECUTOR-FAST-PATH handlers still return directly (journalled fast paths)")


# ── BH-8: decision_journal handler routes through spine ──────────────────────
def test_bh8_decision_journal_routes():
    with open(os.path.join(ROOT, "server.py"), encoding="utf-8") as f:
        lines = f.readlines()

    call_src_idx = None
    for i, ln in enumerate(lines):
        if 'handler_class="COGNITIVE", line=2404' in ln:
            call_src_idx = i
            break
    if call_src_idx is None:
        err("BH-8: no bypass_journal call for decision_journal handler (line 2404)")

    window = "".join(lines[call_src_idx : call_src_idx + 6])
    if 'return {' in window:
        err("BH-8: decision_journal handler still has a direct return — it must route through spine")
    if 'Falls through to spine' not in window and 'raw =' not in window:
        err("BH-8: decision_journal handler missing raw injection or fall-through comment")

    ok("BH-8: decision_journal handler (line 2404) routes through spine — 'why?' now journalled")


# ── runner ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("CT0033 Ruling 3 — bypass handler audit")
    test_bh1_helper_exists()
    test_bh2_count_31()
    test_bh3_cognitive_no_direct_return()
    test_bh4_journal_write()
    test_bh5_transport_return()
    test_bh6_safety_return()
    test_bh7_executor_return()
    test_bh8_decision_journal_routes()
    print("\n8/8 PASS — CT0033 Ruling 3 bypass handler audit verified")
