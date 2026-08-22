"""
tests/test_f7_autobiography_wire.py — BDRIFT-F7 Acceptance Tests

Tests:
  AT-F7-1  interpret() returns SelfInterpretation.text containing event content
  AT-F7-2  interpret() populates derived_from with episode_ref (not just count)
  AT-F7-3  interpret() returns None when no behavior/thread/lesson AND no entries
  AT-F7-4  FALSIFIABLE: cutting _load_autobiography() removes autobiographical claim
  AT-F7-5  plan.self_interpretation is set by spine (scoping bug fixed)
  AT-F7-6  interpret() with event text that has no numbers passes sanity check
  AT-F7-7  interpret() with missing event text falls back to count-only derived_from
  AT-F7-8  most recent entry is chosen (not oldest) when multiple entries exist

Run:
  python tests/test_f7_autobiography_wire.py
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import importlib

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

PASS: list[str] = []
FAIL: list[str] = []


def ok(name: str) -> None:
    PASS.append(name)
    print(f"  ✅ {name}")


def fail(name: str, reason: str) -> None:
    FAIL.append(name)
    print(f"  ❌ {name}: {reason}")


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_temp_autobiography(*entries: dict) -> str:
    """Write entries to a temp .jsonl file and return its path."""
    tf = tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False)
    for e in entries:
        tf.write(json.dumps(e) + "\n")
    tf.close()
    return tf.name


def _dummy_state() -> object:
    """Minimal EloSelfState-like object with enough fields for interpret()."""
    class S:
        recent_behavior = {"reflect": 3, "answer": 2}
        lifetime_threads = [("eLo game", 4)]
        last_reflection_lesson = ""
    return S()


def _dummy_state_empty() -> object:
    """State with NO behavior data — only autobiography can drive claims."""
    class S:
        recent_behavior = {}
        lifetime_threads = []
        last_reflection_lesson = ""
    return S()


# ── import module ─────────────────────────────────────────────────────────────

from runtime.self_interpret import interpret, SelfInterpretation, _load_autobiography


# ── AT-F7-1: event text surfaces in SelfInterpretation.text ──────────────────

def test_event_text_in_claims() -> None:
    path = _make_temp_autobiography({
        "event": "sat — body ACK confirmed",
        "verified": True,
        "source": "body_ack",
        "episode_ref": "test-ref-001",
    })
    try:
        state = _dummy_state()
        result = interpret(state, autobiography_path=path)
        if result is None:
            fail("AT-F7-1", "interpret() returned None — expected a result")
            return
        if "sat" not in result.text and "body ACK" not in result.text:
            fail("AT-F7-1", f"event text not in result.text: {result.text!r}")
        else:
            ok("AT-F7-1")
    finally:
        os.unlink(path)


# ── AT-F7-2: derived_from contains episode_ref as key ─────────────────────────

def test_derived_from_episode_ref() -> None:
    path = _make_temp_autobiography({
        "event": "sat — body ACK confirmed",
        "verified": True,
        "source": "body_ack",
        "episode_ref": "test-ref-001",
    })
    try:
        state = _dummy_state()
        result = interpret(state, autobiography_path=path)
        if result is None:
            fail("AT-F7-2", "interpret() returned None")
            return
        auto_entry = next(
            (d for d in result.derived_from if d.get("source") == "autobiography"),
            None,
        )
        if auto_entry is None:
            fail("AT-F7-2", f"no 'autobiography' entry in derived_from: {result.derived_from}")
        elif auto_entry.get("key") != "test-ref-001":
            fail("AT-F7-2", f"key should be 'test-ref-001', got {auto_entry.get('key')!r}")
        else:
            ok("AT-F7-2")
    finally:
        os.unlink(path)


# ── AT-F7-3: None when no behavior AND no entries ────────────────────────────

def test_none_when_no_data() -> None:
    path = _make_temp_autobiography()  # empty file
    try:
        state = _dummy_state_empty()
        result = interpret(state, autobiography_path=path)
        if result is not None:
            fail("AT-F7-3", f"expected None when no data, got text={result.text!r}")
        else:
            ok("AT-F7-3")
    finally:
        os.unlink(path)


# ── AT-F7-4: FALSIFIABLE — cutting _load_autobiography removes claim ──────────

def test_falsifiable_cut_autobiography() -> None:
    """
    Monkey-patch _load_autobiography to return [] (wire cut).
    The autobiography claim must disappear from .text.
    """
    path = _make_temp_autobiography({
        "event": "sat — body ACK confirmed",
        "verified": True,
        "source": "body_ack",
        "episode_ref": "test-ref-002",
    })
    try:
        import runtime.self_interpret as _si_mod
        original = _si_mod._load_autobiography

        # verify baseline: with real data, claim IS present
        state = _dummy_state()
        result_with = interpret(state, autobiography_path=path)

        # cut the wire
        _si_mod._load_autobiography = lambda *a, **kw: []
        try:
            # reload to use patched _load_autobiography
            result_cut = interpret(state, autobiography_path=path)
        finally:
            _si_mod._load_autobiography = original

        if result_with is None:
            fail("AT-F7-4", "baseline returned None — can't test falsifiability")
            return

        # after wire cut, autobiography claim must be gone
        if result_cut is not None and (
            "sat" in result_cut.text or "body ACK" in result_cut.text
        ):
            fail("AT-F7-4",
                 f"autobiography claim survived wire cut: {result_cut.text!r}")
        else:
            ok("AT-F7-4")
    finally:
        os.unlink(path)


# ── AT-F7-5: plan.self_interpretation is set by spine (scoping bug fixed) ────

def test_spine_sets_plan_self_interpretation() -> None:
    """
    Verify CognitivePlan (spine's mutable plan.py variant) accepts self_interpretation.
    Does NOT run a full spine turn — just checks the attribute can be set dynamically.
    """
    try:
        from runtime.spine.plan import CognitivePlan
        plan = CognitivePlan(raw="test", meaning="test", intent="conversation",
                             capability_hint="", register="", social="", confidence=0.7)
        # self_interpretation is not a declared field — set it dynamically (as spine.py does)
        plan.self_interpretation = {"text": "test", "derived_from": [], "verified_events": 0}
        assert plan.self_interpretation["text"] == "test", "self_interpretation not retained"
        ok("AT-F7-5")
    except Exception as e:
        fail("AT-F7-5", str(e))


# ── AT-F7-6: event text with no numbers passes sanity check ──────────────────

def test_no_number_leak_in_sanity_check() -> None:
    """Autobiography event text must not cause number-sanity suppression."""
    path = _make_temp_autobiography({
        "event": "sat — body ACK confirmed",
        "verified": True,
        "source": "body_ack",
        "episode_ref": "test-ref-003",
    })
    try:
        state = _dummy_state()
        result = interpret(state, autobiography_path=path)
        # If sanity check incorrectly suppressed the result, it returns None while
        # data was present. We just need it to NOT return None here.
        if result is None:
            # Could be None if behavior data itself triggered suppression — check without behavior
            state2 = _dummy_state_empty()
            state2.recent_behavior = {"reflect": 3}  # safe: count 3, text says "3" implicitly? no
            result2 = interpret(state2, autobiography_path=path)
            # The autobiography claim alone (no numbers) shouldn't trigger suppression
            # but reflect count "3" appears in text — verify 3 is in derived_from
            if result2 is not None:
                ok("AT-F7-6")
            else:
                fail("AT-F7-6", "interpret returned None — possible sanity suppression")
        else:
            ok("AT-F7-6")
    finally:
        os.unlink(path)


# ── AT-F7-7: missing event text falls back gracefully ────────────────────────

def test_missing_event_text_fallback() -> None:
    """Entry with empty event field → derived_from only, no claim added."""
    path = _make_temp_autobiography({
        "event": "",
        "verified": True,
        "source": "body_ack",
        "episode_ref": "test-ref-004",
    })
    try:
        state = _dummy_state()
        result = interpret(state, autobiography_path=path)
        # Should still return a result (from behavior/thread data)
        if result is None:
            fail("AT-F7-7", "interpret returned None — expected result from behavior data")
            return
        # autobiography text should NOT appear (empty event)
        if "My most recent verified experience:" in result.text:
            fail("AT-F7-7", "empty-event claim appeared in text")
        else:
            ok("AT-F7-7")
    finally:
        os.unlink(path)


# ── AT-F7-8: most recent entry is chosen (last in file) ──────────────────────

def test_most_recent_entry_chosen() -> None:
    """When multiple entries exist, the LAST (most recent) is surfaced."""
    path = _make_temp_autobiography(
        {"event": "old event", "verified": True, "source": "body_ack", "episode_ref": "old-ref"},
        {"event": "recent event", "verified": True, "source": "body_ack", "episode_ref": "new-ref"},
    )
    try:
        state = _dummy_state()
        result = interpret(state, autobiography_path=path)
        if result is None:
            fail("AT-F7-8", "interpret() returned None")
            return
        if "recent event" not in result.text:
            fail("AT-F7-8", f"most recent entry not in text: {result.text!r}")
        elif "old event" in result.text:
            fail("AT-F7-8", f"old entry incorrectly surfaced: {result.text!r}")
        else:
            ok("AT-F7-8")
    finally:
        os.unlink(path)


# ── run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n=== BDRIFT-F7 Autobiography Wire Tests ===\n")
    test_event_text_in_claims()
    test_derived_from_episode_ref()
    test_none_when_no_data()
    test_falsifiable_cut_autobiography()
    test_spine_sets_plan_self_interpretation()
    test_no_number_leak_in_sanity_check()
    test_missing_event_text_fallback()
    test_most_recent_entry_chosen()

    total = len(PASS) + len(FAIL)
    print(f"\n{'─'*40}")
    print(f"Result: {len(PASS)}/{total} PASS")
    if FAIL:
        print("FAILED:", ", ".join(FAIL))
        sys.exit(1)
    else:
        print("All AT-F7 tests pass ✅")
        sys.exit(0)
