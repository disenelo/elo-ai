"""
tests/test_wo_source_001.py — WO-SOURCE-001: Identity Kernel (Immutable Identity Layer)

AT-1  IdentityKernel is frozen — any mutation raises FrozenInstanceError
AT-2  IdentityKernel.load() returns all 10 fields from YAML (not fallback defaults)
AT-3  executive_faculty receives identity kwarg without exception
AT-4  as_anchor_block() contains [IDENTITY ANCHOR] header and purpose/philosophy/boundaries
AT-5  prompt_builder injects identity_anchor block in assembled prompt
"""
from __future__ import annotations
import os
import sys
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

ok  = lambda msg: print(f"  PASS  {msg}")
err = lambda msg: (print(f"  FAIL  {msg}"), sys.exit(1))


# ── AT-1: FrozenInstanceError on mutation ────────────────────────────────────
def test_at1_immutable():
    """AT-1: frozen=True — any field mutation raises FrozenInstanceError."""
    from dataclasses import FrozenInstanceError
    from runtime.identity_kernel import IdentityKernel, IDENTITY
    try:
        IDENTITY.purpose = "mutated"
        assert False, "AT-1: expected FrozenInstanceError, got no exception"
    except (FrozenInstanceError, AttributeError):
        pass  # FrozenInstanceError IS an AttributeError in some Python versions
    ok("AT-1: IDENTITY is immutable — FrozenInstanceError raised on mutation attempt")


# ── AT-2: all 10 fields loaded from YAML ─────────────────────────────────────
def test_at2_yaml_fields():
    """AT-2: load() reads all 10 fields from kernel/identity/identity_kernel.yaml."""
    from runtime.identity_kernel import IdentityKernel
    identity = IdentityKernel.load()
    required_fields = [
        "purpose", "core_philosophy", "relationship_to_david",
        "relationship_to_disenelo", "creative_worldview", "long_term_mission",
        "communication_boundaries", "ethical_constraints",
        "narrative_consistency", "embodiment_independence",
    ]
    for field in required_fields:
        val = getattr(identity, field, None)
        assert val and len(val) > 10, \
            f"AT-2: field '{field}' empty or missing: {val!r}"
    # Verify it's loading from YAML (not fallback): check YAML-specific phrasing
    assert "Disenelo is building" in identity.purpose, \
        f"AT-2: purpose doesn't match YAML: {identity.purpose!r}"
    ok(f"AT-2: all {len(required_fields)} fields loaded from YAML with non-empty values")


# ── AT-3: _executive_faculty receives identity without exception ──────────────
def test_at3_executive_receives_identity():
    """AT-3: _executive_faculty() accepts identity kwarg (IdentityKernel) without raising."""
    import inspect
    from runtime.spine.spine import _executive_faculty
    from runtime.identity_kernel import IDENTITY
    sig = inspect.signature(_executive_faculty)
    assert "identity" in sig.parameters, \
        "AT-3: _executive_faculty missing 'identity' parameter"
    param = sig.parameters["identity"]
    # Default should be None (module singleton passed at call site)
    assert param.default is None, \
        f"AT-3: identity default should be None, got {param.default!r}"
    ok("AT-3: _executive_faculty has 'identity' parameter with default=None")


# ── AT-4: as_anchor_block() format ───────────────────────────────────────────
def test_at4_anchor_block_format():
    """AT-4: as_anchor_block() has [IDENTITY ANCHOR] header + 3 required lines."""
    from runtime.identity_kernel import IDENTITY
    block = IDENTITY.as_anchor_block()
    assert block.startswith("[IDENTITY ANCHOR]"), \
        f"AT-4: block doesn't start with '[IDENTITY ANCHOR]': {block[:60]!r}"
    assert "purpose:" in block, "AT-4: block missing 'purpose:' line"
    assert "philosophy:" in block, "AT-4: block missing 'philosophy:' line"
    # The label was renamed "boundaries:" -> "hard constraints:" in 6275c55 and
    # this assertion was left behind, so it has been red since. Asserting the
    # CONTENT rather than the label: the point of AT-4 is that the boundaries
    # field reaches the anchor, not what the prefix happens to be called.
    assert IDENTITY.communication_boundaries[:40] in block, \
        "AT-4: block missing the communication_boundaries content"
    # Should NOT include all 10 fields (3 only per D-5 spec)
    assert "relationship_to_david:" not in block, \
        "AT-4: block unexpectedly includes relationship_to_david (spec: 3 fields only)"
    ok(f"AT-4: anchor block correct — 3 fields, [IDENTITY ANCHOR] header")


# ── AT-5: prompt_builder includes identity_anchor ────────────────────────────
def test_at5_prompt_builder_injects_anchor():
    """AT-5: build() includes [IDENTITY ANCHOR] block in assembled prompt."""
    from runtime.prompt_builder import build
    prompt = build(
        user_input="hello",
        attention={"valence": "neutral", "significance": 0.3, "intent": "conversation"},
        exec_decision={"tone": "DIRECT", "max_sentences": 3, "conversation_action": "answer",
                       "valence": "neutral", "momentum": "stable", "vessel_phase": "EXPRESS"},
        personality_block="",
        self_block="",
    )
    assert "[IDENTITY ANCHOR]" in prompt, \
        "AT-5: [IDENTITY ANCHOR] block not found in assembled prompt"
    ok("AT-5: prompt_builder injects [IDENTITY ANCHOR] block in every assembled prompt")


# ── runner ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("WO-SOURCE-001 — Identity Kernel (Immutable Identity Layer)")
    print()
    test_at1_immutable()
    test_at2_yaml_fields()
    test_at3_executive_receives_identity()
    test_at4_anchor_block_format()
    test_at5_prompt_builder_injects_anchor()
    print()
    print("5/5 PASS — identity kernel immutable, YAML loaded, anchor injected")
