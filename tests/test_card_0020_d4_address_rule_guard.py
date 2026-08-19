"""tests/test_card_0020_d4_address_rule_guard.py — Card 0020 · D-4 acceptance.

WO-CANON-I baked the ADDRESS RULE into both `living_presence_spec.txt` and
`_PERSONA`. The 2026-08-19 live test still produced

    "I remember when David first started explaining his concept…"

— third-person, to David. This outbound guard converts every "David …" form
into a second-person address so the rule holds even when the LLM slips.

Run: python3 tests/test_card_0020_d4_address_rule_guard.py
"""
import sys, os
sys.path.insert(0, ".")

PASS = 0; FAIL = 0
def ok(n):      global PASS; PASS += 1; print(f"  ✅ {n}")
def fail(n, r): global FAIL; FAIL += 1; print(f"  ❌ {n}: {r}")


from runtime.address_rule_guard import (
    enforce_second_person_to_david,
    has_third_person_david,
)


# D-4.a — the live-test line becomes second-person address
try:
    live = (
        "I remember when David first started explaining his concept of a "
        "presence that could move between bodies."
    )
    out = enforce_second_person_to_david(live)
    assert "David" not in out, f"'David' survived guard: {out!r}"
    assert "you" in out.lower(), f"second-person address missing: {out!r}"
    ok("D-4.a: live-test third-person line rewritten to second-person")
except Exception as e:
    fail("D-4.a", e)


# D-4.b — verb forms are handled with correct agreement
try:
    cases = [
        ("David's tone is warm.",     "your"),
        ("David is here.",            "you are"),
        ("David has been busy.",      "you have been"),  # "David has" → "you have"
        ("David told me a story.",    "you told"),
        ("David wants a hand.",       "you want"),
        ("David said something.",     "you said"),
    ]
    for src, expected_frag in cases:
        out = enforce_second_person_to_david(src)
        assert "David" not in out, f"{src!r} → {out!r} (David survived)"
        assert expected_frag in out.lower(), f"{src!r} → {out!r} (missing {expected_frag!r})"
    ok("D-4.b: verb forms rewritten with correct second-person agreement")
except Exception as e:
    fail("D-4.b", e)


# D-4.c — no-name responses pass through unchanged
try:
    for src in ("Present. Watching.", "I am eLo.", ""):
        assert enforce_second_person_to_david(src) == src, \
            f"passthrough failed on {src!r}"
    ok("D-4.c: responses without 'David' are pass-through")
except Exception as e:
    fail("D-4.c", e)


# D-4.d — has_third_person_david predicate
try:
    assert has_third_person_david("David is here.")
    assert not has_third_person_david("You are here.")
    assert not has_third_person_david("")
    ok("D-4.d: has_third_person_david predicate correct")
except Exception as e:
    fail("D-4.d", e)


print()
print("=" * 52)
print(f"Card 0020 · D-4 address-rule guard  {PASS} passed  {FAIL} failed")
if FAIL:
    sys.exit(1)
