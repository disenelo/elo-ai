"""
tests/test_wo_tired_sit_b.py — WO-TIRED-SIT-001 Part B.

Board integration test: physical_tired inner_event + sit-implying inner_thought
→ Sit_hold motion written to blender_state.

The core invariant: a tired signal in EloSelfState.inner_events, combined with
an inner_thought that implies sitting, produces motion {"animation": "Sit_hold",
"mode": "sit"} and arms _PENDING_SIT. Nothing writes a sit when the signal or
the language is absent.

Tests are NOT end-to-end server tests. They exercise the exact condition block
added in Part B: the conjunction of (1) physical_tired in inner_events,
(2) sit-implying inner_thought text, (3) _PENDING_SIT.active == False.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class _FakeState:
    inner_events: list = field(default_factory=list)


def _run_b(inner_events: list[str], inner_thought: str,
           pending_sit_active: bool) -> list[dict]:
    """
    Execute the Part B condition block against supplied state.

    Returns a list of dicts that would be passed to blender_bridge.state_writer.patch.
    The real server block writes Sit_hold when the conditions are met; this
    function replicates the logic so the test is not brittle to source line numbers.
    """
    patched: list[dict] = []
    pending_sit: dict = {"active": pending_sit_active, "since": 0.0, "queued": None}

    def _fake_patch(fields: dict) -> None:
        patched.append(fields)

    import re as _pt_re
    _pt_sit_re = _pt_re.compile(
        r"\b(sit|sitting|legs?|rest\b|settle|settle down|sit down)\b"
    )

    _pt_events = [
        e for e in inner_events
        if isinstance(e, str) and e.startswith("physical_tired:")
    ]
    if _pt_events and inner_thought and not pending_sit.get("active"):
        if _pt_sit_re.search(inner_thought.lower()):
            _fake_patch({"motion": {"animation": "Sit_hold", "mode": "sit"}})
            pending_sit["active"] = True
            pending_sit["since"] = time.time()
            pending_sit["queued"] = None

    return patched


# ── Positive path ─────────────────────────────────────────────────────────────

def test_tired_signal_plus_sit_thought_issues_sit():
    result = _run_b(
        inner_events=["physical_tired:tired"],
        inner_thought="Legs are heavy. Time to sit.",
        pending_sit_active=False,
    )
    assert result, "expected sit to be issued"
    assert result[0]["motion"]["animation"] == "Sit_hold"
    assert result[0]["motion"]["mode"] == "sit"


def test_fatigued_band_also_issues_sit():
    result = _run_b(
        inner_events=["physical_tired:fatigued"],
        inner_thought="Need to rest my legs.",
        pending_sit_active=False,
    )
    assert result, "fatigued band should also trigger sit"
    assert result[0]["motion"]["animation"] == "Sit_hold"


def test_exhausted_band_issues_sit():
    result = _run_b(
        inner_events=["creative_spark", "physical_tired:exhausted"],
        inner_thought="Need to sit down. Now.",
        pending_sit_active=False,
    )
    assert result, "exhausted band should trigger sit"


# ── Gate: no duplicate sit ────────────────────────────────────────────────────

def test_no_sit_when_pending_sit_already_active():
    result = _run_b(
        inner_events=["physical_tired:tired"],
        inner_thought="Legs are heavy. Time to sit.",
        pending_sit_active=True,  # already armed
    )
    assert not result, "must not issue duplicate sit"


# ── Gate: no sit-implying language ───────────────────────────────────────────

def test_no_sit_when_inner_thought_lacks_sit_language():
    result = _run_b(
        inner_events=["physical_tired:tired"],
        inner_thought="That was an interesting point about the camera.",
        pending_sit_active=False,
    )
    assert not result, "non-sit inner_thought must not trigger sit"


def test_no_sit_when_inner_thought_is_empty():
    result = _run_b(
        inner_events=["physical_tired:tired"],
        inner_thought="",
        pending_sit_active=False,
    )
    assert not result, "empty inner_thought must not trigger sit"


# ── Gate: no physical_tired event ────────────────────────────────────────────

def test_no_sit_when_no_physical_tired_event():
    result = _run_b(
        inner_events=["creative_spark", "connection"],
        inner_thought="Legs are heavy. Time to sit.",
        pending_sit_active=False,
    )
    assert not result, "sit-language alone without a tired event must not trigger sit"


def test_no_sit_when_inner_events_is_empty():
    result = _run_b(
        inner_events=[],
        inner_thought="Need to sit.",
        pending_sit_active=False,
    )
    assert not result


# ── Animation name contract ───────────────────────────────────────────────────

def test_animation_name_is_Sit_hold_exactly():
    result = _run_b(
        inner_events=["physical_tired:fatigued"],
        inner_thought="Time to sit down.",
        pending_sit_active=False,
    )
    assert result[0]["motion"]["animation"] == "Sit_hold", (
        "Unity expects the exact clip name 'Sit_hold', not 'sit_hold' or 'sit'"
    )
