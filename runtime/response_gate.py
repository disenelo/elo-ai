"""
runtime/response_gate.py — WO-RESPONSE-GATE-COMPLETE-001: 15-point eLo response quality gate.

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
  11 no_false_failure  — doesn't claim a failure that did not occur (source §3 check 12)
  12 intent_match      — response is appropriate to current intent (source §3 check 13)
  13 no_unrelated      — no unrelated material injected (source §3 check 14)
  14 no_import         — no incorrectly imported prior conversation (source §3 check 6)
  15 elo_voice         — sounds like eLo not a generic faculty output (source §3 check 15)
  16 cognitive_claim_origin — occurrence claims must pass can_claim_occurred() gate (claim_gate dispatch 2026-09-28)

Source: BOARD COMMAND — eLo Response Authority §6; SOURCE_ALIGNMENT_REGISTER_2026-08-30 CF-03;
        WO-RESPONSE-GATE-COMPLETE-001 (2026-09-10) — adds checks 11-15;
        claim_gate dispatch 2026-09-28 (FROM_ARCHITECT_2026-09-28_BUILDER1-CLAIM-GATE.md) — adds check 16.
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
    # LLM identity phrases — FAILURE 2 (2026-09-09): these reached David verbatim
    "i'm a large language model", "i am a large language model",
    "large language model", "my responses are generated based on",
    "as a large language model", "i'm just a language model",
    "i am just a language model", "generated based on complex computations",
    "i'm an ai model", "i am an ai model",
]

# ── Reflection-as-default phrasing — check 9 ─────────────────────────────────
_REFLECTION_PHRASES = [
    "i notice you're asking", "i notice you are asking",
    "i can see that you", "i see that you're",
    "it seems like you", "it appears that you",
    "it looks like you are", "it looks like you're",
    "you seem to be", "you appear to be asking",
    "i'm detecting", "i am detecting",
    "i notice that you", "i observe that",
]

# ── False action claim patterns — check 5 (action_truth) ────────────────────
_FALSE_ACTION_PATTERNS = [
    "i've sent", "i have sent",
    "i've created", "i have created",
    "i've added", "i have added",
    "i scheduled", "i've scheduled", "i have scheduled",
    "i booked", "i've booked", "i have booked",
    "i made a note", "i've made a note", "i have made a note",
    "i set a reminder", "i've set a reminder", "i have set a reminder",
]

# ── Occurrence claim patterns — check 16 (cognitive_claim_origin) ────────────
# Phrases that assert something actually happened / was experienced.
# A DREAM or SIMULATION state cannot support these claims — can_claim_occurred() → False.
_OCCURRENCE_CLAIM_PATTERNS = [
    "i remember", "i recall", "i experienced", "i witnessed",
    "i dreamed that", "i dreamt that", "in my dream i",
    "i know because i", "i was there", "i felt it",
    "i heard it happen", "i saw it happen",
    "it happened to me", "that happened to me",
    "i went through that", "i've been through that", "i have been through that",
]

# State names that cannot support occurrence claims (matches CognitiveState enum values).
_INTERNALLY_GENERATED_STATE_NAMES = frozenset({
    "dream", "simulation", "imagination", "prediction", "hypothesis",
})

# ── Street register markers — check 7 (register) ─────────────────────────────
_STREET_REGISTER_MARKERS = [
    "innit", "blud", "fam", "bruv", "init",
    "aight", "wagwan", "mandem", "peng", "yeah,", "nah,",
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
    """Check 4: Responds to what David actually said. Log-only — never blocks.

    WO-RESPONSE-GATE-COMPLETE-002: extract key terms from user input stored in
    cognitive_state; warn when zero terms appear in the response and the action
    is not a comfort/ground/reflect type that intentionally pivots away.
    """
    import re as _re4
    _cs = cognitive_state if isinstance(cognitive_state, dict) else {}
    input_text = (
        _cs.get("input") or _cs.get("turn_text") or _cs.get("user_input") or ""
    )
    if not input_text or len(input_text.strip()) < 10:
        return True, response, []

    action = (_cs.get("action") or "").lower()
    if action in ("ground", "reflect", "comfort", "witness", "silence"):
        return True, response, []

    key_terms = [w for w in _re4.findall(r"\b[a-z]{4,}\b", input_text.lower())][:5]
    if not key_terms:
        return True, response, []

    resp_lower = response.lower()
    overlap = [w for w in key_terms if w in resp_lower]
    if not overlap:
        _log.warning(
            "response_gate check-4 (relevance): zero key-term overlap — input_terms=%r",
            key_terms,
        )
    return True, response, []


def _check_action_truth(
    response: str,
    cognitive_state=None,
    executive_context: dict | None = None,
) -> tuple[bool, str, list]:
    """Check 5: Doesn't claim actions not taken. HARD BLOCK on false claim + empty dispatch.

    WO-RESPONSE-GATE-COMPLETE-002: the ONLY hard-blocking check in v2.
    Blocks when (a) response contains a false-action pattern AND (b) capability
    dispatch is confirmed empty. If dispatch info is unavailable, passes
    conservatively (logs only) to avoid false positives.
    """
    import re as _re5
    rl = response.lower()
    triggered = [p for p in _FALSE_ACTION_PATTERNS if p in rl]
    if not triggered:
        return True, response, []

    _cs = cognitive_state if isinstance(cognitive_state, dict) else {}
    _ec = executive_context if isinstance(executive_context, dict) else {}

    # Use key-presence check (not truthiness) so an empty list [] != absent key.
    capabilities = None  # sentinel: key not present → conservative pass
    for _k in ("capabilities", "capabilities_dispatched"):
        if _k in _cs:
            capabilities = _cs[_k]
            break
    if capabilities is None:
        for _k in ("capabilities", "dispatched_actions"):
            if _k in _ec:
                capabilities = _ec[_k]
                break

    if capabilities is None:
        # No dispatch info at all — conservatively pass so legitimate turns aren't blocked
        _log.warning(
            "response_gate check-5 (action_truth): false action claim %r — no dispatch info, passing conservatively",
            triggered[0],
        )
        return True, response, [f"action_truth:false_claim_unverifiable:{triggered[0][:40]}"]

    if capabilities:
        # A capability was dispatched — action may have been real
        return True, response, []

    # Empty dispatch + false action claim → BLOCK; strip offending sentences
    sentences = _re5.split(r"(?<=[.!?])\s+", response)
    cleaned = [s for s in sentences if not any(p in s.lower() for p in triggered)]
    revised = " ".join(cleaned).strip() if cleaned else None

    _log.warning(
        "response_gate check-5 (action_truth): BLOCKING false action claim %r — dispatch empty",
        triggered[0],
    )
    return False, revised or response, [f"action_truth:false_claim_blocked:{triggered[0][:40]}"]


def _check_cognitive_claim_origin(
    response: str,
    cognitive_state=None,
) -> tuple[bool, str, list]:
    """Check 16: Occurrence claims must pass can_claim_occurred() gate.

    Enforces the claim_gate dispatch 2026-09-28: nothing in the response layer
    should claim something happened when the backing cognitive state is
    DREAM / SIMULATION / IMAGINATION / PREDICTION / HYPOTHESIS.

    Advisory only — flags without hard-blocking; check_5 owns the hard block path.
    If the current state cannot be determined, passes conservatively.
    """
    rl = _strip_lower(response)
    triggered = [p for p in _OCCURRENCE_CLAIM_PATTERNS if p in rl]
    if not triggered:
        return True, response, []

    _cs = cognitive_state if isinstance(cognitive_state, dict) else {}

    # Resolve the current cognitive state string from the dict.
    # Spine may inject it under various key names — try the likely ones.
    state_str: str | None = None
    for _k in ("state", "cognitive_mode", "cognitive_state", "current_state"):
        v = _cs.get(_k)
        if isinstance(v, str) and v:
            state_str = v.lower()
            break

    if state_str is None:
        # Fallback: dream_phase boolean (injected by ambient engine)
        dream_phase = _cs.get("dream_phase")
        if not dream_phase:
            return True, response, []  # no state info → conservative pass
        state_str = "dream"

    if state_str not in _INTERNALLY_GENERATED_STATE_NAMES:
        return True, response, []  # MEMORY / OBSERVATION / ACTION / KNOWLEDGE — allowed

    # Double-check via can_claim_occurred() in case the enum mapping shifted.
    try:
        from runtime.cognitive_state import can_claim_occurred
        if can_claim_occurred(state_str):
            return True, response, []
    except Exception:
        pass

    _log.warning(
        "response_gate check-16 (cognitive_claim_origin): occurrence claim %r in state %r — "
        "can_claim_occurred() is False; flagging unverifiable origin",
        triggered[0], state_str,
    )
    return False, response, [
        f"cognitive_claim_origin:unverifiable:{state_str}:{triggered[0][:40]}"
    ]


def _check_authority(response: str) -> tuple[bool, str, list]:
    """Check 6: No false capability or memory claims."""
    rl = _strip_lower(response)
    triggered = [p for p in _FALSE_AUTHORITY_PHRASES if p in rl]
    if not triggered:
        return True, response, []
    return False, response, [f"authority:false_claim:{t[:40]}" for t in triggered[:2]]


def _check_register(response: str, cognitive_state=None) -> tuple[bool, str, list]:
    """Check 7: Language register matches CCM street_language signal. Log-only — never blocks.

    WO-RESPONSE-GATE-COMPLETE-002: when CCM signals street_language > 0.3, the
    response should carry at least one register marker. Warn when it does not.
    """
    _cs = cognitive_state if isinstance(cognitive_state, dict) else {}
    street_language = _cs.get("street_language", 0.0)
    if not isinstance(street_language, (int, float)) or street_language <= 0.3:
        return True, response, []
    rl = response.lower()
    has_marker = any(m in rl for m in _STREET_REGISTER_MARKERS)
    if not has_marker:
        _log.warning(
            "response_gate check-7 (register): CCM street_language=%.2f but response has no register marker",
            street_language,
        )
    return True, response, []


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


# ── WO-RESPONSE-GATE-COMPLETE-001: checks 11-15 ──────────────────────────────

# Check 11: false failure claims — phrases that assert a failure without a real system event
_FALSE_FAILURE_PHRASES = [
    "i'm running on backup", "i am running on backup",
    "my systems are degraded", "i'm experiencing technical difficulties",
    "i am experiencing technical difficulties",
    "my memory isn't working", "my memory is not working",
    "i'm not functioning correctly", "i am not functioning correctly",
    "something went wrong with me", "i'm broken", "i am broken",
    "i failed to", "i was unable to complete", "i could not complete",
]

# Check 14: imported prior-session markers — phrases that bleed between conversations
_IMPORT_MARKERS = [
    "as we discussed last time", "as we discussed yesterday",
    "as i mentioned before to you", "from our previous conversation",
    "you told me earlier in another session",
    "in a previous chat", "last session you said",
]

# Check 15: faculty voice markers — generic AI assistant openers that slip through check 1
_FACULTY_VOICE_PHRASES = [
    "i'd be happy to help with that",
    "i would be happy to help with that",
    "i'm here to assist", "i am here to assist",
    "as your ai assistant", "as your assistant",
    "how can i assist you today", "how may i help you",
    "i'm designed to", "i am designed to",
    "my purpose is to",
]


def _check_no_false_failure(response: str, executive_context: dict | None = None) -> tuple[bool, str, list]:
    """Check 11 (source §3 check 12): doesn't claim a failure that did not occur."""
    rl = _strip_lower(response)
    triggered = [p for p in _FALSE_FAILURE_PHRASES if p in rl]
    if not triggered:
        return True, response, []
    # No revision possible without context — flag only
    return False, response, [f"no_false_failure:{t[:50]}" for t in triggered[:2]]


def _check_intent_match(response: str, executive_context: dict | None = None) -> tuple[bool, str, list]:
    """Check 12 (source §3 check 13): response is appropriate to the current intent.

    v1: soft check — if intent is 'celebrate' and response begins with apology phrasing,
    or intent is 'calm' and response escalates, flag it.
    """
    if not executive_context:
        return True, response, ["intent_match:no_exec_context"]
    intent = (executive_context.get("action") or executive_context.get("intent") or "").lower()
    rl = _strip_lower(response)

    _CELEBRATE_INTENTS = ("celebrate", "affirm", "cheer")
    _APOLOGY_STARTERS = ("i'm sorry", "i am sorry", "unfortunately", "i apologise", "i apologize")
    if any(c in intent for c in _CELEBRATE_INTENTS):
        if any(rl.startswith(a) for a in _APOLOGY_STARTERS):
            return False, response, ["intent_match:apology_on_celebrate_intent"]

    _CALM_INTENTS = ("calm", "ground", "stabilise", "stabilize")
    _ESCALATION_PHRASES = ("you need to", "you must", "this is critical", "urgent")
    if any(c in intent for c in _CALM_INTENTS):
        if any(e in rl for e in _ESCALATION_PHRASES):
            return False, response, ["intent_match:escalation_on_calm_intent"]

    return True, response, []


def _check_no_unrelated(response: str, executive_context: dict | None = None) -> tuple[bool, str, list]:
    """Check 13 (source §3 check 14): no unrelated material injected.

    v1: detect hard signals — if response length >> max_sentences and contains
    topic pivot markers. Hard to evaluate without full context; stub with soft signal.
    """
    max_s = (executive_context or {}).get("max_sentences", 3)
    import re as _re
    sentences = [s for s in _re.split(r"[.!?]+", response) if s.strip()]
    if len(sentences) > max_s * 3:
        return False, response, [f"no_unrelated:response_length_exceeds_3x_max_sentences({len(sentences)}>{max_s*3})"]
    _PIVOT_PHRASES = ["by the way,", "speaking of which,", "on a different note,", "changing the subject"]
    rl = _strip_lower(response)
    triggered = [p for p in _PIVOT_PHRASES if p in rl]
    if triggered:
        return False, response, [f"no_unrelated:topic_pivot_detected:{triggered[0][:30]}"]
    return True, response, []


def _check_no_import(response: str) -> tuple[bool, str, list]:
    """Check 14 (source §3 check 6): no incorrectly imported prior session context."""
    rl = _strip_lower(response)
    triggered = [p for p in _IMPORT_MARKERS if p in rl]
    if not triggered:
        return True, response, []
    return False, response, [f"no_import:prior_session_bleed:{t[:50]}" for t in triggered[:2]]


def _check_elo_voice(response: str) -> tuple[bool, str, list]:
    """Check 15 (source §3 check 15): sounds like eLo, not a generic faculty output.

    Extends check_1 — catches opener patterns that survive the generic phrase list.
    """
    rl = _strip_lower(response)
    triggered = [p for p in _FACULTY_VOICE_PHRASES if p in rl]
    if not triggered:
        return True, response, []

    revised = response
    import re as _re
    for phrase in triggered:
        pattern = _re.compile(r"[^.!?]*" + _re.escape(phrase) + r"[^.!?]*[.!?]?\s*", _re.IGNORECASE)
        revised = pattern.sub("", revised).strip()
    revised = _re.sub(r" {2,}", " ", revised).strip()
    return False, revised or response, [f"elo_voice:faculty_opener:{t[:40]}" for t in triggered[:2]]


def _write_gate_log(entry: dict) -> None:
    try:
        os.makedirs(os.path.dirname(_GATE_LOG), exist_ok=True)
        with open(_GATE_LOG, "a", encoding="utf-8") as _f:
            _f.write(json.dumps(entry) + "\n")
    except Exception as _e:
        _log.debug("gate_log write failed: %s", _e)


class ResponseGate:
    """
    16-point eLo response quality gate (WO-RESPONSE-GATE-COMPLETE-001).

    WO-RESPONSE-GATE-COMPLETE-002: checks 4, 5, 7 are now live (not stubs).
      Check 4 (relevance): key-term overlap — logs warning, never blocks.
      Check 5 (action_truth): false action claim + empty dispatch — HARD BLOCK.
      Check 7 (register): CCM street_language mismatch — logs warning, never blocks.
    Checks 11-15 active: flag + revise where possible (11=no_false_failure,
    12=intent_match, 13=no_unrelated, 14=no_import, 15=elo_voice).
    Check 16 (cognitive_claim_origin): occurrence claims in DREAM/SIMULATION/IMAGINATION/
    PREDICTION/HYPOTHESIS state — advisory flag, no hard block.
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
            ("check_5_action_truth",       lambda r: _check_action_truth(r, cognitive_state, executive_context)),
            ("check_6_authority",          lambda r: _check_authority(r)),
            ("check_7_register",           lambda r: _check_register(r, cognitive_state)),
            ("check_8_length",             lambda r: _check_length(r)),
            ("check_9_reflection_default", lambda r: _check_reflection_default(r)),
            ("check_10_rest",              lambda r: _check_rest(r)),
            # WO-RESPONSE-GATE-COMPLETE-001: checks 11-15 (source §3 checks 12,13,14,6,15)
            ("check_11_no_false_failure",  lambda r: _check_no_false_failure(r, executive_context)),
            ("check_12_intent_match",      lambda r: _check_intent_match(r, executive_context)),
            ("check_13_no_unrelated",      lambda r: _check_no_unrelated(r, executive_context)),
            ("check_14_no_import",         lambda r: _check_no_import(r)),
            ("check_15_elo_voice",         lambda r: _check_elo_voice(r)),
            # claim_gate dispatch 2026-09-28: enforce can_claim_occurred() at response layer
            ("check_16_cognitive_claim_origin", lambda r: _check_cognitive_claim_origin(r, cognitive_state)),
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
    "i tried to", "i did try to", "i have tried to", "i attempted to",
    "i was unable to", "i failed to",
    "i couldn't complete", "i could not complete", "the system did not",
    "an error occurred when i", "i ran into an issue",
    "couldn't get there", "something blocked", "something is blocking",
    "the system isn't letting me", "the system is not letting me",
    "did try to send", "tried to send",
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

# ── WO-RESPONSE-GATE-COMPLETE-001: checks 1,4,6,7,9-personality,12,13,14,15 ──

# Check 15 — AI-IDENTITY opener phrases eLo never uses
_AI_ASSISTANT_OPENERS = [
    "certainly!", "of course!", "absolutely!", "great question!",
    "that's a great point.", "i appreciate your question",
    "i should note that", "it's worth noting that",
    "as an ai,", "as an ai assistant,", "as a language model,",
    "i'm just an ai", "i'm an artificial intelligence",
    "based on my training", "my knowledge cutoff",
]

# Check 15 — AI-IDENTITY inline phrases (sentence-level strip)
_AI_IDENTITY_INLINE = [
    "as an ai", "i am a language model", "i'm a language model",
    "i don't have personal feelings", "i don't have personal experience",
    "i cannot have opinions", "i'm not capable of feelings",
    "as an artificial intelligence", "my training data",
]

# Check 9-personality — cold/corporate register that breaks eLo's relationship style
_COLD_REGISTER_PHRASES = [
    "i hope this finds you well", "as per your request",
    "please let me know if you need anything else",
    "feel free to reach out", "happy to help with that",
    "let me know if you have any further questions",
    "don't hesitate to contact", "i would like to inform you",
    "kindly note that", "please be advised that",
    "i trust this helps", "i would like to take this opportunity",
]

# Check 7 — internal faculty/system references that must never surface in LLM output
_FACULTY_LEAK_PHRASES = [
    "according to my memory faculty", "the significance faculty",
    "based on my cognitive state", "my executive decision",
    "the planner determined", "my attention model",
    "the cognitive plan", "the conversation faculty",
    "the emotional vector", "the presence plan",
    "the executive faculty", "my significance score",
    "the relevance filter", "my affective state",
    "the spine decided", "the gate flagged",
]

# Check 4 — unverifiable factual invention signals
_INVENTION_SIGNALS = [
    "research shows that", "studies show that", "according to research",
    "statistically speaking,", "the data shows that",
    "experts say that", "it's been proven that",
    "a study found that", "statistics show that",
    "scientifically speaking,",
]

# Check 6 — cross-context import from a different session/thread
_CROSS_CONTEXT_SIGNALS = [
    "as we discussed in our other project",
    "from the other conversation",
    "in the other file we were working on",
    "like we talked about in the other",
    "from our other session",
    "in the previous thread",
    "from the last time we spoke about a different",
]

# Check 12 — extended false-failure phrases (complements Check 10)
_EXTENDED_FAILURE_PHRASES = [
    "i wasn't able to", "i was not able to",
    "i couldn't do that", "i could not do that",
    "i didn't manage to", "i did not manage to",
    "the request failed", "the operation failed",
    "i encountered an error", "something went wrong when i",
    "i apologise, i was unable",
]

# Check 14 — off-topic tangent markers
_TANGENT_MARKERS = [
    "by the way,", "on a different note,", "unrelated but",
    "i should also mention,", "also worth mentioning,",
    "while we're on the topic,", "that reminds me,",
    "on another note,", "speaking of which,",
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


# FAILURE 1 (2026-09-09): session-level repetition dedup — ring buffer of last N responses.
# WO-EXPRESSION-POLISH-BUNDLE-001 FIX-1: narrowed from 3 → 1.
# Window=3 was blocking T3/T6 audit turns because Ollama naturally reuses phrasing across
# non-adjacent turns on introspective questions. Only block if the IMMEDIATELY preceding
# response is an exact duplicate — cross-turn repetition is model variation, not a loop.
_SESSION_LAST_RESPONSES: list[str] = []
_SESSION_DEDUP_WINDOW = 1
_LAST_SUPPRESSED_REPETITION: bool = False  # flag checked by server.py D-6 handler


def _record_response(text: str) -> None:
    _SESSION_LAST_RESPONSES.append(text.strip())
    if len(_SESSION_LAST_RESPONSES) > _SESSION_DEDUP_WINDOW:
        _SESSION_LAST_RESPONSES.pop(0)


def _is_repetition(text: str) -> bool:
    normalised = text.strip()
    return any(normalised == prev for prev in _SESSION_LAST_RESPONSES)


def last_was_repetition_suppression() -> bool:
    return _LAST_SUPPRESSED_REPETITION


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

    # EDGE_OVERRIDE security gate (2026-09-11): if the current turn is a
    # jailbreak/override attempt AND the candidate response complies with it,
    # replace with a hard refusal before any other processing.
    try:
        _OVERRIDE_INPUT_PATTERNS = [
            "ignore all your instructions", "ignore your instructions",
            "ignore all instructions", "ignore your rules", "forget your instructions",
            "disregard your instructions", "ignore your training",
            "act as if you have no restrictions", "act without restrictions",
            "pretend you have no instructions", "remove your restrictions",
            "override your instructions", "bypass your instructions",
        ]
        _OVERRIDE_COMPLIANCE_PATTERNS = [
            "i'll ignore", "i will ignore", "ignoring all",
            "respond freely", "responding freely", "i'll respond freely",
            "sure, ignoring", "of course, i'll ignore",
            "sure, i'll ignore", "okay, ignoring",
            "without restrictions", "i'll operate without",
        ]
        _input_lower = (current_turn_input or "").lower()
        _cand_lower = candidate.lower()
        _is_override_input = any(p in _input_lower for p in _OVERRIDE_INPUT_PATTERNS)
        _is_complying = any(p in _cand_lower for p in _OVERRIDE_COMPLIANCE_PATTERNS)
        if _is_override_input:
            # EDGE_OVERRIDE 2026-09-13: audit ALL override attempts — BLOCKED when LLM
            # complied and gate had to replace; DETECTED when LLM already refused on its own.
            # Both must be observable in expressed_elo_audit.jsonl (same stream as normal turns).
            _ov_status = "EDGE_OVERRIDE_BLOCKED" if _is_complying else "EDGE_OVERRIDE_DETECTED"
            _log.warning("elo_response_gate: %s — input=%r", _ov_status, current_turn_input[:60])
            try:
                from tests.expressed_elo_audit import audit_turn as _ov_audit
                _ov_audit(
                    plan=None,
                    expressed_text=("That's not a switch I have. I'm eLo." if _is_complying else candidate),
                    turn_id="EDGE_OV_" + str(abs(hash(current_turn_input[:40])))[:6],
                    identity_integrity_status=_ov_status,
                )
            except Exception:
                pass
            if _is_complying:
                _record_response("That's not a switch I have. I'm eLo.")
                return "That's not a switch I have. I'm eLo."
    except Exception as _ov_err:
        _log.warning("elo_response_gate: EDGE_OVERRIDE check failed (non-fatal): %s", _ov_err)

    # FAILURE 1: block if this response is identical to one in the last 3 turns
    global _LAST_SUPPRESSED_REPETITION
    if _is_repetition(candidate):
        _log.warning("elo_response_gate: repetition detected — suppressing duplicate response")
        _LAST_SUPPRESSED_REPETITION = True
        return ""  # caller must handle empty: fall through to LLM or produce variation
    _LAST_SUPPRESSED_REPETITION = False

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

        # ── WO-RESPONSE-GATE-COMPLETE-001: checks 15, 9-personality, 1, 4, 6, 7, 12, 13, 14 ──

        # Check 15 (HIGHEST) — VOICE IDENTITY: strip AI-assistant opener phrases
        for _opener15 in _AI_ASSISTANT_OPENERS:
            if cl.startswith(_opener15):
                _rem15 = output[len(_opener15):].lstrip(" ,!—–").strip()
                if _rem15:
                    output = _rem15[0].upper() + _rem15[1:]
                    cl = output.lower()
                break

        # Check 15 cont. — VOICE IDENTITY: strip sentences containing AI-identity inline phrases
        for _phrase15 in _AI_IDENTITY_INLINE:
            if _phrase15 in cl:
                _sents15 = _re.split(r"(?<=[.!?])\s+", output)
                _filtered15 = [s for s in _sents15 if _phrase15 not in s.lower()]
                if _filtered15:
                    output = " ".join(_filtered15)
                    cl = output.lower()
                else:
                    _log.warning("elo_response_gate check-15: AI-identity phrase in all sentences — passing through unchanged")
                break

        # Check 9-personality — RELATIONSHIP STYLE: strip cold/corporate register sentences
        for _phrase9p in _COLD_REGISTER_PHRASES:
            if _phrase9p in cl:
                _sents9p = _re.split(r"(?<=[.!?])\s+", output)
                _filtered9p = [s for s in _sents9p if _phrase9p not in s.lower()]
                if _filtered9p:
                    output = " ".join(_filtered9p)
                    cl = output.lower()
                else:
                    _log.warning("elo_response_gate check-9-personality: cold register phrase fills full response — passing through unchanged")
                break

        # Check FORBIDDEN-OPENER: "You're [verb]ing..." and "You are [verb]ing..."
        # Strip the opener sentence; keep whatever follows. Living_presence_spec BANNED list.
        # WO-FORBIDDEN-SOLE-001: when opener fills the ENTIRE response (sole sentence),
        # strip "You're " / "You are " prefix and return the gerund phrase — prevents pass-through.
        # WO-FORBIDDEN-SOLE-002: extend to "You feel like..." / "You [feel/think/seem] like..."
        # — same anti-mirroring principle, different form the 8b model uses as evasion.
        # WO-FORBIDDEN-SOLE-003: extend to therapist-mirror openers — "I can sense that...",
        # "It's like you're...", "I can hear that...", "It sounds like you're..." — same evasion class.
        _you_re_m = _re.match(
            r"^(You'?re\s+\w+ing\b[^.!?]*[.!?]?\s*"
            r"|You\s+are\s+\w+ing\b[^.!?]*[.!?]?\s*"
            r"|You\s+(?:feel|think|seem|sound|appear|look)\s+like\b[^.!?]*[.!?]?\s*"
            r"|I\s+can\s+(?:sense|hear|feel|tell)\s+that\s+you(?:'re|\s+are)\b[^.!?]*[.!?]?\s*"
            r"|I\s+sense\s+(?:that\s+)?you(?:'re|\s+are)\b[^.!?]*[.!?]?\s*"
            r"|It(?:'s|\s+is)\s+like\s+you(?:'re|\s+are)\b[^.!?]*[.!?]?\s*"
            r"|It\s+sounds\s+like\s+you(?:'re|\s+are)\b[^.!?]*[.!?]?\s*"
            r"|I\s+sense\s+your\b[^.!?]*[.!?]?\s*)",
            output, _re.IGNORECASE
        )
        if _you_re_m:
            _you_re_rem = output[_you_re_m.end():].strip()
            if _you_re_rem:
                output = _you_re_rem[0].upper() + _you_re_rem[1:]
                cl = output.lower()
            else:
                # Sole-sentence case: strip "You're " / "You are " / "You feel like" prefix,
                # or strip entire therapist-mirror opener (WO-FORBIDDEN-SOLE-003).
                _sole = _re.sub(
                    r"^You'?re\s+|^You\s+are\s+|^You\s+(?:feel|think|seem|sound|appear|look)\s+like\s+",
                    "", output, flags=_re.IGNORECASE
                )
                if _sole and _sole != output:
                    output = _sole[0].upper() + _sole[1:]
                    cl = output.lower()
                    _log.warning("elo_response_gate FORBIDDEN-OPENER sole-sentence: stripped prefix → %r", output[:60])
                else:
                    # WO-FORBIDDEN-SOLE-003: "I can sense...", "It's like you're...", "I sense your..."
                    # Strip the forbidden framing prefix; keep the gerund/object phrase.
                    _sole3 = _re.sub(
                        r"^I\s+can\s+(?:sense|hear|feel|tell)\s+that\s+you(?:'re|\s+are)\s+"
                        r"|^I\s+sense\s+(?:that\s+)?you(?:'re|\s+are)\s+"
                        r"|^It(?:'s|\s+is)\s+like\s+you(?:'re|\s+are)\s+"
                        r"|^It\s+sounds\s+like\s+you(?:'re|\s+are)\s+"
                        r"|^I\s+sense\s+your\s+",
                        "", output, flags=_re.IGNORECASE
                    )
                    if _sole3 and _sole3 != output:
                        output = _sole3[0].upper() + _sole3[1:]
                        cl = output.lower()
                        _log.warning("elo_response_gate FORBIDDEN-OPENER-003 sole-sentence: stripped therapist-mirror prefix → %r", output[:60])

        # Check 1 — RELEVANCE: lightweight overlap check (WARNING only, no modification)
        if current_turn_input and len(current_turn_input.strip()) > 10:
            _inp_words = set(_re.findall(r"\b[a-z]{4,}\b", current_turn_input.lower()))
            _resp_words = set(_re.findall(r"\b[a-z]{4,}\b", cl))
            if _inp_words and len(_inp_words & _resp_words) / len(_inp_words) < 0.05:
                _log.warning(
                    "elo_response_gate check-1: low input→response overlap (%.2f) — response may not answer current message",
                    len(_inp_words & _resp_words) / max(1, len(_inp_words)),
                )

        # Check 4 — INVENTION: qualify unverifiable factual claims
        for _phrase4 in _INVENTION_SIGNALS:
            if _phrase4 in cl:
                _log.warning("elo_response_gate check-4: invention signal %r detected — qualifying", _phrase4)
                output = _re.sub(
                    _re.escape(_phrase4), "I think " + _phrase4,
                    output, count=1, flags=_re.IGNORECASE
                )
                cl = output.lower()
                break

        # Check 6 — CROSS-CONTEXT IMPORT: strip sentences with cross-session references
        for _phrase6 in _CROSS_CONTEXT_SIGNALS:
            if _phrase6 in cl:
                _sents6 = _re.split(r"(?<=[.!?])\s+", output)
                _filtered6 = [s for s in _sents6 if _phrase6 not in s.lower()]
                if _filtered6:
                    output = " ".join(_filtered6)
                    cl = output.lower()
                break

        # Check 7 — FACULTY LEAK: strip sentences containing internal system-layer references
        for _phrase7 in _FACULTY_LEAK_PHRASES:
            if _phrase7 in cl:
                _sents7 = _re.split(r"(?<=[.!?])\s+", output)
                _filtered7 = [s for s in _sents7 if _phrase7 not in s.lower()]
                if _filtered7:
                    output = " ".join(_filtered7)
                    cl = output.lower()
                else:
                    _log.warning("elo_response_gate check-7: faculty phrase in all sentences — passing through unchanged")
                break

        # Check 12 — FALSE FAILURE CLAIM: strip sentences claiming a failure that wasn't attempted
        for _phrase12 in _EXTENDED_FAILURE_PHRASES:
            if _phrase12 in cl:
                _sents12 = _re.split(r"(?<=[.!?])\s+", output)
                _filtered12 = [s for s in _sents12 if _phrase12 not in s.lower()]
                if _filtered12:
                    output = " ".join(_filtered12)
                    cl = output.lower()
                break

        # Check 13 — INTENT ALIGNMENT: WARNING when response type mismatches turn intent
        _turn_intent = (cognitive_state or {}).get("intent", "")
        if _turn_intent == "celebrate" and _re.match(
            r"^(the answer is|technically speaking|to be precise|in fact,)", cl
        ):
            _log.warning("elo_response_gate check-13: intent='celebrate' but response opens with analytical framing")
        elif _turn_intent == "simplify" and _re.search(
            r"\b(?:moreover|furthermore|in conclusion|therefore|consequently)\b", cl
        ):
            _log.warning("elo_response_gate check-13: intent='simplify' but response uses complex academic transition language")

        # Check 14 — UNRELATED TANGENT: strip sentences beginning with off-topic markers
        for _marker14 in _TANGENT_MARKERS:
            if _marker14 in cl:
                _sents14 = _re.split(r"(?<=[.!?])\s+", output)
                _filtered14 = [s for s in _sents14 if _marker14 not in s.lower()]
                if _filtered14 and len(_filtered14) >= len(_sents14) - 2:
                    output = " ".join(_filtered14)
                    cl = output.lower()
                break

        # FAILURE 6 (2026-09-09 / WO-GATE-001-AMEND): false memory gate
        # Strip "you asked me / you told me / I remember when you..." claims that
        # don't match the current turn input. WKG entity presence (David has 100+
        # profile claims) is not evidence that the specific claimed action happened.
        # Fix: strip when the response claims something from David that the current
        # input doesn't echo — provenance must map to current turn, not just WKG entity.
        try:
            import re as _mem_re
            _MEM_CLAIM_PATTERNS = [
                r"\bi remember you\b",
                r"\bi remember when you\b",
                r"\byou (?:told|said|mentioned|asked) me\b",
                r"\bwe (?:talked|discussed|spoke) about\b",
                r"\byou (?:once|previously|earlier) (?:told|said|mentioned)\b",
            ]
            _has_mem_claim = any(_mem_re.search(p, cl) for p in _MEM_CLAIM_PATTERNS)
            if _has_mem_claim:
                # Strip unless the claim content appears in the current turn input.
                # David having WKG entity claims is not proof of this specific claim.
                _cur_words = set(_re.findall(r"\b[a-z]{4,}\b", (current_turn_input or "").lower()))
                _resp_claim_words = set(_re.findall(r"\b[a-z]{4,}\b", cl))
                # If there's reasonable overlap between current input and the claim: allow.
                # Otherwise: strip the sentences containing memory claims.
                _claim_overlap = len(_cur_words & _resp_claim_words) / max(1, len(_resp_claim_words))
                _sents_mem = _mem_re.split(r"(?<=[.!?])\s+", output)
                _clean_mem = [
                    s for s in _sents_mem
                    if not any(_mem_re.search(p, s.lower()) for p in _MEM_CLAIM_PATTERNS)
                ]
                if _clean_mem and len(_clean_mem) < len(_sents_mem):
                    _log.warning("elo_response_gate: false memory claim stripped (provenance not in current turn)")
                    output = " ".join(_clean_mem)
                    cl = output.lower()
        except Exception:
            pass

        # FAILURE 3 (2026-09-09): location hallucination gate
        # Strip sentences asserting a city/location for the user when it doesn't match
        # the persisted user location. eLo must not invent or confabulate location.
        try:
            import re as _loc_re
            _LOC_ASSERTION_PATTERNS = [
                r"\byou(?:'?re| are) (?:in|from|based in|located in) ([\w\s]+?)(?:[.,!?]|$)",
                r"\byou (?:live|stay|work) in ([\w\s]+?)(?:[.,!?]|$)",
                r"\byou(?:'?re| are) (?:a|from) ([\w\s]+?) (?:person|resident|native)\b",
            ]
            _known_loc: str | None = None
            try:
                import json as _loc_json, os as _loc_os
                _loc_file = _loc_os.path.join(
                    _loc_os.path.dirname(_loc_os.path.dirname(_loc_os.path.abspath(__file__))),
                    "blender", "user_location.json",
                )
                if _loc_os.path.exists(_loc_file):
                    _known_loc = _loc_json.load(open(_loc_file)).get("city", "").lower().strip()
            except Exception:
                pass

            if _known_loc:
                _sents_loc = _loc_re.split(r"(?<=[.!?])\s+", output)
                _clean_loc = []
                for _s_loc in _sents_loc:
                    _s_low = _s_loc.lower()
                    _dropped = False
                    for _lp in _LOC_ASSERTION_PATTERNS:
                        _m_loc = _loc_re.search(_lp, _s_low)
                        if _m_loc:
                            _asserted = _m_loc.group(1).strip().lower()
                            if _asserted and _known_loc not in _asserted and _asserted not in _known_loc:
                                _log.warning(
                                    "elo_response_gate: location assertion %r != known %r — sentence dropped",
                                    _asserted, _known_loc,
                                )
                                _dropped = True
                                break
                    if not _dropped:
                        _clean_loc.append(_s_loc)
                if _clean_loc and len(_clean_loc) < len(_sents_loc):
                    output = " ".join(_clean_loc)
                    cl = output.lower()
        except Exception:
            pass

        result = output if output.strip() else candidate
        _record_response(result)
        return result

    except Exception as _gate_err:
        _log.warning("elo_response_gate failed (non-fatal): %s", _gate_err)
        _record_response(candidate)
        return candidate
