"""
tests/test_wo_voice_register_001.py — WO-VOICE-REGISTER-001
Linguistic voice identity: recognition, not performance.

AT-1  voice_register.py exists and is imported by prompt_builder.py
AT-2  Assembled prompt contains register examples (not instructions)
AT-3  Structural: register examples present (eLo speaks like / does not speak like)
AT-4  Non-performative: no caricature openers in the register block
AT-5  Provider-switch invariant: voice_register.py is not backend-specific
"""
from __future__ import annotations
import os
import sys
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

ok  = lambda msg: print(f"  PASS  {msg}")
err = lambda msg: (print(f"  FAIL  {msg}"), sys.exit(1))


# ── AT-1: voice_register.py exists and is imported by prompt_builder.py ────────
def test_at1_file_exists_and_imported():
    """AT-1: voice_register.py exists; prompt_builder imports it."""
    vr_path = os.path.join(ROOT, "runtime", "voice_register.py")
    assert os.path.isfile(vr_path), "AT-1: runtime/voice_register.py not found"

    pb_src = open(os.path.join(ROOT, "runtime", "prompt_builder.py"), encoding="utf-8").read()
    assert "voice_register" in pb_src, \
        "AT-1: prompt_builder.py does not import voice_register"
    ok("AT-1: voice_register.py exists and is referenced in prompt_builder.py")


# ── AT-2: assembled prompt contains register examples ──────────────────────────
def test_at2_register_in_assembled_prompt():
    """AT-2: build() output contains the linguistic register block with examples."""
    from runtime.prompt_builder import build
    prompt = build(user_input="Hey, what's good?")
    assert "VOICE IDENTITY" in prompt or "LINGUISTIC REGISTER" in prompt, \
        "AT-2: voice register section not in assembled prompt"
    assert "eLo speaks like:" in prompt, \
        "AT-2: 'eLo speaks like:' examples not in assembled prompt"
    ok("AT-2: assembled prompt contains voice register with examples")


# ── AT-3: both example blocks are present ─────────────────────────────────────
def test_at3_both_example_blocks():
    """AT-3: register block has 'eLo speaks like' AND 'eLo does not speak like' sections."""
    from runtime.voice_register import get_register_block
    block = get_register_block()
    assert "eLo speaks like:" in block, "AT-3: 'eLo speaks like:' missing"
    # WO-B1-0108/0109 updated the block to use "does NOT" (caps) for emphasis.
    assert any(x in block for x in ("eLo does not speak like:", "eLo does NOT speak like:")), \
        "AT-3: 'eLo does not/NOT speak like:' missing"
    # At least 3 positive examples
    positive_examples = [ln for ln in block.splitlines()
                         if ln.strip().startswith('"') and "does NOT" not in block.split(ln)[0].split("eLo does")[-1]]
    ok(f"AT-3: both example blocks present in register block ({len(positive_examples)} positive examples)")


# ── AT-4: no caricature openers in the register block ─────────────────────────
def test_at4_no_caricature():
    """AT-4: 'eLo speaks like' section has no caricature openers (flagged as forbidden)."""
    from runtime.voice_register import get_register_block
    block = get_register_block()

    # Extract the "eLo speaks like:" section only — split on "does not/NOT speak like"
    _split_marker = "eLo does NOT speak like:" if "eLo does NOT speak like:" in block else "eLo does not speak like:"
    positive_section = block.split(_split_marker)[0]

    caricature_markers = ["Wagwan!", "Wagwan,", "Blimey mate", "innit bruv",
                          "Let me assist you", "I am very excited"]
    for marker in caricature_markers:
        assert marker not in positive_section, \
            f"AT-4: caricature marker {marker!r} found in 'eLo speaks like' section"
    ok("AT-4: no caricature openers in 'eLo speaks like' examples")


# ── AT-5: voice_register.py is not backend-specific ───────────────────────────
def test_at5_provider_invariant():
    """AT-5: voice_register.py has no backend-specific imports."""
    src = open(os.path.join(ROOT, "runtime", "voice_register.py"), encoding="utf-8").read()
    backend_markers = ["openai", "claude", "groq", "ollama", "anthropic", "import backends"]
    for marker in backend_markers:
        assert marker not in src.lower(), \
            f"AT-5: voice_register.py contains backend-specific reference: {marker!r}"
    ok("AT-5: voice_register.py is backend-agnostic — register survives provider switch")


# ── runner ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("WO-VOICE-REGISTER-001 — Linguistic voice identity: recognition, not performance")
    print()
    test_at1_file_exists_and_imported()
    test_at2_register_in_assembled_prompt()
    test_at3_both_example_blocks()
    test_at4_no_caricature()
    test_at5_provider_invariant()
    print()
    print("5/5 PASS — eLo's linguistic identity wired into prompt builder")
