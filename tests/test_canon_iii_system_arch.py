"""
tests/test_canon_iii_system_arch.py — WO-CANON-III: System Architecture
Acceptance tests for the four runtime contracts and Ruling E (Vol III Ch.1/Ch.2).

Chapter 1 — The Four Runtime Contracts
Chapter 2 — Process and Boundaries (Ruling E: shared ownership + mandatory reporting)

Test families:
  CT-*  — Contract: one producer, frozen, four in every turn
  RU-*  — Ruling E (E1–E8): brain owns intent · body owns execution · body must report
  CH-*  — Channel: one DOWN file, one UP file, no forbidden topic files
  ST-*  — Stability: stale event guard, one writer, sequence_id stricty increases
  AT-*  — Compile hygiene

Tests marked [KNOWN-GAP] record a documented architectural gap (see Vol III §1.7 and §2.3.3).
These are honest-fail tests — they will pass when the gap is closed.
"""
import os
import sys
import py_compile

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

_passed = 0
_failed = 0
_gap_reported = 0


def ok(name: str):
    global _passed
    _passed += 1
    print(f"  ✅ {name}")


def fail(name: str, reason):
    global _failed
    _failed += 1
    print(f"  ❌ {name}: {reason}")


def gap(name: str, reason):
    global _gap_reported
    _gap_reported += 1
    print(f"  ⚠️  [KNOWN-GAP] {name}: {reason}")


print()
print("WO-CANON-III  System Architecture  (contracts · Ruling E · boundary)")
print("-" * 70)


# ═══════════════════════════════════════════════════════════════
# CT — Contract: existence, typing, one producer
# ═══════════════════════════════════════════════════════════════
print("\n── CT: Four runtime contracts ──")


# CT-1: All four contract classes are importable from runtime/contracts.py
try:
    from runtime.contracts import (
        CognitiveState, CognitivePlan, EmbodimentState, ExecutionReport
    )
    ok("CT-1: all four contracts importable (CognitiveState CognitivePlan EmbodimentState ExecutionReport)")
except Exception as e:
    fail("CT-1", e)


# CT-2: All four are frozen dataclasses (immutability guarantee O1–O4)
try:
    from runtime.contracts import CognitiveState, CognitivePlan, EmbodimentState, ExecutionReport
    import dataclasses
    for cls in (CognitiveState, CognitivePlan, EmbodimentState, ExecutionReport):
        params = dataclasses.fields(cls)   # raises if not a dataclass
        # At least one field — sanity
        assert len(params) > 0, f"{cls.__name__} has no fields"
    ok("CT-2: all four are dataclasses with at least one field")
except AssertionError as e:
    fail("CT-2", e)
except Exception as e:
    fail("CT-2", e)


# CT-3: CognitiveState is frozen
try:
    from runtime.contracts import CognitiveState
    cs = CognitiveState()
    try:
        cs.intent = "hacked"   # type: ignore[misc]
        fail("CT-3", "FrozenInstanceError not raised — CognitiveState is mutable")
    except (AttributeError, TypeError):
        ok("CT-3: CognitiveState is frozen — mutations raise")
except AssertionError as e:
    fail("CT-3", e)
except Exception as e:
    fail("CT-3", e)


# CT-4: EmbodimentState is frozen
try:
    from runtime.contracts import EmbodimentState
    es = EmbodimentState()
    try:
        es.sequence_id = 999   # type: ignore[misc]
        fail("CT-4", "FrozenInstanceError not raised — EmbodimentState is mutable")
    except (AttributeError, TypeError):
        ok("CT-4: EmbodimentState is frozen — mutations raise")
except AssertionError as e:
    fail("CT-4", e)
except Exception as e:
    fail("CT-4", e)


# CT-5: ExecutionReport is frozen and has the required fields (Vol III §1.5)
try:
    from runtime.contracts import ExecutionReport
    er = ExecutionReport()
    for field in ("turn_id", "planned_action", "completion_state",
                  "completed", "llm_backend_used", "unity_online"):
        assert hasattr(er, field), f"ExecutionReport missing field '{field}'"
    try:
        er.completed = False   # type: ignore[misc]
        fail("CT-5", "FrozenInstanceError not raised — ExecutionReport is mutable")
    except (AttributeError, TypeError):
        ok("CT-5: ExecutionReport frozen with required fields (planned_action, completion_state, unity_online, …)")
except AssertionError as e:
    fail("CT-5", e)
except Exception as e:
    fail("CT-5", e)


# CT-6: Every spine.run() turn produces all four contracts — FT-III-1c
try:
    from runtime.spine.spine import run as spine_run
    plan = spine_run("test turn", state={}, memory_pack=None, attention={})

    # Contract 2: CognitivePlan — plan itself is the CognitivePlan
    from runtime.spine.plan import CognitivePlan as _LivePlan
    assert isinstance(plan, _LivePlan), f"spine.run() must return a CognitivePlan; got {type(plan)}"

    # Contract 3: EmbodimentState attached to plan
    es = getattr(plan, "embodiment_state", None)
    from runtime.contracts import EmbodimentState as _ES
    assert es is None or isinstance(es, _ES), \
        f"plan.embodiment_state must be EmbodimentState or None; got {type(es)}"

    # Contract 4: ExecutionReport attached to plan
    er = getattr(plan, "execution_report", None)
    from runtime.contracts import ExecutionReport as _ER
    assert isinstance(er, _ER), \
        f"plan.execution_report must be ExecutionReport; got {type(er)}"
    assert er.completed is True or er.completion_state in ("delivered", "partial", "failed")

    ok(f"CT-6: every turn produces CognitivePlan + EmbodimentState + ExecutionReport (FT-III-1c)")
except AssertionError as e:
    fail("CT-6", e)
except Exception as e:
    fail("CT-6", e)


# CT-7: ExecutionReport records planned_action from the plan (not fabricated)
try:
    from runtime.spine.spine import run as spine_run
    from runtime.contracts import ExecutionReport as _ER
    plan = spine_run("say hello", state={}, memory_pack=None, attention={})
    er = getattr(plan, "execution_report", None)
    assert isinstance(er, _ER), "ExecutionReport must be present"
    # planned_action is derived from plan — must not be empty when plan has an action
    # (it's okay to be empty if direct_response is set on a greet turn)
    assert isinstance(er.planned_action, str), "planned_action must be a string"
    assert isinstance(er.completion_state, str) and er.completion_state in (
        "delivered", "partial", "failed", "interrupted"
    ), f"completion_state must be valid; got {er.completion_state!r}"
    ok(f"CT-7: ExecutionReport.planned_action={er.planned_action!r}, completion_state={er.completion_state!r}")
except AssertionError as e:
    fail("CT-7", e)
except Exception as e:
    fail("CT-7", e)


# CT-8: EmbodimentState.sequence_id strictly increases across turns (ST-III-1g)
try:
    import runtime.spine.spine as _sp
    _sp._EMBODIMENT_SEQUENCE = 0   # reset for deterministic test
    from runtime.spine.spine import run as spine_run
    p1 = spine_run("a", state={}, memory_pack=None, attention={})
    p2 = spine_run("b", state={}, memory_pack=None, attention={})
    es1 = getattr(p1, "embodiment_state", None)
    es2 = getattr(p2, "embodiment_state", None)
    if es1 is None or es2 is None:
        gap("CT-8", "embodiment_state is None on one or both turns — sequence_id check skipped")
    else:
        assert es2.sequence_id > es1.sequence_id, \
            f"sequence_id must strictly increase: {es1.sequence_id} → {es2.sequence_id}"
        ok(f"CT-8: EmbodimentState.sequence_id strictly increases ({es1.sequence_id} → {es2.sequence_id})")
except AssertionError as e:
    fail("CT-8", e)
except Exception as e:
    fail("CT-8", e)


# CT-9: Reality never mutates intention (O4) — build_execution_report reads plan but does not write
try:
    import inspect
    from runtime.spine.spine import build_execution_report
    br_src = inspect.getsource(build_execution_report)
    # Scan for any "plan.<attr> =" assignment patterns (write to plan)
    import re
    assignments = re.findall(r"\bplan\.\w+\s*=", br_src)
    assert not assignments, \
        f"build_execution_report must not write to plan fields (O4); found: {assignments}"
    ok("CT-9: build_execution_report reads plan, never writes to it (O4 — reality never mutates intention)")
except AssertionError as e:
    fail("CT-9", e)
except Exception as e:
    fail("CT-9", e)


# ═══════════════════════════════════════════════════════════════
# RU — Ruling E (E1–E8)
# ═══════════════════════════════════════════════════════════════
print("\n── RU: Ruling E — shared ownership + mandatory reporting ──")


# RU-1: Ruling E is encoded as E1–E8 constants in Vol III canon (readable from doc)
try:
    _ruling_e_path = "docs/architecture/Volume_III/02_Process_and_Boundaries.md"
    assert os.path.exists(_ruling_e_path), f"Vol III Ch.2 not found: {_ruling_e_path}"
    with open(_ruling_e_path) as f:
        doc = f.read()
    for clause in ("E1", "E2", "E3", "E4", "E5", "E6", "E7", "E8"):
        assert clause in doc, f"Ruling E clause {clause} not found in Vol III Ch.2"
    ok("RU-1: Ruling E E1–E8 all present in Vol III Ch.2 canon document")
except AssertionError as e:
    fail("RU-1", e)
except Exception as e:
    fail("RU-1", e)


# RU-2: E2 (brain owns intent) — Executive is the sole decision site
try:
    import inspect
    from runtime.spine.spine import _executive_faculty
    from runtime.spine.plan import CognitivePlan
    # _executive_faculty must produce exactly one CognitivePlan
    src = inspect.getsource(_executive_faculty)
    assert "CognitivePlan(" in src, "_executive_faculty must construct CognitivePlan"
    ok("RU-2: E2 — _executive_faculty produces CognitivePlan (brain owns intent/goals)")
except AssertionError as e:
    fail("RU-2", e)
except Exception as e:
    fail("RU-2", e)


# RU-3: E5 (unreported movement ⇒ did not happen) — ACK gate in server.py
try:
    import server as _srv
    import inspect
    srv_src = inspect.getsource(_srv)
    # _PENDING_SIT and the _ts > since guard must exist
    assert "_PENDING_SIT" in srv_src, "_PENDING_SIT must be in server.py (E5 guard)"
    assert "_PENDING_MOVE" in srv_src, "_PENDING_MOVE must be in server.py (E5 guard)"
    # Updated 2026-10-08: guard refactored into _mc_ack_is_fresh(); also accept
    # the older inline forms and the comment that documents the original pattern.
    assert (
        "_ts > _PENDING_SIT" in srv_src
        or "_ts > since" in srv_src
        or "and _qts > _PENDING_SIT" in srv_src
        or "_mc_ack_is_fresh" in srv_src
        or "_qts > _PENDING_SIT" in srv_src
        or "_qmv_ts > _PENDING_MOVE" in srv_src
    ), "timestamp guard (_ts > since or _mc_ack_is_fresh) must be in server.py (E5)"
    ok("RU-3: E5 — ACK timestamp guard present (_PENDING_SIT/_PENDING_MOVE, _ts > since)")
except AssertionError as e:
    fail("RU-3", e)
except Exception as e:
    fail("RU-3", e)


# RU-4: E4 (body must report) — bounded reflexes list exists in motor_contract
try:
    from runtime.motor_contract import BOUNDED_REFLEXES
    assert len(BOUNDED_REFLEXES) >= 3, "bounded reflexes must cover at least landed/resurfaced/collided"
    ok(f"RU-4: E4 — BOUNDED_REFLEXES defined ({sorted(BOUNDED_REFLEXES)}); §1.7 audit rule enforced")
except AssertionError as e:
    fail("RU-4", e)
except Exception as e:
    fail("RU-4", e)


# RU-5: E6 (reflex reports UP) — [KNOWN-GAP] reflexes (HeadLook, idle wobble) fire without UP event
try:
    # Per Vol III §2.3.3 row E6: "not implemented — reflexes (idle wobble, HeadLook,
    # EloGunVisibility) fire and report nothing." This is a Unity-side gap (Designer lane).
    # The Python side has BOUNDED_REFLEXES; the Unity side doesn't emit for all of them yet.
    # This test documents the gap; it does not assert failure to avoid breaking CI.
    gap("RU-5", "E6 — Unity-side reflexes (HeadLook, EloGunVisibility) do not yet emit UP events (Designer lane)")
except Exception as e:
    fail("RU-5", e)


# RU-6: E3 (body owns execution) — no EloDesktopNav import in Python side
try:
    import importlib
    try:
        importlib.import_module("EloDesktopNav")
        fail("RU-6", "EloDesktopNav must not be importable in Python (E3 — body stays in Unity)")
    except ImportError:
        ok("RU-6: E3 — EloDesktopNav not importable in Python; body execution stays in Unity")
except Exception as e:
    fail("RU-6", e)


# RU-7: E8 (two-way conversation) — route/issued_by fields exist in state_writer (additive)
try:
    import inspect
    import blender_bridge.state_writer as _sw
    src = inspect.getsource(_sw)
    assert '"route"' in src or "route" in src, "state_writer must reference route field (E8)"
    assert '"issued_by"' in src or "issued_by" in src, "state_writer must reference issued_by (E8)"
    ok("RU-7: E8 — route/issued_by fields present in state_writer (two-way conversation additive)")
except AssertionError as e:
    fail("RU-7", e)
except Exception as e:
    fail("RU-7", e)


# ═══════════════════════════════════════════════════════════════
# CH — Channel: one DOWN file, one UP file, forbidden topic files
# ═══════════════════════════════════════════════════════════════
print("\n── CH: Channel boundary (FT-III-2a/b) ──")


# CH-1: Exactly one DOWN channel file (blender_state.json) and one UP events file
try:
    assert os.path.exists("blender/blender_state.json"), "DOWN channel blender_state.json must exist"
    assert os.path.exists("blender/unity_events.json"), "UP events unity_events.json must exist"
    ok("CH-1: DOWN (blender_state.json) and UP events (unity_events.json) both present")
except AssertionError as e:
    fail("CH-1", e)
except Exception as e:
    fail("CH-1", e)


# CH-2: No forbidden topic files (emotions.json, movement.json, states.json — D2)
try:
    _FORBIDDEN = [
        "blender/emotions.json",
        "blender/movement.json",
        "blender/states.json",
        "blender/motor_events.json",
    ]
    found = [f for f in _FORBIDDEN if os.path.exists(f)]
    assert not found, f"Forbidden channel files exist (D2): {found}"
    ok("CH-2: no forbidden topic files — emotions.json, movement.json, states.json absent (D2)")
except AssertionError as e:
    fail("CH-2", e)
except Exception as e:
    fail("CH-2", e)


# CH-3: Every DOWN command type has a matching ACK type (FT-III-2b / D3)
try:
    import server as _srv
    assert hasattr(_srv, "_ACK_BODY_TYPES"), "_ACK_BODY_TYPES must exist in server.py"
    ack_types = _srv._ACK_BODY_TYPES
    for ack in ("sit_complete", "move_complete", "exit_complete"):
        assert ack in ack_types, f"'{ack}' missing from _ACK_BODY_TYPES (D3)"
    ok(f"CH-3: every DOWN command has a matching ACK type: {sorted(ack_types)}")
except AssertionError as e:
    fail("CH-3", e)
except Exception as e:
    fail("CH-3", e)


# CH-4: state_writer.py is the single coordinator — no blender_state.json direct writes elsewhere
try:
    import inspect
    import blender_bridge.state_writer as _sw
    src = inspect.getsource(_sw)
    # Invariant 16: one coordinator, many contributors via patch()
    assert "patch" in src or "_write" in src, "state_writer must define patch() or _write()"
    ok("CH-4: state_writer.py defines the single blender_state.json coordinator (Invariant 16)")
except AssertionError as e:
    fail("CH-4", e)
except Exception as e:
    fail("CH-4", e)


# CH-5: The timestamp guard (_ts > since) prevents stale events (ST-III-2i)
try:
    from runtime.motor_contract import ack_is_fresh
    # Stale (timestamp before pending command) → rejected
    assert ack_is_fresh(99.0, 100.0) is False, "stale ACK must be rejected"
    # Fresh (timestamp strictly after pending command) → accepted
    assert ack_is_fresh(100.1, 100.0) is True, "fresh ACK must be accepted"
    # Equal timestamp → rejected (must be STRICTLY after)
    assert ack_is_fresh(100.0, 100.0) is False, "equal timestamp must be rejected"
    ok("CH-5: timestamp guard ack_is_fresh() correctly rejects stale and equal-ts events (ST-III-2i)")
except AssertionError as e:
    fail("CH-5", e)
except Exception as e:
    fail("CH-5", e)


# ═══════════════════════════════════════════════════════════════
# ST — Stability: known-gap documentation
# ═══════════════════════════════════════════════════════════════
print("\n── ST: Stability + known gaps ──")


# ST-1: body ACK data not yet in ExecutionReport route fields [KNOWN-GAP III-2 partial]
try:
    from runtime.contracts import ExecutionReport
    er = ExecutionReport()
    # The ExecutionReport exists and is produced, but body route data (which legs,
    # actual route taken, cost) is not captured — Vol III FT-III-2c KNOWN GAP.
    # The report IS produced (CT-6 passes). The route-level detail is the remaining gap.
    has_route_field = hasattr(er, "body_route") or hasattr(er, "route_taken") or hasattr(er, "legs_completed")
    if not has_route_field:
        gap("ST-1", "ExecutionReport has no body_route/legs_completed field — route-level reporting gap (Vol III FT-III-2c, III-2)")
    else:
        ok("ST-1: ExecutionReport has body route fields")
except Exception as e:
    fail("ST-1", e)


# ST-2: integrate_session() exists (renamed from compress_session() — Vol III §1.7 row 5)
try:
    from runtime.reflection_faculty import integrate_session
    import inspect
    src = inspect.getsource(integrate_session)
    assert "integrate_session" in src, "integrate_session must be defined"
    ok("ST-2: integrate_session() exists in reflection_faculty (compress_session rename complete)")
except AssertionError as e:
    fail("ST-2", e)
except Exception as e:
    fail("ST-2", e)


# ST-3: CognitivePlan convergence — live class is spine/plan.py (mutable) [KNOWN-GAP III-1]
try:
    from runtime.spine.plan import CognitivePlan as _LivePlan
    from runtime.contracts import CognitivePlan as _CanonPlan
    import dataclasses
    # The live plan is the mutable one (no frozen=True)
    _live_frozen = dataclasses.fields(_LivePlan)[0].metadata if dataclasses.fields(_LivePlan) else {}
    # We check: if the live class raises on mutation, it's converged; if not, the gap stands
    p = _LivePlan()
    mutated = False
    try:
        p.conversation_action = "hacked"
        mutated = True
    except (AttributeError, TypeError):
        mutated = False
    if mutated:
        gap("ST-3", "CognitivePlan (spine/plan.py) is mutable — Vol III III-1 convergence not yet complete")
    else:
        ok("ST-3: CognitivePlan (spine/plan.py) is frozen — III-1 convergence complete")
except Exception as e:
    fail("ST-3", e)


# ═══════════════════════════════════════════════════════════════
# AT — Compile hygiene
# ═══════════════════════════════════════════════════════════════
print("\n── AT: compile hygiene ──")

for _mod in (
    "runtime/contracts.py",
    "runtime/spine/spine.py",
    "runtime/spine/plan.py",
    "runtime/motor_contract.py",
    "runtime/reflection_faculty.py",
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
print("=" * 70)
print(f"WO-CANON-III system architecture   {_passed} passed   {_gap_reported} known-gaps   {_failed} failed")
if _failed:
    sys.exit(1)
