"""
runtime/router/pipeline.py — Unified Routing Pipeline

NOTE: pipeline.run() is superseded by runtime/spine/spine.py.
The spine imports the individual modules below directly and owns orchestration.
Only push_turn() from this file remains in active use (server.py:997).
Do not call pipeline.run() — it is not part of the main request path.
See: engineering/work_packages/WP_B_IMPLEMENTATION_PLAN.md § GAP 3

Entry point (SUPERSEDED): run(raw) → enriched routing decision.
Active export: push_turn() — session continuity push, called from server.py.

Stages (orchestrated by spine.py now, not this file):
    01  meaning_engine   — normalise + detect social
    02  typo_engine      — repair typos
    03  conversation_matrix — context + continuity
    04  intent_engine    — classify intent
    05  agent_router     — select agents (max 2)
    06  execution_gate   — gate system actions
    07  confidence_engine — score + decide
    10  learning_buffer  — record outcome for diagnostics

Architecture authority: 01_one_brain.md, 14_spine_runtime.md
"""
from __future__ import annotations
from typing import Optional

from runtime.router.meaning_engine      import normalise
from runtime.router.typo_engine         import repair
from runtime.router.conversation_matrix import analyse, push as _push
from runtime.router.intent_engine       import detect as detect_intent
from runtime.router.agent_router        import route as route_agents, is_conversation_only
from runtime.router.learning_buffer     import record as _record, record_typo as _record_typo
from runtime.router.execution_gate      import (
    gate, has_pending, execute_pending, cancel_pending,
    should_execute, should_cancel, get_pending_desc,
)
from runtime.router.confidence_engine   import from_pipeline


def run(raw: str, session: dict | None = None) -> dict:
    """
    Full pipeline run. Returns a routing decision dict.

    Return shape:
    {
        original        — unchanged input
        cleaned         — normalised
        repaired        — typo-repaired
        social          — "" | "greeting" | "affirmation" | "farewell"
        intent          — classified intent string
        chain           — [] or [intent1, intent2] for multi-agent
        agents          — [(agent_name, query), ...] max 2
        confidence      — 0.0–1.0
        gate_action     — "proceed" | "confirm" | "ask"
        gate_message    — message for eLo to optionally speak
        system_pending  — True if a system action is waiting for confirm
        system_desc     — description of pending system action
        context         — {hidden_goal, references, continuity, ...}
        conversation_only — True if no agent needed
    }
    """

    # ── Gate: pending system confirmation check ───────────────────────────────
    if has_pending():
        if should_execute(raw):
            result = execute_pending()
            return {
                "original": raw, "cleaned": raw, "repaired": raw,
                "social": "", "intent": "system_confirm",
                "chain": [], "agents": [],
                "confidence": 1.0, "gate_action": "proceed",
                "gate_message": result,
                "system_pending": False, "system_desc": "",
                "context": {}, "conversation_only": False,
                "system_result": result,
            }
        # Not a confirmation — clear the stale pending action so it doesn't bleed
        # into subsequent turns and produce "[SYSTEM CONFIRM: ...]" injections.
        cancel_pending()

    # ── Stage 01: Normalise ───────────────────────────────────────────────────
    meaning = normalise(raw)
    cleaned = meaning["cleaned"]
    social  = meaning["social"]

    # ── Stage 02: Typo repair ─────────────────────────────────────────────────
    typo = repair(cleaned)
    repaired = typo["interpretation"] if typo["confidence"] >= 0.80 else cleaned

    # ── Stage 03: Conversational matrix ──────────────────────────────────────
    context = analyse(repaired, session=session)

    # ── Stage 04: Intent ──────────────────────────────────────────────────────
    intent_result = detect_intent(repaired, session)
    intent = intent_result["intent"]
    chain  = intent_result.get("chain", [])

    # ── Stage 05: Agent routing ───────────────────────────────────────────────
    agents = route_agents(intent, repaired, chain=chain if chain else None)

    # ── Stage 06: Execution gate for system actions ───────────────────────────
    system_pending  = False
    system_desc     = ""
    gate_override   = {}

    if intent in ("system", "file_ops") and agents:
        agent_name, query = agents[0]
        if agent_name == "system":
            try:
                from tools.system_agent import detect as sys_detect
                detected = sys_detect(query)
                if detected:
                    action, arg = detected
                    gate_result = gate(action, arg)
                    if not gate_result["execute"]:
                        system_pending = True
                        system_desc    = gate_result["confirmation"]
                        agents = []   # don't execute yet
            except Exception:
                pass

    # ── Stage 07: Confidence ──────────────────────────────────────────────────
    conf = from_pipeline(meaning, typo, intent_result)

    # ── Stage 10: Learning buffer ─────────────────────────────────────────────
    outcome = (
        "confirmed" if system_pending else
        "no_agent"  if not agents      else
        "success"
    )
    agent_names = [a[0] for a in agents]
    _record(raw, intent, agent_names, conf["confidence"], outcome, typo_fixed=typo.get("changed", False))
    if typo.get("changed"):
        _record_typo(cleaned, repaired, typo.get("confidence", 1.0))

    return {
        "original":         raw,
        "cleaned":          cleaned,
        "repaired":         repaired,
        "social":           social,
        "intent":           intent,
        "chain":            chain,
        "agents":           agents,
        "confidence":       conf["confidence"],
        "gate_action":      conf["action"],
        "gate_message":     conf.get("message", ""),
        "system_pending":   system_pending,
        "system_desc":      system_desc,
        "context":          context,
        "conversation_only": is_conversation_only(intent) and not agents,
    }


def push_turn(user_input: str, elo_response: str = "") -> None:
    """Call after each turn to maintain session continuity."""
    _push(user_input, elo_response)
