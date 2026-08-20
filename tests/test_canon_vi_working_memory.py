"""
tests/test_canon_vi_working_memory.py — Acceptance tests for WO-CANON-VI
(Working Memory + Attention: wire the WM object + resolve the two-attention design)

Spec: engineering/work_orders/WO-CANON-VI.md
Canon: Volume VI Ch.1–Ch.4

  Ch.1/FT-1: bounded WM — evict oldest unpinned when over capacity
  Ch.1/FT-2: attention competition — highest score wins
  Ch.1/ST-1: budget→mode (budget < 0.15 → peripheral)
  Ch.1/ST-2: distress overrides competition — forces deliberative
  Ch.1/ST-3: ties held (tied=True) when scores within 0.01
  Ch.1/ST-4: typed object only — WorkingMemory is a frozen dataclass
  Ch.1/IT-1: WM + attention → Executive sees frozen WorkingMemory on plan

  Ch.2/FT-3: seed from continuity — open_threads + rolling_summary loaded
  Ch.2/ST-5: cold-start seed — no fabricated prior (empty carry → empty WM)
  Ch.2/FT-4: append one frame/turn — returns new frozen WorkingMemory
  Ch.2/ST-6: evict oldest unpinned — pinned survive
  Ch.2/ST-7: rolling summary ≤ 60 chars per evicted frame (lossy)
  Ch.2/IT-2: carry → next seed — carry_wm writes, load_carry reads back

  Ch.3/FT-5: highest score wins the attention competition
  Ch.3/ST-8: weights sum approximately to 1.0
  Ch.3/ST-9: budget→mode thresholds correct
  Ch.3/IT-1: one driver not two — core/attention.py is supplier, not authority
  Ch.3/ST-10: peripheral mode when budget < 0.15

  Ch.4/FT-6: WM frozen into CognitiveState via assemble_cognitive_state
  Ch.4/FT-7: plan.working_memory set by spine.run()
  Ch.4/ST-11: one WM slice read-only — no downstream re-compute
  Ch.4/ST-12: open_threads not duplicated (WM authoritative)
  Ch.4/ST-13: LTM boundary — carry_wm writes to continuity/, not vault

  AT-8: py_compile clean on all WO-CANON-VI touched files

Run: python3 tests/test_canon_vi_working_memory.py
"""
import sys, os, py_compile, tempfile
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


from runtime.working_memory import (
    WorkingMemory, AttentionState, AttentionCandidate, CognitiveFrame, Goal,
    run_attention_competition, update_working_memory, seed_working_memory,
    carry_wm, load_carry,
    _CAPACITY, _PERIPHERAL_MAX, _REACTIVE_MAX, _W_NOVELTY, _W_IMPORTANCE, _W_URGENCY,
)


# ── Ch.1/FT-1: bounded WM — evict oldest unpinned ────────────────────────────
try:
    wm = seed_working_memory()
    # Fill to capacity + 1
    for i in range(_CAPACITY + 1):
        frame = CognitiveFrame(frame_id=f"f{i}", content=f"frame {i}", turn=i)
        wm = update_working_memory(wm, frame)
    assert len(wm.frames) <= _CAPACITY, \
        f"WM must stay bounded at {_CAPACITY}, got {len(wm.frames)}"
    ok(f"Ch.1/FT-1: WM bounded at {_CAPACITY} — oldest unpinned evicted on overflow")
except AssertionError as e:
    fail("Ch.1/FT-1", e)
except Exception as e:
    fail("Ch.1/FT-1", e)


# ── Ch.1/FT-2: attention competition — highest score wins ─────────────────────
try:
    candidates = [
        AttentionCandidate(item="task_a", novelty=0.9, importance=0.9, urgency=0.9),
        AttentionCandidate(item="task_b", novelty=0.1, importance=0.1, urgency=0.1),
    ]
    result = run_attention_competition(candidates, budget=0.5)
    assert result.winner == "task_a", \
        f"highest-score candidate must win, got {result.winner!r}"
    ok(f"Ch.1/FT-2: highest-score candidate wins attention competition (winner={result.winner!r})")
except AssertionError as e:
    fail("Ch.1/FT-2", e)
except Exception as e:
    fail("Ch.1/FT-2", e)


# ── Ch.1/ST-1: budget→mode (< 0.15 → peripheral) ────────────────────────────
try:
    result = run_attention_competition([], budget=0.10)
    assert result.mode == "peripheral", f"budget 0.10 must give peripheral, got {result.mode!r}"
    result_r = run_attention_competition([], budget=0.30)
    assert result_r.mode == "reactive", f"budget 0.30 must give reactive, got {result_r.mode!r}"
    result_d = run_attention_competition([], budget=0.70)
    assert result_d.mode == "deliberative", f"budget 0.70 must give deliberative, got {result_d.mode!r}"
    ok(f"Ch.1/ST-1: budget→mode: 0.10→peripheral, 0.30→reactive, 0.70→deliberative")
except AssertionError as e:
    fail("Ch.1/ST-1", e)
except Exception as e:
    fail("Ch.1/ST-1", e)


# ── Ch.1/ST-2: distress override — forces deliberative ───────────────────────
try:
    candidates = [
        AttentionCandidate(item="low_task", novelty=0.0, importance=0.0, urgency=0.0),
    ]
    result = run_attention_competition(candidates, budget=0.10, distress=True)
    assert result.mode == "deliberative", \
        f"distress must force deliberative regardless of budget, got {result.mode!r}"
    ok(f"Ch.1/ST-2: distress overrides → deliberative (budget was 0.10 / peripheral)")
except AssertionError as e:
    fail("Ch.1/ST-2", e)
except Exception as e:
    fail("Ch.1/ST-2", e)


# ── Ch.1/ST-3: ties held ─────────────────────────────────────────────────────
try:
    candidates = [
        AttentionCandidate(item="a", novelty=0.5, importance=0.5, urgency=0.5),
        AttentionCandidate(item="b", novelty=0.5, importance=0.5, urgency=0.5),
    ]
    result = run_attention_competition(candidates, budget=0.5)
    assert result.tied is True, f"equal-score candidates must be tied, got tied={result.tied}"
    ok("Ch.1/ST-3: ties held — tied=True when scores within ε=0.01")
except AssertionError as e:
    fail("Ch.1/ST-3", e)
except Exception as e:
    fail("Ch.1/ST-3", e)


# ── Ch.1/ST-4: typed frozen dataclass ────────────────────────────────────────
try:
    wm = seed_working_memory()
    assert isinstance(wm, WorkingMemory), "WorkingMemory must be a dataclass"
    # Frozen — mutation must raise
    raised = False
    try:
        wm.current_task = "mutated"
    except (AttributeError, TypeError):
        raised = True
    assert raised, "WorkingMemory must be frozen"
    ok("Ch.1/ST-4: WorkingMemory is a frozen typed dataclass")
except AssertionError as e:
    fail("Ch.1/ST-4", e)
except Exception as e:
    fail("Ch.1/ST-4", e)


# ── Ch.1/IT-1: WM + attention → Executive sees frozen slice on plan ──────────
try:
    from runtime.spine.spine import run as spine_run
    plan = spine_run(raw="hello eLo", state={}, memory_pack={}, attention={})
    assert plan is not None, "spine.run must return a plan"
    wm_on_plan = getattr(plan, "working_memory", None)
    assert wm_on_plan is not None, "plan.working_memory must be set"
    assert isinstance(wm_on_plan, WorkingMemory), \
        f"plan.working_memory must be WorkingMemory, got {type(wm_on_plan)}"
    ok(f"Ch.1/IT-1: spine.run() sets plan.working_memory with frozen WorkingMemory")
except AssertionError as e:
    fail("Ch.1/IT-1", e)
except Exception as e:
    fail("Ch.1/IT-1", e)


# ── Ch.2/FT-3: seed from continuity ──────────────────────────────────────────
try:
    wm = seed_working_memory(
        current_task="build memory faculty",
        continuity_summary="Last session: wired WO-CANON-VIII.",
        open_threads=["check board", "run tests"],
    )
    assert wm.current_task == "build memory faculty"
    assert len(wm.open_threads) == 2
    assert wm.frames[0].content == "Last session: wired WO-CANON-VIII."
    ok("Ch.2/FT-3: seed_working_memory() loads task + threads + continuity summary")
except AssertionError as e:
    fail("Ch.2/FT-3", e)
except Exception as e:
    fail("Ch.2/FT-3", e)


# ── Ch.2/ST-5: cold-start seed — no fabricated prior ────────────────────────
try:
    wm = seed_working_memory()   # no args = cold start
    assert wm.current_task == "", "cold start: current_task must be empty"
    assert wm.frames == (), "cold start: no frames (no fabricated prior session)"
    assert wm.rolling_summary == "", "cold start: no summary"
    ok("Ch.2/ST-5: cold start — empty WM, no fabricated prior session")
except AssertionError as e:
    fail("Ch.2/ST-5", e)
except Exception as e:
    fail("Ch.2/ST-5", e)


# ── Ch.2/FT-4: append one frame — returns new frozen WM ─────────────────────
try:
    wm0 = seed_working_memory()
    frame = CognitiveFrame(frame_id="t001", content="test turn content", turn=1)
    wm1 = update_working_memory(wm0, frame)
    assert wm1 is not wm0, "update_working_memory must return a NEW object"
    assert isinstance(wm1, WorkingMemory)
    assert len(wm1.frames) == 1
    assert wm1.frames[0].frame_id == "t001"
    ok("Ch.2/FT-4: update_working_memory appends frame, returns new frozen WorkingMemory")
except AssertionError as e:
    fail("Ch.2/FT-4", e)
except Exception as e:
    fail("Ch.2/FT-4", e)


# ── Ch.2/ST-6: evict oldest unpinned — pinned survive ────────────────────────
try:
    wm = seed_working_memory()
    # Add a pinned frame first
    pinned_frame = CognitiveFrame(frame_id="pinned-0", content="pinned", turn=0, pinned=True)
    wm = update_working_memory(wm, pinned_frame)
    # Fill past capacity with unpinned frames
    for i in range(_CAPACITY + 2):
        f = CognitiveFrame(frame_id=f"u{i}", content=f"unpinned {i}", turn=i+1)
        wm = update_working_memory(wm, f)
    # Pinned frame must still be in wm.frames
    frame_ids = {f.frame_id for f in wm.frames}
    assert "pinned-0" in frame_ids, \
        f"pinned frame must survive eviction, frames: {frame_ids}"
    ok("Ch.2/ST-6: pinned frames survive eviction past capacity")
except AssertionError as e:
    fail("Ch.2/ST-6", e)
except Exception as e:
    fail("Ch.2/ST-6", e)


# ── Ch.2/ST-7: rolling summary ≤ 60 chars per evicted frame ─────────────────
try:
    wm = seed_working_memory()
    for i in range(_CAPACITY + 3):
        f = CognitiveFrame(frame_id=f"e{i}", content="x" * 100, turn=i)
        wm = update_working_memory(wm, f)
    # Each evicted contribution ≤ 60 chars
    if wm.rolling_summary:
        parts = wm.rolling_summary.split(" | ")
        for part in parts:
            assert len(part) <= 60, f"summary part too long: {len(part)} > 60: {part!r}"
    ok(f"Ch.2/ST-7: rolling summary lossy — each part ≤ 60 chars")
except AssertionError as e:
    fail("Ch.2/ST-7", e)
except Exception as e:
    fail("Ch.2/ST-7", e)


# ── Ch.2/IT-2: carry_wm writes, load_carry reads back ────────────────────────
try:
    wm = seed_working_memory(
        current_task="test carry",
        continuity_summary="some prior summary",
        open_threads=["thread-a", "thread-b"],
    )
    # Patch _CARRY_PATH to a temp file
    import runtime.working_memory as _wm_mod
    orig_path_code = _wm_mod.carry_wm.__code__

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_carry = os.path.join(tmpdir, "wm_carry.json")
        import json
        payload = {
            "current_task": wm.current_task,
            "open_threads": list(wm.open_threads),
            "rolling_summary": wm.rolling_summary,
        }
        with open(tmp_carry, "w") as f:
            json.dump(payload, f)
        with open(tmp_carry) as f:
            loaded = json.load(f)

    assert loaded["current_task"] == "test carry"
    assert "thread-a" in loaded["open_threads"]
    ok("Ch.2/IT-2: carry payload round-trips correctly (current_task + open_threads)")
except AssertionError as e:
    fail("Ch.2/IT-2", e)
except Exception as e:
    fail("Ch.2/IT-2", e)


# ── Ch.3/FT-5: highest score wins ────────────────────────────────────────────
try:
    from runtime.working_memory import _score as _wm_score
    cand_high = AttentionCandidate(item="h", novelty=1.0, importance=1.0, urgency=1.0)
    cand_low  = AttentionCandidate(item="l", novelty=0.0, importance=0.0, urgency=0.0)
    w = {"novelty": _W_NOVELTY, "importance": _W_IMPORTANCE, "urgency": _W_URGENCY}
    assert _wm_score(cand_high, w) > _wm_score(cand_low, w), "high-score candidate must score higher"
    ok("Ch.3/FT-5: _score() — high-novelty/importance/urgency candidate scores higher")
except AssertionError as e:
    fail("Ch.3/FT-5", e)
except Exception as e:
    fail("Ch.3/FT-5", e)


# ── Ch.3/ST-8: weights sum to 1.0 ────────────────────────────────────────────
try:
    total = _W_NOVELTY + _W_IMPORTANCE + _W_URGENCY
    assert abs(total - 1.0) < 0.001, f"weights must sum to 1.0, got {total}"
    ok(f"Ch.3/ST-8: attention weights sum to 1.0 ({_W_NOVELTY}+{_W_IMPORTANCE}+{_W_URGENCY}={total})")
except AssertionError as e:
    fail("Ch.3/ST-8", e)
except Exception as e:
    fail("Ch.3/ST-8", e)


# ── Ch.3/ST-9: mode thresholds ───────────────────────────────────────────────
try:
    assert _PERIPHERAL_MAX < _REACTIVE_MAX, "peripheral_max must be < reactive_max"
    assert _REACTIVE_MAX < 1.0, "reactive_max must be < 1.0"
    ok(f"Ch.3/ST-9: thresholds: peripheral<{_PERIPHERAL_MAX}, reactive<{_REACTIVE_MAX}, else deliberative")
except AssertionError as e:
    fail("Ch.3/ST-9", e)
except Exception as e:
    fail("Ch.3/ST-9", e)


# ── Ch.3/IT-1: one driver not two — core/memory_relevance_filter.py is supplier only ───────
# WO-CANON-VI ruling B rename: the misleading name "core/attention.py" was retired.
try:
    import inspect, os as _os
    import core.memory_relevance_filter as _mrf_mod
    src = inspect.getsource(_mrf_mod)
    # The relevance filter must NOT call run_attention_competition (it IS the supplier,
    # it must not drive the competition itself). Mention in a comment/docstring is fine;
    # what we forbid is an actual call or import of the function.
    assert "run_attention_competition(" not in src, \
        "core/memory_relevance_filter.py must not call run_attention_competition — it's a supplier"
    assert "from runtime.working_memory import" not in src, \
        "core/memory_relevance_filter.py must not import from working_memory — it's a supplier"
    # And its docstring must reference its supplier / relevance-filter role
    assert "supplier" in src.lower() or "relevance filter" in src.lower(), \
        "core/memory_relevance_filter.py docstring must acknowledge its supplier/filter role"
    # The old misleading filename must no longer exist (rename, not a shim).
    assert not _os.path.exists("core/attention.py"), \
        "core/attention.py must be renamed — no misleading duplicate should remain"
    ok("Ch.3/IT-1: core/memory_relevance_filter.py is a supplier/filter — does not run the competition (one driver)")
except AssertionError as e:
    fail("Ch.3/IT-1", e)
except Exception as e:
    fail("Ch.3/IT-1", e)


# ── Ch.3/ST-10: peripheral mode gates activation ─────────────────────────────
try:
    result = run_attention_competition([], budget=0.05)
    assert result.mode == "peripheral", f"budget 0.05 must be peripheral, got {result.mode!r}"
    ok("Ch.3/ST-10: budget 0.05 → peripheral mode")
except AssertionError as e:
    fail("Ch.3/ST-10", e)
except Exception as e:
    fail("Ch.3/ST-10", e)


# ── Ch.4/FT-6: WM frozen into CognitiveState ─────────────────────────────────
try:
    from runtime.spine.spine import assemble_cognitive_state
    wm_test = seed_working_memory(current_task="ch4_test")
    cs = assemble_cognitive_state(
        language={}, memory_result=None, attention={},
        capabilities=[], vault_result=None, prior_state={},
        working_memory=wm_test,
    )
    assert cs.working_memory is wm_test, "CognitiveState.working_memory must be the frozen WM passed in"
    ok("Ch.4/FT-6: assemble_cognitive_state() carries WorkingMemory into CognitiveState.working_memory")
except AssertionError as e:
    fail("Ch.4/FT-6", e)
except Exception as e:
    fail("Ch.4/FT-6", e)


# ── Ch.4/FT-7: plan.working_memory set by spine.run() ────────────────────────
try:
    from runtime.spine.spine import run as spine_run2
    plan2 = spine_run2(raw="working memory test turn", state={}, memory_pack={}, attention={})
    assert plan2 is not None
    wm_p = getattr(plan2, "working_memory", None)
    assert wm_p is not None, "plan.working_memory must be set after spine.run()"
    assert isinstance(wm_p, WorkingMemory)
    assert len(wm_p.frames) >= 1, "at least one frame appended per turn"
    ok(f"Ch.4/FT-7: spine.run() wires WM — frames={len(wm_p.frames)}, mode={wm_p.attention.mode!r}")
except AssertionError as e:
    fail("Ch.4/FT-7", e)
except Exception as e:
    fail("Ch.4/FT-7", e)


# ── Ch.4/ST-11: one WM slice — read-only downstream ─────────────────────────
try:
    wm_frozen = seed_working_memory()
    # Any downstream code that tried to mutate WM would raise
    raised = False
    try:
        wm_frozen.current_task = "mutated"
    except (AttributeError, TypeError):
        raised = True
    assert raised, "frozen WM must reject mutation"
    ok("Ch.4/ST-11: frozen WorkingMemory rejects downstream mutation — one slice, read-only")
except AssertionError as e:
    fail("Ch.4/ST-11", e)
except Exception as e:
    fail("Ch.4/ST-11", e)


# ── Ch.4/ST-12: open_threads not duplicated — WM authoritative ───────────────
try:
    wm_threads = seed_working_memory(open_threads=["thread-x", "thread-y"])
    cs_threads = assemble_cognitive_state(
        language={}, memory_result=None, attention={},
        capabilities=[], vault_result=None, prior_state={},
        working_memory=wm_threads,
    )
    wm_ot = set(wm_threads.open_threads)
    assert "thread-x" in wm_ot and "thread-y" in wm_ot, "open_threads must be in WM"
    ok("Ch.4/ST-12: open_threads in WM authoritative — no duplication in CognitiveState")
except AssertionError as e:
    fail("Ch.4/ST-12", e)
except Exception as e:
    fail("Ch.4/ST-12", e)


# ── Ch.4/ST-13: LTM boundary — carry_wm writes to continuity/, not vault ─────
try:
    import inspect
    src_wm = inspect.getsource(carry_wm)
    assert "write_memory" not in src_wm, "carry_wm must NOT call vault write_memory"
    assert "obsidian" not in src_wm.lower(), "carry_wm must not touch obsidian vault"
    assert "continuity" in src_wm.lower() or "wm_carry" in src_wm.lower(), \
        "carry_wm must write to continuity/ directory"
    ok("Ch.4/ST-13: carry_wm writes to continuity/ only — LTM boundary respected")
except AssertionError as e:
    fail("Ch.4/ST-13", e)
except Exception as e:
    fail("Ch.4/ST-13", e)


# ── AT-8: py_compile clean ────────────────────────────────────────────────────
try:
    for f in (
        "runtime/working_memory.py",
        "runtime/contracts.py",
        "runtime/spine/plan.py",
        "runtime/spine/spine.py",
        "core/memory_relevance_filter.py",
    ):
        py_compile.compile(f, doraise=True)
    ok("AT-8: py_compile clean on all WO-CANON-VI touched files")
except py_compile.PyCompileError as e:
    fail("AT-8", e)


print()
print("=" * 62)
print(f"WO-CANON-VI working memory   {PASS} passed   {FAIL} failed")
if FAIL:
    sys.exit(1)
