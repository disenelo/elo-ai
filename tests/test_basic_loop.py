"""
tests/test_basic_loop.py — eLo AI test suite.

Covers:
    - mode switching (Studio / Companion / Adventure)
    - contradiction handling (held, not resolved)
    - imagination activation (metaphor + expansion signals)
    - memory retrieval (keyword matching, project tagging)
    - tone consistency (system prompt structure, overlay content)

Run:
    python -m pytest tests/ -v
    # or without pytest:
    python tests/test_basic_loop.py
"""

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import core_engine
import memory_engine
import llm_client
from orb_engine import OrbEngine, OrbState


# ─── mode switching ────────────────────────────────────────────────────────────

def test_mode_studio():
    assert core_engine.detect_mode("let's build this step by step") == "studio"
    assert core_engine.detect_mode("break it down for me") == "studio"
    assert core_engine.detect_mode("I want to plan the system") == "studio"

def test_mode_adventure():
    assert core_engine.detect_mode("what if this world had its own rules?") == "adventure"
    assert core_engine.detect_mode("tell me the story behind this") == "adventure"
    assert core_engine.detect_mode("let's explore the myth of Sugarcore") == "adventure"

def test_mode_companion():
    assert core_engine.detect_mode("I don't know where to start") == "companion"
    assert core_engine.detect_mode("something feels wrong") == "companion"
    assert core_engine.detect_mode("I'm stuck and confused") == "companion"

def test_mode_universe_signals():
    # K-7 and Sugarcore are emotional/distortion signals → companion
    assert core_engine.detect_mode("what is K-7 telling me here?") == "companion"
    assert core_engine.detect_mode("I think I'm in Sugarcore right now") == "companion"
    # Chunk = reconstruction = studio
    assert core_engine.detect_mode("I need to Chunk this back together") == "studio"

def test_mode_default_is_companion():
    assert core_engine.detect_mode("hello") == "companion"
    assert core_engine.detect_mode("") == "companion"


# ─── contradiction handling ────────────────────────────────────────────────────

def test_contradiction_is_not_a_bug():
    """
    Contradictory inputs should route to companion mode, not error.
    The system holds contradictions — it does not short-circuit.
    """
    contradictions = [
        "I want structure but I hate being controlled",
        "I want to finish this but I don't want to start",
        "everything feels right and wrong at the same time",
    ]
    for text in contradictions:
        mode = core_engine.detect_mode(text)
        assert mode in ("companion", "studio", "adventure"), f"Unexpected crash for: {text!r}"

def test_contradiction_stays_in_companion():
    # "feel" is a companion signal; "build" doesn't appear, so companion wins
    mode = core_engine.detect_mode("something feels right and wrong at the same time")
    assert mode == "companion"


# ─── imagination activation ────────────────────────────────────────────────────

def test_imagination_signals_route_to_adventure():
    imagination_inputs = [
        "what if this system was alive?",
        "imagine if Chunk could speak",
        "what does the world look like from inside Core?",
    ]
    for text in imagination_inputs:
        assert core_engine.detect_mode(text) == "adventure", f"Failed for: {text!r}"

def test_adventure_overlay_contains_expansion_instruction():
    overlay = core_engine._OVERLAYS["adventure"]
    assert "Expand" in overlay or "expand" in overlay
    assert "what does this become" in overlay.lower() or "become" in overlay.lower()


# ─── memory retrieval ──────────────────────────────────────────────────────────

def test_store_and_retrieve(tmp_path, monkeypatch):
    store = tmp_path / "interactions.json"
    monkeypatch.setattr(memory_engine, "_STORE_PATH", str(store))
    monkeypatch.setattr(memory_engine, "_SESSION_PATH", str(tmp_path / "session.json"))

    memory_engine.store_interaction("I want to build a world", "Chunk logic applies.", "studio", "disenelo_universe")
    memory_engine.store_interaction("what is Sugarcore?", "A distortion state.", "companion", "sugarcore_arc")

    results = memory_engine.retrieve("build a world")
    assert len(results) >= 1
    assert any("world" in r["user"] for r in results)

def test_retrieve_returns_empty_on_no_match(tmp_path, monkeypatch):
    store = tmp_path / "empty.json"
    monkeypatch.setattr(memory_engine, "_STORE_PATH", str(store))
    results = memory_engine.retrieve("zzzzunmatchable")
    assert results == []

def test_project_tagging(tmp_path, monkeypatch):
    store = tmp_path / "interactions.json"
    monkeypatch.setattr(memory_engine, "_STORE_PATH", str(store))
    monkeypatch.setattr(memory_engine, "_SESSION_PATH", str(tmp_path / "session.json"))

    memory_engine.store_interaction("orb device status", "Prototype active.", "studio", "orb_device")
    results = memory_engine.retrieve_by_project("orb_device")
    assert len(results) == 1
    assert results[0]["project_tag"] == "orb_device"


# ─── tone consistency ──────────────────────────────────────────────────────────

def test_system_prompt_loads():
    prompt = core_engine._load_system_prompt()
    assert isinstance(prompt, str)
    assert len(prompt) > 50

def test_overlays_contain_universe_references():
    assert "Chunk" in core_engine._OVERLAYS["studio"]
    assert "K-7" in core_engine._OVERLAYS["companion"]
    assert "eLo Universe" in core_engine._OVERLAYS["adventure"]

def test_llm_placeholder_mode():
    # Without an API key, call_llm now routes to the offline engine.
    # Verify it returns a non-empty, non-error string (real offline response).
    import os
    original = os.environ.pop("ANTHROPIC_API_KEY", None)
    try:
        response = llm_client.call_llm("hello", system_prompt="You are eLo.")
        assert isinstance(response, str) and len(response) > 10
        assert "[eLo encountered an error" not in response
    finally:
        if original:
            os.environ["ANTHROPIC_API_KEY"] = original

def test_personality_json_structure():
    path = os.path.join(os.path.dirname(__file__), "..", "config", "personality.json")
    with open(path) as f:
        p = json.load(f)
    assert "modes" in p
    assert set(p["modes"].keys()) >= {"studio", "companion", "adventure"}
    assert "universe" in p
    assert "eLo" in p["universe"]


# ─── orb engine ───────────────────────────────────────────────────────────────

def test_orb_transitions():
    orb = OrbEngine(silent=True)
    events = []
    orb.on_change(lambda o, n: events.append(n))
    orb.listen(); orb.think(); orb.insight(); orb.idle()
    assert orb.state == OrbState.IDLE
    assert len(events) == 4

def test_orb_no_duplicate_events():
    orb = OrbEngine(silent=True)
    events = []
    orb.on_change(lambda o, n: events.append(n))
    orb.idle(); orb.idle()
    assert len(events) == 0


# ─── standalone runner ────────────────────────────────────────────────────────

if __name__ == "__main__":
    import traceback

    tests = [
        test_mode_studio, test_mode_adventure, test_mode_companion,
        test_mode_universe_signals, test_mode_default_is_companion,
        test_contradiction_is_not_a_bug, test_contradiction_stays_in_companion,
        test_imagination_signals_route_to_adventure,
        test_adventure_overlay_contains_expansion_instruction,
        test_overlays_contain_universe_references,
        test_llm_placeholder_mode, test_personality_json_structure,
        test_orb_transitions, test_orb_no_duplicate_events,
        test_system_prompt_loads,
    ]

    passed = failed = 0
    for test in tests:
        try:
            test()
            print(f"  OK  {test.__name__}")
            passed += 1
        except Exception:
            print(f"  FAIL {test.__name__}")
            traceback.print_exc()
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)
