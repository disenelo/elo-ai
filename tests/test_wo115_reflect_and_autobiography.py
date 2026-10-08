"""
tests/test_wo115_reflect_and_autobiography.py — WO-115: REFLECT + HISTORY rows 21, 23.

AT-115-1: apply_lesson() updates EloSelfState.last_reflection_lesson
AT-115-2: apply_lesson() is idempotent — same statement is a no-op
AT-115-3: append_autobiography creates the file; recent_autobiography grows it
AT-115-4: recent_autobiography returns entries in chronological order (oldest first)
AT-115-5: Entries not written via append_autobiography do not appear
AT-115-6: compile() includes autobiography key (Executive-visible)
"""
from __future__ import annotations

import os
import sys
import json
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


# ── AT-115-1: apply_lesson updates last_reflection_lesson ────────────────────

def test_apply_lesson_updates_self_model():
    from self.elo_self_model import EloSelfState, apply_lesson
    s = EloSelfState()
    assert s.last_reflection_lesson == "", "baseline should be empty"
    lesson = {"statement": "Partial progress on build — check dependencies before next attempt."}
    s = apply_lesson(s, lesson)
    assert s.last_reflection_lesson == lesson["statement"], (
        f"apply_lesson did not write to last_reflection_lesson: {s.last_reflection_lesson!r}"
    )


# ── AT-115-2: apply_lesson is idempotent ─────────────────────────────────────

def test_apply_lesson_idempotent():
    from self.elo_self_model import EloSelfState, apply_lesson
    lesson = {"statement": "Completed a capability milestone — reinforce this pattern."}
    s = EloSelfState(last_reflection_lesson=lesson["statement"])
    s_before = s.last_reflection_lesson
    s = apply_lesson(s, lesson)
    assert s.last_reflection_lesson == s_before, (
        "apply_lesson should not update when statement is unchanged"
    )


# ── AT-115-3: append_autobiography creates file; grows on repeated calls ─────

def test_autobiography_creates_and_grows(tmp_path, monkeypatch):
    import self.emergent_cognition as ec
    test_file = str(tmp_path / "autobiography.jsonl")
    monkeypatch.setattr(ec, "_AUTOB", test_file)

    assert not os.path.exists(test_file), "file should not exist before first append"

    ec.append_autobiography("sat — body ACK confirmed", kind="action", verified=True, source="body_ack", episode_ref="test-ep-1")
    assert os.path.exists(test_file), "append_autobiography should create the file"

    ec.append_autobiography("moved (right) — body ACK confirmed", kind="action", verified=True, source="body_ack", episode_ref="test-ep-2")
    entries = ec.recent_autobiography(10)
    assert len(entries) == 2, f"expected 2 entries, got {len(entries)}"


# ── AT-115-4: recent_autobiography returns entries oldest-first ───────────────

def test_autobiography_chronological_order(tmp_path, monkeypatch):
    import self.emergent_cognition as ec
    import time
    test_file = str(tmp_path / "autobiography.jsonl")
    monkeypatch.setattr(ec, "_AUTOB", test_file)

    ec.append_autobiography("first event", kind="action", verified=True, source="body_ack", episode_ref="test-ep-1")
    ec.append_autobiography("second event", kind="action", verified=True, source="body_ack", episode_ref="test-ep-2")
    ec.append_autobiography("third event", kind="action", verified=True, source="body_ack", episode_ref="test-ep-3")

    entries = ec.recent_autobiography(10)
    assert len(entries) == 3
    events = [e["event"] for e in entries]
    assert events == ["first event", "second event", "third event"], (
        f"entries not in chronological order: {events}"
    )
    # timestamps must be non-decreasing
    ts_list = [e["ts"] for e in entries]
    assert ts_list == sorted(ts_list), f"timestamps not sorted: {ts_list}"


# ── AT-115-5: only explicit writes appear — no inference contamination ────────

def test_autobiography_only_explicit_writes(tmp_path, monkeypatch):
    import self.emergent_cognition as ec
    test_file = str(tmp_path / "autobiography.jsonl")
    monkeypatch.setattr(ec, "_AUTOB", test_file)

    ec.append_autobiography("verified: sat — ACK confirmed", kind="action", verified=True, source="body_ack", episode_ref="test-ep-1")
    entries = ec.recent_autobiography(10)
    assert len(entries) == 1, f"expected exactly 1 entry, got {len(entries)}"
    assert entries[0]["event"] == "verified: sat — ACK confirmed"
    # No phantom entries from constructing or loading EloSelfState
    from self.elo_self_model import EloSelfState
    _ = EloSelfState()
    entries_after = ec.recent_autobiography(10)
    assert len(entries_after) == 1, (
        "EloSelfState construction must NOT write autobiography entries"
    )


# ── AT-115-6: compile() exposes autobiography to the Executive ────────────────

def test_moment_compile_includes_autobiography():
    from runtime.the_moment import compile as tm_compile
    from unittest.mock import MagicMock
    state = MagicMock()
    state.embodiment = "desktop"
    state.pose = "perched"
    state.surface = "Terminal"
    state.location = ""
    state.balance = "stable"
    state.size = {"height_cm": 18, "reach_cm": 30, "jump_cm": 30}
    state.available_actions = []
    state.current_action = "idle"
    state.locomotion_faculty_health = "ok"
    state.nearby_surfaces = []
    state.mood = 0.5
    state.curiosity = 0.5
    state.goal = ""
    state.last_updated = 0.0
    state.recent_behavior = {}

    moment = tm_compile(state)
    assert "autobiography" in moment, (
        "compile() must include 'autobiography' key — Executive can't see it otherwise"
    )
    assert "autobiography_tier" in moment, "compile() must include 'autobiography_tier'"
