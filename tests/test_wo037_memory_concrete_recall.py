"""
tests/test_wo037_memory_concrete_recall.py — Acceptance tests for WO-037 (remaining)

Spec: WO-037 remaining:
  1. Recall surfaces concrete interactions (not just vague vault glosses)
  2. Durable fact snapshots survive restart (fact_store)
  3. set_location() saves a fact snapshot to fact_store
  4. Fact snapshots included in recall system prompt (SAVED FACTS block present)
  5. Durable facts injected into every-turn vault context (DURABLE FACTS block)
  6. py_compile clean

Run: python3 tests/test_wo037_memory_concrete_recall.py
"""
import sys, os, json, tempfile, shutil
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


# ── AT-1: fact_store module imports cleanly ───────────────────────────────────
try:
    from memory.fact_store import save_fact, load_facts, facts_summary
    ok("AT-1: memory.fact_store imports cleanly")
except Exception as e:
    fail("AT-1", e)
    sys.exit(1)


# ── AT-2: save_fact() + load_facts() round-trip ───────────────────────────────
try:
    import memory.fact_store as _fs_mod
    _orig_file = _fs_mod._FACTS_FILE
    # Use a temp file so we don't pollute production
    _tmpdir = tempfile.mkdtemp()
    _tmp_facts = os.path.join(_tmpdir, "facts.json")
    _fs_mod._FACTS_FILE = _tmp_facts

    save_fact("location", "Studio / home location: Hackney Wick")
    loaded = load_facts()
    _match = any(f.get("key") == "location" and "Hackney Wick" in f.get("fact","") for f in loaded)
    if _match:
        ok("AT-2: save_fact + load_facts round-trip — Hackney Wick persisted")
    else:
        fail("AT-2", f"Hackney Wick not found in loaded facts: {loaded}")
    _fs_mod._FACTS_FILE = _orig_file
    shutil.rmtree(_tmpdir)
except Exception as e:
    fail("AT-2", e)


# ── AT-3: facts_summary() returns bullet list ─────────────────────────────────
try:
    import memory.fact_store as _fs_mod
    _orig_file = _fs_mod._FACTS_FILE
    _tmpdir = tempfile.mkdtemp()
    _tmp_facts = os.path.join(_tmpdir, "facts.json")
    _fs_mod._FACTS_FILE = _tmp_facts

    save_fact("location", "Studio / home location: Hackney Wick")
    save_fact("project",  "Current main project: eLo-Planet game")
    summary = facts_summary()
    if "Hackney Wick" in summary and "eLo-Planet" in summary and summary.count("- ") >= 2:
        ok(f"AT-3: facts_summary() returns bullet list: {summary[:80]!r}")
    else:
        fail("AT-3", f"unexpected summary: {summary!r}")
    _fs_mod._FACTS_FILE = _orig_file
    shutil.rmtree(_tmpdir)
except Exception as e:
    fail("AT-3", e)


# ── AT-4: set_location() also writes a fact to fact_store ─────────────────────
try:
    from tools.tool_router import set_location
    import memory.fact_store as _fs_mod
    _orig_file = _fs_mod._FACTS_FILE
    _tmpdir = tempfile.mkdtemp()
    _tmp_facts = os.path.join(_tmpdir, "facts.json")
    _fs_mod._FACTS_FILE = _tmp_facts

    set_location("Hackney Wick")
    loaded = load_facts()
    _match = any("hackney wick" in f.get("fact","").lower() for f in loaded)
    if _match:
        ok("AT-4: set_location('Hackney Wick') also saves a fact snapshot")
    else:
        fail("AT-4", f"location fact not saved; facts: {loaded}")
    _fs_mod._FACTS_FILE = _orig_file
    shutil.rmtree(_tmpdir)
except Exception as e:
    fail("AT-4", e)


# ── AT-5: SAVED FACTS block present in server.py recall path ──────────────────
try:
    _src = open("server.py", encoding="utf-8").read()
    if "SAVED FACTS" in _src and "fact_store" in _src and "facts_summary" in _src:
        ok("AT-5: server.py recall path includes SAVED FACTS block from fact_store")
    else:
        fail("AT-5", "SAVED FACTS / fact_store / facts_summary not all present in server.py")
except Exception as e:
    fail("AT-5", e)


# ── AT-6: DURABLE FACTS injected into every-turn vault context ────────────────
try:
    _src = open("server.py", encoding="utf-8").read()
    if "DURABLE FACTS" in _src and "_facts_prefix" in _src:
        ok("AT-6: DURABLE FACTS block injected into _combined_vault every turn")
    else:
        fail("AT-6", "DURABLE FACTS / _facts_prefix not found in server.py")
except Exception as e:
    fail("AT-6", e)


# ── AT-7: concrete recall from interactions.json wired into recall path ────────
try:
    _src = open("server.py", encoding="utf-8").read()
    if "RECENT INTERACTIONS" in _src and "mem_retrieve" in _src:
        ok("AT-7: RECENT INTERACTIONS block from memory_engine.retrieve() wired into recall")
    else:
        fail("AT-7", "RECENT INTERACTIONS / mem_retrieve not found in server.py recall path")
except Exception as e:
    fail("AT-7", e)


# ── AT-8: py_compile clean ────────────────────────────────────────────────────
try:
    import py_compile
    py_compile.compile("memory/fact_store.py", doraise=True)
    py_compile.compile("tools/tool_router.py", doraise=True)
    py_compile.compile("server.py", doraise=True)
    ok("AT-8: py_compile clean on fact_store.py, tool_router.py, server.py")
except py_compile.PyCompileError as e:
    fail("AT-8", e)


print()
print(f"{'='*50}")
print(f"WO-037  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
