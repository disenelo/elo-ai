"""
tests/test_elo_self_knowledge_001.py — Self-knowledge module
eLo knows what it can and cannot do from the registry at runtime.

AT-1  build_self_knowledge() returns a SelfKnowledge object
AT-2  can_do list is non-empty and all entries have available=True
AT-3  cannot_do list contains future=True capabilities
AT-4  can_do and cannot_do are disjoint
AT-5  knows_it_cannot() returns True for a future capability
AT-6  knows_it_cannot() returns False for an enabled capability
AT-7  is_self_model_complete(): all registry capabilities accounted for
AT-8  gap_for_goal() returns relevant missing capabilities
AT-9  Mobile embodiment: subset differs from terminal
AT-10 self_knowledge_block() returns non-empty string
AT-11 self_knowledge_block() contains "CAN DO NOW" and "NOT YET BUILT"
AT-12 self_knowledge_block() never raises (resilient)
AT-13 Server.py wiring present
AT-14 py_compile clean
"""
from __future__ import annotations

import os
import sys
import py_compile

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from runtime.self_knowledge import (
    build_self_knowledge,
    self_knowledge_block,
    SelfKnowledge,
    CapabilitySnapshot,
    _EMBODIMENT_TERMINAL,
    _EMBODIMENT_MOBILE,
)


# ── AT-1 ──────────────────────────────────────────────────────────────────────

def test_at1_build_self_knowledge_returns_object():
    sk = build_self_knowledge()
    assert isinstance(sk, SelfKnowledge)
    assert sk.embodiment == _EMBODIMENT_TERMINAL


# ── AT-2 ──────────────────────────────────────────────────────────────────────

def test_at2_can_do_is_non_empty_and_available():
    sk = build_self_knowledge()
    assert sk.can_do, "AT-2 FAIL: can_do list is empty — registry may not be loading"
    for c in sk.can_do:
        assert isinstance(c, CapabilitySnapshot)
        assert c.available is True, f"AT-2 FAIL: {c.id} in can_do but available=False"
        assert c.id
        assert c.display_name


# ── AT-3 ──────────────────────────────────────────────────────────────────────

def test_at3_cannot_do_contains_future_capabilities():
    sk = build_self_knowledge()
    # Registry has multiple future=True capabilities (robot_*, terminal, camera, etc.)
    assert sk.cannot_do, (
        "AT-3 FAIL: cannot_do list is empty — either all capabilities are built "
        "(unlikely) or future=True flag is not being read correctly"
    )
    for c in sk.cannot_do:
        assert c.available is False, f"AT-3 FAIL: {c.id} in cannot_do but available=True"


# ── AT-4 ──────────────────────────────────────────────────────────────────────

def test_at4_can_do_and_cannot_do_are_disjoint():
    sk = build_self_knowledge()
    overlap = sk.can_do_ids & sk.cannot_do_ids
    assert not overlap, (
        f"AT-4 FAIL: {overlap} appear in both can_do and cannot_do — self-model is contradictory"
    )


# ── AT-5 ──────────────────────────────────────────────────────────────────────

def test_at5_knows_it_cannot_true_for_future():
    from runtime.capabilities.registry import ALL_CAPABILITIES
    future_ids = [c.id for c in ALL_CAPABILITIES if c.future]
    assert future_ids, "AT-5: no future capabilities in registry — test needs future cap to exist"

    sk = build_self_knowledge()
    # Pick the first future capability
    future_id = future_ids[0]
    assert sk.knows_it_cannot(future_id), (
        f"AT-5 FAIL: eLo does not know it cannot do '{future_id}' — a future capability. "
        "Self-model is incomplete."
    )


# ── AT-6 ──────────────────────────────────────────────────────────────────────

def test_at6_knows_it_cannot_false_for_enabled():
    sk = build_self_knowledge()
    assert sk.can_do, "AT-6: need at least one enabled capability"
    enabled_id = sk.can_do[0].id
    assert not sk.knows_it_cannot(enabled_id), (
        f"AT-6 FAIL: eLo incorrectly believes it cannot do '{enabled_id}' — "
        "which is actually enabled."
    )


# ── AT-7 ──────────────────────────────────────────────────────────────────────

def test_at7_self_model_is_complete():
    sk = build_self_knowledge()
    assert sk.is_self_model_complete(), (
        "AT-7 FAIL: self-model is incomplete — some registry capabilities are not "
        "accounted for in can_do + cannot_do + not_on_body. "
        "eLo has a blind spot in its self-knowledge."
    )


# ── AT-8 ──────────────────────────────────────────────────────────────────────

def test_at8_gap_for_goal():
    sk = build_self_knowledge()
    if not sk.cannot_do:
        pytest.skip("No future capabilities to test gap_for_goal")
    # Pick a capability from cannot_do and construct a goal mentioning it
    target = sk.cannot_do[0]
    gaps = sk.gap_for_goal(target.display_name)
    assert any(g.id == target.id for g in gaps), (
        f"AT-8 FAIL: gap_for_goal() did not surface '{target.id}' for goal "
        f"mentioning '{target.display_name}'"
    )


# ── AT-9 ──────────────────────────────────────────────────────────────────────

def test_at9_mobile_subset_differs_from_terminal():
    sk_terminal = build_self_knowledge(_EMBODIMENT_TERMINAL)
    sk_mobile   = build_self_knowledge(_EMBODIMENT_MOBILE)
    # Mobile has fewer capabilities (no desktop apps, no volume control etc.)
    assert len(sk_mobile.can_do) < len(sk_terminal.can_do) or sk_mobile.not_on_body, (
        "AT-9 FAIL: mobile and terminal have same can_do set — embodiment filter not working. "
        "Mobile should have fewer capabilities than terminal."
    )


# ── AT-10 ─────────────────────────────────────────────────────────────────────

def test_at10_self_knowledge_block_non_empty():
    block = self_knowledge_block()
    assert isinstance(block, str), "AT-10 FAIL: self_knowledge_block() did not return string"
    assert len(block) > 50, (
        f"AT-10 FAIL: self_knowledge_block() too short ({len(block)} chars)"
    )


# ── AT-11 ─────────────────────────────────────────────────────────────────────

def test_at11_block_contains_required_sections():
    block = self_knowledge_block()
    assert "CAN DO NOW" in block, "AT-11 FAIL: missing 'CAN DO NOW' section"
    assert "NOT YET BUILT" in block, "AT-11 FAIL: missing 'NOT YET BUILT' section"
    assert "SELF-KNOWLEDGE" in block, "AT-11 FAIL: missing 'SELF-KNOWLEDGE' header"


# ── AT-12 ─────────────────────────────────────────────────────────────────────

def test_at12_self_knowledge_block_resilient():
    from unittest.mock import patch
    import runtime.self_knowledge as sk_mod

    # Simulate build_self_knowledge raising unexpectedly
    def _boom(embodiment=_EMBODIMENT_TERMINAL):
        raise RuntimeError("simulated registry failure")

    with patch.object(sk_mod, "build_self_knowledge", _boom):
        try:
            result = sk_mod.self_knowledge_block()
            assert isinstance(result, str), "AT-12 FAIL: should return str on error"
            # On error path the block returns "" — that's fine
        except Exception as exc:
            pytest.fail(f"AT-12 FAIL: self_knowledge_block raised: {exc}")


# ── AT-13 ─────────────────────────────────────────────────────────────────────

def test_at13_server_wiring():
    server_path = os.path.join(ROOT, "server.py")
    with open(server_path, encoding="utf-8") as f:
        source = f.read()
    assert "self_knowledge_block" in source, (
        "AT-13 FAIL: self_knowledge_block not in server.py"
    )
    assert "runtime.self_knowledge" in source, (
        "AT-13 FAIL: runtime.self_knowledge import missing from server.py"
    )


# ── AT-14 ─────────────────────────────────────────────────────────────────────

def test_at14_py_compile_clean():
    files = [
        os.path.join(ROOT, "runtime", "self_knowledge.py"),
        os.path.join(ROOT, "server.py"),
    ]
    for path in files:
        try:
            py_compile.compile(path, doraise=True)
        except py_compile.PyCompileError as exc:
            pytest.fail(f"AT-14: {os.path.basename(path)} compile error: {exc}")
