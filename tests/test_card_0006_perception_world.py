"""
tests/test_card_0006_perception_world.py — Acceptance tests for card 0006
(WO-CANON-XII + XV finish: perception → world state, single-read discipline,
structured fidelity flags)

Card: blender/agent_bus/builder/DOING/06_WO-CANON-XII_XV_perception_world.md
Specs: Volume_XII/03_World_State_Handoff.md · Volume_XII/04_Perceptual_Fidelity.md
       Volume_XV/00_Metadata.md · Volume_XV/01_Unified_World_State.md

  AT-1: assemble_world_state(perception=…) populates DesktopState from a live window
        (not `absent`) — the Vol XII Ch.3 §3.2 copy step is live.
  AT-2: Faculties read the world from the carrier (Temporal reads world.time verbatim,
        never calls time.time() mid-turn).
  AT-3: A truncated modality read → PerceptionResult.partial=True (structural signal,
        not just a Chrome-path prompt rail). Vol XII Ch.4 §4.3.
  AT-4: PerceptionResult carries a `relations` tuple (default empty) — perception
        asserts no inter-item relations unless grounded. Vol XII Ch.4 §4.1.3.
  AT-5: perception.partial propagates to LiveWorldState.domain_health.desktop.partial
        — one carrier-side flag downstream consumers can enforce pre-prompt.
  AT-6: claim_gate._vision_gate reads from the carrier when passed (single-read
        discipline; no second read of blender_state.json for the same fact).
  AT-7: py_compile clean on all edited files.

Run: python3 tests/test_card_0006_perception_world.py
"""
from __future__ import annotations

import os
import py_compile
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_passed = _failed = 0


def ok(label: str) -> None:
    global _passed
    _passed += 1
    print(f"  ✅ {label}")


def fail(label: str, err) -> None:
    global _failed
    _failed += 1
    print(f"  ❌ {label}: {err}")


_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ── Stub window state so `assemble_world_state` / `perceive_from_live_state`
#    see a populated desktop deterministically ──────────────────────────────────

class _FakeWS:
    app = "Visual Studio Code"
    title = "spine.py — elo-ai"
    activity = "coding"
    available = True


_fake_ws_mod = types.ModuleType("desktop.window_state")
_fake_ws_mod.get = lambda: _FakeWS()
sys.modules["desktop.window_state"] = _fake_ws_mod


def _reload(name_fragment: str) -> None:
    for k in list(sys.modules):
        if name_fragment in k:
            del sys.modules[k]


# Fresh imports pick up the stubbed window_state module.
_reload("live_world_state")
_reload("perception_faculty")

from faculties.perception.perception_faculty import (
    PerceptionResult,
    perceive,
    perceive_from_live_state,
    tag_partial,
)
from world.live_world_state import assemble_world_state


# ── AT-1: perception → world-state copy populates DesktopState from live window ─
try:
    perception = perceive_from_live_state()
    world = assemble_world_state(turn_id="at1", perception=perception)

    assert world.desktop.active_app == "Visual Studio Code", (
        f"desktop.active_app expected 'Visual Studio Code', got {world.desktop.active_app!r}"
    )
    desk_health = world.domain_health.get("desktop", {})
    assert desk_health.get("status") != "absent", (
        f"desktop should not be absent when a window is present; health={desk_health!r}"
    )
    assert desk_health.get("source") == "PerceptionFaculty", (
        f"desktop.source should be PerceptionFaculty (Ch.3 §3.2 copy), got {desk_health.get('source')!r}"
    )
    ok("AT-1: DesktopState populated from PerceptionResult (Vol XII Ch.3 §3.2 copy)")
except AssertionError as e:
    fail("AT-1", e)
except Exception as e:
    fail("AT-1", e)


# ── AT-2: Faculties read the world from the carrier (Temporal reads world.time) ─
try:
    from faculties.temporal.faculty import _build_temporal_state

    world = assemble_world_state(turn_id="at2")
    # world.time is set by assemble_world_state from time.localtime — Temporal reads
    # this domain slice, not time.time() itself. Verifies the read discipline.
    ts = _build_temporal_state(world, last_interaction_ts=0.0, idle_seconds=0.0)
    assert ts.now_iso == world.time.now_iso, (
        "temporal faculty must read world.time.now_iso verbatim from the carrier "
        f"(got {ts.now_iso!r}, expected {world.time.now_iso!r})"
    )
    assert ts.part_of_day == world.time.part_of_day, (
        "temporal.part_of_day must equal world.time.part_of_day (no double-read)"
    )
    ok("AT-2: temporal faculty reads world.time from the carrier (no double-read)")
except AssertionError as e:
    fail("AT-2", e)
except Exception as e:
    fail("AT-2", e)


# ── AT-3: Truncated modality read → PerceptionResult.partial=True (structured) ──
try:
    # A truncated window title is a fragment — the structural fidelity flag must fire,
    # independent of any Chrome-path prompt rail.
    result_partial = perceive(window_app="Chrome", window_title="A very long title that got cut…")
    assert result_partial.partial is True, (
        "partial must be True when a modality read ends with an ellipsis "
        f"(modality_reads={result_partial.modality_reads!r})"
    )

    # A clean title must NOT trip the partial flag on its own (confidence permitting).
    result_clean = perceive(window_app="Chrome", window_title="Full complete title")
    # Note: confidence penalty from absent vision may still make it partial; the point is
    # that truncation is a sufficient trigger and does not require the Chrome rail.
    assert tag_partial("cut off…").startswith("[PARTIAL:"), "tag_partial must flag truncated text"
    assert tag_partial("clean") == "clean", "tag_partial must pass clean text through"
    ok("AT-3: PerceptionResult.partial fires structurally on truncated reads (Ch.4 §4.3)")
except AssertionError as e:
    fail("AT-3", e)
except Exception as e:
    fail("AT-3", e)


# ── AT-4: PerceptionResult.relations exists and defaults empty ─────────────────
try:
    result = perceive(window_app="Chrome", window_title="A title")
    assert hasattr(result, "relations"), "PerceptionResult must expose a `relations` tuple"
    assert isinstance(result.relations, tuple), (
        f"relations must be a tuple, got {type(result.relations).__name__}"
    )
    assert result.relations == (), (
        "relations must default to () — perception asserts no inter-item links (Ch.4 §4.1.3)"
    )
    ok("AT-4: PerceptionResult.relations = () default (no fabricated links)")
except AssertionError as e:
    fail("AT-4", e)
except Exception as e:
    fail("AT-4", e)


# ── AT-5: perception.partial propagates to domain_health.desktop.partial ───────
try:
    partial_perception = perceive(window_app="Chrome", window_title="Cut off title…")
    assert partial_perception.partial is True, "sanity: perception must be partial for this test"

    world = assemble_world_state(turn_id="at5", perception=partial_perception)
    desk_health = world.domain_health.get("desktop", {})
    assert desk_health.get("partial") is True, (
        f"domain_health.desktop.partial must be True when perception.partial=True; "
        f"got {desk_health!r}"
    )
    ok("AT-5: perception.partial → domain_health.desktop.partial (carrier-side flag)")
except AssertionError as e:
    fail("AT-5", e)
except Exception as e:
    fail("AT-5", e)


# ── AT-6: claim_gate._vision_gate reads from the carrier ───────────────────────
try:
    _reload("claim_gate")
    from runtime.claim_gate import _vision_gate, classify_and_gate
    from world.live_world_state import EnvironmentState, LiveWorldState

    class _WorldVisionOff:
        environment = EnvironmentState(os_name="macOS", screen_record=False, vision_active=False)

    class _WorldVisionOn:
        environment = EnvironmentState(os_name="macOS", screen_record=False, vision_active=True)

    off = _vision_gate(world=_WorldVisionOff())
    on = _vision_gate(world=_WorldVisionOn())

    assert off is not None, "vision_active=False in carrier should trip the UNKNOWN tier"
    assert "vision isn't active" in off.lower(), (
        f"expected UNKNOWN response about vision, got {off!r}"
    )
    assert on is None, (
        f"vision_active=True in carrier should NOT trip the gate; got {on!r}"
    )

    # classify_and_gate passes world through.
    _t, _r = classify_and_gate("can you see my screen", world=_WorldVisionOff())
    assert _t == "capability.vision" and _r is not None, (
        f"classify_and_gate should forward world to _vision_gate; got ({_t!r}, {_r!r})"
    )
    ok("AT-6: claim_gate reads vision from the carrier (single-read discipline)")
except AssertionError as e:
    fail("AT-6", e)
except Exception as e:
    fail("AT-6", e)


# ── AT-7: py_compile clean on all edited files ─────────────────────────────────
try:
    for rel in (
        "faculties/perception/perception_faculty.py",
        "world/live_world_state.py",
        "runtime/claim_gate.py",
        "runtime/spine/spine.py",
    ):
        py_compile.compile(os.path.join(_BASE, rel), doraise=True)
    ok("AT-7: py_compile clean on all edited files")
except py_compile.PyCompileError as e:
    fail("AT-7", e)
except Exception as e:
    fail("AT-7", e)


print()
print("=" * 62)
print(f"card 0006 perception/world    {_passed} passed   {_failed} failed")
if _failed:
    sys.exit(1)
