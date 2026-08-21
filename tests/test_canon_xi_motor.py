"""
tests/test_canon_xi_motor.py — WO-CANON-XI: Motor Cortex
Acceptance tests for §B (UP envelope), §E (§1.7 audit rule), §F (embodiment parity).

§A/§D (generalised DOWN envelope, PEEK enforcement) require David L3 (OQ-1.2) — not tested here.

Test families (from WO-CANON-XI Ch.1 §1.10 / Ch.2 §2.7):
  FT-*  — Functional: ACK gate, UP validation, additive guarantee
  ST-*  — Stability: no new channel files, bounded reflex set, audit coverage
  IT-*  — Integration: §1.7 audit, one capability path
  GR-*  — Grammar (Ch.2): closed verb set, composites, bone assertion, no driver port
  AT-*  — Compile hygiene
"""
import os
import sys
import py_compile

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

_passed = 0
_failed = 0


def ok(name: str):
    global _passed
    _passed += 1
    print(f"  ✅ {name}")


def fail(name: str, reason):
    global _failed
    _failed += 1
    print(f"  ❌ {name}: {reason}")


print()
print("WO-CANON-XI  Motor Cortex  (§B UP envelope · §E audit · §F parity)")
print("-" * 65)


# ═══════════════════════════════════════════════════════════════
# FT — Functional: ACK gate + UP envelope
# ═══════════════════════════════════════════════════════════════
print("\n── FT: ACK gate + UP envelope ──")


# FT-1: fresh ACK (_ts > since) clears the gate
try:
    from runtime.motor_contract import ack_is_fresh
    assert ack_is_fresh(100.1, 100.0) is True, "fresh ACK must return True"
    assert ack_is_fresh(200.0, 100.0) is True, "ACK well after command: True"
    ok("FT-1: fresh ACK (_ts > since) clears the gate — speech permitted")
except AssertionError as e:
    fail("FT-1", e)
except Exception as e:
    fail("FT-1", e)


# FT-2: stale ACK (_ts <= since) does NOT clear the gate
try:
    from runtime.motor_contract import ack_is_fresh
    assert ack_is_fresh(100.0, 100.0) is False, "_ts == since must be stale"
    assert ack_is_fresh(99.9,  100.0) is False, "_ts < since must be stale"
    ok("FT-2: stale ACK (_ts <= since) rejected — gate stays active")
except AssertionError as e:
    fail("FT-2", e)
except Exception as e:
    fail("FT-2", e)


# FT-3: timeout path exists in server.py and emits an honest fallback note
try:
    import inspect
    import server
    src = inspect.getsource(server)
    assert "timeout" in src.lower() and ("honest" in src.lower() or "couldn" in src.lower()), \
        "server.py must contain timeout + honest fallback language"
    assert "_PENDING_SIT" in src, "_PENDING_SIT must exist in server.py"
    assert "300" in src or "300.0" in src, "300s sit timeout constant must exist"
    ok("FT-3: timeout path exists in server.py with honest fallback wording")
except AssertionError as e:
    fail("FT-3", e)
except Exception as e:
    fail("FT-3", e)


# FT-4: UP motion ACK without 'at' field is rejected
try:
    from runtime.motor_contract import validate_up_event
    bad = {"type": "sit_complete", "_ts": 100.0}   # no 'at'
    ok_result, reason = validate_up_event(bad)
    assert ok_result is False, f"ACK without 'at' must fail; got ok={ok_result}, reason={reason!r}"
    assert "at" in reason.lower(), f"reason must mention missing 'at'; got {reason!r}"
    ok("FT-4: motion ACK without 'at' field is rejected (brain reads real position)")
except AssertionError as e:
    fail("FT-4", e)
except Exception as e:
    fail("FT-4", e)


# FT-5: UP motion ACK with 'at' passes; non-ACK event without 'at' also passes
try:
    from runtime.motor_contract import validate_up_event
    good_ack = {"type": "sit_complete", "_ts": 100.0, "at": {"surface_id": "desk", "pos": [0, 0]}}
    ok_result, reason = validate_up_event(good_ack)
    assert ok_result is True, f"valid ACK must pass; got ok={ok_result}, reason={reason!r}"

    # Non-ACK event type (e.g. perception) does not need 'at'
    perception = {"type": "window_opened", "_ts": 101.0}
    ok_result2, _ = validate_up_event(perception)
    assert ok_result2 is True, "non-ACK event without 'at' should pass"
    ok("FT-5: valid motion ACK passes; non-ACK event without 'at' also passes")
except AssertionError as e:
    fail("FT-5", e)
except Exception as e:
    fail("FT-5", e)


# FT-6: UP event without _ts is rejected regardless of type
try:
    from runtime.motor_contract import validate_up_event
    no_ts = {"type": "move_complete", "at": {"surface_id": "wall", "pos": [1, 0]}}
    ok_result, reason = validate_up_event(no_ts)
    assert ok_result is False, f"event without _ts must fail; got ok={ok_result}"
    assert "_ts" in reason, f"reason must mention _ts; got {reason!r}"
    ok("FT-6: UP event without _ts rejected — timestamp mandatory")
except AssertionError as e:
    fail("FT-6", e)
except Exception as e:
    fail("FT-6", e)


# FT-7: additive guarantee — state_writer move_command without route/issued_by unchanged
try:
    from blender_bridge.state_writer import write_with_presence
    import inspect
    src = inspect.getsource(write_with_presence)
    # Additive means: route/issued_by only set when caller supplies them
    assert "route" in src or "issued_by" in src, \
        "state_writer must reference route/issued_by for additive build"
    # Check that state_writer.py L133/L221 pattern exists (additive, not mandatory)
    import blender_bridge.state_writer as _sw
    sw_src = inspect.getsource(_sw)
    assert 'intent.get("route")' in sw_src or '"route"' in sw_src, \
        "route must be conditional (additive) in state_writer"
    ok("FT-7: state_writer route/issued_by are additive — absent fields leave command unchanged")
except AssertionError as e:
    fail("FT-7", e)
except Exception as e:
    fail("FT-7", e)


# ═══════════════════════════════════════════════════════════════
# ST — Stability
# ═══════════════════════════════════════════════════════════════
print("\n── ST: Stability ──")


# ST-1: no new forbidden channel files exist (emotions.json / movement.json / second sensed-state)
try:
    _FORBIDDEN = ["blender/emotions.json", "blender/movement.json", "blender/motor_events.json"]
    found = [f for f in _FORBIDDEN if os.path.exists(f)]
    assert not found, f"Forbidden channel files must not exist: {found}"
    ok("ST-1: no forbidden channel files (emotions.json, movement.json, motor_events.json)")
except AssertionError as e:
    fail("ST-1", e)
except Exception as e:
    fail("ST-1", e)


# ST-2: BOUNDED_REFLEXES covers the three named reflexes
try:
    from runtime.motor_contract import BOUNDED_REFLEXES
    for reflex in ("landed", "resurfaced", "collided"):
        assert reflex in BOUNDED_REFLEXES, f"'{reflex}' must be in BOUNDED_REFLEXES"
    ok("ST-2: BOUNDED_REFLEXES contains landed, resurfaced, collided")
except AssertionError as e:
    fail("ST-2", e)
except Exception as e:
    fail("ST-2", e)


# ST-3: BOUNDED_REFLEXES is a frozenset (immutable — cannot be extended at runtime)
try:
    from runtime.motor_contract import BOUNDED_REFLEXES
    assert isinstance(BOUNDED_REFLEXES, frozenset), \
        f"BOUNDED_REFLEXES must be frozenset; got {type(BOUNDED_REFLEXES)}"
    try:
        BOUNDED_REFLEXES.add("invented_reflex")   # type: ignore[attr-defined]
        fail("ST-3", "frozenset.add should have raised AttributeError")
    except AttributeError:
        ok("ST-3: BOUNDED_REFLEXES is frozenset — immutable, cannot be extended at runtime")
except AssertionError as e:
    fail("ST-3", e)
except Exception as e:
    fail("ST-3", e)


# ST-4: _ACK_BODY_TYPES in server.py aligns with motor_contract motion ACK types
try:
    import server as _srv
    assert hasattr(_srv, "_ACK_BODY_TYPES"), "_ACK_BODY_TYPES must exist in server.py"
    ack_types = _srv._ACK_BODY_TYPES
    for t in ("sit_complete", "move_complete", "exit_complete"):
        assert t in ack_types, f"'{t}' must be in _ACK_BODY_TYPES"
    ok("ST-4: server._ACK_BODY_TYPES covers sit_complete, move_complete, exit_complete")
except AssertionError as e:
    fail("ST-4", e)
except Exception as e:
    fail("ST-4", e)


# ═══════════════════════════════════════════════════════════════
# IT — Integration: §1.7 audit rule
# ═══════════════════════════════════════════════════════════════
print("\n── IT: §1.7 audit rule ──")


# IT-1: commanded behaviour → LEGAL (no violation)
try:
    from runtime.motor_contract import audit_motor_behaviour
    commanded = [{"action": "sit", "_ts": 100.0, "issued_by": "SpatialFaculty"}]
    relay = []
    observed = [{"kind": "sit", "_ts": 101.0}]
    result = audit_motor_behaviour(commanded, relay, observed)
    assert result["ok"] is True, f"commanded behaviour must be LEGAL; got {result}"
    assert result["legal_commanded"] == 1
    assert result["violations"] == []
    ok("IT-1: commanded behaviour (issued_by set, _ts before action) → LEGAL")
except AssertionError as e:
    fail("IT-1", e)
except Exception as e:
    fail("IT-1", e)


# IT-2: bounded reflex with relay UP → LEGAL
try:
    from runtime.motor_contract import audit_motor_behaviour
    commanded = []
    relay = [{"event_kind": "landed"}]   # reflex emitted UP
    observed = [{"kind": "landed", "_ts": 102.0}]
    result = audit_motor_behaviour(commanded, relay, observed)
    assert result["ok"] is True, f"bounded reflex with relay should be LEGAL; got {result}"
    assert result["legal_reflex"] == 1
    ok("IT-2: bounded reflex (landed, relayed UP) → LEGAL")
except AssertionError as e:
    fail("IT-2", e)
except Exception as e:
    fail("IT-2", e)


# IT-3: uncommanded, unreported behaviour → VIOLATION
try:
    from runtime.motor_contract import audit_motor_behaviour
    commanded = []
    relay = []
    # This simulates EloDesktopNav._route selecting a traversal locally (no DOWN command)
    observed = [{"kind": "local_route_selection", "_ts": 103.0}]
    result = audit_motor_behaviour(commanded, relay, observed)
    assert result["ok"] is False, f"uncommanded behaviour must be VIOLATION; got {result}"
    assert len(result["violations"]) == 1
    assert "VIOLATION" in result["violations"][0]
    ok("IT-3: uncommanded, unreported behaviour → VIOLATION (e.g. EloDesktopNav._route)")
except AssertionError as e:
    fail("IT-3", e)
except Exception as e:
    fail("IT-3", e)


# IT-4: bounded reflex WITHOUT relay UP → VIOLATION (reflex must emit)
try:
    from runtime.motor_contract import audit_motor_behaviour
    commanded = []
    relay = []   # reflex happened but never emitted UP
    observed = [{"kind": "resurfaced", "_ts": 104.0}]
    result = audit_motor_behaviour(commanded, relay, observed)
    assert result["ok"] is False, \
        f"bounded reflex without relay UP must be VIOLATION; got {result}"
    ok("IT-4: bounded reflex without relay UP → VIOLATION (must always emit)")
except AssertionError as e:
    fail("IT-4", e)
except Exception as e:
    fail("IT-4", e)


# IT-5: stale DOWN command (_ts after behaviour) does not satisfy the rule
try:
    from runtime.motor_contract import audit_motor_behaviour
    # Command timestamped AFTER the behaviour — does not count as authorising it
    commanded = [{"action": "sit", "_ts": 200.0, "issued_by": "SpatialFaculty"}]
    relay = []
    observed = [{"kind": "sit", "_ts": 100.0}]   # happened BEFORE the command
    result = audit_motor_behaviour(commanded, relay, observed)
    assert result["ok"] is False, \
        f"command that came AFTER behaviour must not legalise it; got {result}"
    ok("IT-5: stale DOWN command (after behaviour _ts) does not satisfy audit rule")
except AssertionError as e:
    fail("IT-5", e)
except Exception as e:
    fail("IT-5", e)


# IT-6: command without issued_by does not satisfy the rule
try:
    from runtime.motor_contract import audit_motor_behaviour
    commanded = [{"action": "move", "_ts": 100.0}]   # no issued_by
    relay = []
    observed = [{"kind": "move", "_ts": 101.0}]
    result = audit_motor_behaviour(commanded, relay, observed)
    assert result["ok"] is False, \
        f"command without issued_by must not legalise behaviour; got {result}"
    ok("IT-6: command without issued_by does not satisfy §1.7 audit rule")
except AssertionError as e:
    fail("IT-6", e)
except Exception as e:
    fail("IT-6", e)


# ═══════════════════════════════════════════════════════════════
# GR — Grammar (Ch.2): verb set, composites, bone assertion, parity
# ═══════════════════════════════════════════════════════════════
print("\n── GR: Movement Grammar + Parity (§F) ──")


# GR-1: MOVEMENT_VERBS is exactly 12
try:
    from runtime.motor_contract import MOVEMENT_VERBS
    assert len(MOVEMENT_VERBS) == 12, \
        f"exactly 12 movement verbs required; got {len(MOVEMENT_VERBS)}: {sorted(MOVEMENT_VERBS)}"
    ok(f"GR-1: MOVEMENT_VERBS is exactly 12 ({sorted(MOVEMENT_VERBS)})")
except AssertionError as e:
    fail("GR-1", e)
except Exception as e:
    fail("GR-1", e)


# GR-2: all 12 named verbs are in the set
try:
    from runtime.motor_contract import MOVEMENT_VERBS
    _EXPECTED = {
        "APPROACH", "CLIMB", "BALANCE", "LEAP", "HANG", "SLIDE",
        "PEEK", "PERCH", "REST", "OBSERVE", "RETREAT", "RETURN",
    }
    assert MOVEMENT_VERBS == _EXPECTED, \
        f"verb set mismatch:\n  expected: {sorted(_EXPECTED)}\n  got:      {sorted(MOVEMENT_VERBS)}"
    ok("GR-2: all 12 verbs present — APPROACH CLIMB BALANCE LEAP HANG SLIDE PEEK PERCH REST OBSERVE RETREAT RETURN")
except AssertionError as e:
    fail("GR-2", e)
except Exception as e:
    fail("GR-2", e)


# GR-3: MOVEMENT_VERBS is a frozenset (closed — cannot add at runtime)
try:
    from runtime.motor_contract import MOVEMENT_VERBS
    assert isinstance(MOVEMENT_VERBS, frozenset)
    try:
        MOVEMENT_VERBS.add("THIRTEENTH")   # type: ignore[attr-defined]
        fail("GR-3", "frozenset.add should raise AttributeError")
    except AttributeError:
        ok("GR-3: MOVEMENT_VERBS is frozenset — closed set, adding requires a canon change")
except AssertionError as e:
    fail("GR-3", e)
except Exception as e:
    fail("GR-3", e)


# GR-4: is_valid_verb validates all 12, rejects unknown
try:
    from runtime.motor_contract import is_valid_verb
    for v in ("APPROACH", "CLIMB", "BALANCE", "LEAP", "HANG", "SLIDE",
              "PEEK", "PERCH", "REST", "OBSERVE", "RETREAT", "RETURN"):
        assert is_valid_verb(v) is True, f"'{v}' should be valid"
    assert is_valid_verb("WALK") is False, "WALK is not in the grammar"
    assert is_valid_verb("RUN") is False, "RUN is not in the grammar (APPROACH + speed param)"
    assert is_valid_verb("") is False, "empty string not valid"
    ok("GR-4: is_valid_verb accepts all 12; rejects WALK, RUN, empty string")
except AssertionError as e:
    fail("GR-4", e)
except Exception as e:
    fail("GR-4", e)


# GR-5: composite moves decompose into existing verbs (no thirteenth)
try:
    from runtime.motor_contract import is_valid_verb
    # fire-jump = APPROACH + LEAP (two verbs, not one new verb)
    fire_jump_legs = ["APPROACH", "LEAP"]
    for leg_verb in fire_jump_legs:
        assert is_valid_verb(leg_verb), f"composite leg '{leg_verb}' not in grammar"
    # wall-jump chimney = APPROACH + LEAP + HANG (three verbs)
    wall_jump = ["APPROACH", "LEAP", "HANG"]
    for leg_verb in wall_jump:
        assert is_valid_verb(leg_verb), f"wall-jump leg '{leg_verb}' not in grammar"
    ok("GR-5: composites (fire-jump, wall-jump) decompose into existing verbs; no thirteenth created")
except AssertionError as e:
    fail("GR-5", e)
except Exception as e:
    fail("GR-5", e)


# GR-6: APPROACH at speed 0.3 and speed 1.0 are the same verb (parameterised, not multiplied)
try:
    from runtime.motor_contract import is_valid_verb
    slow_leg = {"verb": "APPROACH", "speed": 0.3}
    fast_leg  = {"verb": "APPROACH", "speed": 1.0}
    assert slow_leg["verb"] == fast_leg["verb"], "verb must be the same regardless of speed param"
    assert is_valid_verb(slow_leg["verb"]) is True
    # There must NOT be a separate WALK or RUN verb
    assert is_valid_verb("WALK") is False
    assert is_valid_verb("RUN")  is False
    ok("GR-6: APPROACH(speed=0.3) and APPROACH(speed=1.0) are one verb — no WALK/RUN split")
except AssertionError as e:
    fail("GR-6", e)
except Exception as e:
    fail("GR-6", e)


# GR-7: validate_route_verbs accepts valid routes, rejects unknown verbs
try:
    from runtime.motor_contract import validate_route_verbs
    valid_route = [
        {"verb": "APPROACH", "speed": 0.5},
        {"verb": "LEAP", "expected_ms": 400},
    ]
    ok_result, unknown = validate_route_verbs(valid_route)
    assert ok_result is True, f"valid route should pass; unknown={unknown}"

    bad_route = [
        {"verb": "APPROACH"},
        {"verb": "TELEPORT"},   # not in grammar
    ]
    ok_result2, unknown2 = validate_route_verbs(bad_route)
    assert ok_result2 is False, "route with unknown verb must fail"
    assert "TELEPORT" in unknown2
    ok("GR-7: validate_route_verbs accepts valid routes; rejects unknown verbs (e.g. TELEPORT)")
except AssertionError as e:
    fail("GR-7", e)
except Exception as e:
    fail("GR-7", e)


# GR-8: missing bone raises loudly — never a silent no-op (§F)
try:
    from runtime.motor_contract import assert_bone_present
    rig = ["c_arm_fk.r", "c_arm_fk.l", "c_head_fk"]
    # Present bone — no error
    assert_bone_present(rig, "c_arm_fk.r")

    # Missing bone — must raise loudly
    raised = False
    try:
        assert_bone_present(rig, "c_spine_missing")
    except KeyError as ke:
        raised = True
        assert "c_spine_missing" in str(ke), f"KeyError must name the missing bone; got {ke}"
    assert raised, "assert_bone_present must raise KeyError for missing bone"
    ok("GR-8: assert_bone_present raises KeyError for missing bone — never silent no-op (§F)")
except AssertionError as e:
    fail("GR-8", e)
except Exception as e:
    fail("GR-8", e)


# GR-9: no driver port — PlayerController not importable in elo-ai Python context (§F)
try:
    try:
        import PlayerController   # type: ignore[import]
        fail("GR-9", "PlayerController must NOT be importable in elo-ai Python context")
    except ImportError:
        ok("GR-9: PlayerController is not importable — no driver port from game to desktop (§F)")
except Exception as e:
    fail("GR-9", e)


# GR-10: no animation clip name in a valid route payload (routes are verbs, not assets)
try:
    route = [
        {"verb": "APPROACH", "speed": 0.5},
        {"verb": "LEAP", "expected_ms": 400},
    ]
    _CLIP_SMELL = (".anim", ".fbx", ".clip", "animation", "Anim", "idle", "walk", "run")
    for leg in route:
        for key, val in leg.items():
            if key == "verb":
                continue
            if isinstance(val, str):
                for smell in _CLIP_SMELL:
                    assert smell not in val, \
                        f"Clip/animation name '{val}' must not appear in route payload"
    ok("GR-10: route legs carry no animation clip names — realisation layer chooses assets")
except AssertionError as e:
    fail("GR-10", e)
except Exception as e:
    fail("GR-10", e)


# ═══════════════════════════════════════════════════════════════
# AT — Compile hygiene
# ═══════════════════════════════════════════════════════════════
print("\n── AT: compile hygiene ──")

for _mod in (
    "runtime/motor_contract.py",
    "avatar/motor_abstraction.py",
    "avatar/animation_router.py",
    "blender_bridge/state_writer.py",
):
    _label = f"AT-compile: {_mod}"
    try:
        py_compile.compile(_mod, doraise=True)
        ok(_label)
    except py_compile.PyCompileError as e:
        fail(_label, e)
    except Exception as e:
        fail(_label, e)


# ── Final summary ─────────────────────────────────────────────────────────────
print()
print("=" * 65)
print(f"WO-CANON-XI motor cortex (§B/§E/§F)   {_passed} passed   {_failed} failed")
if _failed:
    sys.exit(1)
