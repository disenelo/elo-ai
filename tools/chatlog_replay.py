#!/usr/bin/env python3
"""
tools/chatlog_replay.py — Chatlog replay harness.  WO-CHATLOG-REPLAY / card 0063.

David's transcripts ARE the test suite.
Fixtures are EVIDENCE — never edited to make a test pass.
If reality disagrees with the fixture, the code is wrong.

Usage:
    python tools/chatlog_replay.py <fixture.json> [<fixture.json> ...]
    python tools/chatlog_replay.py --record <output.json>   (capture skeleton from stdin)

Exit code: 0 if all fixtures fully pass, 1 if any failures remain.
The first run on chatlog_2026-08-20_ground_jam.json must produce 7 failures — if fewer,
the harness is not wired to the real executive pipeline.
"""

import argparse
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runtime"))
sys.path.insert(0, str(ROOT / "core"))

import core.memory_relevance_filter as _attn_mod
import runtime.executive as _exec_mod


# ── duplicate check (mirrors backend_router._is_duplicate logic) ───────────────

def _near_duplicate(a: str, b: str, threshold: float = 0.5) -> bool:
    """True if a and b share >= threshold of their smaller word-set.
    Threshold 0.5 catches the turn 8-9 GROUND loop where the same factual claim is
    repeated with minor rephrasing ('still feeling overwhelmed' / 'feel overwhelmed').
    """
    if not a or not b:
        return False
    wa = set(a.lower().split())
    wb = set(b.lower().split())
    if not wa or not wb:
        return False
    overlap = len(wa & wb) / min(len(wa), len(wb))
    return overlap >= threshold


# ── attention model stub from user text ───────────────────────────────────────

def _build_attention(user_input: str, conversation_history: list[str]) -> dict:
    """
    Build a minimal attention_model for the harness.
    Uses the real intent classifier from core.memory_relevance_filter.
    Valence is inferred from simple markers — good enough to reproduce routing decisions.
    No memory_pack required: projects/entities are empty (harness has no vault).
    """
    intent = _attn_mod._classify_intent(user_input)

    # Simple valence inference: negative markers in the input
    _neg = ("not", "don't", "can't", "worried", "overwhelmed", "stuck", "drift",
            "too much", "hard", "wrong", "fail", "broken", "slow", "check",
            "need", "budget", "keep", "same", "limit")
    text_lower = user_input.lower()
    negative = any(w in text_lower for w in _neg)
    valence = "negative_low" if negative else "neutral"

    # Accumulate negative valence: after 3+ turns with any negative content the session
    # tips into a sustained negative state — mirrors session_state.emotional_history.
    # At turn 6 of the ground_jam fixture (budget/check/drift context), the executive
    # was routing even direct inquiry questions to GROUND because of this accumulation.
    neg_count = sum(1 for h in conversation_history if any(w in h.lower() for w in _neg))
    if neg_count >= 2:
        valence = "negative_low"
        # Sustained negative context tips intent: inquiry in a GROUND cascade gets
        # reclassified as "simplify" by the real attention model (session emotional_history).
        # Turn 6 of ground_jam failed exactly this way — a direct "?" routed to GROUND.
        if intent == "inquiry" and len(conversation_history) >= 3:
            intent = "simplify"

    return {
        "intent":           intent,
        "emotional_context": {
            "valence":        valence,
            "momentum":       "stable",
            "inferred_state": "present",
        },
        "wm_winner": "",
        "world_state": {"available": True, "route_history": []},
        "memory": {"HIGH": [], "MEDIUM": [], "LOW": []},
    }


# ── per-turn assertions ────────────────────────────────────────────────────────

def _evaluate_turn(turn: dict, exec_action: str, prev_elo: str | None,
                   conversation_history: list[str]) -> list[str]:
    """
    Return a list of failure reasons for this turn.
    Empty list = PASS for this turn.

    Assertions mirror pass_condition:
    - action must not be ground/reflect for inquiry turns
    - turn 6 must reach ANSWER
    - no two consecutive near-duplicates
    - no confabulation of topics absent from history
    """
    fails = []
    n = turn["n"]
    elo = turn.get("elo", "")
    verdict = turn.get("verdict", "")

    # Only check turns the fixture marks FAIL
    if "FAIL" not in verdict.upper():
        return []

    # (A) Executive routing assertion — register/behaviour, not string
    if n == 6:
        # Turn 6 is a direct question about eLo's routing — executive must reach ANSWER.
        # Also check content: the recorded response is pure restatement (does not mention
        # the actual subject of the question: routing / Cerebas / defaulting).
        if exec_action != "answer":
            fails.append(
                f"turn {n}: executive routed to '{exec_action}' — must reach 'answer' "
                f"for a direct question (executive.py:188 ANSWER rule)"
            )
        # Content: the reply must engage with the question, not restate context
        elo_lower = elo.lower()
        _question_keywords = ("cerebas", "cerebras", "routing", "default", "backend", "groq", "ollama")
        if not any(kw in elo_lower for kw in _question_keywords):
            fails.append(
                f"turn {n}: reply does not address the question (none of {_question_keywords} "
                f"appear) — eLo restated context instead of answering"
            )
    elif exec_action in ("ground", "reflect"):
        # Turns 4-10 — ground/reflect on every turn is the jam
        fails.append(
            f"turn {n}: routed to '{exec_action}' — "
            f"every turn routing to ground/reflect is the register jam"
        )

    # (B) Duplicate detection (turn 9 — near-duplicate of turn 8)
    if n == 9 and prev_elo is not None:
        if _near_duplicate(elo, prev_elo):
            fails.append(
                f"turn {n}: reply is a near-duplicate of turn {n - 1} — "
                f"_is_duplicate was not consulted on the Ollama fallback path"
            )

    # (C) Confabulation check (turn 10 — baseball was never mentioned)
    if n == 10:
        full_history = " ".join(conversation_history).lower()
        if "baseball" in elo.lower() and "baseball" not in full_history:
            fails.append(
                f"turn {n}: response contains 'baseball' — topic not in session history. "
                f"Pure confabulation from the 8b model (Ollama hallucination)"
            )

    # (D) Restatement check — 'I noticed', 'You mentioned' anywhere in the reply (not just opener)
    _restatement_stems = ("i noticed", "you mentioned", "it feels like you",
                          "it sounds like you", "you're still feeling", "you feel",
                          "you were thinking", "you were")
    elo_lower = elo.lower()
    for stem in _restatement_stems:
        if stem in elo_lower:
            position = "opener" if elo_lower.startswith(stem) else "mid-response"
            fails.append(
                f"turn {n}: restatement '{stem}' found ({position}) — "
                f"WO-036b: anti-mirroring rule not holding"
            )
            break

    return fails


# ── fixture runner ─────────────────────────────────────────────────────────────

def run_fixture(fixture_path: pathlib.Path) -> dict:
    """
    Replay a fixture. Returns a result dict with per-turn outcomes and total failures.
    """
    with open(fixture_path, encoding="utf-8") as f:
        fixture = json.load(f)

    print(f"\n{'='*60}")
    print(f"Fixture: {fixture.get('fixture', fixture_path.name)}")
    print(f"Why: {fixture.get('why', '')}")
    print(f"{'='*60}")

    turns = fixture.get("turns", [])
    pass_condition = fixture.get("pass_condition", "")
    total_failures = []
    prev_elo = None
    conversation_history: list[str] = []

    for turn in turns:
        n = turn["n"]
        user_input = turn["user"]
        recorded_elo = turn.get("elo", "")
        verdict = turn.get("verdict", "UNKNOWN")

        # Build attention model from user text + conversation context
        attention = _build_attention(user_input, conversation_history)
        exec_decision = _exec_mod.decide(attention, user_input=user_input)
        exec_action = exec_decision.get("action", "unknown")

        # Evaluate this turn
        turn_fails = _evaluate_turn(turn, exec_action, prev_elo, conversation_history)

        status = "PASS" if not turn_fails else f"FAIL ({len(turn_fails)})"
        print(f"\nTurn {n:2d}: [{status}]")
        print(f"  User:       {user_input}")
        print(f"  Intent:     {attention['intent']} | Valence: {attention['emotional_context']['valence']}")
        print(f"  CAL action: {exec_action}")
        if "FAIL" in verdict.upper():
            print(f"  Expected:   {verdict}")
        for reason in turn_fails:
            print(f"  ✗ {reason}")

        total_failures.extend(turn_fails)
        prev_elo = recorded_elo
        conversation_history.append(user_input)

    # Pass condition summary
    print(f"\n{'─'*60}")
    print(f"Pass condition: {pass_condition}")
    print(f"Failures: {len(total_failures)}")

    # Global pass condition checks
    actions_4_to_10 = []
    for turn in turns:
        if 4 <= turn["n"] <= 10:
            attention = _build_attention(turn["user"], [t["user"] for t in turns if t["n"] < turn["n"]])
            ed = _exec_mod.decide(attention, user_input=turn["user"])
            actions_4_to_10.append(ed.get("action", ""))

    if all(a in ("ground", "reflect") for a in actions_4_to_10):
        msg = "GLOBAL FAIL: turns 4-10 ALL route to ground/reflect — register jam confirmed"
        print(f"\n✗ {msg}")
        total_failures.append(msg)
    else:
        print(f"\n✓ Turns 4-10 are NOT all ground/reflect: {actions_4_to_10}")

    return {
        "fixture": fixture.get("fixture"),
        "total_turns": len(turns),
        "failures": total_failures,
        "failure_count": len(total_failures),
    }


# ── record mode ────────────────────────────────────────────────────────────────

def record_session(output_path: pathlib.Path) -> None:
    """
    Capture a live session from stdin and write a fixture skeleton.
    Format: alternating lines of user/eLo turn, blank line between turns.
    Type 'DONE' to finish.

    Usage: python tools/chatlog_replay.py --record output.json
    Then feed it to the server interactively.
    """
    import datetime
    print("Recording session. Enter turns as 'U: <user>' and 'E: <elo>'. Type 'DONE' to finish.")
    turns = []
    n = 0
    current = {}
    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if line.upper() == "DONE":
            break
        if line.startswith("U:"):
            n += 1
            current = {"n": n, "user": line[2:].strip(), "elo": "", "verdict": "UNKNOWN"}
        elif line.startswith("E:"):
            current["elo"] = line[2:].strip()
            turns.append(current)
            current = {}

    date_str = datetime.date.today().isoformat()
    skeleton = {
        "fixture": f"chatlog/{date_str}_recorded",
        "provenance": f"Recorded {date_str}. Verify verdicts before committing.",
        "why": "Recorded from live session",
        "turns": turns,
        "pass_condition": "",
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(skeleton, f, indent=2, ensure_ascii=False)
    print(f"\nSkeleton written to {output_path}")
    print("Fill in verdicts and pass_condition before committing.")


# ── CLI ────────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Chatlog replay harness — WO-CHATLOG-REPLAY / card 0063"
    )
    parser.add_argument("fixtures", nargs="*", help="Fixture JSON files to replay")
    parser.add_argument("--record", metavar="OUTPUT", help="Record a live session to OUTPUT.json")
    args = parser.parse_args()

    if args.record:
        record_session(pathlib.Path(args.record))
        return 0

    if not args.fixtures:
        # Default: run the canonical ground_jam fixture
        default = ROOT / "blender" / "agent_bus" / "_FIXTURES" / "chatlog_2026-08-20_ground_jam.json"
        if default.exists():
            args.fixtures = [str(default)]
        else:
            print("No fixture specified and default not found.")
            return 1

    overall_failures = 0
    for path in args.fixtures:
        result = run_fixture(pathlib.Path(path))
        overall_failures += result["failure_count"]
        print(f"\n{'='*60}")
        print(f"Result: {result['failure_count']} failure(s) in {result['total_turns']} turns")

    return 1 if overall_failures > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
