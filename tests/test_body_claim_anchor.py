"""
eLo must not claim to be in the physical robot.

Live, 2026-09-29, real server, real conversation:

    > Which body are you in right now?
    < I'm in the physical robot body, the one with the rounded inflatable
      TPU shell.

The robot has never been built. This is the conflation WO-CAP-EMB-051 calls
non-negotiable, and it came straight from the identity anchor, which said:

    "Form: rounded inflatable TPU shell, chibi proportions (~40cm tall) ..."
    "... I am the AI OS, not the physical robot."

A vivid concrete "Form:" followed by an abstract denial. The model resolved
it in favour of the concrete description.

The form description is kept -- eLo needs it to describe how the robot is
designed -- but scoped to the robot's DESIGN, with the body eLo is actually
in named from the live embodiment signal.
"""
from __future__ import annotations

import os
import re

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ROUTER = os.path.join(_ROOT, "runtime", "backend_router.py")


def _src() -> str:
    return open(_ROUTER, encoding="utf-8").read()


def test_anchor_names_the_live_body():
    """The anchor states the real body, not a static guess."""
    s = _src()
    assert "BODY RULE: I am in {_body_label} right now" in s
    assert "from runtime.embodiment_capabilities import current_body" in s


def test_the_shell_is_described_as_the_robots_design_not_as_elos_form():
    s = _src()
    assert 'Form: rounded inflatable TPU shell' not in s, (
        'the shell is presented as eLo\'s own "Form:" again — that is the '
        "phrasing that produced the live false-embodiment claim"
    )
    assert "is the DESIGN of the physical robot" in s


def test_anchor_forbids_claiming_the_robot_body():
    s = _src()
    for required in (
        "That robot has not been built and I have never been inside it",
        "never the robot",
        "Never claim to have physically done",
    ):
        assert required in s, required


def test_the_live_body_is_not_the_robot():
    """
    The embodiment signal must resolve to a simulated body on this machine.
    If this ever returns robot, the anchor would truthfully say robot -- so
    the guard is on the signal, not on the wording.
    """
    from runtime.embodiment_capabilities import current_body, ROBOT
    from runtime.memory_origin import can_claim_physical_experience, origin_for_embodiment
    body = current_body()
    assert body != ROBOT, f"live embodiment resolved to {body}"
    assert can_claim_physical_experience(origin_for_embodiment(body)) is False


def test_robot_capabilities_remain_future_tense():
    """EMB-002: the robot's abilities are 'Can eventually', never present."""
    from runtime.embodiment_capabilities import can, can_eventually, ROBOT
    for action in ("see", "move", "touch", "manipulate"):
        assert can(action, ROBOT) is False
        assert can_eventually(action, ROBOT) is True


def test_no_stray_control_bytes():
    assert b"\x08" not in open(_ROUTER, "rb").read()
