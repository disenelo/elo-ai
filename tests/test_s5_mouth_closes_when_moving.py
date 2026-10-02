"""
S5 — eLo's mouth closes while his body is moving.

eLo has NO EYES. Expression is body posture and mouth only, which makes an
open mouth carry more than it would on a face with eyes — and makes it read
as gormless during locomotion: a wide-open mouth sprinting across the desktop.

expression_mapper had no motion awareness at all, so MouthOpen.Wide from an
emotional blend stayed open through a walk, a run or a jump.
"""
from __future__ import annotations

import pytest

from expression.expression_mapper import (
    build_expression, close_mouth_if_moving, is_locomoting,
    LOCOMOTION_CLIPS, MOUTH_OPEN_KEYS,
)
from presence.presence_state import PresenceMode


def _mouth(motion, mode=PresenceMode.CELEBRATING, action="CELEBRATE"):
    return build_expression(mode, action, 0.9, motion)["shape_keys"].get("MouthOpen.Wide")


@pytest.mark.parametrize("clip", ["walk", "run", "jump", "pace", "wander", "hop"])
def test_mouth_closes_while_travelling(clip):
    assert _mouth({"animation": clip, "mode": clip}) == 0.0, clip


@pytest.mark.parametrize("clip", ["idle", "sit", "float", "calm", "breathe"])
def test_mouth_opens_when_still(clip):
    assert _mouth({"animation": clip, "mode": clip}) > 0.0, clip


def test_no_motion_given_leaves_expression_untouched():
    """Back-compat: the parameter is optional and absent means unchanged."""
    assert _mouth(None) == _mouth({"animation": "idle"})


def test_only_the_mouth_closes():
    """Smile and cheeks are posture-compatible — eLo can be happy while moving."""
    still = build_expression(PresenceMode.CELEBRATING, "CELEBRATE", 0.9,
                             {"animation": "idle"})["shape_keys"]
    moving = build_expression(PresenceMode.CELEBRATING, "CELEBRATE", 0.9,
                              {"animation": "run"})["shape_keys"]
    for k, v in still.items():
        if k in MOUTH_OPEN_KEYS:
            assert moving[k] == 0.0
        else:
            assert moving[k] == v, f"{k} changed and is not a mouth key"


def test_the_key_stays_present_at_zero():
    """
    Dropping the key would leave Blender holding its last value and the mouth
    would simply stick open. It must be present and zero.
    """
    moving = build_expression(PresenceMode.CELEBRATING, "CELEBRATE", 0.9,
                              {"animation": "walk"})["shape_keys"]
    assert "MouthOpen.Wide" in moving and moving["MouthOpen.Wide"] == 0.0


def test_accepts_a_bare_clip_name_or_a_motion_dict():
    assert is_locomoting("run") and is_locomoting({"animation": "run"})
    assert not is_locomoting("idle") and not is_locomoting({})


def test_handles_junk_without_raising():
    for probe in (None, "", {}, {"animation": None}, 7, object()):
        assert isinstance(is_locomoting(probe), bool)
        assert close_mouth_if_moving({"MouthOpen.Wide": 1.0}, probe)


def test_locomotion_vocabulary_matches_the_animation_driver():
    """A clip the driver knows as travel must be in the set."""
    from blender_bridge.animation_driver import KNOWN_CLIPS
    for travel in ("walk", "jump"):
        assert travel in KNOWN_CLIPS and travel in LOCOMOTION_CLIPS


def test_the_turn_path_passes_motion():
    """Without this the mapper never learns the body is moving."""
    import os
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src = open(os.path.join(root, "server.py"), encoding="utf-8").read()
    assert "_expr_build(_pstate.mode, _action, _pstate.intensity, _cmd)" in src
