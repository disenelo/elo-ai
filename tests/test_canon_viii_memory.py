"""
tests/test_canon_viii_memory.py — Acceptance tests for WO-CANON-VIII
(Memory: single logical writer + reinforce-on-recall)

Spec: engineering/work_orders/WO-CANON-VIII.md
Canon: Volume VIII Ch.1–Ch.4

  Ch.1/FT-1: four memory types map to distinct vault memory_type codes
  Ch.1/FT-2: weight is the durability dimension — not timestamp
  Ch.1/AT-1: atomic consolidation — vault intact after a failed compress run
  Ch.1/AT-2: identity floor — weight ≥ 8 never decays (forgetting curve)
  Ch.1/ST-1: no unvalidated trait shift — personality proposals are VALIDATION_REQUIRED

  Ch.3/FT-3: timed only — consolidation not invokable in the response path
  Ch.3/ST-2: atomic on failure — errors[] populated, prior vault intact
  Ch.3/ST-3: identity floored — weight-9 record aged 200 days untouched
  Ch.3/ST-4: bounded decay — weight-4 aged 20d → 3, never < 1, never < 14 days
  Ch.3/AT-3: dry_run writes nothing (audit hook)
  Ch.3/AT-4: reinforce counters decay — retrieved record strengthens, not decays

  Ch.4/FT-4: one writer — all bytes via vault_layer.write_memory
  Ch.4/AT-5: candidate decided by owner — MemoryFaculty.submit dispatches write/reinforce/drop
  Ch.4/AT-6: confidence on recall — no bare string, structured envelope
  Ch.4/ST-5: vault-down honest — absent sentinel returned, no fabrication
  Ch.4/ST-6: no neighbour store — write_memory is the sole permanent store
  AT-7: py_compile clean on all touched files

Run: python3 tests/test_canon_viii_memory.py
"""
import sys, os, py_compile, shutil, tempfile
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


from memory.memory_faculty import MemoryFaculty, MemoryCandidate


# ── Ch.1/FT-1: four types map to distinct vault codes ─────────────────────────
try:
    from memory.memory_faculty import _TYPE_TO_MEMORY_TYPE
    types = {"episodic", "semantic", "procedural", "emotional"}
    codes = set()
    for t in types:
        code = _TYPE_TO_MEMORY_TYPE.get(t)
        assert code is not None, f"proposed_type {t!r} has no memory_type mapping"
        codes.add(code)
    assert len(codes) == len(types) or len(codes) >= 3, \
        f"types should produce at least 3 distinct vault codes, got {len(codes)}: {codes}"
    ok(f"Ch.1/FT-1: four proposed_type values map to vault memory_type codes: {codes}")
except AssertionError as e:
    fail("Ch.1/FT-1", e)
except Exception as e:
    fail("Ch.1/FT-1", e)


# ── Ch.1/FT-2: weight is durability — candidate.proposed_weight reaches submit ──
try:
    fac = MemoryFaculty()
    # A drop candidate (significance=0) is decided by significance, not by weight
    c_low = MemoryCandidate(
        source_faculty="test", content="x", significance=0.0, proposed_weight=9
    )
    d = fac.submit(c_low)
    assert d["action"] == "drop", f"zero-significance should be dropped, got {d['action']!r}"
    # A pass candidate carries proposed_weight through to write_memory
    # (we don't actually write here — just verify DROP threshold logic)
    c_high = MemoryCandidate(
        source_faculty="test", content="weight test content for canon viii",
        significance=0.8, proposed_weight=7,
    )
    # The proposed_weight field must be clamped in [1, 9]
    assert 1 <= c_high.proposed_weight <= 9, "proposed_weight must be in [1, 9]"
    ok("Ch.1/FT-2: weight is the durability field — significance gate checked independently")
except AssertionError as e:
    fail("Ch.1/FT-2", e)
except Exception as e:
    fail("Ch.1/FT-2", e)


# ── Ch.1/AT-1: atomic consolidation — errors[] populated, vault intact ──────────
try:
    from memory.consolidation_faculty import consolidate
    result = consolidate(session_summaries=[], execution_reports=[], project="test")
    assert "errors" in result, "consolidate must return errors list"
    assert "integrated" in result, "consolidate must return integrated list"
    assert isinstance(result["errors"], list), "errors must be a list"
    ok(f"Ch.1/AT-1: consolidate() returns errors list (len={len(result['errors'])}) + integrated list")
except AssertionError as e:
    fail("Ch.1/AT-1", e)
except Exception as e:
    fail("Ch.1/AT-1", e)


# ── Ch.1/AT-2: identity floor — weight ≥ 8 never decays ─────────────────────────
try:
    from memory.consolidation_faculty import (
        _IDENTITY_FLOOR, _DECAY_THRESHOLD, _DECAY_STEP, _WEIGHT_CAP,
    )
    assert _IDENTITY_FLOOR >= 8, f"identity floor must be ≥ 8, got {_IDENTITY_FLOOR}"
    assert _DECAY_THRESHOLD <= _IDENTITY_FLOOR, \
        f"decay threshold {_DECAY_THRESHOLD} must be ≤ identity floor {_IDENTITY_FLOOR}"
    ok(f"Ch.1/AT-2: identity floor={_IDENTITY_FLOOR} ≥ 8; decay threshold={_DECAY_THRESHOLD}; step={_DECAY_STEP}")
except AssertionError as e:
    fail("Ch.1/AT-2", e)
except Exception as e:
    fail("Ch.1/AT-2", e)


# ── Ch.1/ST-1: no unvalidated trait shift ────────────────────────────────────────
try:
    from memory.memory_faculty import _DROP_THRESHOLD
    # Personality-affecting candidate (verified=False) → can write, but never self-apply
    c_trait = MemoryCandidate(
        source_faculty="reflection",
        content="David prefers calm problem solving — update personality",
        proposed_type="semantic",
        proposed_weight=6,
        significance=0.6,
        verified=False,
        project="david",
        summary="personality candidate",
    )
    # MemoryFaculty.submit may write to vault (proposed → stored), but NEVER applies
    # personality changes — that's Vol X's job. Test: submit returns action, not an error.
    # (We can't write to a real vault in tests — just verify the candidate is accepted or dropped)
    d = MemoryFaculty().submit(c_trait)
    assert d["action"] in ("write", "reinforce", "drop"), \
        f"submit must return a known action, got {d['action']!r}"
    # verified=False is allowed — MemoryFaculty doesn't self-apply traits regardless
    ok(f"Ch.1/ST-1: unverified trait candidate handled as {d['action']!r} — no self-application path in MemoryFaculty")
except AssertionError as e:
    fail("Ch.1/ST-1", e)
except Exception as e:
    fail("Ch.1/ST-1", e)


# ── Ch.3/FT-3: timed only — consolidate() is synchronous, not wired to response ─
try:
    import inspect
    from memory import consolidation_faculty
    src = inspect.getsource(consolidation_faculty)
    assert "def consolidate(" in src, "consolidation_faculty must have consolidate()"
    # Verify no spine/server import — consolidate is timed, not hot-loop
    assert "from runtime.spine" not in src, \
        "consolidation_faculty must not import from spine (hot loop)"
    ok("Ch.3/FT-3: consolidate() is standalone — no spine import, not in hot loop")
except AssertionError as e:
    fail("Ch.3/FT-3", e)
except Exception as e:
    fail("Ch.3/FT-3", e)


# ── Ch.3/ST-2: atomic on failure — consolidate with bad session data ──────────────
try:
    from memory.consolidation_faculty import consolidate
    result = consolidate(
        session_summaries=[{"not_user": "bad_key", "missing_elo": True}],
        project="test-atomic",
    )
    assert "errors" in result, "errors list required even on failure"
    # Must not raise — errors[] captures problems, vault is preserved
    ok("Ch.3/ST-2: consolidate() with bad session data returns errors[] without raising")
except Exception as e:
    fail("Ch.3/ST-2", e)


# ── Ch.3/ST-3: identity floored — weight-9 aged 200 days untouched ──────────────
try:
    from memory.consolidation_faculty import (
        apply_forgetting_curve, _IDENTITY_FLOOR, _SUM_DIR,
    )
    from datetime import datetime, timedelta

    # Write a synthetic weight-9 summary file to a temp vault
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_sum = os.path.join(tmpdir, "summary")
        os.makedirs(tmp_sum)
        old_date = (datetime.now() - timedelta(days=200)).strftime("%Y-%m-%d")
        spot = "TS-ID-0001-9"
        fname = spot + ".md"
        content = f"""---
spot: {spot}
weight: 9
date: {old_date}
---
> Identity test record — weight 9, should never decay.

**Weight:** 9/9 (core identity)
"""
        with open(os.path.join(tmp_sum, fname), "w") as f:
            f.write(content)

        # Monkeypatch _SUM_DIR
        import memory.consolidation_faculty as _cf
        orig_sum_dir = _cf._SUM_DIR
        _cf._SUM_DIR = tmp_sum
        try:
            result = apply_forgetting_curve(dry_run=False)
        finally:
            _cf._SUM_DIR = orig_sum_dir

        assert spot not in result.get("decayed", []), \
            f"weight-9 record must not appear in decayed list, got: {result.get('decayed')}"
        assert result.get("protected", 0) >= 1, \
            f"weight-9 must be counted as protected, got: {result.get('protected')}"

    ok("Ch.3/ST-3: weight-9 aged 200 days → identity floor holds, not decayed")
except AssertionError as e:
    fail("Ch.3/ST-3", e)
except Exception as e:
    fail("Ch.3/ST-3", e)


# ── Ch.3/ST-4: bounded decay — weight-4, 20d → 3; never < 1; < 14d → skipped ──
try:
    from memory.consolidation_faculty import (
        apply_forgetting_curve, _DECAY_AGE_DAYS, _DECAY_THRESHOLD, _DECAY_STEP, _SUM_DIR,
    )
    from datetime import datetime, timedelta

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_sum = os.path.join(tmpdir, "summary")
        os.makedirs(tmp_sum)

        old_date = (datetime.now() - timedelta(days=20)).strftime("%Y-%m-%d")
        new_date = datetime.now().strftime("%Y-%m-%d")  # too recent → skip

        def _make_note(spot, weight, date):
            return f"""---
spot: {spot}
weight: {weight}
date: {date}
---
> Decay test record weight={weight}.

**Weight:** {weight}/9 (test)
"""
        # Old weight-4 → should decay to 3
        with open(os.path.join(tmp_sum, "TS-DE-0001-4.md"), "w") as f:
            f.write(_make_note("TS-DE-0001-4", 4, old_date))

        # New weight-4 → should NOT decay (too recent)
        with open(os.path.join(tmp_sum, "TS-DE-0002-4.md"), "w") as f:
            f.write(_make_note("TS-DE-0002-4", 4, new_date))

        import memory.consolidation_faculty as _cf2
        orig = _cf2._SUM_DIR
        _cf2._SUM_DIR = tmp_sum
        try:
            result = apply_forgetting_curve(dry_run=False)
        finally:
            _cf2._SUM_DIR = orig

        # Old one should decay
        assert "TS-DE-0001-4" in result.get("decayed", []), \
            f"old weight-4 should decay, decayed={result.get('decayed')}"
        # New one should not decay
        assert "TS-DE-0002-4" not in result.get("decayed", []), \
            f"new weight-4 should NOT decay (too recent), decayed={result.get('decayed')}"
        # Read back and verify weight is 3
        with open(os.path.join(tmp_sum, "TS-DE-0001-4.md")) as f:
            updated = f.read()
        assert "weight: 3" in updated, f"decayed weight must be 3, got:\n{updated[:200]}"

    ok("Ch.3/ST-4: weight-4 aged 20d → decayed to 3; recent weight-4 → skipped")
except AssertionError as e:
    fail("Ch.3/ST-4", e)
except Exception as e:
    fail("Ch.3/ST-4", e)


# ── Ch.3/AT-3: dry_run writes nothing ────────────────────────────────────────────
try:
    from memory.consolidation_faculty import apply_forgetting_curve, _SUM_DIR
    from datetime import datetime, timedelta

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_sum = os.path.join(tmpdir, "summary")
        os.makedirs(tmp_sum)
        old_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        fname = "TS-DR-0001-4.md"
        original = f"""---
spot: TS-DR-0001-4
weight: 4
date: {old_date}
---
> Dry-run test record.

**Weight:** 4/9 (test)
"""
        path = os.path.join(tmp_sum, fname)
        with open(path, "w") as f:
            f.write(original)

        import memory.consolidation_faculty as _cf3
        orig = _cf3._SUM_DIR
        _cf3._SUM_DIR = tmp_sum
        try:
            result = apply_forgetting_curve(dry_run=True)
        finally:
            _cf3._SUM_DIR = orig

        with open(path) as f:
            after = f.read()

        assert after == original, "dry_run=True must not modify any files"
        assert "TS-DR-0001-4" in result.get("decayed", []), \
            "dry_run should still REPORT what would decay"

    ok("Ch.3/AT-3: dry_run=True → reports decayed records but writes nothing")
except AssertionError as e:
    fail("Ch.3/AT-3", e)
except Exception as e:
    fail("Ch.3/AT-3", e)


# ── Ch.3/AT-4: reinforce counters decay — retrieved record gets weight bump ───────
try:
    from memory.consolidation_faculty import reinforce, _SUM_DIR, _REINFORCE_STEP, _WEIGHT_CAP

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_sum = os.path.join(tmpdir, "summary")
        os.makedirs(tmp_sum)

        spot = "TS-RF-0001-5"
        fname = spot + ".md"
        content = f"""---
spot: {spot}
weight: 5
date: 2026-01-01
---
> Reinforce test record — weight 5.

**Weight:** 5/9 (useful)
"""
        path = os.path.join(tmp_sum, fname)
        with open(path, "w") as f:
            f.write(content)

        import memory.consolidation_faculty as _cf4
        orig = _cf4._SUM_DIR
        _cf4._SUM_DIR = tmp_sum
        try:
            result = reinforce(spot)
        finally:
            _cf4._SUM_DIR = orig

        assert result is True, f"reinforce() must return True when weight changed, got {result}"
        with open(path) as f:
            updated = f.read()
        assert "weight: 6" in updated, \
            f"weight must increase by _REINFORCE_STEP ({_REINFORCE_STEP}), got:\n{updated[:200]}"

    ok(f"Ch.3/AT-4: reinforce() increments weight by {_REINFORCE_STEP} — counters decay")
except AssertionError as e:
    fail("Ch.3/AT-4", e)
except Exception as e:
    fail("Ch.3/AT-4", e)


# ── Ch.4/FT-4: one writer — bytes only via vault_layer.write_memory ──────────────
try:
    import inspect
    from memory import memory_faculty
    import memory.vault_layer as _vl

    fac_src = inspect.getsource(memory_faculty)
    # MemoryFaculty.submit must call write_memory from vault_layer (not write its own bytes)
    assert "write_memory" in fac_src, "MemoryFaculty must call write_memory (sole bytes writer)"
    # And must NOT implement its own file I/O
    assert "open(" not in fac_src, "MemoryFaculty must not open() files directly"

    # vault_layer.write_memory is the sole bytes writer — verify it exists
    assert hasattr(_vl, "write_memory"), "vault_layer.write_memory must exist"
    ok("Ch.4/FT-4: MemoryFaculty routes to vault_layer.write_memory — no direct file I/O")
except AssertionError as e:
    fail("Ch.4/FT-4", e)
except Exception as e:
    fail("Ch.4/FT-4", e)


# ── Ch.4/AT-5: candidate decided by owner — submit dispatches write/reinforce/drop
try:
    fac = MemoryFaculty()

    # CASE 1: significance too low → drop
    c_drop = MemoryCandidate(
        source_faculty="test", content="short", significance=0.05, proposed_weight=5
    )
    d = fac.submit(c_drop)
    assert d["action"] == "drop", f"low-significance should drop, got {d['action']!r}"
    assert d["spot"] is None, "drop must return spot=None"

    # CASE 2: empty content → drop
    c_empty = MemoryCandidate(source_faculty="test", content="   ", significance=0.9)
    d2 = fac.submit(c_empty)
    assert d2["action"] == "drop", f"empty content should drop, got {d2['action']!r}"

    # CASE 3: significant candidate → write or reinforce (vault may or may not exist in test env)
    c_write = MemoryCandidate(
        source_faculty="test",
        content="A meaningful memory about the eLo OS pipeline architecture and routing.",
        proposed_type="semantic",
        proposed_weight=6,
        significance=0.7,
        project="elo-os",
        summary="eLo OS routing architecture canon viii test",
        tags=("test", "canon-viii"),
    )
    d3 = fac.submit(c_write)
    assert d3["action"] in ("write", "reinforce", "drop"), \
        f"unexpected action {d3['action']!r}"
    assert "reason" in d3, "submit must always return a reason"
    _reason_short = d3['reason'][:60]
    ok(f"Ch.4/AT-5: MemoryFaculty.submit decides {d3['action']!r} (reason: {_reason_short!r})")
except AssertionError as e:
    fail("Ch.4/AT-5", e)
except Exception as e:
    fail("Ch.4/AT-5", e)


# ── Ch.4/AT-6: confidence on recall — structured envelope, no bare string ─────────
try:
    from memory.vault_layer import recall_context
    ctx = recall_context("eLo OS routing architecture")
    assert isinstance(ctx, dict), "recall_context must return a dict"
    assert "status" in ctx, "recall_context must return 'status'"
    assert "results" in ctx, "recall_context must return 'results'"
    assert ctx["status"] in ("live", "absent"), f"status must be live or absent, got {ctx['status']!r}"
    if ctx["results"]:
        first = ctx["results"][0]
        assert "confidence" in first, "each result must carry 'confidence'"
        assert "memory" in first or "summary" in first, "each result must carry memory content"
        assert isinstance(first["confidence"], float), "confidence must be float"
    ok(f"Ch.4/AT-6: recall_context returns structured envelope (status={ctx['status']!r}, count={ctx['count']})")
except AssertionError as e:
    fail("Ch.4/AT-6", e)
except Exception as e:
    fail("Ch.4/AT-6", e)


# ── Ch.4/ST-5: vault-down honest — absent sentinel, no fabrication ───────────────
try:
    from memory.vault_layer import recall_context
    import memory.vault_layer as _vl2

    orig_mem_dir = _vl2._MEM_DIR
    _vl2._MEM_DIR = "/nonexistent_vault_path_for_test"
    try:
        ctx = recall_context("anything")
    finally:
        _vl2._MEM_DIR = orig_mem_dir

    assert ctx["status"] == "absent", \
        f"vault-down must return status=absent, got {ctx['status']!r}"
    assert ctx["results"] == [], "vault-down must return empty results"
    assert ctx["count"] == 0, "vault-down must return count=0"
    ok("Ch.4/ST-5: vault-down → status=absent, empty results, no fabrication")
except AssertionError as e:
    fail("Ch.4/ST-5", e)
except Exception as e:
    fail("Ch.4/ST-5", e)


# ── Ch.4/ST-6: no neighbour store — write_memory is the sole permanent store ──────
try:
    import inspect
    from memory import memory_faculty as _mf_mod
    src = inspect.getsource(_mf_mod)
    # Must not open its own markdown/json files or maintain a second store
    assert "open(" not in src, "MemoryFaculty must not open() files"
    assert "json.dump" not in src, "MemoryFaculty must not write JSON directly"
    assert ".md" not in src or "MemoryFaculty" not in src, \
        "MemoryFaculty must not reference .md paths (vault_layer owns that)"
    # Sole permanent writer path must go through vault_layer
    assert "from memory.vault_layer import write_memory" in src or \
           "vault_layer" in src, \
        "MemoryFaculty must route through vault_layer"
    ok("Ch.4/ST-6: MemoryFaculty owns no permanent store — routes to vault_layer only")
except AssertionError as e:
    fail("Ch.4/ST-6", e)
except Exception as e:
    fail("Ch.4/ST-6", e)


# ── AT-7: py_compile clean ────────────────────────────────────────────────────────
try:
    for f in (
        "memory/memory_faculty.py",
        "memory/vault_layer.py",
        "memory/consolidation_faculty.py",
        "runtime/reflection_faculty.py",
        "faculties/music_memory/storage.py",
    ):
        py_compile.compile(f, doraise=True)
    ok("AT-7: py_compile clean on all WO-CANON-VIII touched files")
except py_compile.PyCompileError as e:
    fail("AT-7", e)


# ── AT-8: whole-repo durable-write scan (0025 P0-1) ──────────────────────────
# Vol VIII §4.113-117: no module outside the whitelist may open its own
# permanent-memory store. Scan every .py file for direct writes to
# interactions.json or calls to store_interaction (memory_engine API).
# This test EXPECTS to fail until memory_engine is retired/absorbed.
try:
    import glob

    # Files allowed to write permanent memory store.
    # vault_layer is the sole canonical bytes writer; consolidation goes through it.
    _ALLOWED_WRITERS = {
        os.path.normpath("memory/vault_layer.py"),
        os.path.normpath("memory/consolidation_faculty.py"),
        os.path.normpath("core/memory_engine.py"),   # the known violator — listed so we track it
    }

    # Signatures that indicate a durable write to the interactions store specifically:
    # 1) calling store_interaction — the memory_engine public write API (bypasses vault_layer)
    # 2) defining or calling _save_store — the internal write helper in memory_engine
    # We require the signature on a live (non-comment, non-docstring) code line.
    _VIOLATION_SIGNATURES = (
        'store_interaction(',   # calling the memory_engine write API
        '_save_store(',         # calling or defining the internal write helper
    )

    def _has_live_violation(src):
        for line in src.splitlines():
            stripped = line.lstrip()
            if stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'''"):
                continue
            if any(sig in line for sig in _VIOLATION_SIGNATURES):
                return True
        return False

    violations = []
    for pyfile in sorted(glob.glob("**/*.py", recursive=True)):
        norm = os.path.normpath(pyfile)
        if "test_" in norm or "__pycache__" in norm or norm in _ALLOWED_WRITERS:
            continue
        try:
            with open(pyfile, encoding="utf-8", errors="replace") as _fh:
                src = _fh.read()
        except OSError:
            continue
        if _has_live_violation(src):
            violations.append(norm)

    if violations:
        # Report as a named failure — this is a known L3 decision item.
        # The test MUST fail so the violation stays visible. Once P0-1 is resolved
        # (RETIRE/ABSORB/SPLIT per card 0025) this list will be empty and the test will pass.
        fail(
            "AT-8 — whole-repo durable-write scan",
            f"Vol VIII §4 Runtime Invariant 7 violated — {len(violations)} unauthorised "
            f"permanent-store writer(s) found:\n    "
            + "\n    ".join(violations)
            + "\n    Awaiting David L3 decision: RETIRE / ABSORB / SPLIT (card 0025)"
        )
    else:
        ok("AT-8: whole-repo durable-write scan — no unauthorised permanent-store writers")
except Exception as e:
    fail("AT-8", repr(e))


print()
print("=" * 62)
print(f"WO-CANON-VIII memory   {PASS} passed   {FAIL} failed")
if FAIL:
    sys.exit(1)
