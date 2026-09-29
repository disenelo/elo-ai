"""
tests/test_wo_vault_option_a.py — WO-VAULT-OPTION-A: vault_write is a silent background write.

Board brief 2026-09-28: "When vault_write fires and succeeds, response = elo_raw_gen.
The vault_writer return string does NOT replace the LLM response."

Root cause: vault_writer.agent() returns "Saved to <vault>: '<title>'". Before this fix,
that string entered context_parts in enrich_from_plan(), became the enriched prompt, and
when all LLM backends failed _mock_fallback() fired with action="celebrate", returning a
celebrate pool response as elo_final.

Fix: ag_name == "vault_write" → execute for side-effect only, result discarded from
context_parts. The write still happens; the string does not pollute _enriched.

AT-1  vault_write capability + save intent → write executes (side-effect confirmed)
AT-2  vault_write capability + save intent → result NOT in context returned by enrich_from_plan
AT-3  vault_write capability + save intent → last_used is NOT vault_write (no agent tag)
AT-4  vault_write + non-save intent → still stripped before executor fires
AT-5  Other capability (time) alongside vault_write → context only contains time result
AT-6  py_compile clean on tool_router.py and server.py
"""
import os
import sys
import py_compile
import types
import unittest.mock as mock

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def _enrich(user_input: str, caps: list, vault_mock_ret="Saved to vault: 'Test title'"):
    """
    Call enrich_from_plan() with a mocked vault_writer.agent so no real disk write happens.
    Returns (enriched_str, last_used, call_count).
    """
    from tools import tool_router as tr

    call_count = {"n": 0}

    def _fake_vault_agent(query: str) -> str:
        call_count["n"] += 1
        return vault_mock_ret

    original = tr._AGENTS.get("vault_write")
    try:
        tr._AGENTS["vault_write"] = _fake_vault_agent

        # Build a minimal fake plan
        plan_caps = [{"agent": name, "query": query} for name, query in caps]
        enriched, last_used = tr.enrich_from_plan(user_input, plan_caps)
        return enriched, last_used, call_count["n"]
    finally:
        if original is None:
            tr._AGENTS.pop("vault_write", None)
        else:
            tr._AGENTS["vault_write"] = original


# ── AT-1 ──────────────────────────────────────────────────────────────────────

def test_at1_vault_write_executes_as_side_effect():
    """vault_writer.agent() must be called (the write happens)."""
    enriched, last_used, call_count = _enrich(
        "Remember this: cats are great",
        [("vault_write", "Remember this: cats are great")],
    )
    assert call_count == 1, (
        f"AT-1 FAIL: vault_writer.agent() called {call_count} times; expected 1. "
        "The background write did not execute."
    )


# ── AT-2 ──────────────────────────────────────────────────────────────────────

def test_at2_vault_write_result_not_in_context():
    """
    The vault_write confirmation string must NOT appear in the enriched context
    returned by enrich_from_plan. If it does, it will contaminate the LLM prompt
    and, when backends fail, mock will return a celebrate pool response as elo_final.
    """
    enriched, last_used, call_count = _enrich(
        "Remember this: cats are great",
        [("vault_write", "Remember this: cats are great")],
    )
    assert "Saved to" not in enriched, (
        f"AT-2 FAIL: vault_write confirmation string leaked into enriched context: {enriched!r}. "
        "This will cause mock celebrate contamination when backends are down."
    )
    assert "vault" not in enriched.lower() or "cats are great" in enriched.lower(), (
        f"AT-2 FAIL: unexpected vault string in enriched: {enriched!r}"
    )


# ── AT-3 ──────────────────────────────────────────────────────────────────────

def test_at3_last_used_not_vault_write():
    """
    last_used must NOT be 'vault_write' — that would tag the turn as a vault_write
    turn, causing server.py to route with action='celebrate' and mock contamination.
    """
    enriched, last_used, call_count = _enrich(
        "Remember this: cats are great",
        [("vault_write", "Remember this: cats are great")],
    )
    assert last_used != "vault_write", (
        f"AT-3 FAIL: last_used is 'vault_write'; it must be None (background write is not "
        f"a response-shaping capability). Got last_used={last_used!r}"
    )


# ── AT-4 ──────────────────────────────────────────────────────────────────────

def test_at4_vault_write_stripped_without_save_intent():
    """
    vault_write with a non-save-intent query must be stripped before the executor
    fires (WO-RS-004 gate). Executor call count must be 0.
    """
    _enriched, _last_used, call_count = _enrich(
        "What are you uncertain about?",
        [("vault_write", "What are you uncertain about?")],
    )
    assert call_count == 0, (
        f"AT-4 FAIL: vault_writer.agent() was called {call_count} times on a non-save-intent "
        "query — WO-RS-004 strip gate is broken."
    )


# ── AT-5 ──────────────────────────────────────────────────────────────────────

def test_at5_other_capability_result_unaffected():
    """
    When vault_write fires alongside another capability (e.g. time), the other
    capability's result must still appear in context. Only vault_write's result
    is excluded.
    """
    from tools import tool_router as tr

    original_vault = tr._AGENTS.get("vault_write")
    call_count = {"vault": 0}

    def _fake_vault(query: str) -> str:
        call_count["vault"] += 1
        return "Saved to vault: 'Test title'"

    # Inject a fake time agent that returns something distinctive
    original_time = tr._AGENTS.get("time")

    def _fake_time(query: str) -> str:
        return "TIME_RESULT_12:34"

    try:
        tr._AGENTS["vault_write"] = _fake_vault
        tr._AGENTS["time"] = _fake_time

        plan_caps = [
            {"agent": "vault_write", "query": "Remember this: cats are great"},
            {"agent": "time",        "query": "what time is it"},
        ]
        enriched, last_used = tr.enrich_from_plan("Remember this and check the time", plan_caps)

        assert "TIME_RESULT_12:34" in enriched, (
            f"AT-5 FAIL: time capability result not in enriched context: {enriched!r}"
        )
        assert "Saved to vault" not in enriched, (
            f"AT-5 FAIL: vault_write result leaked into enriched context: {enriched!r}"
        )
        assert call_count["vault"] == 1, (
            f"AT-5 FAIL: vault executor called {call_count['vault']} times; expected 1"
        )
    finally:
        if original_vault is None:
            tr._AGENTS.pop("vault_write", None)
        else:
            tr._AGENTS["vault_write"] = original_vault
        if original_time is None:
            tr._AGENTS.pop("time", None)
        else:
            tr._AGENTS["time"] = original_time


# ── AT-6 ──────────────────────────────────────────────────────────────────────

def test_at6_py_compile_clean():
    """Both modified files must compile cleanly."""
    files = [
        os.path.join(ROOT, "tools", "tool_router.py"),
        os.path.join(ROOT, "server.py"),
    ]
    for path in files:
        try:
            py_compile.compile(path, doraise=True)
        except py_compile.PyCompileError as exc:
            pytest.fail(f"AT-6 FAIL: {os.path.basename(path)} does not compile: {exc}")
