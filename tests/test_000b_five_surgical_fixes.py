"""
tests/test_000b_five_surgical_fixes.py — 000b card surgical fixes 2-5.

Fix 1 (WHERE key names) covered by test_wo099b_gaze_consume.py AT-GAZE-1.

AT-FIX-2: REMEMBER — reinforce fires after vault recall in server.py (static check)
AT-FIX-3: BODY — embodiment="desktop" written by _self_apply_embodiment call (static)
AT-FIX-3b: BODY — embodiment_tier computed (not hardcoded "verified") in the_moment.py
AT-FIX-4: SELF-OBSERVE — record_behaviour called after self_update in server.py (static)
AT-FIX-4b: SELF-OBSERVE — topics extracted from raw input (not always [])
AT-FIX-5: INTEND — CognitivePlan has intent_source field defaulting "david"
AT-FIX-5b: INTEND — server.py wires internal_intents to set intent_source="self"
"""
import ast
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def _src(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


# ── AT-FIX-2: reinforce fires after vault recall ──────────────────────────────

def test_remember_reinforce_after_lookup():
    src = _src("server.py")
    # consolidation_faculty must be imported for reinforcement
    assert "consolidation_faculty" in src, \
        "server.py must use consolidation_faculty for memory reinforcement"
    # vault hits must be queued for reinforcement after lookup (deferred-drain pattern)
    idx_lookup = src.find("_vault_hits = _vlookup")
    idx_queue  = src.find("_vault_reinforce_queue.append", idx_lookup)
    assert idx_lookup != -1, "_vlookup call not found in server.py"
    assert idx_queue  != -1, "vault hits must be queued for reinforce after _vlookup"
    # reinforce must be imported from consolidation_faculty (the drainer uses it)
    assert "reinforce as _rf" in src, \
        "server.py must import reinforce as _rf from consolidation_faculty"


# ── AT-FIX-3: embodiment="desktop" in _self_apply_embodiment call ────────────

def test_body_embodiment_written():
    src = _src("server.py")
    # _self_apply_embodiment must be called with an embodiment= keyword argument
    # (uses _active_body variable which holds the concrete embodiment string at runtime)
    assert "_self_apply_embodiment" in src and "embodiment=_active_body" in src, (
        "server.py must call _self_apply_embodiment with embodiment=_active_body"
    )


# ── AT-FIX-3b: embodiment_tier computed not hardcoded ────────────────────────

def test_body_tier_computed():
    src = _src("runtime/the_moment.py")
    # Must use tier_fact(state.embodiment, ...) — dynamic, not hardcoded "verified"
    assert "tier_fact(state.embodiment," in src, (
        "the_moment.py must compute embodiment_tier via tier_fact(state.embodiment, ...) not hardcode"
    )
    # Must not hardcode a string literal for embodiment_tier
    assert '"embodiment_tier":  "verified"' not in src and "'embodiment_tier': 'verified'" not in src, (
        "the_moment.py must NOT hardcode 'verified' for embodiment_tier"
    )


# ── AT-FIX-4: record_behaviour called after self_update ──────────────────────

def test_self_observe_record_behaviour_called():
    src = _src("server.py")
    # record_behaviour is called via _rb inside _apply_end_of_turn closure (param s)
    assert "record_behaviour as _rb" in src, (
        "server.py must import record_behaviour as _rb"
    )
    assert "_rb(s, _action)" in src, (
        "server.py must call _rb(s, _action) inside the end-of-turn mutator closure"
    )
    # _self_update(s, _turn_data) and _rb(s, _action) both appear in _apply_end_of_turn
    idx_update = src.find("_self_update(s, _turn_data)")
    idx_rb     = src.find("_rb(s, _action)", idx_update)
    assert idx_update != -1, "_self_update(s, _turn_data) not found in server.py"
    assert idx_rb != -1, "_rb(s, _action) must appear after _self_update in the closure"


# ── AT-FIX-4b: topics extracted from raw (not always []) ─────────────────────

def test_self_observe_real_topics_extracted():
    src = _src("server.py")
    assert "_so_topics" in src, "server.py must extract _so_topics from raw"
    idx_topics = src.find('"topics":     _so_topics')
    assert idx_topics != -1, "self_update must receive _so_topics not []"


# ── AT-FIX-5: CognitivePlan has intent_source field ──────────────────────────

def test_intend_intent_source_on_plan():
    from runtime.spine.plan import CognitivePlan
    plan = CognitivePlan()
    assert hasattr(plan, "intent_source"), "CognitivePlan must have intent_source field"
    assert plan.intent_source == "david", (
        f"CognitivePlan.intent_source default must be 'david'; got: '{plan.intent_source}'"
    )


# ── AT-FIX-5b: server.py wires internal_intents to set intent_source="self" ──

def test_intend_server_wires_internal_intents():
    src = _src("server.py")
    assert "internal_intents as _ec_intents" in src, (
        "server.py must import internal_intents as _ec_intents"
    )
    assert '_plan.intent_source = "self"' in src or "_plan.intent_source = 'self'" in src, (
        "server.py must set _plan.intent_source='self' when internal intents fire"
    )
    # Verify _ec_intents call appears before intent_source assignment
    idx_call   = src.find("_ec_raw = _ec_intents")
    idx_assign = src.find('_plan.intent_source = "self"')
    assert idx_call != -1 and idx_assign != -1
    assert idx_call < idx_assign, "_ec_intents must be called before intent_source assignment"


# ── Self-runner ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    _tests = [
        ("AT-FIX-2",  test_remember_reinforce_after_lookup),
        ("AT-FIX-3",  test_body_embodiment_written),
        ("AT-FIX-3b", test_body_tier_computed),
        ("AT-FIX-4",  test_self_observe_record_behaviour_called),
        ("AT-FIX-4b", test_self_observe_real_topics_extracted),
        ("AT-FIX-5",  test_intend_intent_source_on_plan),
        ("AT-FIX-5b", test_intend_server_wires_internal_intents),
    ]
    _passed = 0
    _failed = 0
    for label, fn in _tests:
        try:
            fn()
            print(f"  ✅ {label}: {fn.__name__}")
            _passed += 1
        except Exception as _e:
            print(f"  ❌ {label}: {fn.__name__} — {_e}")
            _failed += 1
    print()
    print("=" * 62)
    print(f"000b surgical fixes   {_passed}/{_passed + _failed} passed, {_failed} failed")
    if _failed:
        sys.exit(1)
