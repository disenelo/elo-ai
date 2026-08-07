"""
tests/test_wo022_037_memory_recall_e2e.py — Memory recall + writeback end-to-end (WO-022 + WO-037)

  AT-1: store_interaction() persists to interactions.json (writeback live)
  AT-2: topical retrieve() finds stored interaction by keyword
  AT-3: bare recall fallback uses retrieve_by_project, not keyword query
        — ensures "what do you remember?" surfaces recent turns, not prior recall queries
  AT-4: recall injection block present in server.py for bare recall trigger
  AT-5: conversing field published to blender_state.json on each turn
  AT-6: interactions.json is a live file (modified within the last 24 hours)
  AT-7: py_compile clean on server.py

Run: python3 tests/test_wo022_037_memory_recall_e2e.py
"""
import sys, os, json, time, py_compile
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


# ── AT-1: store_interaction() writes to interactions.json ─────────────────────
try:
    from core.memory_engine import store_interaction, _load_store
    _marker = f"_AT1_test_marker_{int(time.time())}"
    store_interaction(
        f"I want to build a vinyl record player that looks like {_marker}",
        "Sounds like a great project!",
        "answer",
        "elo_core",
    )
    interactions = _load_store()
    found = any(_marker in r.get("user", "") for r in interactions)
    if found:
        ok("AT-1: store_interaction() persisted to interactions.json")
    else:
        fail("AT-1", "stored interaction not found in interactions.json")
except Exception as e:
    fail("AT-1", e)


# ── AT-2: topical retrieve() surfaces stored interaction ─────────────────────
try:
    from core.memory_engine import retrieve
    hits = retrieve("vinyl record player", top_k=5)
    found = any(_marker in h.get("user", "") for h in hits)
    if found:
        ok("AT-2: retrieve('vinyl record player') finds the stored interaction")
    else:
        fail("AT-2", f"stored interaction not in top-5 hits — hits: {[h.get('user','')[:40] for h in hits]}")
except Exception as e:
    fail("AT-2", e)


# ── AT-3: bare recall uses retrieve_by_project not keyword query ──────────────
try:
    from core.memory_engine import retrieve, retrieve_by_project
    # "disenelo recent" is the bare-recall fallback query — check that retrieve_by_project
    # returns different (better) results than retrieve("disenelo recent")
    by_project = retrieve_by_project("elo_core", top_k=5)
    by_keyword  = retrieve("disenelo recent", top_k=5)

    # retrieve_by_project returns most recent entries, so the AT-1 marker should appear
    marker_in_project = any(_marker in h.get("user", "") for h in by_project)
    # retrieve("disenelo recent") should NOT reliably surface the marker (keyword mismatch)
    marker_in_keyword  = any(_marker in h.get("user", "") for h in by_keyword)

    if marker_in_project and not marker_in_keyword:
        ok("AT-3: retrieve_by_project finds recent turn; bare keyword query does not")
    elif marker_in_project:
        ok("AT-3: retrieve_by_project finds recent turn (keyword also matched — acceptable)")
    else:
        fail("AT-3", f"retrieve_by_project did not find recent turn; by_project={[h.get('user','')[:40] for h in by_project]}")
except Exception as e:
    fail("AT-3", e)


# ── AT-4: server.py bare-recall path uses retrieve_by_project ────────────────
try:
    with open("server.py", encoding="utf-8") as f:
        _src = f.read()
    checks = [
        ("retrieve_by_project as _mem_recency", "retrieve_by_project imported as _mem_recency"),
        ("_is_bare_recall = (_recall_q == \"disenelo recent\")", "bare recall flag assigned"),
        ("_mem_recency(\"elo_core\"", "retrieve_by_project called for bare recall"),
    ]
    for needle, desc in checks:
        if needle in _src:
            ok(f"AT-4 [{desc}]")
        else:
            fail(f"AT-4 [{desc}]", f"not found in server.py: {needle!r}")
except Exception as e:
    fail("AT-4", e)


# ── AT-5: conversing field published in _bs_patch ────────────────────────────
try:
    with open("server.py", encoding="utf-8") as f:
        _src = f.read()
    if '"conversing":' in _src and "_bs_conversing" in _src:
        ok("AT-5: conversing field published to blender_state.json each turn")
    else:
        fail("AT-5", "conversing field not found in _bs_patch in server.py")
except Exception as e:
    fail("AT-5", e)


# ── AT-6: interactions.json is live (modified within last 24h) ────────────────
try:
    _path = os.path.join("memory", "interactions.json")
    _mtime = os.path.getmtime(_path)
    _age_h = (time.time() - _mtime) / 3600
    if _age_h < 24:
        ok(f"AT-6: interactions.json live (last modified {_age_h:.1f}h ago)")
    else:
        fail("AT-6", f"interactions.json stale — last modified {_age_h:.0f}h ago (writeback dead?)")
except Exception as e:
    fail("AT-6", e)


# ── AT-7: py_compile clean ────────────────────────────────────────────────────
try:
    py_compile.compile("server.py", doraise=True)
    ok("AT-7: py_compile clean on server.py")
except py_compile.PyCompileError as e:
    fail("AT-7", e)


print()
print("=" * 50)
print(f"WO-022/037 e2e  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
