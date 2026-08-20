"""
test_0037_single_self_model_authority.py — Card 0037 (WO-ONEBRAIN-015) acceptance.

Ruling: single self-model authority. No long-lived in-memory copy that writes back
its snapshot. Every mutation is load→mutate→save via one accessor.

Four assertions (from the card):
  A. Reflection writes last_reflection_lesson; a subsequent turn saves; the field
     survives. (The exact failure the card names — asserted directly.)
  B. Two writers touching different fields in the same turn both persist.
  C. Grep proves no module-level `_self_load()` remains in server.py.
  D. A deliberate stale-overwrite attempt fires the WARNING.
"""
from __future__ import annotations

import io
import json
import logging
import os
import re
import sys
import tempfile
from pathlib import Path

# Ensure repo root on path when run directly
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _ok(msg):  print(f"[PASS] {msg}")
def _fail(k, m): print(f"[FAIL] {k}: {m}"); sys.exit(1)


def _use_temp_state_file() -> Path:
    """Point elo_self_model._STATE_PATH at a fresh tempdir so tests don't touch real state."""
    from self import elo_self_model as esm
    tmpdir = Path(tempfile.mkdtemp(prefix="test_0037_"))
    esm._STATE_PATH = tmpdir / "elo_self_state.json"
    return esm._STATE_PATH


def test_A_reflection_lesson_survives_subsequent_turn():
    """The exact failure the card names: reflection writes lesson, turn saves, lesson survives."""
    _use_temp_state_file()
    from self import elo_self_model as esm

    # Start fresh
    esm.save(esm.EloSelfState())

    # Reflection writes a lesson via truth_sync's path (update + apply_lesson through mutator)
    _lesson = {"statement": "cheerful greetings land as connection when David is calm."}
    esm.update(lambda s: esm.apply_lesson(s, _lesson))

    # Verify it's on disk
    on_disk_after_reflection = esm.load()
    if on_disk_after_reflection.last_reflection_lesson != _lesson["statement"]:
        _fail("A.pre",
              f"lesson did not persist: on-disk={on_disk_after_reflection.last_reflection_lesson!r}")

    # Simulate a subsequent turn: server does apply_turn + record_behaviour through the mutator
    def _apply_turn(s):
        esm.apply_turn(s, {"action": "connect", "tone": "JOYFUL",
                           "response": "yeah — nice one", "user_input": "hey",
                           "topics": ["greet"]})
        esm.record_behaviour(s, "connect")
        return s
    esm.update(_apply_turn)

    # Assert: lesson survives the turn save
    final = esm.load()
    if final.last_reflection_lesson != _lesson["statement"]:
        _fail("A", f"lesson clobbered by turn save: got {final.last_reflection_lesson!r}")
    _ok("A: reflection-lesson survives subsequent turn save (Rule 1 primary failure closed)")


def test_B_two_writers_different_fields_both_persist():
    """Two writers touching different fields in one turn → both persist."""
    _use_temp_state_file()
    from self import elo_self_model as esm

    esm.save(esm.EloSelfState())

    # Writer 1: reflection lesson
    esm.update(lambda s: esm.apply_lesson(s, {"statement": "steady turns hold something"}))

    # Writer 2: pose change (as if from sit ACK)
    def _apply_pose(s):
        s.pose = "sitting"
        s.available_actions = ["stand", "look", "wave", "gesture"]
        return s
    esm.update(_apply_pose)

    on_disk = esm.load()
    if on_disk.last_reflection_lesson != "steady turns hold something":
        _fail("B", f"lesson lost: {on_disk.last_reflection_lesson!r}")
    if on_disk.pose != "sitting":
        _fail("B", f"pose lost: {on_disk.pose!r}")
    if on_disk.available_actions != ["stand", "look", "wave", "gesture"]:
        _fail("B", f"available_actions lost: {on_disk.available_actions!r}")
    _ok("B: two writers touching different fields both persist")


def test_C_no_module_level_self_load_in_server():
    """No module-level `_self_load()` remains anywhere in server.py."""
    server_path = _ROOT / "server.py"
    with open(server_path, encoding="utf-8") as f:
        lines = f.read().splitlines()

    # A module-level statement is one at indentation 0 that isn't inside a def/class.
    # Simple heuristic: look for `_self_load()` calls at indentation 0.
    offenders = []
    for i, line in enumerate(lines, start=1):
        stripped = line.lstrip()
        # skip comments
        if stripped.startswith("#"):
            continue
        # skip lines that don't contain the call
        if "_self_load()" not in stripped:
            continue
        # count leading spaces
        indent = len(line) - len(stripped)
        if indent == 0:
            offenders.append((i, line))
    if offenders:
        _fail("C", f"module-level _self_load() found: {offenders}")
    _ok("C: no module-level _self_load() in server.py — long-lived cache retired")


def test_D_stale_overwrite_fires_warning():
    """Deliberately race disk state between load and save → WARN naming the field."""
    _use_temp_state_file()
    from self import elo_self_model as esm

    esm.save(esm.EloSelfState())

    # Capture WARN log from elo_self_model
    logger = logging.getLogger("self.elo_self_model")
    prev_level = logger.level
    logger.setLevel(logging.WARNING)
    buf = io.StringIO()
    handler = logging.StreamHandler(buf)
    handler.setLevel(logging.WARNING)
    logger.addHandler(handler)

    try:
        # A fn that, mid-mutation, sneaks in a disk write to a DIFFERENT field.
        # Our fn mutates mood; the sneak-write changes pose. When update() reloads
        # disk before its own save, it should see pose changed — and since our
        # save would restore pose to its pre-sneak value, Rule 1 must fire.
        def _racy(state):
            # Sneak: another writer flips pose on disk
            other = esm.load()
            other.pose = "sitting"
            esm.save(other)
            # Our mutation: mood
            state.mood = 0.9
            return state
        esm.update(_racy)
    finally:
        logger.removeHandler(handler)
        logger.setLevel(prev_level)

    log_output = buf.getvalue()
    if "Rule 1" not in log_output:
        _fail("D", f"no Rule 1 WARN fired. captured log: {log_output!r}")
    if "pose" not in log_output:
        _fail("D", f"WARN fired but did not name the stale field 'pose'. log: {log_output!r}")
    _ok("D: stale-overwrite fires Rule 1 WARNING naming the field")


if __name__ == "__main__":
    test_A_reflection_lesson_survives_subsequent_turn()
    test_B_two_writers_different_fields_both_persist()
    test_C_no_module_level_self_load_in_server()
    test_D_stale_overwrite_fires_warning()
    print("\n[0037] all 4 acceptance assertions passed")
