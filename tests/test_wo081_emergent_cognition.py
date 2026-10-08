"""
tests/test_wo081_emergent_cognition.py — WO-081: Emergent Cognition Cluster

Assertions:
  AT-0: internal_intents returns [] for an empty/bare state (no fabricated urgency)
  AT-1: internal_intents returns items only when real cognitive state justifies it
  AT-2: absence threshold — idle < 300s + real state → no idle intent; idle ≥ 300s → intent fires
  AT-3: append_autobiography creates and appends — never overwrites existing entries
  AT-4: server.py wires emergent_block; py_compile clean

Run: python3 tests/test_wo081_emergent_cognition.py
"""
from __future__ import annotations

import json
import os
import py_compile
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_passed = _failed = 0


def ok(label: str):
    global _passed
    _passed += 1
    print(f"  ✅ {label}")


def fail(label: str, err):
    global _failed
    _failed += 1
    print(f"  ❌ {label}: {err}")


_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _empty_state():
    from self.elo_self_model import EloSelfState
    return EloSelfState(
        mood=0.55,
        curiosity=0.60,
        focal_thread="",
        inner_events=[],
        lifetime_threads=[],
        recent_behavior={},
        session_turns=0,
        current_action="idle",
    )


# ── AT-0: empty state → no intents (no fabricated urgency) ───────────────────
try:
    from self.emergent_cognition import internal_intents

    state = _empty_state()
    result = internal_intents(state, idle_seconds=0.0)
    assert isinstance(result, list), "internal_intents must return a list"
    assert result == [], (
        f"internal_intents must return [] for empty state, got {result}"
    )

    # Even with long idle, empty state must produce nothing
    result_idle = internal_intents(state, idle_seconds=1000.0)
    assert result_idle == [], (
        f"internal_intents must return [] for empty state even with high idle, got {result_idle}"
    )
    ok("AT-0: internal_intents returns [] for empty state — no fabricated urgency")
except AssertionError as e:
    fail("AT-0", e)
except Exception as e:
    fail("AT-0", e)


# ── AT-1: real state → intents generate, tracing to cognitive cause ───────────
try:
    from self.emergent_cognition import internal_intents

    # High curiosity + focal_thread + enough session turns + matching inner events
    state = _empty_state()
    state.focal_thread = "the game world"
    state.session_turns = 5
    state.curiosity = 0.85
    state.current_action = "idle"
    state.inner_events = ["drawn_in", "curiosity_spike", "drawn_in", "creative_spark"]
    state.lifetime_threads = [["creativity", 3]]

    result = internal_intents(state, idle_seconds=0.0)
    assert isinstance(result, list), "must return a list"
    assert len(result) > 0, (
        f"internal_intents should produce items for rich state (focal_thread + curiosity + events), got {result}"
    )
    for item in result:
        assert "kind" in item,     f"each intent must have 'kind': {item}"
        assert "source" in item,   f"each intent must have 'source': {item}"
        assert "trigger" in item,  f"each intent must have 'trigger': {item}"
        assert "priority" in item, f"each intent must have 'priority': {item}"
        assert item["priority"] == "low", (
            f"internal intents must be low priority, got {item['priority']!r}"
        )
    sources = [i["source"] for i in result]
    assert any(s in sources for s in ("active_thread", "curiosity_peak", "absence_awareness")), (
        f"at least one intent must trace to a real source, got sources: {sources}"
    )
    ok(f"AT-1: internal_intents generates {len(result)} item(s) from real state, all low-priority")
except AssertionError as e:
    fail("AT-1", e)
except Exception as e:
    fail("AT-1", e)


# ── AT-2: absence threshold — idle gate enforced ──────────────────────────────
try:
    from self.emergent_cognition import internal_intents, _ABSENT_THRESHOLD

    # State with real history but idle below threshold — no absence intent
    state = _empty_state()
    state.focal_thread = "exploration"
    state.curiosity = 0.85
    state.lifetime_threads = [["movement", 4]]
    state.inner_events = ["curiosity_spike", "drawn_in"]

    below = [i for i in internal_intents(state, idle_seconds=_ABSENT_THRESHOLD - 1)
             if i.get("source") == "absence_awareness"]
    assert below == [], (
        f"no absence_awareness intent below threshold, got {below}"
    )

    # Same state but idle AT threshold → absence intent should fire
    above = [i for i in internal_intents(state, idle_seconds=_ABSENT_THRESHOLD)
             if i.get("source") == "absence_awareness"]
    assert len(above) >= 1, (
        f"absence_awareness intent should fire at threshold {_ABSENT_THRESHOLD}s, got {above}"
    )
    assert above[0]["kind"] == "exploration", (
        f"absence intent should be exploration kind, got {above[0]['kind']!r}"
    )
    ok(f"AT-2: absence threshold enforced at {_ABSENT_THRESHOLD}s — below=no intent, at=intent fires")
except AssertionError as e:
    fail("AT-2", e)
except Exception as e:
    fail("AT-2", e)


# ── AT-3: append_autobiography is append-only, creates the file ───────────────
try:
    from unittest.mock import patch
    from self.emergent_cognition import append_autobiography, recent_autobiography

    with tempfile.TemporaryDirectory() as td:
        fake_autob = os.path.join(td, "autobiography.jsonl")
        import self.emergent_cognition as _ec_mod
        original_path = _ec_mod._AUTOB
        _ec_mod._AUTOB = fake_autob
        try:
            # File doesn't exist yet — should create
            append_autobiography("wall-jump succeeded", kind="movement",
                                 verified=True, source="body_ack", episode_ref="test.001")
            assert os.path.exists(fake_autob), "append_autobiography must create the file"

            # Append a second entry — first must still be there
            append_autobiography("sat beside David", kind="presence",
                                 verified=True, source="body_ack", episode_ref="test.002")
            with open(fake_autob, encoding="utf-8") as f:
                lines = [l.strip() for l in f if l.strip()]
            assert len(lines) == 2, f"must have 2 entries after 2 appends, got {len(lines)}"

            entries = [json.loads(l) for l in lines]
            kinds = [e["kind"] for e in entries]
            assert "movement" in kinds and "presence" in kinds, (
                f"both kinds must be present, got {kinds}"
            )
            # First entry must NOT have been overwritten
            assert entries[0]["event"] == "wall-jump succeeded", (
                f"first entry overwritten — must be append-only: {entries[0]}"
            )
        finally:
            _ec_mod._AUTOB = original_path

    ok("AT-3: append_autobiography creates file + is truly append-only (2 entries confirmed)")
except AssertionError as e:
    fail("AT-3", e)
except Exception as e:
    fail("AT-3", e)


# ── AT-4: server.py wires emergent_block; py_compile clean ────────────────────
try:
    server_path = os.path.join(_BASE, "server.py")
    with open(server_path, encoding="utf-8") as f:
        src = f.read()

    assert "emergent_cognition" in src, (
        "server.py must import from self.emergent_cognition (WO-081 wiring)"
    )
    assert "_ec_emergent_block" in src, (
        "server.py must call _ec_emergent_block() (WO-081 injection)"
    )
    assert "WO-081" in src, (
        "server.py must carry WO-081 marker at injection site"
    )

    py_compile.compile(server_path, doraise=True)
    ok("AT-4: server.py wires emergent_block with WO-081 marker; py_compile clean")
except AssertionError as e:
    fail("AT-4", e)
except Exception as e:
    fail("AT-4", e)


# ── Summary ───────────────────────────────────────────────────────────────────
print()
print("=" * 62)
print(f"WO-081 emergent cognition   {_passed} passed   {_failed} failed")
if _failed:
    sys.exit(1)
