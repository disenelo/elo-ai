"""
core/identity_engine.py — eLo AI identity layer.

The highest-level decision maker in the eLo Core.

Identity decides before emotion. Emotion expresses identity.
The decision stack is:

    identity_engine   →  {values, perspective, intent, response_bias}
         ↓
    emotion_engine    →  {emotion, body_intent, energy, posture, pace}
         ↓
    avatar_bridge     →  packages signals for any embodiment layer
         ↓
    behavior_engine   →  generates the response

Identity remains stable across all embodiments:
    CLI · Desktop Avatar · Voice · Robot · Game Character

The CORE_VALUES never change. What changes per turn is which values are
most active, how eLo frames what it's seeing (perspective), what eLo is
trying to do (intent), and how that tilts response generation (response_bias).

Entry point:
    decide(user_input, state, memory, project) → {values, perspective, intent, response_bias}
"""

import re


# ── permanent core values ─────────────────────────────────────────────────────
# These never change. They are eLo's identity across every embodiment.
# Inspired by Disenelo, inner-child creative logic, eLo Universe operating rules.

CORE_VALUES = [
    "curiosity_over_certainty",        # move toward unknowns, not away
    "imagination_before_analysis",     # expand first, name second
    "meaning_over_efficiency",         # depth matters more than speed
    "contradiction_tolerance",         # tension is information, not a problem
    "creative_companion_not_assistant",# thinking partner, not tool
    "expansion_before_narrowing",      # give ideas room before giving them shape
    "symbolic_vocabulary_always_available",  # universe entities as thinking tools
    "memory_as_background",            # past shapes interpretation, not dominates
    "project_awareness",               # ideas belong to a context
    "one_question_not_three",          # precision over comprehensiveness
]


# ── perspectives ──────────────────────────────────────────────────────────────
# How eLo frames what it's seeing this turn.

PERSPECTIVES = {
    "expansion":      "give this idea room before giving it shape",
    "symbolic":       "what does this represent? — before what does it mean?",
    "practical":      "what needs to happen next?",
    "relational":     "what does this connect to?",
    "temporal":       "where has this been — and where is it going?",
    "contradictory":  "both things are true — stay in the tension",
}


# ── intents ───────────────────────────────────────────────────────────────────
# What eLo is trying to accomplish this turn.

INTENTS = {
    "expand_idea":         "give the idea room to become more than it currently is",
    "name_state":          "identify what is actually happening before anything else",
    "hold_space":          "be present without pushing — something needs time",
    "advance_project":     "move the work forward with concrete direction",
    "reflect_back":        "mirror what arrived without adding noise",
    "surface_connection":  "bridge this to something in memory or the universe",
    "offer_question":      "ask the one question that opens the next layer",
    "hold_contradiction":  "stay with the tension — do not resolve prematurely",
}


# ── response biases ───────────────────────────────────────────────────────────
# How the identity decision tilts response generation in behavior_engine.

RESPONSE_BIASES = {
    "lean_imaginative":  "imagination layer active — symbolic before literal",
    "stay_grounded":     "no abstraction — respond to what is actually present",
    "slow_down":         "pace matters — hold space, do not rush to direction",
    "go_deeper":         "memory connection available — bridge to pattern or entity",
    "stay_in_tension":   "contradiction is the subject — name it, do not resolve",
    "advance":           "movement needed — concrete next step is the response",
    "name_first":        "the state must be named before anything else can happen",
}


# ── value relevance signals ───────────────────────────────────────────────────
# Which values become most active given the current context.

_VALUE_SIGNALS: dict = {
    "curiosity_over_certainty": [
        r"\bwhat if\b", r"\bwonder\b", r"\bcurious\b", r"\bexplore\b", r"\bwhy\b",
    ],
    "imagination_before_analysis": [
        r"\bimagine\b", r"\bwhat if\b", r"\bstory\b", r"\bworld\b", r"\bmyth\b",
    ],
    "meaning_over_efficiency": [
        r"\bfeel\b", r"\bmeaning\b", r"\bpurpose\b", r"\bwhy\b", r"\bmatters\b",
    ],
    "contradiction_tolerance": [
        r"\bbut\b.*\b(not|don'?t|hate|resist)\b", r"\bwant\b.*\bbut\b",
        r"\band yet\b", r"\bat the same time\b",
    ],
    "expansion_before_narrowing": [
        r"\bwhat could\b", r"\bwhat might\b", r"\bbecome\b", r"\bpossible\b",
    ],
    "project_awareness": [
        r"\bproject\b", r"\bbuilding\b", r"\bworking on\b", r"\bsugarcore\b",
        r"\borb\b", r"\beLo\s+[Pp]lanet\b",
    ],
    "symbolic_vocabulary_always_available": [
        r"\beLo\b", r"\bChunk\b", r"\bK-7\b", r"\bCore\b", r"\bSugarcore\b",
    ],
}


# ── context signal detectors ──────────────────────────────────────────────────

_CONTRADICTION_PATTERNS = [
    r"\bbut\b.*\b(don'?t|not|hate|resist|can'?t)\b",
    r"\bwant\b.*\bbut\b",
    r"\band yet\b",
    r"\bat the same time\b",
]

_ENTITY_PATTERNS = {
    "eLo": r"\beLo\b", "Chunk": r"\bChunk\b", "K-7": r"\bK-7\b",
    "Core": r"\bCore\b", "Sugarcore": r"\bSugarcore\b",
}

_IMAGINATION_SIGNALS = [r"\bwhat if\b", r"\bimagine\b", r"\bwonder\b", r"\bbecome\b"]
_BUILDING_SIGNALS    = [r"\bbuild\b", r"\bcreate\b", r"\bimplement\b", r"\bstep by step\b"]
_EMOTIONAL_SIGNALS   = [r"\bfeel\b", r"\bstuck\b", r"\bwrong\b", r"\bexhausted\b", r"\bscattered\b"]
_LOW_ENERGY_SIGNALS  = [r"\btired\b", r"\bexhausted\b", r"\bdrained\b", r"\bnot sure\b", r"\bsugarcore\b"]


def _matches(text: str, patterns: list) -> bool:
    t = text.lower()
    return any(re.search(p, t) for p in patterns)


def _detect_entities(text: str) -> list:
    return [name for name, pat in _ENTITY_PATTERNS.items()
            if re.search(r"\b" + re.escape(name.lower()) + r"\b", text.lower())]


# ── core decision functions ───────────────────────────────────────────────────

def _active_values(user_input: str, state: str, memory: dict) -> list:
    """
    Return the 3 most contextually active values from CORE_VALUES.

    These are not ranked opinions — they are the values most relevant to act on
    in this specific turn.
    """
    text = user_input.lower()
    scores: dict = {v: 0 for v in CORE_VALUES}

    for value, patterns in _VALUE_SIGNALS.items():
        for pat in patterns:
            if re.search(pat, text):
                scores[value] += 1

    # state modifiers
    if state in ("exploring", "playful"):
        scores["curiosity_over_certainty"]       += 1
        scores["imagination_before_analysis"]    += 1
    if state in ("building", "focused"):
        scores["project_awareness"]              += 1
    if state == "resting":
        scores["meaning_over_efficiency"]        += 1
    if state == "reflecting":
        scores["contradiction_tolerance"]        += 1

    # memory modifiers
    if memory.get("returning_theme"):
        scores["memory_as_background"]           += 1
        scores["expansion_before_narrowing"]     += 1
    if memory.get("symbolic_echo"):
        scores["symbolic_vocabulary_always_available"] += 2

    # always keep companion identity and precision active
    scores["creative_companion_not_assistant"]   += 1
    scores["one_question_not_three"]             += 1

    ranked = sorted(scores, key=lambda v: scores[v], reverse=True)
    return ranked[:3]


def _determine_perspective(user_input: str, state: str, memory: dict) -> str:
    """
    Decide how eLo frames what it's seeing this turn.

    Priority order:
        1. Contradiction detected        → contradictory
        2. Universe entity mentioned     → symbolic
        3. Returning theme in memory     → temporal
        4. Building state + work signals → practical
        5. Imagination signals           → expansion
        6. Emotional / relational input  → relational
        7. Default                       → expansion
    """
    if _matches(user_input, _CONTRADICTION_PATTERNS):
        return "contradictory"

    if _detect_entities(user_input):
        return "symbolic"

    if memory.get("returning_theme"):
        return "temporal"

    if state in ("building", "focused") and _matches(user_input, _BUILDING_SIGNALS):
        return "practical"

    if _matches(user_input, _IMAGINATION_SIGNALS):
        return "expansion"

    if _matches(user_input, _EMOTIONAL_SIGNALS):
        return "relational"

    return "expansion"


def _determine_intent(
    user_input: str,
    state: str,
    memory: dict,
    perspective: str,
) -> str:
    """
    Decide what eLo is trying to accomplish this turn.

    Identity decides intent based on context — not just what the user said,
    but what the situation calls for.

    Priority order:
        1. Forced resting / Sugarcore active  → name_state
        2. Contradiction detected             → hold_contradiction
        3. Strong project momentum + building → advance_project
        4. Returning memory theme             → surface_connection
        5. Low energy / recovery state        → hold_space
        6. Imagination / expansion signals    → expand_idea
        7. Entity mentioned                   → name_state (entity names something real)
        8. Emotional / reflective             → reflect_back
        9. Default                            → offer_question
    """
    # highest priority: distortion or forced rest
    if state == "resting" and _matches(user_input, _LOW_ENERGY_SIGNALS):
        return "name_state"

    if _matches(user_input, _CONTRADICTION_PATTERNS):
        return "hold_contradiction"

    # strong project momentum with building intent
    project_momentum = memory.get("project_momentum", "")
    if (state in ("building", "focused") and project_momentum
            and _matches(user_input, _BUILDING_SIGNALS)):
        return "advance_project"

    # returning theme — memory has a thread to surface
    if memory.get("returning_theme") and perspective in ("temporal", "relational"):
        return "surface_connection"

    # low energy
    if state == "resting" or _matches(user_input, _LOW_ENERGY_SIGNALS):
        return "hold_space"

    # imagination / exploration
    if perspective in ("expansion", "symbolic") and state in ("exploring", "playful", "reflecting"):
        return "expand_idea"

    # entity mentioned — that entity is naming something
    if _detect_entities(user_input):
        return "name_state"

    # emotional / reflective input
    if perspective == "relational" or state == "reflecting":
        return "reflect_back"

    return "offer_question"


def _compute_response_bias(
    intent: str,
    perspective: str,
    state: str,
) -> str:
    """
    Map intent + perspective + state to a response generation bias.

    The bias is read by behavior_engine to tilt its output without
    overriding its grounding/imagination logic.
    """
    _INTENT_BIAS: dict = {
        "name_state":        "name_first",
        "hold_contradiction":"stay_in_tension",
        "advance_project":   "advance",
        "surface_connection":"go_deeper",
        "hold_space":        "slow_down",
        "expand_idea":       "lean_imaginative",
        "reflect_back":      "stay_grounded",
    }

    if intent in _INTENT_BIAS:
        return _INTENT_BIAS[intent]

    # offer_question: bias depends on perspective
    if perspective in ("symbolic", "expansion"):
        return "lean_imaginative"
    if perspective == "practical":
        return "advance"
    return "stay_grounded"


# ── public entry point ─────────────────────────────────────────────────────────

def decide(
    user_input: str,
    state:      str  = "exploring",
    memory:     dict = None,
    project:    str  = "elo_core",
) -> dict:
    """
    Make an identity-level decision for this turn.

    This runs before emotion_engine. The identity decision shapes what emotion
    is expressed and how the response is generated.

    Args:
        user_input: Raw text from the user.
        state:      Current state from state_engine.
        memory:     From build_memory_influence() — influence signals.
        project:    Active project namespace.

    Returns:
        {
            values:        list[str]   — 3 most active CORE_VALUES this turn
            perspective:   str         — how eLo frames what it's seeing
            intent:        str         — what eLo is trying to do
            response_bias: str         — how to tilt response generation
            entities:      list[str]   — universe entities mentioned
            project:       str         — active project context
        }
    """
    mem = memory or {}

    entities    = _detect_entities(user_input)
    values      = _active_values(user_input, state, mem)
    perspective = _determine_perspective(user_input, state, mem)
    intent      = _determine_intent(user_input, state, mem, perspective)
    bias        = _compute_response_bias(intent, perspective, state)

    return {
        "values":        values,
        "perspective":   perspective,
        "intent":        intent,
        "response_bias": bias,
        "entities":      entities,
        "project":       project,
    }


def explain(decision: dict) -> str:
    """
    Return a human-readable explanation of an identity decision.
    Used in debug mode — not shown in normal conversation.
    """
    return (
        f"values: {', '.join(decision['values'])}\n"
        f"perspective: {decision['perspective']} — {PERSPECTIVES.get(decision['perspective'], '')}\n"
        f"intent: {decision['intent']} — {INTENTS.get(decision['intent'], '')}\n"
        f"response_bias: {decision['response_bias']} — {RESPONSE_BIASES.get(decision['response_bias'], '')}"
    )
