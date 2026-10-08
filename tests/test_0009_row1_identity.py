"""
tests/test_0009_row1_identity.py — Row 1 IDENTITY proof.

Proof: Change a field in EloSelfState → the rendered prompt changes.
No identity fields missing; no hardcoded string.

Tests:
    ID-1  identity_block() contains identity_name from state
    ID-2  Changing identity_name → block changes
    ID-3  Changing core_values → block changes
    ID-4  Changing invariants → block changes (if non-empty)
    ID-5  [IDENTITY] header present in every render

Run: python3 tests/test_0009_row1_identity.py
"""
import sys
sys.path.insert(0, ".")

import logging
logging.basicConfig(level=logging.CRITICAL)

PASS = 0; FAIL = 0

def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


from self.elo_self_model import EloSelfState, identity_block


_DEFAULT = EloSelfState()
_DEFAULT_BLOCK = identity_block(_DEFAULT)


print("\nID-1: identity_block() contains identity_name from state")
try:
    if _DEFAULT.identity_name in _DEFAULT_BLOCK:
        ok(f"ID-1 — identity_name={_DEFAULT.identity_name!r} present in block")
    else:
        fail("ID-1", f"identity_name {_DEFAULT.identity_name!r} missing from block")
except Exception as e:
    fail("ID-1", repr(e))


print("\nID-2: changing identity_name → block changes")
try:
    altered = EloSelfState(identity_name="TestBot")
    altered_block = identity_block(altered)
    if _DEFAULT_BLOCK != altered_block and "TestBot" in altered_block:
        ok("ID-2 — identity_name change propagates to rendered block")
    else:
        _preview = repr(_DEFAULT_BLOCK[:60])
        fail("ID-2", f"block did not change: default={_preview}")
except Exception as e:
    fail("ID-2", repr(e))


print("\nID-3: core_values NOT in block (BDRIFT-U ruling 2026-08-22)")
# Updated 2026-10-08: BDRIFT-U (David L3) removed core_values from the identity
# block. core_values is experiential self-state, not constitutional identity.
# Canonical character traits come from canonical_identity.md via personality_block.
# This test now guards the BDRIFT-U decision — core_values must NOT appear.
try:
    altered = EloSelfState(core_values=["novel_value_xyz"])
    altered_block = identity_block(altered)
    if "novel_value_xyz" not in altered_block:
        ok("ID-3 — core_values absent from identity block (BDRIFT-U ruling held)")
    else:
        fail("ID-3", "core_values leaked into identity block — BDRIFT-U ruling violated")
except Exception as e:
    fail("ID-3", repr(e))


print("\nID-4: changing invariants → block changes")
try:
    altered = EloSelfState(invariants=["novel_invariant_abc"])
    altered_block = identity_block(altered)
    if "novel_invariant_abc" in altered_block:
        ok("ID-4 — invariants change propagates to rendered block")
    else:
        _preview = repr(altered_block[:80])
        fail("ID-4", f"novel_invariant_abc missing from block: {_preview}")
except Exception as e:
    fail("ID-4", repr(e))


print("\nID-5: [IDENTITY] header present in every render")
try:
    for name in ["eLo", "TestBot", "X"]:
        b = identity_block(EloSelfState(identity_name=name))
        if "[IDENTITY" not in b:
            fail("ID-5", f"[IDENTITY] header missing for name={name!r}")
            break
    else:
        ok("ID-5 — [IDENTITY] header present across all renders")
except Exception as e:
    fail("ID-5", repr(e))


print(f"\n{'='*40}")
print(f"Row 1 IDENTITY: {PASS} passed, {FAIL} failed")
print()
print("Row verified by this test:")
print("  1  IDENTITY — EloSelfState fields drive the rendered identity prompt")
if __name__ == "__main__":
    if FAIL:
        sys.exit(1)
