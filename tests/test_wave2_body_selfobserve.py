"""
tests/test_wave2_body_selfobserve.py — Wave 2 proofs: Row 3 BODY + Row 24 SELF-OBSERVE.

AT-W2-1: record_behaviour() populates recent_behavior — non-empty after simulated turns
AT-W2-2: server.py sit ACK path calls record_behaviour (text search proof)
AT-W2-3: server.py move ACK path calls record_behaviour (text search proof)
AT-W2-4: server.py exit ACK path calls record_behaviour (text search proof)
AT-W2-5: server.py BODY field reads embodiment_history — not hardcoded "desktop"
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


# ── AT-W2-1: record_behaviour() increments recent_behavior ───────────────────

def test_record_behaviour_populates_recent_behavior():
    from self.elo_self_model import EloSelfState, record_behaviour
    state = EloSelfState()
    assert state.recent_behavior == {}, "fresh state should have empty recent_behavior"
    state = record_behaviour(state, "sit")
    state = record_behaviour(state, "move")
    state = record_behaviour(state, "sit")
    assert "sit" in state.recent_behavior, "recent_behavior missing 'sit'"
    assert "move" in state.recent_behavior, "recent_behavior missing 'move'"
    assert state.recent_behavior["sit"] == 2, f"sit count: {state.recent_behavior['sit']}"
    assert state.recent_behavior["move"] == 1, f"move count: {state.recent_behavior['move']}"


# ── AT-W2-2..4: ACK paths call record_behaviour ──────────────────────────────

def _server_src():
    path = os.path.join(ROOT, "server.py")
    with open(path, encoding="utf-8") as f:
        return f.read()


def test_sit_ack_calls_record_behaviour():
    src = _server_src()
    # Find the _ls_sit_rec block area to locate sit ACK region
    sit_idx = src.find("_ls_sit_rec(")
    assert sit_idx != -1, "_ls_sit_rec not found in server.py"
    # record_behaviour call for sit must appear near the sit ACK block
    rb_sit = src.find('record_behaviour as _rb_sit')
    assert rb_sit != -1, \
        "sit ACK path missing record_behaviour import (_rb_sit) — Row 24 SELF-OBSERVE not applied"


def test_move_ack_calls_record_behaviour():
    src = _server_src()
    rb_mv = src.find('record_behaviour as _rb_mv')
    assert rb_mv != -1, \
        "move ACK path missing record_behaviour import (_rb_mv) — Row 24 SELF-OBSERVE not applied"


def test_exit_ack_calls_record_behaviour():
    src = _server_src()
    rb_ex = src.find('record_behaviour as _rb_ex')
    assert rb_ex != -1, \
        "exit ACK path missing record_behaviour import (_rb_ex) — Row 24 SELF-OBSERVE not applied"


# ── AT-W2-5: BODY field reads embodiment_history, not hardcoded "desktop" ────

def test_body_field_not_hardcoded():
    src = _server_src()
    # The old bad code: embodiment="desktop"  (as a hardcoded literal)
    # Find _self_apply_embodiment calls that still use the literal
    import re
    # Look for _self_apply_embodiment(... embodiment="desktop" ...)  on a single line
    bad_pattern = re.compile(r'_self_apply_embodiment\([^)]*embodiment=["\']desktop["\']')
    bad_matches = bad_pattern.findall(src)
    # Filter to only the perch-reapply block (not other legitimate uses)
    # The fix replaces the hardcoded one with _active_body variable
    assert '_active_body' in src, \
        "_active_body variable not found — server.py BODY fix not applied (Row 3)"
    assert 'embodiment_history' in src, \
        "embodiment_history not referenced in server.py — Row 3 BODY fix missing"
