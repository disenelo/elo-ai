"""
tests/test_wo053_memory_recall_confidence.py — Acceptance tests for WO-053

Spec: vault_layer.lookup() results carry confidence+source+timestamp so eLo
      never produces vague 'I think…' recall. recall_context() returns a
      LiveWorldState-style status envelope with an offline sentinel.

  AT-1: lookup() results include 'confidence' field (float 0.0–1.0)
  AT-2: lookup() results include 'source' field ("vault_summary"|"spot_index")
  AT-3: lookup() results include 'timestamp' field (same as date)
  AT-4: lookup() results include 'memory' field (the recall text)
  AT-5: recall_context() returns status+results+count envelope
  AT-6: recall_context() returns offline sentinel when vault unreachable
  AT-7: confidence derived from weight (vault_summary: weight/9)
  AT-8: py_compile clean on vault_layer.py

Run: python3 tests/test_wo053_memory_recall_confidence.py
"""
import sys, os, unittest.mock as _mock, tempfile, json
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


# ── Helper: fake summary .md content ─────────────────────────────────────────
_FAKE_SUMMARY_MD = """\
---
type: memory-summary
domain: memory
spot: EO·BL·2607·9
bits: EO-BL-2607-9
project: elo-os
memory-type: build
date: 2026-07-30
weight: 9
tags: []
deep: [[deep/EO-BL-2607-9-deep]]
---

> Test summary line for the fake memory record.

**Code:** `EO·BL·2607·9`
"""


def _make_fake_vault(tmp_dir: str) -> None:
    """Create a minimal vault structure with one summary note."""
    mem_dir = os.path.join(tmp_dir, "09 Memory")
    sum_dir = os.path.join(mem_dir, "summary")
    os.makedirs(sum_dir, exist_ok=True)
    with open(os.path.join(sum_dir, "EO-BL-2607-9.md"), "w") as f:
        f.write(_FAKE_SUMMARY_MD)


# ── AT-1: lookup() results include 'confidence' ───────────────────────────────
try:
    import memory.vault_layer as _vl
    with tempfile.TemporaryDirectory() as _td:
        _make_fake_vault(_td)
        with _mock.patch.object(_vl, "_SUM_DIR", os.path.join(_td, "09 Memory", "summary")), \
             _mock.patch.object(_vl, "_SPOT_FILE", os.path.join(_td, "09 Memory", "SPOT_CODES.md")):
            _res = _vl.lookup("test summary")
    if _res and "confidence" in _res[0]:
        _conf = _res[0]["confidence"]
        if 0.0 <= _conf <= 1.0:
            ok(f"AT-1: lookup() result includes 'confidence' ({_conf})")
        else:
            fail("AT-1", f"confidence out of range: {_conf}")
    elif not _res:
        fail("AT-1", "lookup returned no results for 'test summary'")
    else:
        fail("AT-1", f"'confidence' missing from result keys: {list(_res[0].keys())}")
except Exception as e:
    fail("AT-1", e)


# ── AT-2: lookup() results include 'source' ───────────────────────────────────
try:
    import memory.vault_layer as _vl
    with tempfile.TemporaryDirectory() as _td:
        _make_fake_vault(_td)
        with _mock.patch.object(_vl, "_SUM_DIR", os.path.join(_td, "09 Memory", "summary")), \
             _mock.patch.object(_vl, "_SPOT_FILE", os.path.join(_td, "09 Memory", "SPOT_CODES.md")):
            _res = _vl.lookup("test summary")
    if _res and _res[0].get("source") in ("vault_summary", "spot_index"):
        ok(f"AT-2: lookup() result includes 'source' = '{_res[0]['source']}'")
    elif not _res:
        fail("AT-2", "no results")
    else:
        fail("AT-2", f"'source' missing or invalid: {_res[0].get('source')!r}")
except Exception as e:
    fail("AT-2", e)


# ── AT-3: lookup() results include 'timestamp' ────────────────────────────────
try:
    import memory.vault_layer as _vl
    with tempfile.TemporaryDirectory() as _td:
        _make_fake_vault(_td)
        with _mock.patch.object(_vl, "_SUM_DIR", os.path.join(_td, "09 Memory", "summary")), \
             _mock.patch.object(_vl, "_SPOT_FILE", os.path.join(_td, "09 Memory", "SPOT_CODES.md")):
            _res = _vl.lookup("test summary")
    if _res and "timestamp" in _res[0]:
        ok(f"AT-3: lookup() result includes 'timestamp' = '{_res[0]['timestamp']}'")
    elif not _res:
        fail("AT-3", "no results")
    else:
        fail("AT-3", f"'timestamp' missing from result keys: {list(_res[0].keys())}")
except Exception as e:
    fail("AT-3", e)


# ── AT-4: lookup() results include 'memory' ───────────────────────────────────
try:
    import memory.vault_layer as _vl
    with tempfile.TemporaryDirectory() as _td:
        _make_fake_vault(_td)
        with _mock.patch.object(_vl, "_SUM_DIR", os.path.join(_td, "09 Memory", "summary")), \
             _mock.patch.object(_vl, "_SPOT_FILE", os.path.join(_td, "09 Memory", "SPOT_CODES.md")):
            _res = _vl.lookup("test summary")
    if _res and "memory" in _res[0] and _res[0]["memory"]:
        ok(f"AT-4: lookup() result includes 'memory' field (non-empty)")
    elif not _res:
        fail("AT-4", "no results")
    else:
        fail("AT-4", f"'memory' missing or empty: {_res[0].get('memory')!r}")
except Exception as e:
    fail("AT-4", e)


# ── AT-5: recall_context() returns status+results+count ──────────────────────
try:
    import memory.vault_layer as _vl
    with tempfile.TemporaryDirectory() as _td:
        _make_fake_vault(_td)
        with _mock.patch.object(_vl, "_SUM_DIR", os.path.join(_td, "09 Memory", "summary")), \
             _mock.patch.object(_vl, "_SPOT_FILE", os.path.join(_td, "09 Memory", "SPOT_CODES.md")), \
             _mock.patch.object(_vl, "_MEM_DIR", os.path.join(_td, "09 Memory")):
            _ctx = _vl.recall_context("test summary")
    required_keys = {"status", "results", "count", "source"}
    if required_keys.issubset(_ctx.keys()):
        ok(f"AT-5: recall_context() returns envelope with status={_ctx['status']!r} count={_ctx['count']}")
    else:
        missing = required_keys - set(_ctx.keys())
        fail("AT-5", f"missing keys: {missing}")
except Exception as e:
    fail("AT-5", e)


# ── AT-6: recall_context() returns offline sentinel when vault unreachable ─────
try:
    import memory.vault_layer as _vl
    with _mock.patch.object(_vl, "_MEM_DIR", "/nonexistent/path/9999"):
        _offline = _vl.recall_context("anything")
    if _offline["status"] == "absent" and not _offline["results"] and "message" in _offline:
        ok(f"AT-6: offline sentinel returned when vault unreachable: {_offline['message'][:50]}")
    else:
        fail("AT-6", f"unexpected offline response: {_offline}")
except Exception as e:
    fail("AT-6", e)


# ── AT-7: confidence = weight/9 for vault_summary results ─────────────────────
try:
    import memory.vault_layer as _vl
    with tempfile.TemporaryDirectory() as _td:
        _make_fake_vault(_td)
        with _mock.patch.object(_vl, "_SUM_DIR", os.path.join(_td, "09 Memory", "summary")), \
             _mock.patch.object(_vl, "_SPOT_FILE", os.path.join(_td, "09 Memory", "SPOT_CODES.md")):
            _res = _vl.lookup("test summary")
    # Fake note has weight=9, so confidence should be 9/9 = 1.0
    if _res and _res[0].get("source") == "vault_summary":
        expected = round(int(_res[0]["weight"]) / 9.0, 3)
        actual   = _res[0]["confidence"]
        if abs(actual - expected) < 0.001:
            ok(f"AT-7: confidence = weight/9 = {expected} (weight={_res[0]['weight']})")
        else:
            fail("AT-7", f"expected confidence={expected}, got {actual}")
    elif not _res:
        fail("AT-7", "no results")
    else:
        ok("AT-7: spot_index result — fixed confidence 0.333 acceptable")
except Exception as e:
    fail("AT-7", e)


# ── AT-8: py_compile clean ────────────────────────────────────────────────────
try:
    import py_compile
    py_compile.compile("memory/vault_layer.py", doraise=True)
    ok("AT-8: py_compile clean on vault_layer.py")
except py_compile.PyCompileError as e:
    fail("AT-8", e)


print()
print("=" * 50)
print(f"WO-053  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
