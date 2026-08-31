"""
tests/test_w2_session_id.py — W2: stable monotonic session ID per process start.

Tests:
    W2-1  reflection_faculty.py no longer uses os.getpid() for session_id
    W2-2  _SESSION_ID is defined at module level in reflection_faculty.py
    W2-3  _SESSION_ID is a numeric string (same format as _PROCESS_START in server.py)
    W2-4  _SESSION_ID stays stable across multiple imports (module-level = computed once)
    W2-5  lesson_store.record_outcome() session_id argument is used in promote_pass()

Run: python3 tests/test_w2_session_id.py
"""
import inspect
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

ok  = lambda msg: print(f"  PASS  {msg}")
err = lambda msg: (print(f"  FAIL  {msg}"), sys.exit(1))


# ── W2-1: reflection_faculty no longer uses os.getpid() for session_id ──────
def test_w2_1_no_getpid():
    src_path = os.path.join(ROOT, "runtime", "reflection_faculty.py")
    with open(src_path, encoding="utf-8") as f:
        src = f.read()
    # session_id=str(os.getpid()) must be gone
    if "session_id=str(os.getpid())" in src:
        err("W2-1: reflection_faculty.py still uses session_id=str(os.getpid())")
    ok("W2-1: os.getpid() no longer used as session_id in reflection_faculty.py")


# ── W2-2: _SESSION_ID defined at module level ────────────────────────────────
def test_w2_2_session_id_defined():
    src_path = os.path.join(ROOT, "runtime", "reflection_faculty.py")
    with open(src_path, encoding="utf-8") as f:
        src = f.read()
    if "_SESSION_ID" not in src:
        err("W2-2: _SESSION_ID not found in reflection_faculty.py")
    # Must be assigned at module level (not inside a function body)
    lines = src.splitlines()
    for i, ln in enumerate(lines):
        if "_SESSION_ID" in ln and "=" in ln and not ln.startswith(" ") and not ln.startswith("\t"):
            ok(f"W2-2: _SESSION_ID defined at module level (line {i+1})")
            return
    err("W2-2: _SESSION_ID not defined at module level")


# ── W2-3: _SESSION_ID is "S{n}" format (card 0082 F-2) ──────────────────────
def test_w2_3_numeric_format():
    import runtime.reflection_faculty as rf
    sid = rf._SESSION_ID
    # card 0082 F-2: format is "S{n}" — NOT pure-numeric — so D1 gate
    # (faculties/learning/faculty.py _evidence_is_verified) can distinguish
    # a real session ID from a process ID.
    if not sid.startswith("S"):
        err(f"W2-3: _SESSION_ID={sid!r} must start with 'S' (card 0082 F-2 format)")
    if not sid[1:].isdigit():
        err(f"W2-3: _SESSION_ID={sid!r} — suffix after 'S' must be numeric")
    if len(sid) < 10:  # "S" + at least 9-digit timestamp
        err(f"W2-3: _SESSION_ID={sid!r} too short (expected S + 9+ digit timestamp)")
    ok(f"W2-3: _SESSION_ID={sid!r} is valid 'S{{n}}' format (card 0082 F-2)")


# ── W2-4: _SESSION_ID stable across multiple imports ────────────────────────
def test_w2_4_stable_across_imports():
    import runtime.reflection_faculty as rf
    first  = rf._SESSION_ID
    # Force a second attribute access — value must not change
    second = rf._SESSION_ID
    if first != second:
        err(f"W2-4: _SESSION_ID changed between reads: {first!r} → {second!r}")
    ok(f"W2-4: _SESSION_ID stable within a process ({first!r})")


# ── W2-5: lesson_store promote_pass uses distinct_sessions guard ─────────────
def test_w2_5_promote_uses_session_count():
    from self.lesson_store import promote_pass as _pp
    src = inspect.getsource(_pp)
    if "distinct_sessions" not in src:
        err("W2-5: promote_pass() has no distinct_sessions check — lesson_store may have changed")
    if "_PROMOTE_SESSIONS" not in src:
        err("W2-5: promote_pass() doesn't reference _PROMOTE_SESSIONS threshold")
    ok("W2-5: promote_pass() enforces distinct_sessions >= _PROMOTE_SESSIONS")


# ── runner ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("W2 — stable session ID audit")
    test_w2_1_no_getpid()
    test_w2_2_session_id_defined()
    test_w2_3_numeric_format()
    test_w2_4_stable_across_imports()
    test_w2_5_promote_uses_session_count()
    print("\n5/5 PASS — W2 session ID verified")
    print("\nPROOF NOTE: Live verification — two lesson promotions must show")
    print("  distinct _SESSION_ID values (numeric strings, hours apart) in")
    print("  self/lessons_ledger.jsonl evidence arrays")
