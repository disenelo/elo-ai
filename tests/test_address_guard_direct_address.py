"""tests/test_address_guard_direct_address.py — B3-2026-10-10 defect regression.

address_rule_guard D-4 was rewriting DIRECT ADDRESS uses of "David" to "you":
  "I'm here, David." → "I'm here, you."
  "Hello David, how are you?" → "Hello you, how are you?"

Fix: mask direct-address spans before substitution, restore after.
Run: python3 -m pytest tests/test_address_guard_direct_address.py -v
"""
import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from runtime.address_rule_guard import enforce_second_person_to_david as guard


# ── AT-1: End-of-clause vocative preserved ───────────────────────────────────
def test_at1_end_clause_vocative_preserved():
    assert guard("I am here, David.") == "I am here, David."


# ── AT-2: Greeting + comma preserved ─────────────────────────────────────────
def test_at2_greeting_comma_preserved():
    assert guard("Hello David, how are you?") == "Hello David, how are you?"


# ── AT-3: Hey-form preserved ──────────────────────────────────────────────────
def test_at3_hey_form_preserved():
    assert guard("Hey David what you saying?") == "Hey David what you saying?"


# ── AT-4: Start-of-clause vocative preserved ─────────────────────────────────
def test_at4_start_clause_vocative_preserved():
    assert guard("David, I think we should go.") == "David, I think we should go."


# ── AT-5: Exclamation vocative preserved ─────────────────────────────────────
def test_at5_exclamation_vocative_preserved():
    assert guard("I am right here, David!") == "I am right here, David!"


# ── AT-6: Period-ended vocative preserved ────────────────────────────────────
def test_at6_period_vocative_preserved():
    assert guard("Great to see you, David.") == "Great to see you, David."


# ── AT-7: Third-person subject still rewritten ───────────────────────────────
def test_at7_third_person_subject_rewritten():
    assert guard("I remember when David first started explaining.") == \
        "I remember when you first started explaining."


# ── AT-8: Possessive still rewritten ─────────────────────────────────────────
def test_at8_possessive_rewritten():
    assert guard("David's work is impressive.") == "your work is impressive."


# ── AT-9: Mixed sentence — third-person rewritten, vocative preserved ─────────
def test_at9_mixed_third_person_and_vocative():
    text = "I know David mentioned it, but I'm here, David."
    result = guard(text)
    assert "you mentioned" in result, f"Third-person not rewritten: {result!r}"
    assert "I'm here, David." in result, f"Vocative mangled: {result!r}"


# ── AT-10: No David at all — no-op ───────────────────────────────────────────
def test_at10_no_david_noop():
    text = "How are you doing today?"
    assert guard(text) == text


# ── AT-11: "I'm here, David" (prior live bug) ────────────────────────────────
def test_at11_live_bug_ive_here_david():
    assert guard("I'm here, David.") == "I'm here, David."


# ── AT-12: Greeting-only form (no comma after David) ─────────────────────────
def test_at12_greeting_hi_david():
    assert guard("Hi David how's it going?") == "Hi David how's it going?"
