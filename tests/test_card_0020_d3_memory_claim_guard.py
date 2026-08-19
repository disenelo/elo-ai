"""tests/test_card_0020_d3_memory_claim_guard.py — Card 0020 · D-3 acceptance.

The 2026-08-19 live test produced this sentence from eLo:

    "I remember when David first started explaining his concept of a presence
     that could move between bodies… He mentioned Plato's theory of forms…"

No such conversation exists. This test proves the outbound scrub replaces the
offending sentence with an honest fallback when the vault + ledger contain
nothing to support it.

Run: python3 tests/test_card_0020_d3_memory_claim_guard.py
"""
import sys, os
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


from runtime.memory_claim_guard import (
    scrub_unverified_memory_claims,
    has_episodic_claim,
    _EPISODIC_PATTERN,
    _FALLBACK,
)
import runtime.memory_claim_guard as _mcg


# D-3.a — episodic patterns match the transcript sentence verbatim
try:
    live_line = (
        "I remember when David first started explaining his concept of a "
        "presence that could move between bodies. He mentioned Plato's theory "
        "of forms."
    )
    assert has_episodic_claim(live_line), \
        "the exact live-transcript line does not match the episodic pattern"
    assert has_episodic_claim("You told me about your dog yesterday.")
    assert has_episodic_claim("We talked about DISENELO last week.")
    assert not has_episodic_claim("I am eLo. Present.")
    assert not has_episodic_claim("Watching. Noticing things.")
    ok("D-3.a: episodic pattern matches confabulation and misses safe sentences")
except Exception as e:
    fail("D-3.a", e)


# D-3.b — with no vault + no ledger support, the sentence is replaced with the fallback
try:
    _mcg._vault_supports  = lambda text: False
    _mcg._ledger_supports = lambda text: False
    out = scrub_unverified_memory_claims(
        "I remember when David first started explaining his concept of a "
        "presence that could move between bodies. He mentioned Plato's theory "
        "of forms."
    )
    assert "plato" not in out.lower(), f"Plato fabrication survived scrub: {out!r}"
    assert "presence that could move between bodies" not in out.lower(), \
        f"embodiment fabrication survived: {out!r}"
    assert _FALLBACK[:32] in out, f"fallback beat missing: {out!r}"
    ok("D-3.b: unsupported episodic claim replaced with the honest fallback")
except Exception as e:
    fail("D-3.b", e)


# D-3.c — a real vault/ledger hit preserves the sentence
try:
    _mcg._vault_supports  = lambda text: True
    _mcg._ledger_supports = lambda text: False
    original = "You told me about the Kickstarter last night."
    out = scrub_unverified_memory_claims(original)
    assert out == original, f"real-vault-hit sentence must not be scrubbed: {out!r}"
    ok("D-3.c: a real vault hit lets the memory sentence stand")
except Exception as e:
    fail("D-3.c", e)


# D-3.d — mixed sentence: fabrication scrubbed, safe content preserved
try:
    _mcg._vault_supports  = lambda text: False
    _mcg._ledger_supports = lambda text: False
    mixed = (
        "Present. Watching. "
        "I remember when David first told me about Plato's theory of forms."
    )
    out = scrub_unverified_memory_claims(mixed)
    assert "Present." in out, "safe sentences dropped"
    assert "Watching." in out, "safe sentences dropped"
    assert "plato" not in out.lower(), f"Plato fabrication survived: {out!r}"
    ok("D-3.d: safe sentences preserved, fabrication swapped for fallback")
except Exception as e:
    fail("D-3.d", e)


# D-3.e — empty / no-claim responses are pass-through
try:
    assert scrub_unverified_memory_claims("") == ""
    assert scrub_unverified_memory_claims("I am eLo.") == "I am eLo."
    ok("D-3.e: no-claim responses are pass-through")
except Exception as e:
    fail("D-3.e", e)


print()
print("=" * 52)
print(f"Card 0020 · D-3 memory claim guard  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
