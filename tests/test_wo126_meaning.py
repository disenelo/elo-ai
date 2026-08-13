"""
tests/test_wo126_meaning.py — Row 26 MEANING.

Proof: significance score from a prior turn is accessible to the Executive.

Ruling: Option A — `last_significance: dict` on the_moment. Conditions:
  1. Name is `last_significance` (not `significance`) — it is the PREVIOUS turn's score.
  2. No score (file absent) → empty dict. eLo must not claim significance without it.
  3. The profile carries the outcome that produced it (outcome= is threaded, WO-101).

The test does NOT prove eLo says the right sentence — that is a live-run check.
It proves the SCORE reaches the Executive assembly: journal_router writes it,
the_moment reads it, compile() exposes it.

AT-126-1: journal_router.route() writes last_significance.json with profile + ts + action
AT-126-2: the_moment.compile() exposes last_significance from that file
AT-126-3: when file is absent, last_significance is empty dict (no false claim)
AT-126-4: profile carries overall + reward when outcome= is threaded (WO-101 join)
AT-126-5: last_significance is previous turn's score — the file from turn N is read at turn N+1
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


# ── AT-126-1: journal_router.route() writes last_significance.json ────────────

def test_route_writes_last_significance(tmp_path):
    """route() must write last_significance.json to self/state/."""
    from memory import journal_router as jr

    sig_path = tmp_path / "last_significance.json"

    # Monkey-patch _ROOT for this call so writes go to tmp_path
    original_root = jr._ROOT
    try:
        state_dir = tmp_path / "self" / "state"
        state_dir.mkdir(parents=True)

        import unittest.mock as mock
        with mock.patch.object(jr, "_ROOT", str(tmp_path)):
            # Also patch the significance file path by patching os.path.join result indirectly
            # (the path is built inside route() using _ROOT)
            jr.route(
                raw="let's build something",
                response="Sure, what are we making?",
                action="build",
                state={},
            )
    finally:
        pass  # no cleanup needed — tmp_path is temporary

    sig_file = state_dir / "last_significance.json"
    assert sig_file.exists(), (
        "journal_router.route() must write self/state/last_significance.json"
    )
    record = json.loads(sig_file.read_text())
    assert "ts" in record, "last_significance must have ts field"
    assert "action" in record, "last_significance must have action field"
    assert "profile" in record, "last_significance must have profile field"
    assert "overall" in record["profile"], (
        "profile must include overall significance score"
    )


# ── AT-126-2: the_moment.compile() exposes last_significance ──────────────────

def test_compile_exposes_last_significance(tmp_path):
    """compile() must include last_significance when file exists."""
    from self.elo_self_model import EloSelfState
    from runtime import the_moment

    state_dir = tmp_path / "self" / "state"
    state_dir.mkdir(parents=True)
    sig_file = state_dir / "last_significance.json"
    sig_file.write_text(json.dumps({
        "ts": time.time() - 5.0,
        "action": "build",
        "profile": {"overall": 0.74, "creation": 0.90, "system_change": 0.65, "reward": 0.72},
    }))

    original_root = the_moment._ROOT
    import unittest.mock as mock
    with mock.patch.object(the_moment, "_ROOT", str(tmp_path)):
        moment = the_moment.compile(EloSelfState())

    assert "last_significance" in moment, (
        "compile() must include last_significance key"
    )
    assert moment["last_significance"].get("profile", {}).get("overall") == 0.74, (
        f"last_significance profile must match written file: {moment['last_significance']}"
    )


# ── AT-126-3: absent file → empty dict (no false claim) ──────────────────────

def test_compile_last_significance_empty_when_no_file(tmp_path):
    """When last_significance.json does not exist, last_significance must be {}."""
    from self.elo_self_model import EloSelfState
    from runtime import the_moment

    state_dir = tmp_path / "self" / "state"
    state_dir.mkdir(parents=True)
    # No file written

    import unittest.mock as mock
    with mock.patch.object(the_moment, "_ROOT", str(tmp_path)):
        moment = the_moment.compile(EloSelfState())

    sig = moment.get("last_significance", None)
    assert sig is not None, "last_significance key must always be present"
    assert sig == {}, (
        f"last_significance must be empty dict when no file exists — no false claim. Got: {sig}"
    )


# ── AT-126-4: profile carries reward when outcome= is threaded (WO-101) ───────

def test_profile_carries_reward_with_outcome():
    """When outcome= is passed, profile includes embodiment/efficiency/safety/reward."""
    from memory.significance_engine import evaluate

    outcome = {
        "verified":    True,
        "ack_received": True,
        "completion":  "met",
        "cost":        {"seconds": 2.5, "legs": 1, "retries": 0, "fallback_used": False},
        "ack_type":    "sit",
    }
    profile = evaluate(
        raw="sit down",
        response="I'm sitting.",
        action="sit",
        outcome=outcome,
    )
    assert "reward" in profile, (
        "Profile must include 'reward' when outcome= is threaded (WO-101 join)"
    )
    assert profile["reward"] > 0, (
        f"Reward must be positive for a met+verified sit ACK: {profile['reward']}"
    )
    assert "embodiment" in profile and "safety" in profile, (
        "Profile must include embodiment and safety outcome dims when outcome= is supplied"
    )


# ── AT-126-5: last_significance is previous turn's score ─────────────────────

def test_last_significance_is_previous_turn(tmp_path):
    """
    Row 26 MEANING core timing proof.
    Turn N writes last_significance.json. Turn N+1 reads it.
    The score visible at speak time is one turn old — never the current sentence's score.
    """
    from memory import journal_router as jr
    from self.elo_self_model import EloSelfState
    from runtime import the_moment

    state_dir = tmp_path / "self" / "state"
    state_dir.mkdir(parents=True)

    import unittest.mock as mock

    # Turn N: route() writes the significance file
    with mock.patch.object(jr, "_ROOT", str(tmp_path)):
        jr.route(
            raw="what are we building?",
            response="Something meaningful.",
            action="build",
            state={},
        )

    sig_file = state_dir / "last_significance.json"
    assert sig_file.exists(), "Turn N must have written last_significance.json"
    written_ts = json.loads(sig_file.read_text())["ts"]

    # Tiny sleep so Turn N+1 has a different timestamp
    time.sleep(0.01)

    # Turn N+1: compile() reads it — this is what eLo sees when he speaks next
    with mock.patch.object(the_moment, "_ROOT", str(tmp_path)):
        moment = the_moment.compile(EloSelfState())

    read_ts = moment["last_significance"].get("ts")
    assert read_ts is not None, "last_significance must be present in Turn N+1's moment"
    assert read_ts == written_ts, (
        "The score visible at speak time (Turn N+1) must be Turn N's score — not current"
    )
