"""
tests/test_vault_write_routing.py — WO-VAULT-WRITE-ROUTING: vault_write intent detection

Verifies that David's memory-store phrasings route to vault_write intent.
Root issue: "remember this: X" returned no recorded response.
"""
from __future__ import annotations

import pytest
from runtime.router.intent_engine import detect


@pytest.mark.parametrize("phrase", [
    "remember this: I like coffee",
    "remember this",
    "remember that",
    "don't forget my birthday",
    "dont forget this",
    "save this for later",
    "save that",
    "write that down",
    "write this down",
    "keep that",
    "keep this",
    "note this down",
    "note that",
])
def test_vault_write_phrases_route_to_vault_write(phrase):
    result = detect(phrase)
    assert result["intent"] == "vault_write", (
        f"expected vault_write for {phrase!r}, got {result['intent']!r}"
    )
