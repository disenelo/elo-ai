"""
tests/test_card_0019_dead_personality_and_past.py — Acceptance for Card 0019

Two P0s from the volume audit:

  P0-A · fabricated past (Vol XXI · D-XXI-2, Verified Speech breach)
        eLo was narrating a past that never happened, every turn.
        Defaults in elo_self_model.py hard-coded 'adventuring in eLo-Planet'
        and 'first learned to move on the desktop'. Removed.

  P0-B · dead personality-change path (Vol X D-09 · Vol XVIII D-XVIII-1)
        lesson_store._try_personality_delta was broken on 4 independent counts
        AND the reflection_faculty payload was wrong before the call
        convention was wrong. Silently swallowed by bare except.

Report outcomes:
  1. Does a fresh eLo decline to invent a past? (P0-A)
  2. Does self/personality_vector.json exist after a real confirmed lesson? (P0-B)

Run: python3 tests/test_card_0019_dead_personality_and_past.py
"""
from __future__ import annotations

import json
import logging
import os
import sys
import tempfile
import time

sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


# ────────────────────────────────────────────────────────────────────────────
# P0-A · Fresh eLo does not invent a past
# ────────────────────────────────────────────────────────────────────────────
print("── P0-A: fabricated past ────────────────────────────────────────────")

# AT-A1: module-level defaults are empty (not fabricated)
try:
    from self.elo_self_model import (
        _DEFAULT_EMBODIMENT_HISTORY,
        _DEFAULT_EMBODIMENT_MILESTONES,
    )
    assert _DEFAULT_EMBODIMENT_HISTORY == [], \
        f"expected empty default history, got {_DEFAULT_EMBODIMENT_HISTORY!r}"
    assert _DEFAULT_EMBODIMENT_MILESTONES == [], \
        f"expected empty default milestones, got {_DEFAULT_EMBODIMENT_MILESTONES!r}"
    ok("AT-A1: module defaults are empty (no fabricated content)")
except AssertionError as e:
    fail("AT-A1", e)

# AT-A2: fresh state's narrative block declines to invent a past
try:
    from self.elo_self_model import EloSelfState, narrative_block
    fresh = EloSelfState()
    block = narrative_block(fresh)
    lower = block.lower()
    assert "no verified autobiography yet" in lower, \
        "fresh narrative block must state 'no autobiography yet'"
    assert "do not invent" in lower or "silence is the correct answer" in lower, \
        "fresh narrative block must contain anti-fabrication instruction"
    # Must NOT contain the specific fabricated phrases from the old defaults:
    for tainted in (
        "adventuring in elo-planet",
        "one day a physical body",
        "early glimpses",
        "where i've mostly lived",
        "first learned to move on the desktop",
    ):
        assert tainted not in lower, f"fresh block leaks tainted phrase: '{tainted}'"
    ok("AT-A2: fresh eLo declines to invent a past — no leaked fabrications")
except AssertionError as e:
    fail("AT-A2", e)
except Exception as e:
    fail("AT-A2", e)

# AT-A3: load() with partial JSON produces empty history (not fabricated defaults)
try:
    from self import elo_self_model as _esm
    old_path = _esm._STATE_PATH
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump({"mood": 0.5}, f)
        tmp_path = f.name
    _esm._STATE_PATH = tmp_path
    try:
        loaded = _esm.load()
        assert loaded.embodiment_history == [], \
            f"expected empty history on partial JSON, got {loaded.embodiment_history!r}"
        assert loaded.embodiment_milestones == [], \
            f"expected empty milestones on partial JSON, got {loaded.embodiment_milestones!r}"
        ok("AT-A3: load() with partial JSON gives empty history — no rehydrated fabrication")
    finally:
        _esm._STATE_PATH = old_path
        try: os.unlink(tmp_path)
        except OSError: pass
except AssertionError as e:
    fail("AT-A3", e)
except Exception as e:
    fail("AT-A3", e)

# AT-A4: block still narrates truthfully when populated with a verified embodiment
try:
    from self.elo_self_model import EloSelfState, narrative_block
    populated = EloSelfState()
    populated.embodiment_history = [
        {"name": "desktop", "status": "active", "note": ""},
    ]
    populated.embodiment_milestones = [
        {"note": "first sit_ACK confirmed by the body"},
    ]
    block = narrative_block(populated)
    assert "desktop" in block, "populated state must narrate 'desktop'"
    assert "first sit_ACK confirmed by the body" in block, "populated milestone missing"
    assert "no verified autobiography yet" not in block.lower(), \
        "populated state should NOT show the empty-state branch"
    ok("AT-A4: populated state narrates the truth (block still works)")
except AssertionError as e:
    fail("AT-A4", e)
except Exception as e:
    fail("AT-A4", e)


# ────────────────────────────────────────────────────────────────────────────
# P0-B · Personality path is alive; personality_vector.json is written
# ────────────────────────────────────────────────────────────────────────────
print()
print("── P0-B: dead personality path ──────────────────────────────────────")

# AT-B1: _try_personality_delta with a well-formed row writes personality_vector.json
try:
    from self import lesson_store
    from faculties.personality import personality_evolution_faculty as _pef

    with tempfile.TemporaryDirectory() as tmp_root:
        # Redirect the personality vector to a temp path so we don't stomp real state
        old_state_dir = _pef._STATE_DIR
        old_state_path = _pef._STATE_PATH
        import pathlib as _pl
        _pef._STATE_DIR  = _pl.Path(tmp_root)
        _pef._STATE_PATH = _pl.Path(tmp_root) / "personality_vector.json"

        try:
            # Guarantee the file does not exist before the call
            if _pef._STATE_PATH.exists():
                _pef._STATE_PATH.unlink()

            confirmed_row = {
                "lesson_key": "test_lkey_A",
                "scope": "preference",
                "status": "confirmed",
                "strength": 0.9,
                "evidence": [
                    {"episode_ref": "e1", "verified": True,  "session_id": "s1", "ts": time.time()},
                    {"episode_ref": "e2", "verified": True,  "session_id": "s2", "ts": time.time()},
                    {"episode_ref": "e3", "verified": True,  "session_id": "s1", "ts": time.time()},
                ],
                "proposes": {
                    "trait":     "curiosity",
                    "direction": "increase",
                    "magnitude": 0.02,
                },
            }
            transitions = {"promoted": [], "demoted": [], "retired": [], "personality_delta": []}
            lesson_store._try_personality_delta(confirmed_row, transitions)

            assert _pef._STATE_PATH.exists(), \
                f"personality_vector.json was NOT written to {_pef._STATE_PATH}"
            assert "test_lkey_A" in transitions["personality_delta"], \
                f"lesson_key not appended to personality_delta list: {transitions}"

            with open(_pef._STATE_PATH, encoding="utf-8") as f:
                pv_data = json.load(f)
            assert "curiosity" in pv_data, "curiosity trait missing from persisted vector"
            assert pv_data["curiosity"]["value"] > 0.62, \
                f"expected curiosity > 0.62 after +0.02 increase, got {pv_data['curiosity']['value']}"
            ok("AT-B1: _try_personality_delta writes personality_vector.json on a confirmed lesson")
        finally:
            _pef._STATE_DIR = old_state_dir
            _pef._STATE_PATH = old_state_path
except AssertionError as e:
    fail("AT-B1", e)
except Exception as e:
    fail("AT-B1", e)

# AT-B2: malformed proposal is REJECTED with a LOG (not swallowed)
try:
    from self import lesson_store
    logger = logging.getLogger("self.lesson_store")
    captured = []
    class _CaptureHandler(logging.Handler):
        def emit(self, record): captured.append(record.getMessage())
    h = _CaptureHandler(); h.setLevel(logging.DEBUG)
    logger.addHandler(h); logger.setLevel(logging.DEBUG)
    try:
        bad_row = {
            "lesson_key": "test_lkey_bad",
            "proposes": {"trait": "curiosity", "direction": 1, "magnitude": 0.02},  # direction as int → invalid
            "evidence": [{"episode_ref": "e1", "verified": True}],
        }
        transitions = {"promoted": [], "demoted": [], "retired": [], "personality_delta": []}
        lesson_store._try_personality_delta(bad_row, transitions)
        assert "test_lkey_bad" not in transitions["personality_delta"], \
            "invalid direction should NOT produce a personality_delta"
        assert any("test_lkey_bad" in m and ("rejected" in m.lower() or "malformed" in m.lower())
                   for m in captured), \
            f"expected a logged rejection for test_lkey_bad; captured={captured}"
        ok("AT-B2: malformed proposal is rejected AND logged (bare except removed)")
    finally:
        logger.removeHandler(h)
except AssertionError as e:
    fail("AT-B2", e)
except Exception as e:
    fail("AT-B2", e)

# AT-B3: reflection_faculty proposes payload SHAPE is correct (or None), never wrong
try:
    from runtime import reflection_faculty as _rf

    # Case A: natural preference-verb action ("prefer") — NOT a trait name.
    # Per Vol XVIII §1.7 we do NOT emit a proposal we know will be rejected,
    # so proposes must be None (honest — no invalid payload to swallow later).
    lesson_a = _rf._form_lesson(
        session_summary="prefer to sit down when David is quiet — reads better",
        action="prefer",
        completion_state="partial",
        planned_objective="respect the silence",
    )
    if lesson_a is not None and lesson_a.get("scope") == "preference":
        assert lesson_a.get("proposes") is None, \
            f"non-trait preference action must NOT emit proposes; got {lesson_a.get('proposes')}"

    # Case B: any lesson that DOES emit proposes must have the correct shape —
    # direction ∈ {"increase","decrease"} (STRING, not int), magnitude ≤ MAX_STEP.
    #
    # We synthesise this by driving _form_lesson through the internal trait
    # gate: temporarily add "prefer" → "curiosity" mapping and re-check that
    # if proposes is present, its shape is valid.
    from unittest.mock import patch
    with patch.object(_rf, "_PERSONALITY_TRAIT_NAMES", frozenset({"prefer"})):
        lesson_b = _rf._form_lesson(
            session_summary="prefer to sit down when David is quiet",
            action="prefer",
            completion_state="partial",
            planned_objective="respect the silence",
        )
        assert lesson_b is not None, "expected a preference lesson"
        assert lesson_b.get("scope") == "preference"
        proposes = lesson_b.get("proposes")
        assert proposes is not None, "expected proposes when action IS a trait"
        assert proposes["direction"] in ("increase", "decrease"), \
            f"direction must be string increase/decrease, got {proposes['direction']!r}"
        assert isinstance(proposes["magnitude"], float), \
            f"magnitude must be float, got {type(proposes['magnitude'])}"
        assert 0.0 < proposes["magnitude"] <= 0.02, \
            f"magnitude must satisfy 0<mag<=MAX_STEP(0.02), got {proposes['magnitude']}"
    ok("AT-B3: proposes payload SHAPE is correct — direction is string, magnitude present")
except AssertionError as e:
    fail("AT-B3", e)
except Exception as e:
    fail("AT-B3", e)

# AT-B4: end-to-end — promote_pass on a hand-built ledger writes personality_vector.json
try:
    from self import lesson_store
    from faculties.personality import personality_evolution_faculty as _pef
    import pathlib as _pl

    with tempfile.TemporaryDirectory() as tmp_root:
        ledger_path = os.path.join(tmp_root, "self", "lessons_ledger.jsonl")
        os.makedirs(os.path.dirname(ledger_path), exist_ok=True)
        os.makedirs(os.path.join(tmp_root, "self", "journals"), exist_ok=True)

        # Redirect personality vector to isolated temp
        old_state_dir = _pef._STATE_DIR
        old_state_path = _pef._STATE_PATH
        _pef._STATE_DIR  = _pl.Path(tmp_root) / "self"
        _pef._STATE_PATH = _pef._STATE_DIR / "personality_vector.json"
        try:
            candidate_row = {
                "id":         "L-test",
                "lesson_key": "endtoend_lkey",
                "statement":  "prefers curiosity when unsure",
                "scope":      "preference",
                "cause":      "met",
                "status":     "candidate",
                "strength":   0.90,
                "delta":      "met",
                "first_seen": "2026-08-19T00:00:00Z",
                "last_seen":  "2026-08-19T00:00:00Z",
                "promoted_at": None,
                "retired_at":  None,
                "reason":      None,
                "evidence": [
                    {"episode_ref": "e1", "verified": True, "session_id": "s1", "ts": time.time()},
                    {"episode_ref": "e2", "verified": True, "session_id": "s2", "ts": time.time()},
                    {"episode_ref": "e3", "verified": True, "session_id": "s1", "ts": time.time()},
                ],
                "proposes": {
                    "trait":     "curiosity",
                    "direction": "increase",
                    "magnitude": 0.02,
                },
                "ts": "2026-08-19T00:00:00Z",
            }
            with open(ledger_path, "w", encoding="utf-8") as f:
                f.write(json.dumps(candidate_row) + "\n")

            transitions = lesson_store.promote_pass(ledger_path=ledger_path)
            assert "endtoend_lkey" in transitions.get("promoted", []), \
                f"lesson not promoted: {transitions}"
            assert "endtoend_lkey" in transitions.get("personality_delta", []), \
                f"personality_delta not emitted: {transitions}"
            assert _pef._STATE_PATH.exists(), \
                f"personality_vector.json missing at {_pef._STATE_PATH}"
            ok("AT-B4: promote_pass end-to-end writes personality_vector.json")
        finally:
            _pef._STATE_DIR = old_state_dir
            _pef._STATE_PATH = old_state_path
except AssertionError as e:
    fail("AT-B4", e)
except Exception as e:
    fail("AT-B4", e)


print()
print("=" * 60)
print(f"Card 0019 acceptance  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
