"""
tests/test_w5_executive_context.py — W5: ONEBRAIN-012 Executive Consumption Contract

Tests:
    W5-1  ExecutiveContext is importable from runtime.executive_context
    W5-2  as_dict() contains all 4 keys exec_decide() currently reads
    W5-3  canonical extensions (ec_capabilities, ec_memory, ec_identity) present
    W5-4  NEW ASSUMPTIONs (agency, significance, epistemic_state) stay None
    W5-5  build_executive_context() populates intent/emotion/world correctly
    W5-6  spine._executive_faculty imports executive_context without error
    W5-7  UNKNOWN condition: internal_intent is set POST-spine in server.py (evidence recorded)

Run: python3 tests/test_w5_executive_context.py
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

ok  = lambda msg: print(f"  PASS  {msg}")
err = lambda msg: (print(f"  FAIL  {msg}"), sys.exit(1))


# ── W5-1: ExecutiveContext importable ────────────────────────────────────────
def test_w5_1_importable():
    from runtime.executive_context import ExecutiveContext, build_executive_context
    ok("W5-1: ExecutiveContext and build_executive_context importable")


# ── W5-2: as_dict() has the 4 keys executive.decide() currently reads ────────
def test_w5_2_frozen_executive_keys():
    from runtime.executive_context import build_executive_context
    ec = build_executive_context(
        intent="inquiry",
        emotional_context={"valence": "positive"},
        world=None, working_memory=None, capabilities=[],
        cognitive_state=None, affordances=None,
        attention={"intent": "inquiry", "emotional_context": {"valence": "positive"}},
    )
    d = ec.as_dict()
    for key in ("intent", "emotional_context", "wm_winner", "world_state"):
        if key not in d:
            err(f"W5-2: as_dict() missing key consumed by FROZEN executive.decide(): {key!r}")
    ok("W5-2: as_dict() contains all 4 keys executive.decide() currently reads")


# ── W5-3: canonical extensions present ──────────────────────────────────────
def test_w5_3_canonical_extensions():
    from runtime.executive_context import build_executive_context
    ec = build_executive_context(
        intent="conversation",
        emotional_context={},
        world=None, working_memory=None,
        capabilities=[{"name": "web_search", "available": True}],
        cognitive_state=None, affordances=None,
        attention={},
    )
    d = ec.as_dict()
    for key in ("ec_capabilities", "ec_memory", "ec_identity"):
        if key not in d:
            err(f"W5-3: canonical extension {key!r} missing from as_dict()")
    assert d["ec_capabilities"] == [{"name": "web_search", "available": True}], \
        f"W5-3: ec_capabilities wrong: {d['ec_capabilities']}"
    ok("W5-3: canonical extensions (ec_capabilities, ec_memory, ec_identity) present and typed")


# ── W5-4: NEW ASSUMPTIONs are None (not quietly populated) ──────────────────
def test_w5_4_new_assumptions_none():
    from runtime.executive_context import build_executive_context
    ec = build_executive_context(
        intent="conversation", emotional_context={},
        world=None, working_memory=None, capabilities=[],
        cognitive_state=None, affordances=None, attention={},
    )
    d = ec.as_dict()
    for key in ("ec_agency", "ec_significance", "ec_epistemic_state"):
        if d.get(key) is not None:
            err(f"W5-4: NEW ASSUMPTION {key!r} was quietly populated — must stay None until CA rules")
    assert ec.agency is None,           "W5-4: agency must be None (NEW ASSUMPTION)"
    assert ec.significance is None,     "W5-4: significance must be None (faculty not implemented)"
    assert ec.epistemic_state is None,  "W5-4: epistemic_state must be None (NEW ASSUMPTION)"
    ok("W5-4: NEW ASSUMPTIONs (agency, significance, epistemic_state) remain None — not quietly added")


# ── W5-5: build populates intent/emotion/world correctly ─────────────────────
def test_w5_5_build_correctness():
    from runtime.executive_context import build_executive_context
    ec = build_executive_context(
        intent="creation",
        emotional_context={"valence": "positive", "momentum": "building", "energy": 0.8},
        world=None, working_memory=None, capabilities=[],
        cognitive_state=None, affordances=["stand", "run"],
        attention={"intent": "creation",
                   "emotional_context": {"valence": "positive", "momentum": "building", "energy": 0.8}},
    )
    assert ec.intent == "creation",                              f"W5-5: intent wrong: {ec.intent}"
    assert ec.emotion.get("valence") == "positive",             f"W5-5: emotion wrong: {ec.emotion}"
    assert ec.world == {},                                       f"W5-5: world wrong (should be empty when None): {ec.world}"
    d = ec.as_dict()
    assert d["surface_affordances"] == ["stand", "run"],        f"W5-5: affordances wrong: {d.get('surface_affordances')}"
    ok("W5-5: build_executive_context() populates intent/emotion/affordances correctly")


# ── W5-6: spine._executive_faculty imports executive_context ─────────────────
def test_w5_6_spine_imports():
    with open(os.path.join(ROOT, "runtime", "spine", "spine.py"), encoding="utf-8") as f:
        src = f.read()
    if "build_executive_context" not in src:
        err("W5-6: spine.py does not import build_executive_context — W5 not wired")
    if "executive_context" not in src:
        err("W5-6: spine.py does not reference executive_context module")
    ok("W5-6: spine._executive_faculty references build_executive_context (W5 wired)")


# ── W5-7: UNKNOWN condition evidence — internal_intent is set POST-spine ─────
def test_w5_7_unknown_internal_intent():
    """
    Evidence for the UNKNOWN condition (LA ruling 2026-08-16):
    'Can spine.run() correctly accept empty raw with populated internal_intent?'

    Finding: internal_intent is set on _plan (the spine's return value) AFTER
    spine.run() returns in server.py. Therefore internal_intent is NEVER
    available to _executive_faculty() inside spine.run() in the current code.

    Evidence from server.py source:
      1. spine.run() called at server.py:2428 → returns _plan
      2. _ec_intents() called at server.py:3088 (650+ lines later)
      3. _plan.internal_intent = _ec_raw[0] at server.py:3091

    Smallest fix when ambient routing is authorised (after W5):
      Add `internal_intent` parameter to spine.run(); pass it through to
      _executive_faculty(); include it in ExecutiveContext; Executive decides
      SPEAK/STAY SILENT with self-initiated intent in context.
    """
    with open(os.path.join(ROOT, "server.py"), encoding="utf-8") as f:
        lines = f.readlines()

    spine_call_line = None
    intent_set_line = None

    for i, ln in enumerate(lines):
        if "_spine_run(" in ln and spine_call_line is None:
            spine_call_line = i + 1   # 1-indexed
        if "_plan.internal_intent = " in ln and intent_set_line is None:
            intent_set_line = i + 1

    if spine_call_line is None:
        err("W5-7: _spine_run() call not found in server.py")
    if intent_set_line is None:
        err("W5-7: _plan.internal_intent assignment not found in server.py")

    if intent_set_line <= spine_call_line:
        err(f"W5-7: internal_intent set at line {intent_set_line} BEFORE spine call at {spine_call_line}"
            " — UNKNOWN condition may have changed")

    ok(f"W5-7: CONFIRMED — spine call at L{spine_call_line}, internal_intent set at "
       f"L{intent_set_line} (post-spine). Executive never sees internal_intent today. "
       f"Smallest fix: add internal_intent param to spine.run()")


# ── runner ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("W5 — ONEBRAIN-012 Executive Consumption Contract")
    test_w5_1_importable()
    test_w5_2_frozen_executive_keys()
    test_w5_3_canonical_extensions()
    test_w5_4_new_assumptions_none()
    test_w5_5_build_correctness()
    test_w5_6_spine_imports()
    test_w5_7_unknown_internal_intent()
    print("\n7/7 PASS — W5 Executive Consumption Contract verified")
    print()
    print("NEW ASSUMPTIONS flagged to CA:")
    print("  agency       — not in any contract; CA: don't build yet (P2)")
    print("  epistemic_state — no structured contract field; Vol VII Ch.3 is speech-licensing only")
    print("  significance — Vol V §1.5 schema exists; significance_faculty.py does NOT")
    print()
    print("UNKNOWN CONDITION ANSWERED (W5-7):")
    print("  internal_intent is set POST-spine; Executive cannot see it today.")
    print("  Fix path (when ambient authorised): add internal_intent param to spine.run()")
