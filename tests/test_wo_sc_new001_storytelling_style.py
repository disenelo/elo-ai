"""
tests/test_wo_sc_new001_storytelling_style.py

WO-SC-NEW-001: §2/§5 Build List — Storytelling style + speaking style.
Proves storytelling_style is computed in CognitivePlan and injected into
the system prompt in server.py.

Run: ~/miniconda3/bin/python3 -m pytest tests/test_wo_sc_new001_storytelling_style.py -q
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

_ROOT = os.path.join(os.path.dirname(__file__), "..")


def test_cognitive_plan_initialises_with_none():
    """AT-1: CognitivePlan() default storytelling_style is None."""
    from runtime.spine.plan import CognitivePlan
    plan = CognitivePlan()
    assert plan.storytelling_style is None, (
        f"AT-1: storytelling_style must default to None; got {plan.storytelling_style!r}"
    )


def test_studio_mode_infers_collaborative():
    """AT-2: STUDIO_MODE → 'collaborative' storytelling_style."""
    from runtime.spine.plan import CognitivePlan
    from runtime.spine.spine import _conversation_faculty
    plan = CognitivePlan(mode="STUDIO_MODE", raw="let's build something")
    _conversation_faculty(plan)
    assert plan.storytelling_style == "collaborative", (
        f"AT-2: STUDIO_MODE → 'collaborative'; got {plan.storytelling_style!r}"
    )


def test_no_mode_conversation_intent_is_none():
    """AT-3: empty mode, intent=conversation → storytelling_style remains None."""
    from runtime.spine.plan import CognitivePlan
    from runtime.spine.spine import _conversation_faculty
    plan = CognitivePlan(mode="", intent="conversation", raw="hello")
    _conversation_faculty(plan)
    assert plan.storytelling_style is None, (
        f"AT-3: empty mode/conversation → None; got {plan.storytelling_style!r}"
    )


def test_storytelling_style_is_accessible_dataclass_field():
    """AT-4: storytelling_style is a proper dataclass field on CognitivePlan."""
    import dataclasses
    from runtime.spine.plan import CognitivePlan
    fields = {f.name for f in dataclasses.fields(CognitivePlan)}
    assert "storytelling_style" in fields, (
        "AT-4: storytelling_style must be a dataclass field on CognitivePlan"
    )


def test_server_injects_storytelling_frame():
    """AT-5: server.py contains the WO-SC-NEW-001 D-3 injection block."""
    src = open(os.path.join(_ROOT, "server.py"), encoding="utf-8").read()
    assert "WO-SC-NEW-001" in src, (
        "AT-5: server.py must contain WO-SC-NEW-001 marker"
    )
    assert "STORYTELLING FRAME" in src, (
        "AT-5: server.py must inject [STORYTELLING FRAME] into system prompt"
    )
    assert "storytelling_style" in src, (
        "AT-5: server.py must reference plan.storytelling_style"
    )
