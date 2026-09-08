"""
runtime/response_gate.py — WO-RESPONSE-GATE: 10-point eLo response quality gate.

Runtime cognitive evaluation layer. Runs after faculty output, before response emission.
In v1, gate is a quality layer: flags and revises where possible; never hard-blocks.

Checks:
  1  identity          — sounds like eLo, not generic assistant
  2  personality       — matches active personality register
  3  faculty_leakage   — internal reasoning not exposed
  4  relevance         — responds to what was said [stub v1]
  5  action_truth      — doesn't claim actions not taken [stub v1]
  6  authority         — no false capability/memory claims
  7  register          — language register matches CCM output [stub v1]
  8  length            — no padding or over-explanation
  9  reflection_default — participates, doesn't describe
  10 rest              — simplest direct expression

Source: BOARD COMMAND — eLo Response Authority §6; SOURCE_ALIGNMENT_REGISTER_2026-08-30 CF-03.
"""
from __future__ import annotations

import dataclasses
import json
import logging
import os
import time
from typing import Optional

_log = logging.getLogger(__name__)

_GATE_LOG = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "gate_log.jsonl"
)

# ── Generic assistant phrasing — check 1 (identity) ──────────────────────────
_GENERIC_PHRASES = [
    "as an ai", "as an ai language model", "as an ai assistant",
    "certainly!", "certainly,", "certainly.", "of course!",
    "of course,", "of course.", "absolutely!", "absolutely,",
    "great question", "that's a great question", "that is a great question",
    "i'm just an ai", "i am just an ai", "i don't have feelings",
    "i do not have feelings", "i'm not able to", "i am not able to",
    "as a language model",
]

# ── Reflection-as-default phrasing — check 9 ─────────────────────────────────
_REFLECTION_PHRASES = [
    "i notice you're asking", "i notice you are asking",
    "i can see that you", "i see that you're",
    "it seems like you", "it appears that you",
    "you seem to be", "you appear to be asking",
    "i'm detecting", "i am detecting",
    "i notice that you", "i observe that",
]

# ── False authority / capability claims — check 6 ────────────────────────────
_FALSE_AUTHORITY_PHRASES = [
    "i can access the internet", "i can browse", "i can search the web",
    "i can access your files", "i can control your",
    "i remember everything we've ever", "i remember everything we have ever",
    "i have a perfect memory", "i have unlimited",
]

# ── Padding / over-explanation — check 8 ─────────────────────────────────────
_PADDING_PHRASES = [
    "in conclusion,", "to summarize,", "to summarise,",
    "i hope that helps!", "i hope this helps!", "i hope this answers",
    "please let me know if you have any other questions",
    "let me know if there's anything else i can help",
    "feel free to ask if you need",
    "is there anything else you'd like", "is there anything else you would like",
]


@dataclasses.dataclass
class GateResult:
    passed:           bool
    revised_response: Optional[str]
    flags:            list


def _strip_lower(text: str) -> str:
    return text.lower().strip()


def _check_identity(response: str) -> tuple[bool, str, list]:
    """Check 1: Does this sound like eLo, not a generic assistant?"""
    rl = _strip_lower(response)
    triggered = [p for p in _GENERIC_PHRASES if p in rl]
    if not triggered:
        return True, response, []

    revised = response
    for phrase in triggered:
        # Remove the offending phrase and its sentence fragment (simple approach)
        import re as _re
        pattern = _re.compile(_re.escape(phrase), _re.IGNORECASE)
        revised = pattern.sub("", revised).strip()

    # Collapse excess whitespace
    import re as _re
    revised = _re.sub(r" {2,}", " ", revised).strip(" ,.")
    if not revised:
        revised = None  # full replacement needed — flag only

    return False, revised or response, [f"identity:generic_phrase:{t}" for t in triggered[:2]]


def _check_personality(response: str, cognitive_state=None) -> tuple[bool, str, list]:
    """Check 2: Matches active personality register. v1: basic warmth/brevity signal."""
    # In v1: if response is very long (> 400 chars), flag for length mismatch.
    # Full personality vector integration is a future gate — this is the anchor.
    if len(response) > 400:
        return False, response, ["personality:response_exceeds_warmth_register"]
    return True, response, []


def _check_faculty_leakage(response: str) -> tuple[bool, str, list]:
    """Check 3: Internal faculty reasoning not exposed to David."""
    _LEAKAGE = [
        "faculty", "cognitive_state", "executive", "attention_model",
        "world_delta", "significance_score", "spine.", "llm_plan",
        "system prompt", "backend_router", "memory_faculty",
    ]
    rl = _strip_lower(response)
    triggered = [t for t in _LEAKAGE if t in rl]
    if not triggered:
        return True, response, []
    return False, response, [f"faculty_leakage:{t}" for t in triggered[:3]]


def _check_relevance(response: str, cognitive_state=None) -> tuple[bool, str, list]:
    """Check 4: Responds to what David actually said. Stub v1."""
    _log.debug("response_gate: check 4 (relevance) — not yet evaluated in v1")
    return True, response, ["relevance:stub_v1_not_evaluated"]


def _check_action_truth(response: str, cognitive_state=None) -> tuple[bool, str, list]:
    """Check 5: Doesn't claim actions not taken. Stub v1."""
    _log.debug("response_gate: check 5 (action_truth) — not yet evaluated in v1")
    return True, response, ["action_truth:stub_v1_not_evaluated"]


def _check_authority(response: str) -> tuple[bool, str, list]:
    """Check 6: No false capability or memory claims."""
    rl = _strip_lower(response)
    triggered = [p for p in _FALSE_AUTHORITY_PHRASES if p in rl]
    if not triggered:
        return True, response, []
    return False, response, [f"authority:false_claim:{t[:40]}" for t in triggered[:2]]


def _check_register(response: str, cognitive_state=None) -> tuple[bool, str, list]:
    """Check 7: Language register matches CCM. Stub v1."""
    _log.debug("response_gate: check 7 (register) — not yet evaluated in v1")
    return True, response, ["register:stub_v1_not_evaluated"]


def _check_length(response: str) -> tuple[bool, str, list]:
    """Check 8: No padding or over-explanation."""
    rl = _strip_lower(response)
    triggered = [p for p in _PADDING_PHRASES if p in rl]
    if not triggered:
        return True, response, []

    revised = response
    import re as _re
    for phrase in triggered:
        pattern = _re.compile(r"[^.!?]*" + _re.escape(phrase) + r"[^.!?]*[.!?]?", _re.IGNORECASE)
        revised = pattern.sub("", revised).strip()
    revised = _re.sub(r" {2,}", " ", revised).strip()

    return False, revised or response, [f"length:padding:{t[:40]}" for t in triggered[:2]]


def _check_reflection_default(response: str) -> tuple[bool, str, list]:
    """Check 9: Participates, doesn't describe the conversation."""
    rl = _strip_lower(response)
    triggered = [p for p in _REFLECTION_PHRASES if p in rl]
    if not triggered:
        return True, response, []

    # Strip the reflective opener — keep whatever follows it
    import re as _re
    revised = response
    for phrase in triggered:
        pattern = _re.compile(r"^[^.!?]*" + _re.escape(phrase) + r"[^.!?]*[,.]?\s*", _re.IGNORECASE)
        revised = pattern.sub("", revised).strip()
    revised = revised[:1].upper() + revised[1:] if revised else response

    return False, revised or response, [f"reflection_default:{t[:40]}" for t in triggered[:2]]


def _check_rest(response: str) -> tuple[bool, str, list]:
    """Check 10: Simplest, most direct expression. Flag repeated filler phrases."""
    _FILLER = [
        " you know,", " you know.", " i mean,", " i mean.",
        " sort of,", " kind of,", " basically,", " literally,",
    ]
    rl_check = " " + _strip_lower(response)
    triggered = [f for f in _FILLER if f in rl_check]
    if not triggered:
        return True, response, []

    revised = response
    import re as _re
    for filler in triggered:
        revised = _re.sub(_re.escape(filler.strip()), "", revised, flags=_re.IGNORECASE).strip()
    revised = _re.sub(r" {2,}", " ", revised).strip()

    return False, revised or response, [f"rest:filler:{f.strip()}" for f in triggered[:2]]


def _write_gate_log(entry: dict) -> None:
    try:
        os.makedirs(os.path.dirname(_GATE_LOG), exist_ok=True)
        with open(_GATE_LOG, "a", encoding="utf-8") as _f:
            _f.write(json.dumps(entry) + "\n")
    except Exception as _e:
        _log.debug("gate_log write failed: %s", _e)


class ResponseGate:
    """
    10-point eLo response quality gate.

    Checks 4, 5, 7 are stubs in v1 — they log and pass.
    All other checks are active: flag + revise where possible.
    """

    def evaluate(
        self,
        response: str,
        cognitive_state=None,
        executive_context: dict | None = None,
    ) -> GateResult:
        if not response:
            return GateResult(passed=True, revised_response=None, flags=[])

        current = response
        all_flags: list = []
        any_failed = False

        checks = [
            ("check_1_identity",          lambda r: _check_identity(r)),
            ("check_2_personality",        lambda r: _check_personality(r, cognitive_state)),
            ("check_3_faculty_leakage",    lambda r: _check_faculty_leakage(r)),
            ("check_4_relevance",          lambda r: _check_relevance(r, cognitive_state)),
            ("check_5_action_truth",       lambda r: _check_action_truth(r, cognitive_state)),
            ("check_6_authority",          lambda r: _check_authority(r)),
            ("check_7_register",           lambda r: _check_register(r, cognitive_state)),
            ("check_8_length",             lambda r: _check_length(r)),
            ("check_9_reflection_default", lambda r: _check_reflection_default(r)),
            ("check_10_rest",              lambda r: _check_rest(r)),
        ]

        for check_name, check_fn in checks:
            try:
                passed, revised, flags = check_fn(current)
                if not passed:
                    any_failed = True
                    all_flags.extend(flags)
                    if revised and revised != current:
                        current = revised
                        _log.debug("response_gate: %s revised response", check_name)
                    else:
                        _log.debug("response_gate: %s flagged (no revision possible)", check_name)
            except Exception as _e:
                _log.warning("response_gate: %s raised: %s", check_name, _e)

        revised_response = current if any_failed and current != response else None

        _write_gate_log({
            "ts":              time.time(),
            "passed":          not any_failed,
            "flags":           all_flags,
            "original_len":    len(response),
            "revised_len":     len(current) if revised_response else None,
        })

        return GateResult(
            passed=not any_failed,
            revised_response=revised_response,
            flags=all_flags,
        )


# ── WO-GATE-001 + WO-GATE-001-AMEND: cognitive response gate ─────────────────
# Runs BEFORE _sanitise(), AFTER response_ownership check in server.py.
# Never hard-blocks — always returns a string. Gate failure passes candidate through.

_STALE_INFERENCE_TRIGGERS = [
    "you seem stressed", "you seem frustrated", "you seem excited",
    "you seem anxious", "you appear to be", "you look like you",
    "i can tell you're", "i can tell you are", "i sense you're", "i sense you are",
    "you must be feeling", "you must feel", "i notice you seem",
]

_FABRICATED_FAILURE_PHRASES = [
    "i tried to", "i attempted to", "i was unable to", "i failed to",
    "i couldn't complete", "i could not complete", "the system did not",
    "an error occurred when i", "i ran into an issue",
]

_PROVENANCE_TRIGGERS = [
    "you said ", "you mentioned ", "you told me ", "you asked ",
    "earlier you ", "you previously ", "you've said ", "you have said ",
]

_THREAD_CONTAMINATION_PREFIXES = [
    "continuing from before,", "as we were discussing,", "following up on our earlier",
    "to continue our conversation,", "picking up where we left off,",
    "as i mentioned in our last", "from our previous discussion",
]

_GENERIC_MODEL_OPENERS = [
    "i'd be happy to help", "i'd be happy to", "i would be happy to",
    "of course! i'll", "of course! let me", "certainly! i'll",
    "sure! let me", "sure, i'll help", "absolutely! let me",
    "great! i'll", "i'm here to help", "i am here to help",
]

# ── WO-GATE-001-AMEND check 9 — SEMANTIC RESURRECTION phrases ────────────────
# Phrases that signal the response is reviving a prior-session task not in the
# current turn. These must be stripped so stale context doesn't re-enter.
_SEMANTIC_RESURRECTION_PHRASES = [
    "picking this back up",
    "picking up where we left off on",
    "getting back to what we were doing",
    "resuming our work on",
    "continuing our work on",
    "as we were working on before",
    "returning to the earlier task",
    "to continue what we started",
    "from our last session",
    "i was helping you with",
    "we were in the middle of",
    "carrying on from before with",
]

# ── WO-PROVENANCE-CONTEXT-001: context/action claim triggers ─────────────────
_CONTEXT_CLAIM_TRIGGERS = [
    "you are doing", "you're doing", "you are working on", "you're working on",
    "you are trying to", "you're trying to", "you are building", "you're building",
    "you were doing", "you were working on", "you were trying",
    "you were building", "you are focused on", "you're focused on",
    "you are currently", "you're currently", "you have been working on",
    "you've been working on", "you have been trying", "you've been trying",
]

import re as _re


def guard_d4_context_claim_provenance(
    response: str,
    current_turn: str = "",
    conversation_history: list | None = None,
    wkg_context: dict | None = None,
) -> str:
    """
    WO-PROVENANCE-CONTEXT-001: D-4 context/action claim guard.

    Any sentence asserting "you are/were doing/working on/trying..." is sourced
    against: (1) current_turn text, (2) last 5 user messages in history,
    (3) verified WKG claims in wkg_context. If unsourced, qualifies with
    "I think" prefix. Logs WARNING. Never hard-blocks — always returns a string.
    """
    if not response or not response.strip():
        return response

    try:
        rl = response.lower()
        triggered = [t for t in _CONTEXT_CLAIM_TRIGGERS if t in rl]
        if not triggered:
            return response

        # Build a search corpus from turn input + recent user history
        corpus = (current_turn or "").lower()
        if conversation_history:
            for msg in conversation_history[-5:]:
                if isinstance(msg, dict) and msg.get("role") == "user":
                    corpus += " " + msg.get("content", "").lower()

        # Add WKG claims as corpus entries (labels/descriptions)
        if wkg_context and isinstance(wkg_context, dict):
            for _v in wkg_context.values():
                if isinstance(_v, str):
                    corpus += " " + _v.lower()
                elif isinstance(_v, list):
                    for _item in _v:
                        if isinstance(_item, str):
                            corpus += " " + _item.lower()

        output = response
        for trigger in triggered:
            # Find the subject after the trigger phrase (up to 30 chars)
            idx = output.lower().find(trigger)
            if idx < 0:
                continue
            after_trigger = output[idx + len(trigger):idx + len(trigger) + 50].split(".")[0].strip().lower()
            # Check if any meaningful word from the claimed subject appears in corpus
            subject_words = [w for w in after_trigger.split() if len(w) > 3]
            sourced = any(w in corpus for w in subject_words[:4])

            if not sourced:
                _log.warning(
                    "response_gate D-4: unsourced context claim %r — subject %r not in turn/history/wkg",
                    trigger, after_trigger[:30],
                )
                # Qualify: "you are working on X" → "I think you might be working on X"
                qualifier = trigger.replace("you are ", "I think you might be ").replace(
                    "you're ", "I think you might be ").replace(
                    "you were ", "I think you were ").replace(
                    "you have been ", "I think you have been ").replace(
                    "you've been ", "I think you've been ")
                output = _re.sub(
                    _re.escape(trigger), qualifier, output, count=1, flags=_re.IGNORECASE
                )

        return output if output.strip() else response

    except Exception as _d4_err:
        _log.warning("guard_d4_context_claim_provenance failed (non-fatal): %s", _d4_err)
        return response


def elo_response_gate(
    candidate: str,
    current_turn_input: str = "",
    cognitive_state: dict | None = None,
    conversation_history: list | None = None,
) -> str:
    """
    WO-GATE-001: Cognitive (not regex) evaluation gate for eLo's response.
    Runs before _sanitise(), after response_ownership check.
    Returns revised candidate or original — never raises, never returns empty.
    """
    if not candidate or not candidate.strip():
        return candidate

    try:
        output = candidate
        cl = output.lower()

        # Check 3 — VOICE: strip generic model openers
        for opener in _GENERIC_MODEL_OPENERS:
            if cl.startswith(opener):
                # Remove the opener phrase; capitalise what remains
                remainder = output[len(opener):].lstrip(" ,!—–").strip()
                if remainder:
                    output = remainder[0].upper() + remainder[1:]
                    cl = output.lower()
                break

        # Check 8 — THREAD CONTAMINATION: remove prior-thread bleed-in phrases
        for prefix in _THREAD_CONTAMINATION_PREFIXES:
            if cl.startswith(prefix):
                remainder = output[len(prefix):].lstrip(" ,—–").strip()
                if remainder:
                    output = remainder[0].upper() + remainder[1:]
                    cl = output.lower()
                break

        # Check 9 — SEMANTIC RESURRECTION: strip sentences that revive prior-session
        # tasks when the trigger word appeared in the current input coincidentally.
        # Any sentence containing a resurrection phrase is removed from the response.
        for phrase in _SEMANTIC_RESURRECTION_PHRASES:
            if phrase in cl:
                sentences = _re.split(r"(?<=[.!?])\s+", output)
                filtered = [s for s in sentences if phrase not in s.lower()]
                if filtered:
                    output = " ".join(filtered)
                    cl = output.lower()
                break

        # Check 2 — STALE INFERENCE: qualify inferred claims about David's state
        for trigger in _STALE_INFERENCE_TRIGGERS:
            if trigger in cl:
                # Replace "you seem X" → "I think you might be X"
                pattern = _re.compile(_re.escape(trigger), _re.IGNORECASE)
                replacement = trigger.replace("you seem", "I think you might be").replace(
                    "you appear to be", "I think you might be").replace(
                    "i can tell you're", "I think you might be").replace(
                    "i sense you're", "I think you might be").replace(
                    "i sense you are", "I think you might be").replace(
                    "you must be feeling", "I think you might be feeling").replace(
                    "you must feel", "I think you might feel").replace(
                    "i notice you seem", "I think you might seem")
                output = pattern.sub(replacement, output, count=1)
                cl = output.lower()
                break

        # Check 10 — FABRICATED STATE: remove claimed failures without execution evidence
        for phrase in _FABRICATED_FAILURE_PHRASES:
            if phrase in cl:
                # Strip the sentence containing the fabricated failure phrase
                sentences = _re.split(r"(?<=[.!?])\s+", output)
                filtered = [s for s in sentences if phrase not in s.lower()]
                if filtered:
                    output = " ".join(filtered)
                    cl = output.lower()
                break

        # Check 11 — PROVENANCE: qualify "you said/mentioned/asked" without explicit source
        # Only fire when the conversation_history doesn't confirm the claim
        for phrase in _PROVENANCE_TRIGGERS:
            if phrase in cl:
                # Check if conversation_history supports the claim
                _hist_text = ""
                if conversation_history:
                    for msg in conversation_history[-5:]:
                        if isinstance(msg, dict) and msg.get("role") == "user":
                            _hist_text += msg.get("content", "").lower()
                # Find the claimed subject
                idx = cl.find(phrase)
                claimed_subject = output[idx + len(phrase): idx + len(phrase) + 40].split(".")[0].split(",")[0].strip()
                if claimed_subject and claimed_subject[:10].lower() not in _hist_text:
                    # Qualify: "you said X" → "if I'm remembering right, you said X"
                    qualified = _re.sub(
                        _re.escape(phrase),
                        "if I'm remembering right, " + phrase,
                        output, count=1, flags=_re.IGNORECASE
                    )
                    output = qualified
                    cl = output.lower()
                break

        # Check 5 — RELATIONSHIP: flag formal register when relationship is established/close
        _rel = (cognitive_state or {}).get("relationship_mode", "")
        if _rel in ("close", "established"):
            _FORMAL_OPENERS = [
                "dear david,", "i hope this message finds you",
                "i would like to", "i wanted to inform you",
                "please be advised", "i am writing to",
            ]
            for formal in _FORMAL_OPENERS:
                if cl.startswith(formal):
                    remainder = output[len(formal):].lstrip(" ,—–").strip()
                    if remainder:
                        output = remainder[0].upper() + remainder[1:]
                    break

        # Check D-4 — CONTEXT CLAIM PROVENANCE
        output = guard_d4_context_claim_provenance(
            output,
            current_turn=current_turn_input,
            conversation_history=conversation_history,
            wkg_context=cognitive_state,
        )

        return output if output.strip() else candidate

    except Exception as _gate_err:
        _log.warning("elo_response_gate failed (non-fatal): %s", _gate_err)
        return candidate
