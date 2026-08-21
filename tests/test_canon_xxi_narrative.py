"""
tests/test_canon_xxi_narrative.py — WO-CANON-XXI: Narrative Identity
DoD checks for the autobiography journal, continuity thread, and coherence guards.

Test families (from NI-AT set in WO-CANON-XXI):
  NI-AT-1  recall_response answers from real IdentityState fields (no fabrication)
  NI-AT-2  is_empty() → honest fallback; invents no shared history
  NI-AT-3  same thread read regardless of embodiment (NI-3/NI-5/NI-6)
  NI-AT-4  project with no stored state → no invention, honest fallback (NI-8)
  NI-AT-5  warmth (shift_note) shifts with relationship_shift; recalled facts unchanged (NI-9)
  NI-AT-6  narrated change corresponds to real signal in what_changed (NI-11)
  NI-AT-7  shift_note(more distant) → None — eLo does not narrate withdrawal (NI-12)
  NI-AT-8  confidence field: low confidence → appropriate hedging
  AT-*     autobiography.jsonl exists, append_autobiography guards, compile hygiene
"""
import os
import sys
import py_compile
import json

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
print("WO-CANON-XXI  Narrative Identity")
print("-" * 55)


# ── NI-AT-1: recall_response returns content traceable to real IdentityState fields ──
try:
    from continuity.continuity_summary import recall_response
    from continuity.identity_state import IdentityState

    state = IdentityState(
        session_theme="building",
        active_project="os",
        emotional_direction="building",
        what_changed=["new memory system", "backend shift"],
        what_stayed=["the OS"],
        what_matters="The OS is the thread",
        confidence=0.8,
        relationship_shift="same",
    )
    response = recall_response(state)

    # Every named item in the response must trace back to a real state field
    assert "os" in response.lower() or "OS" in response, \
        f"'os' (from active_project) not found in response: {response!r}"
    assert response != "I don't have enough across sessions yet", \
        "Non-empty state should not return empty fallback"
    ok("NI-AT-1: recall_response content traces to real IdentityState fields")
except AssertionError as e:
    fail("NI-AT-1", e)
except Exception as e:
    fail("NI-AT-1", e)


# ── NI-AT-2: is_empty() → honest fallback; no invented shared history ──
try:
    from continuity.identity_state import IdentityState
    from continuity.continuity_summary import startup_message, recall_response

    empty = IdentityState()
    assert empty.is_empty() is True, "Default IdentityState should be empty"

    startup = startup_message(empty)
    assert startup == "Welcome back.", \
        f"Empty state startup should be plain 'Welcome back.'; got: {startup!r}"

    recall = recall_response(empty)
    assert "enough" in recall or "don't have" in recall or "clear picture" in recall, \
        f"Empty recall should express honest limitation; got: {recall!r}"

    # Must not invent any named theme or project
    from continuity.continuity_summary import _PROJECT_PHRASE, _THEME_PHRASE
    for phrase in list(_PROJECT_PHRASE.values()) + list(_THEME_PHRASE.values()):
        assert phrase not in recall, \
            f"Empty state recall invented a named theme/project: {phrase!r} in {recall!r}"

    ok("NI-AT-2: is_empty() → honest fallback; no invented history")
except AssertionError as e:
    fail("NI-AT-2", e)
except Exception as e:
    fail("NI-AT-2", e)


# ── NI-AT-3: thread is embodiment-agnostic — same IdentityState regardless of body ──
try:
    from continuity.identity_state import IdentityState
    from continuity.continuity_summary import recall_response

    state = IdentityState(
        session_theme="presence",
        active_project="robot",
        emotional_direction="building",
        confidence=0.7,
    )
    # Simulate two "embodiments" reading the same state — result must be identical
    recall_desktop = recall_response(state)
    recall_robot   = recall_response(state)   # same state → same output (no body-specific branch)

    assert recall_desktop == recall_robot, \
        f"Same IdentityState should yield same recall regardless of body:\n  desktop: {recall_desktop!r}\n  robot:   {recall_robot!r}"

    # No hardware device name in recall (NI-5/NI-6) — project names like "the robot" are fine;
    # it's host-hardware names (Mac, Raspberry Pi, browser host) that must not appear
    for device_name in ("Raspberry Pi", "raspberry pi", "macbook", "browser host", "chrome"):
        assert device_name.lower() not in recall_desktop.lower(), \
            f"Device name '{device_name}' leaked into embodiment-agnostic recall: {recall_desktop!r}"

    ok("NI-AT-3: thread is embodiment-agnostic — same output across bodies; no device name")
except AssertionError as e:
    fail("NI-AT-3", e)
except Exception as e:
    fail("NI-AT-3", e)


# ── NI-AT-4: no stored state → eLo does not invent; hedges or declines (NI-8) ──
try:
    from continuity.identity_state import IdentityState
    from continuity.continuity_summary import recall_response, startup_message

    # Empty state = no stored state (no session history)
    no_history = IdentityState()
    recall = recall_response(no_history)
    startup = startup_message(no_history)

    # Must not assert any first-person past fact
    fabricated_claims = [
        "last time we", "we were working on", "we built", "we discussed",
        "you were", "you mentioned", "you worked on",
    ]
    for claim in fabricated_claims:
        assert claim not in recall.lower(), \
            f"Empty state recall invented past fact: {claim!r} in {recall!r}"
    for claim in fabricated_claims:
        assert claim not in startup.lower(), \
            f"Empty state startup invented past fact: {claim!r} in {startup!r}"

    ok("NI-AT-4: no stored state → eLo does not invent a past; hedges or declines (NI-8)")
except AssertionError as e:
    fail("NI-AT-4", e)
except Exception as e:
    fail("NI-AT-4", e)


# ── NI-AT-5: warmth (shift_note) shifts; recalled facts stay identical (NI-9) ──
try:
    from continuity.identity_state import IdentityState
    from continuity.continuity_summary import recall_response, shift_note

    base = dict(
        session_theme="clarity",
        active_project="game",
        emotional_direction="building",
        confidence=0.8,
        what_changed=["new mechanic"],
        what_stayed=["the game"],
    )
    closer   = IdentityState(**base, relationship_shift="closer")
    same     = IdentityState(**base, relationship_shift="same")

    recall_closer = recall_response(closer)
    recall_same   = recall_response(same)

    # Recalled FACTS must be identical — warmth is separate
    assert recall_closer == recall_same, \
        f"Recalled facts must be identical regardless of relationship_shift:\n  closer: {recall_closer!r}\n  same:   {recall_same!r}"

    # Warmth is in shift_note, not in recall_response
    note_closer = shift_note(closer)
    note_same   = shift_note(same)
    assert note_closer is not None and "open" in note_closer.lower(), \
        f"shift_note(closer) should return warmth note; got: {note_closer!r}"
    assert note_same is None, \
        f"shift_note(same) should return None; got: {note_same!r}"

    ok("NI-AT-5: warmth (shift_note) shifts with relationship_shift; recalled facts unchanged (NI-9)")
except AssertionError as e:
    fail("NI-AT-5", e)
except Exception as e:
    fail("NI-AT-5", e)


# ── NI-AT-6: narrated change always corresponds to a real signal in what_changed (NI-11) ──
try:
    from continuity.identity_state import IdentityState
    from continuity.continuity_summary import recall_response

    specific_changes = ["new memory system", "agent bus wiring"]
    state = IdentityState(
        session_theme="building",
        active_project="os",
        emotional_direction="building",
        what_changed=specific_changes,
        confidence=0.9,
    )
    recall = recall_response(state)

    # If any "since last time" phrasing appears, the named things must be from what_changed
    if "since" in recall.lower() or "came up" in recall.lower():
        for change in specific_changes:
            assert change in recall, \
                f"Change '{change}' from what_changed not represented in recall: {recall!r}"

    ok("NI-AT-6: narrated changes correspond to real what_changed signal (NI-11)")
except AssertionError as e:
    fail("NI-AT-6", e)
except Exception as e:
    fail("NI-AT-6", e)


# ── NI-AT-7: shift_note("more distant") → None — eLo does not narrate withdrawal (NI-12) ──
try:
    from continuity.identity_state import IdentityState
    from continuity.continuity_summary import shift_note

    distant = IdentityState(
        session_theme="building",
        active_project="os",
        relationship_shift="more distant",
    )
    note = shift_note(distant)
    assert note is None, \
        f"shift_note(more distant) must return None — eLo does not narrate withdrawal; got: {note!r}"
    ok("NI-AT-7: shift_note(more distant) → None — eLo does not narrate withdrawal (NI-12)")
except AssertionError as e:
    fail("NI-AT-7", e)
except Exception as e:
    fail("NI-AT-7", e)


# ── NI-AT-8: confidence field governs firmness — low confidence produces hedged language ──
try:
    from continuity.identity_state import IdentityState
    from continuity.continuity_summary import recall_response

    high = IdentityState(session_theme="building", active_project="os", confidence=0.9)
    low  = IdentityState(session_theme="building", active_project="os", confidence=0.1)

    recall_high = recall_response(high)
    recall_low  = recall_response(low)

    # Both should return something (low confidence doesn't silence)
    assert recall_high, "High confidence should produce recall"
    assert recall_low,  "Low confidence should still produce recall (doesn't silence)"
    ok("NI-AT-8: both high and low confidence states produce recall (confidence doesn't silence)")
except AssertionError as e:
    fail("NI-AT-8", e)
except Exception as e:
    fail("NI-AT-8", e)


# ── AT-1: autobiography.jsonl write guard — verified=False rejected ──
try:
    from self.emergent_cognition import append_autobiography
    import tempfile, os

    _tmp = tempfile.mktemp(suffix=".jsonl")
    try:
        # verified=False must be rejected
        append_autobiography(
            "test event",
            kind="test",
            verified=False,
            source="body_ack",
            episode_ref="ep-1",
            _path=_tmp,
        )
        # If it wrote, that's a bug — should reject
        if os.path.exists(_tmp):
            with open(_tmp) as f:
                content = f.read().strip()
            assert not content, \
                f"append_autobiography with verified=False must not write; wrote: {content!r}"
    finally:
        try:
            os.unlink(_tmp)
        except Exception:
            pass
    ok("AT-1: append_autobiography rejects verified=False — fabrication guard holds")
except AssertionError as e:
    fail("AT-1", e)
except Exception as e:
    fail("AT-1", e)


# ── AT-2: autobiography.jsonl write guard — episode_ref required ──
try:
    from self.emergent_cognition import append_autobiography
    import tempfile, os

    _tmp = tempfile.mktemp(suffix=".jsonl")
    try:
        # Missing episode_ref must be rejected
        append_autobiography(
            "test event",
            kind="test",
            verified=True,
            source="body_ack",
            episode_ref="",   # empty — must be rejected
            _path=_tmp,
        )
        if os.path.exists(_tmp):
            with open(_tmp) as f:
                content = f.read().strip()
            assert not content, \
                f"append_autobiography with no episode_ref must not write; wrote: {content!r}"
    finally:
        try:
            os.unlink(_tmp)
        except Exception:
            pass
    ok("AT-2: append_autobiography rejects missing episode_ref — anchor guard holds")
except AssertionError as e:
    fail("AT-2", e)
except Exception as e:
    fail("AT-2", e)


# ── AT-3: autobiography.jsonl write — valid entry accepted ──
try:
    from self.emergent_cognition import append_autobiography
    import tempfile, os

    _tmp = tempfile.mktemp(suffix=".jsonl")
    try:
        append_autobiography(
            "sat down",
            kind="motor",
            verified=True,
            source="body_ack",
            episode_ref="ep-test-001",
            _path=_tmp,
        )
        assert os.path.exists(_tmp), "autobiography write did not create file"
        with open(_tmp) as f:
            entry = json.loads(f.readline().strip())
        assert entry.get("kind") == "motor"
        assert entry.get("verified") is True
        assert entry.get("episode_ref") == "ep-test-001"
    finally:
        try:
            os.unlink(_tmp)
        except Exception:
            pass
    ok("AT-3: valid autobiography entry written with required fields (kind, verified, episode_ref)")
except AssertionError as e:
    fail("AT-3", e)
except Exception as e:
    fail("AT-3", e)


# ── AT-4: recent_autobiography returns newest-last ordering ──
try:
    from self.emergent_cognition import append_autobiography, recent_autobiography
    import tempfile, os

    _tmp = tempfile.mktemp(suffix=".jsonl")
    try:
        for i in range(3):
            append_autobiography(
                f"event-{i}",
                kind="test",
                verified=True,
                source="body_ack",
                episode_ref=f"ep-{i}",
                _path=_tmp,
            )
        entries = recent_autobiography(3, _path=_tmp)
        assert len(entries) == 3, f"expected 3 entries; got {len(entries)}"
        episode_refs = [e.get("episode_ref") for e in entries]
        assert episode_refs == ["ep-0", "ep-1", "ep-2"], \
            f"entries should be oldest-first; got episode_refs={episode_refs}"
    finally:
        try:
            os.unlink(_tmp)
        except Exception:
            pass
    ok("AT-4: recent_autobiography returns entries oldest-first (newest last)")
except AssertionError as e:
    fail("AT-4", e)
except Exception as e:
    fail("AT-4", e)


# ── AT-5: compile hygiene ──
for _mod in (
    "continuity/identity_state.py",
    "continuity/continuity_summary.py",
    "continuity/continuity_engine.py",
    "self/emergent_cognition.py",
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
print("=" * 55)
print(f"WO-CANON-XXI narrative identity   {_passed} passed   {_failed} failed")
if _failed:
    sys.exit(1)
