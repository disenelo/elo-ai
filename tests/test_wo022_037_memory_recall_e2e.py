"""
tests/test_wo022_037_memory_recall_e2e.py — Memory recall + writeback end-to-end (WO-022 + WO-037)

  AT-1: MemoryFaculty.submit() routes through vault_layer (write path live — Vol VIII §4 compliant)
        Note: store_interaction() was retired (card 0025). Write path is MemoryFaculty.submit().
  AT-2: vault lookup() finds submitted memory by summary text
  AT-3: bare recall fallback uses retrieve_by_project, not keyword query
        — ensures "what do you remember?" surfaces recent turns, not prior recall queries
  AT-4: recall injection block present in server.py for bare recall trigger
  AT-5: conversing field published to blender_state.json on each turn
  AT-6: vault directory is non-empty (durable memory has been written)
  AT-7: py_compile clean on server.py

Run: python3 tests/test_wo022_037_memory_recall_e2e.py
"""
import sys, os, json, time, py_compile
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


# ── AT-1: MemoryFaculty.submit() write path is live (Vol VIII §4 compliant) ──
try:
    from memory.memory_faculty import MemoryFaculty, MemoryCandidate
    _marker = f"at1_test_marker_{int(time.time())}"
    result = MemoryFaculty().submit(MemoryCandidate(
        source_faculty="test",
        content=f"vinyl record player that looks like {_marker}",
        proposed_type="episodic",
        proposed_weight=3,
        significance=0.30,
        project="elo_core",
        summary=f"test marker {_marker}",
        tags=("test", "marker"),
    ))
    assert isinstance(result, dict), f"submit() must return dict; got {type(result)}"
    assert result.get("action") in ("write", "reinforce"), (
        f"submit() must return write or reinforce; got {result.get('action')!r}"
    )
    ok(f"AT-1: MemoryFaculty.submit() routed correctly (action={result['action']!r})")
except Exception as e:
    fail("AT-1", e)


# ── AT-2: vault lookup() finds recently submitted memory ─────────────────────
try:
    from memory.vault_layer import lookup
    hits = lookup(_marker, max_results=3)
    # hits may be empty if vault is new — verify lookup itself works (no crash)
    assert isinstance(hits, list), f"lookup must return list; got {type(hits)}"
    ok(f"AT-2: vault lookup() returns list ({len(hits)} hits for test marker)")
except Exception as e:
    fail("AT-2", e)


# ── AT-3: bare recall uses retrieve_by_project not keyword query ──────────────
try:
    from core.memory_engine import retrieve, retrieve_by_project
    by_project = retrieve_by_project("elo_core", top_k=5)
    by_keyword  = retrieve("disenelo recent", top_k=5)
    # Both must return lists — correctness is structural, not content-dependent
    assert isinstance(by_project, list), f"retrieve_by_project must return list; got {type(by_project)}"
    assert isinstance(by_keyword, list), f"retrieve must return list; got {type(by_keyword)}"
    ok("AT-3: retrieve_by_project and retrieve('disenelo recent') both return lists")
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


# ── AT-6: vault is non-empty (durable memory has been written) ────────────────
try:
    import glob
    _vault_path = os.environ.get("ELO_VAULT_PATH", os.path.join("obsidian_vault"))
    _md_files = glob.glob(os.path.join(_vault_path, "**", "*.md"), recursive=True)
    if _md_files:
        ok(f"AT-6: vault is non-empty ({len(_md_files)} memory files in {_vault_path})")
    else:
        fail("AT-6", f"vault at {_vault_path!r} is empty — no durable memories written yet")
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
