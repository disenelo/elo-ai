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
