"""
tests/test_s4_rest_decision.py — S4 · WO-TIRED-SIT-001 Part B decision.

Pure policy: does eLo choose to sit, and can he say why not.
"""
from __future__ import annotations

import pytest

from runtime.rest_decision import ACT_BANDS, decide_rest, explain


_WALK = {"animation": "walk", "mode": "walk"}


# ── Acts ──────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("band", sorted(ACT_BANDS))
def test_fatigued_and_exhausted_sit(band):
    out = decide_rest(band, motion=_WALK)
    assert out is not None, band
    assert out["name"] == "sit"
    assert out["issued_by"] == "elo", "a self-initiated sit must be attributable"
    assert explain(band, motion=_WALK) == f"sitting:{band}"


def test_the_intent_shape_is_the_one_state_writer_already_derives_sit_command_from():
    """
    Not a second command contract. state_writer keys off intent["name"] == "sit"
    to write sit_command for Unity; this must hit that same branch.
    """
    from pathlib import Path
    src = (Path(__file__).resolve().parent.parent
           / "blender_bridge" / "state_writer.py").read_text(encoding="utf-8")
    assert 'intent.get("name") == "sit"' in src
    assert decide_rest("exhausted", motion=_WALK)["name"] == "sit"


# ── Declines, each with a named reason ────────────────────────────────────────

def test_tired_is_noticed_not_acted_on():
    assert decide_rest("tired", motion=_WALK) is None
    assert explain("tired", motion=_WALK) == "noticed_not_acted"


@pytest.mark.parametrize("band", ["rested", "normal", "untracked", "", "nonsense"])
def test_untired_bands_do_nothing(band):
    assert decide_rest(band, motion=_WALK) is None
    assert explain(band, motion=_WALK) == "not_tired_enough"


def test_a_dream_is_never_interrupted_to_sit():
    assert decide_rest("exhausted", motion=_WALK, dreaming=True) is None
    assert explain("exhausted", motion=_WALK, dreaming=True) == "dreaming"


def test_does_not_change_posture_mid_sentence():
    assert decide_rest("exhausted", motion=_WALK, speaking=True) is None


def test_davids_instruction_outranks_elos_legs():
    assert decide_rest("exhausted", motion=_WALK, commanded=True) is None
    assert explain("exhausted", motion=_WALK, commanded=True) == "commanded"


@pytest.mark.parametrize("mode", ["calm", "sit", "sitting", "sleeping", "dream",
                                  "lying_down"])
def test_already_resting_is_not_a_reason_to_sit_again(mode):
    assert decide_rest("exhausted", motion={"animation": mode, "mode": mode}) is None
    assert explain("exhausted", motion={"animation": mode, "mode": mode}) == "already_resting"


def test_every_decline_names_itself():
    """No silent refusals — "eLo did not sit" must always be answerable."""
    for kwargs in (
        {"physical_state": "rested"},
        {"physical_state": "tired"},
        {"physical_state": "exhausted", "dreaming": True},
        {"physical_state": "exhausted", "speaking": True},
        {"physical_state": "exhausted", "commanded": True},
        {"physical_state": "exhausted", "motion": {"mode": "calm"}},
    ):
        band = kwargs.pop("physical_state")
        assert decide_rest(band, **kwargs) is None
        assert explain(band, **kwargs).strip(), kwargs


# ── Purity: a decision, not a side effect ─────────────────────────────────────

def test_the_decision_writes_nothing():
    """
    It reads no state and writes none, so nothing acquires a second route to
    the body through this module.

    Checked on the parsed tree, not on the text: the docstring names
    state_writer to explain the intent shape, and a substring scan would read
    prose as behaviour — which is the same mistake as reading a WO instead of
    the source.
    """
    import ast
    from pathlib import Path
    src = (Path(__file__).resolve().parent.parent
           / "runtime" / "rest_decision.py").read_text(encoding="utf-8")
    tree = ast.parse(src)

    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add((node.module or "").split(".")[0])
    assert imported <= {"__future__", "typing"}, imported

    called = {
        node.func.id for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "open" not in called


def test_the_bands_match_the_batterys_own_vocabulary():
    """A band this module names but the battery never emits is dead policy."""
    from core.health_battery import PHYSICAL_STATES
    emitted = {name for _, name in PHYSICAL_STATES}
    from runtime.rest_decision import ACT_BANDS as _A, NOTICE_BANDS as _N
    assert (_A | _N) <= emitted, (_A | _N) - emitted
