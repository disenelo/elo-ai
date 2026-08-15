"""
tests/test_0017_ct4v07_claim_gate.py — CT4V-07: Structural claim-type gate.

Card 0022: Executive Self-Consultation Gate.
  "Before eLo makes a claim about any of these, the Executive must retrieve the
   relevant Self / World / Moment state: identity, location, capability, memory,
   action, intention, learning, history, emotion, current state."
  "Tiers only fall, never rise (Vol VII §3.1.4)."

The gate classifies incoming questions by claim type, checks the named state
source, and returns UNKNOWN-tier responses directly when the source is absent.
LLM is never consulted when the tier is UNKNOWN.

Tests:
    CG-1  Memory recall + empty vault + empty interactions → UNKNOWN response returned
    CG-2  Memory recall + vault has records → None returned (LLM proceeds)
    CG-3  Vision question + vision_active=False → UNKNOWN response returned
    CG-4  Vision question + vision_active=True (or absent) → None returned
    CG-5  History question + empty autobiography → UNKNOWN response returned
    CG-6  History question + entries exist → None returned
    CG-7  Non-claim question → (None, None) returned
    CG-8  spine.py _conversation_faculty has CT4V-07 wiring (source check)

Run: python3 tests/test_0017_ct4v07_claim_gate.py
"""

import inspect
import json
import os
import sys
import tempfile

sys.path.insert(0, ".")

import logging
logging.basicConfig(level=logging.CRITICAL)

PASS = 0; FAIL = 0

def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


# ── CG-1: Memory recall + empty sources → UNKNOWN ────────────────────────────

print("\nCG-1: memory recall with empty vault → UNKNOWN response")
try:
    import unittest.mock as _mock

    _empty_lookup = lambda q, max_results=5: []
    _empty_retrieve = lambda q, top_k=5: []
    _empty_ra = lambda n=10, **kw: []

    with _mock.patch("memory.vault_layer.lookup", _empty_lookup), \
         _mock.patch("core.memory_engine.retrieve", _empty_retrieve), \
         _mock.patch("self.emergent_cognition.recent_autobiography", _empty_ra):
        from runtime.claim_gate import _memory_gate, classify_and_gate
        resp = _memory_gate("do you remember what we discussed last time?")

    if resp is not None and len(resp) > 10:
        ok(f"CG-1 — empty vault → UNKNOWN response returned ({len(resp)} chars)")
    else:
        fail("CG-1", f"expected UNKNOWN response string, got {resp!r}")
except Exception as e:
    fail("CG-1", repr(e))


# ── CG-2: Memory recall + vault has records → None (LLM proceeds) ─────────────

print("\nCG-2: memory recall with vault records → None (LLM proceeds)")
try:
    import importlib

    _hit = [{"spot": "X·BL·0000·5", "summary": "We discussed the eLo game design.", "date": "2026-08-01", "weight": 5}]
    _hit_lookup = lambda q, max_results=5: _hit

    import unittest.mock as _mock2
    import runtime.claim_gate as _cg
    importlib.reload(_cg)

    with _mock2.patch("memory.vault_layer.lookup", _hit_lookup):
        resp2 = _cg._memory_gate("tell me something we talked about before")

    if resp2 is None:
        ok("CG-2 — vault has records → None returned (LLM proceeds)")
    else:
        fail("CG-2", f"expected None when records exist, got {resp2!r}")
except Exception as e:
    fail("CG-2", repr(e))


# ── CG-3: Vision question + vision_active=False → UNKNOWN ─────────────────────

print("\nCG-3: vision question with vision_active=False → UNKNOWN response")
try:
    import runtime.claim_gate as _cg3
    import importlib
    importlib.reload(_cg3)

    with tempfile.TemporaryDirectory() as _tmpdir:
        _blender_dir = os.path.join(_tmpdir, "blender")
        os.makedirs(_blender_dir)
        _bs_path = os.path.join(_blender_dir, "blender_state.json")
        with open(_bs_path, "w") as _f:
            json.dump({"vision_active": False}, _f)

        # Temporarily override _ROOT so the gate reads our test file
        _orig_root = _cg3._ROOT
        _cg3._ROOT = _tmpdir
        try:
            resp3 = _cg3._vision_gate()
        finally:
            _cg3._ROOT = _orig_root

    if resp3 is not None and "can't see" in resp3.lower():
        ok(f"CG-3 — vision_active=False → UNKNOWN response: {resp3[:60]!r}")
    else:
        fail("CG-3", f"expected 'can't see' response, got {resp3!r}")
except Exception as e:
    fail("CG-3", repr(e))


# ── CG-4: Vision question + vision_active=True → None (LLM proceeds) ──────────

print("\nCG-4: vision question with vision_active=True → None (LLM proceeds)")
try:
    import runtime.claim_gate as _cg4
    import importlib
    importlib.reload(_cg4)

    with tempfile.TemporaryDirectory() as _tmpdir4:
        _blender_dir4 = os.path.join(_tmpdir4, "blender")
        os.makedirs(_blender_dir4)
        _bs_path4 = os.path.join(_blender_dir4, "blender_state.json")
        with open(_bs_path4, "w") as _f4:
            json.dump({"vision_active": True}, _f4)

        _orig_root4 = _cg4._ROOT
        _cg4._ROOT = _tmpdir4
        try:
            resp4 = _cg4._vision_gate()
        finally:
            _cg4._ROOT = _orig_root4

    if resp4 is None:
        ok("CG-4 — vision_active=True → None returned (LLM proceeds)")
    else:
        fail("CG-4", f"expected None when vision is active, got {resp4!r}")
except Exception as e:
    fail("CG-4", repr(e))


# ── CG-5: History question + empty autobiography → UNKNOWN ────────────────────

print("\nCG-5: history question with empty autobiography → UNKNOWN response")
try:
    import unittest.mock as _mock5
    import runtime.claim_gate as _cg5
    import importlib
    importlib.reload(_cg5)

    _empty_ra5 = lambda n=10, **kw: []

    with _mock5.patch("self.emergent_cognition.recent_autobiography", _empty_ra5):
        resp5 = _cg5._history_gate()

    if resp5 is not None and len(resp5) > 10:
        ok(f"CG-5 — empty autobiography → UNKNOWN response ({len(resp5)} chars)")
    else:
        fail("CG-5", f"expected UNKNOWN response string, got {resp5!r}")
except Exception as e:
    fail("CG-5", repr(e))


# ── CG-6: History question + entries exist → None (LLM proceeds) ──────────────

print("\nCG-6: history question with autobiography entries → None (LLM proceeds)")
try:
    import unittest.mock as _mock6
    import runtime.claim_gate as _cg6
    import importlib
    importlib.reload(_cg6)

    _entries = [
        {"ts": 1786664350.0, "event": "sat on Chrome", "kind": "physical", "verified": True}
    ]
    _ra_entries = lambda n=10, **kw: _entries

    with _mock6.patch("self.emergent_cognition.recent_autobiography", _ra_entries):
        resp6 = _cg6._history_gate()

    if resp6 is None:
        ok("CG-6 — autobiography has entries → None returned (LLM proceeds)")
    else:
        fail("CG-6", f"expected None when history exists, got {resp6!r}")
except Exception as e:
    fail("CG-6", repr(e))


# ── CG-7: Non-claim question → (None, None) ────────────────────────────────────

print("\nCG-7: non-claim question → (None, None) — no gate fires")
try:
    import runtime.claim_gate as _cg7
    import importlib
    importlib.reload(_cg7)

    _claim_type, _resp = _cg7.classify_and_gate("what's the weather today?")

    if _claim_type is None and _resp is None:
        ok("CG-7 — 'what's the weather today?' → (None, None) — no gate fires")
    else:
        fail("CG-7", f"expected (None, None), got ({_claim_type!r}, {_resp!r})")
except Exception as e:
    fail("CG-7", repr(e))


# ── CG-8: spine.py wires CT4V-07 gate ─────────────────────────────────────────

print("\nCG-8: spine.py _conversation_faculty has CT4V-07 wiring")
try:
    import runtime.spine.spine as _sp
    _src = inspect.getsource(_sp._conversation_faculty)
    _has_ct4v = "CT4V-07" in _src and "classify_and_gate" in _src
    _has_backend = "claim_gate" in _src
    _has_tier_never_rise = "UNKNOWN" in _src or "claim_gate" in _src

    if _has_ct4v and _has_backend:
        ok("CG-8 — spine._conversation_faculty has CT4V-07 wiring + claim_gate backend")
    else:
        fail("CG-8", f"CT4V-07 wiring missing — ct4v={_has_ct4v}, backend={_has_backend}")
except Exception as e:
    fail("CG-8", repr(e))


# ── results ───────────────────────────────────────────────────────────────────

print(f"\n{'='*50}")
print(f"CT4V-07 Claim Gate: {PASS} passed, {FAIL} failed")
print()
print("Gate behaviour:")
print("  memory (empty vault+interactions) → UNKNOWN: 'My memory's clean on that one.'")
print("  memory (records exist)            → None: LLM proceeds with vault context injected")
print("  capability.vision (off)           → UNKNOWN: 'I can't see your screen right now.'")
print("  capability.vision (on/absent)     → None: LLM proceeds")
print("  history (autobiography empty)     → UNKNOWN: 'The record's still building.'")
print("  history (entries exist)           → None: LLM proceeds with autobiography context")
print()
print("Tiers only fall, never rise (Vol VII §3.1.4).")
print("Rule 1 alarm: every downgrade logged at INFO level.")
if FAIL:
    sys.exit(1)
