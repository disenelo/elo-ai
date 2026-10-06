"""
tests/test_perception_decision_trace.py

Acceptance criteria:
  PERC-1: perceive() is called in _process_turn (structural)
  PERC-2: high-sig perception events have significance >= 0.6 (WKG gate)
  PERC-3: high-sig events use SOURCE_ATTRIBUTED epistemic class
  DTRACE-1: CognitiveState has decision_trace field
  DTRACE-2: decision_trace default is empty dict
  DTRACE-3: decision_trace has expected structure keys
  DTRACE-4: data/decision_trace.jsonl path is referenced in server.py
"""
import pathlib, inspect


_SERVER_SRC = pathlib.Path("server.py").read_text()


# ── PERC-1: perceive() is called before get_last_result ──────────────────────

def test_perc_1_perceive_called_in_process_turn():
    """PERC-1: perceive() is imported and called in server.py _process_turn"""
    assert "from runtime.perception_faculty import perceive as _perc_perceive" in _SERVER_SRC
    assert "_perc_perceive(_BLENDER_STATE_PATH)" in _SERVER_SRC


# ── PERC-2: high-sig perception significance clears WKG gate ─────────────────

def test_perc_2_high_sig_clears_wkg_gate():
    """PERC-2: high-sig OBSERVATION significance is >= 0.6"""
    # Server source must declare significance >= 0.6 for high-sig perception
    assert "significance=0.65 if _high else 0.35" in _SERVER_SRC


# ── PERC-3: high-sig events use SOURCE_ATTRIBUTED ─────────────────────────────

def test_perc_3_high_sig_source_attributed():
    """PERC-3: high-sig OBSERVATION uses SOURCE_ATTRIBUTED epistemic class"""
    assert 'epistemic_class="SOURCE_ATTRIBUTED" if _high else' in _SERVER_SRC


# ── DTRACE-1: CognitiveState has decision_trace field ─────────────────────────

def test_dtrace_1_cognitive_state_has_field():
    """DTRACE-1: CognitiveState declares decision_trace"""
    from runtime.contracts import CognitiveState
    assert "decision_trace" in CognitiveState.__dataclass_fields__


# ── DTRACE-2: default is empty dict ───────────────────────────────────────────

def test_dtrace_2_default_empty_dict():
    """DTRACE-2: decision_trace defaults to {}"""
    from runtime.contracts import CognitiveState
    cs = CognitiveState()
    assert cs.decision_trace == {}


# ── DTRACE-3: decision_trace written by server with expected keys ──────────────

def test_dtrace_3_server_writes_expected_keys():
    """DTRACE-3: server.py writes decision_trace with action, cal_reason, grounded_by"""
    assert '"action":' in _SERVER_SRC or "_decision_trace[" in _SERVER_SRC
    assert '"cal_reason"' in _SERVER_SRC
    assert '"grounded_by"' in _SERVER_SRC


# ── DTRACE-4: audit log path is wired ────────────────────────────────────────

def test_dtrace_4_audit_log_path_wired():
    """DTRACE-4: data/decision_trace.jsonl path is referenced in server.py"""
    assert "decision_trace.jsonl" in _SERVER_SRC
