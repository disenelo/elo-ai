"""
tests/test_s4_battery_wiring.py — WO-HEALTH-BATTERY-001 integration points.

Source-level guards that each wiring point is present and on a live path.
They do NOT prove the values reach Unity — that needs a server restart and a
live turn.

The per-turn point matters twice over: `energy_history` right above it tracks
DAVID's emotional energy, and `state.energy` in blender_state.json is that
same conversational affect signal. eLo's battery is a different thing that
happens to share the word. These tests pin that they stay separate.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SERVER = ROOT / "server.py"
AMBIENT = ROOT / "ambient" / "ambient_engine.py"
DREAM_FACULTY = ROOT / "faculties" / "dream" / "dream_faculty.py"


def _src(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_all_touched_files_parse():
    for path in (SERVER, AMBIENT, DREAM_FACULTY):
        ast.parse(_src(path))


# ── PART A section 2 — conversation turn drain ────────────────────────────────

def test_conversation_turn_drains_the_battery():
    src = _src(SERVER)
    assert "on_conversation_turn" in src, (
        "no per-turn battery drain wired in server.py"
    )
    assert re.search(r"from core\.health_battery import", src)


def test_turn_drain_sits_next_to_the_energy_history_block():
    """WO PART A section 1: 'same place energy_history is currently appended'."""
    src = _src(SERVER)
    eh = src.index('_state["energy_history"] = _eh')
    turn = src.index("on_conversation_turn")
    assert 0 < (turn - eh) < 1200, "turn drain is not on the per-turn path"


def test_battery_is_not_wired_into_state_energy():
    """
    state.energy is attention_model.emotional_context.energy — David's
    conversational affect, also feeding presence_plan.voice_energy. Wiring the
    battery into it would look plausible and be wrong.
    """
    src = _src(SERVER)
    window_start = src.index('_state["energy_history"] = _eh')
    window = src[window_start:window_start + 1200]
    assert not re.search(r'"energy"\s*:\s*_?batt', window)
    assert not re.search(r'_energy_now\s*=\s*.*health_battery', src)


def test_publish_called_so_the_fields_reach_blender_state():
    src = _src(SERVER)
    assert re.search(r"publish as _batt_publish", src)
    assert "_batt_publish()" in src


def test_battery_wiring_is_fail_quiet():
    """A battery failure must never take down a conversation turn."""
    src = _src(SERVER)
    idx = src.index("on_conversation_turn")
    block = src[idx - 400:idx + 300]
    assert "except Exception" in block, "battery wiring is not fail-quiet"
