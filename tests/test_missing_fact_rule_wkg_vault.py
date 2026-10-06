"""
tests/test_missing_fact_rule_wkg_vault.py — MISSING-FACT rule WKG/VAULT extension

Acceptance criteria:
  MFR-1: backend_router MISSING-FACT rule checks [WORLD KNOWLEDGE]
  MFR-2: backend_router MISSING-FACT rule checks [VAULT]
  MFR-3: EXCEPTION clause includes [WORLD KNOWLEDGE]
  MFR-4: EXCEPTION clause includes [VAULT]
  MFR-5: IMPORTANT note mentions [WORLD KNOWLEDGE] as a section to check
  MFR-6: original [RELATIONSHIP & PERSPECTIVE] check is preserved
  MFR-7: original [DURABLE FACTS] check is preserved
"""
import pathlib

_ROUTER_SRC = pathlib.Path("runtime/backend_router.py").read_text()


def test_mfr_1_world_knowledge_in_check():
    """MFR-1: NOT in [WORLD KNOWLEDGE] is part of the missing-fact condition"""
    assert "[WORLD KNOWLEDGE]" in _ROUTER_SRC
    # The check should appear in the NOT-in list (negative gate)
    assert "NOT in [WORLD KNOWLEDGE]" in _ROUTER_SRC


def test_mfr_2_vault_in_check():
    """MFR-2: NOT in [VAULT] is part of the missing-fact condition"""
    assert "NOT in [VAULT]" in _ROUTER_SRC


def test_mfr_3_exception_includes_world_knowledge():
    """MFR-3: EXCEPTION clause covers [WORLD KNOWLEDGE]"""
    # Find the EXCEPTION line and confirm [WORLD KNOWLEDGE] is nearby
    idx = _ROUTER_SRC.find("MISSING-FACT RULE does NOT apply")
    assert idx != -1, "EXCEPTION clause not found"
    window = _ROUTER_SRC[max(0, idx - 300):idx + 100]
    assert "[WORLD KNOWLEDGE]" in window, "EXCEPTION clause does not mention [WORLD KNOWLEDGE]"


def test_mfr_4_exception_includes_vault():
    """MFR-4: EXCEPTION clause covers [VAULT]"""
    idx = _ROUTER_SRC.find("MISSING-FACT RULE does NOT apply")
    assert idx != -1
    window = _ROUTER_SRC[max(0, idx - 300):idx + 100]
    assert "[VAULT]" in window, "EXCEPTION clause does not mention [VAULT]"


def test_mfr_5_important_note_mentions_world_knowledge():
    """MFR-5: IMPORTANT note reminds LLM to check [WORLD KNOWLEDGE] before refusing"""
    idx = _ROUTER_SRC.find("ALWAYS check")
    assert idx != -1, "ALWAYS check instruction not found in backend_router"
    window = _ROUTER_SRC[idx:idx + 250]
    assert "[WORLD KNOWLEDGE]" in window


def test_mfr_6_relationship_perspective_preserved():
    """MFR-6: [RELATIONSHIP & PERSPECTIVE] is still in the not-in condition"""
    assert "NOT in [RELATIONSHIP & PERSPECTIVE]" in _ROUTER_SRC


def test_mfr_7_durable_facts_preserved():
    """MFR-7: [DURABLE FACTS] is still in the not-in condition"""
    assert "NOT in [DURABLE FACTS]" in _ROUTER_SRC
