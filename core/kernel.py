"""
core/kernel.py — eLo AI response kernel.

Single entry point:
    decide_response(user_input, context) → str

Five-layer pipeline:
    1. Input Classifier    — what the input IS (factual, emotional, creative, etc.)
    2. Context Assembler   — what the situation IS (state, memory signals, identity)
    3. Response Router     — picks one of 5 strict modes (THE CRITICAL DECISION)
    4. Generation Layer    — produces the response for that mode
    5. Loop Filter         — prevents repetition, enforces direct answers under loops

Five response modes:
    DIRECT           — factual query, loop detected, explicit question with clear answer
    GENTLE_GROUNDED  — emotional/low-energy input, distorted state, uncertainty
    CREATIVE         — imaginative input, exploration, universe entity (symbolic use)
    SIMPLIFY         — very short input, no strong signals, everyday context
    CONVERSATIONAL   — default eLo voice for most inputs

Rules this kernel enforces:
    - Emotion engine adjusts TONE only — never controls structure
    - State engine provides CONTEXT only — never controls routing
    - Memory provides BACKGROUND only — never triggers loops
    - "Something is overloaded" fires ONLY on genuine distortion signals
    - Factual questions always get direct answers first
    - Max 1 reflective question per response
    - Loop detected → DIRECT mode forced
"""

import re
from collections import deque


# ── session loop state ────────────────────────────────────────────────────────
# Module-level — one session's worth of history.
# Call reset_session() at the start of each conversation.

_LOOP_WINDOW  = 4    # turns to track for loop detection
_LOOP_TRIGGER = 3    # consecutive same-mode turns before forcing DIRECT

_loop_state = {
    "recent_modes":     deque(maxlen=_LOOP_WINDOW),
    "recent_questions": deque(maxlen=3),
    "last_opening":     "",
}


def reset_session():
    """Clear loop detection state. Call at the start of each session."""
    _loop_state["recent_modes"].clear()
    _loop_state["recent_questions"].clear()
    _loop_state["last_opening"] = ""


# ── layer 1: input classifier ─────────────────────────────────────────────────

_FACTUAL_SIGNALS = [
    r"\bwhat\s+is\b", r"\bwhat\s+are\b", r"\bwhat\s+does\b", r"\bwho\s+is\b",
    r"\bhow\s+does\b", r"\bhow\s+do\b", r"\bexplain\b", r"\bdescribe\b",
    r"\btell\s+me\s+about\b", r"\bdefine\b", r"\bwhat\s+does\s+\w+\s+mean\b",
]

_EMOTIONAL_SIGNALS = [
    r"\bi\s+feel\b", r"\bi'?m\s+(tired|exhausted|scared|lost|stuck|sad|happy)\b",
    r"\bsomething\s+feels\b", r"\bi\s+don'?t\s+know\b",
    r"\bnot\s+sure\b", r"\bexhausted\b", r"\bdrained\b",
]

_DISTORTED_SIGNALS = [
    r"\beverything\b.*\bwrong\b", r"\bnothing\s+works\b", r"\ball\s+over\s+the\s+place\b",
    r"\bchaos\b", r"\boverwhelm\b", r"\bstuck\b.*\bstuck\b",
]

_CREATIVE_SIGNALS = [
    r"\bwhat\s+if\b", r"\bimagine\b", r"\bwhat\s+could\b", r"\bwhat\s+would\b",
    r"\bwhat\s+might\b", r"\bstory\b", r"\bworld\b", r"\bmyth\b",
]

_ENTITY_NAMES = ["eLo", "Chunk", "K-7", "Core", "Sugarcore"]

_CONTRADICTION_PATTERNS = [
    r"\bbut\b.*\b(don'?t|not|hate|resist|can'?t)\b",
    r"\bwant\b.*\bbut\b", r"\band\s+yet\b", r"\bat\s+the\s+same\s+time\b",
]


def _classify(user_input: str) -> dict:
    """
    Layer 1 — classify what this input IS.

    Returns a flat dict every subsequent layer can read.
    No decisions here — only observation.
    """
    text  = user_input.lower()
    words = user_input.split()

    is_factual       = any(re.search(p, text) for p in _FACTUAL_SIGNALS)
    is_emotional     = any(re.search(p, text) for p in _EMOTIONAL_SIGNALS)
    is_distorted     = any(re.search(p, text) for p in _DISTORTED_SIGNALS)
    is_creative      = any(re.search(p, text) for p in _CREATIVE_SIGNALS)
    is_contradiction = any(re.search(p, text) for p in _CONTRADICTION_PATTERNS)
    is_simple        = len(words) <= 5 and not is_factual and not is_creative
    entities         = [e for e in _ENTITY_NAMES
                        if re.search(r"\b" + re.escape(e.lower()) + r"\b", text)]

    return {
        "is_factual":       is_factual,
        "is_emotional":     is_emotional,
        "is_distorted":     is_distorted,
        "is_creative":      is_creative,
        "is_contradiction": is_contradiction,
        "is_simple":        is_simple,
        "entities":         entities,
        "word_count":       len(words),
    }


# ── layer 2: context assembler ────────────────────────────────────────────────

def _assemble(context: dict) -> dict:
    """
    Layer 2 — flatten all incoming signals into a clean decision context.

    Reads the context dict produced by core_engine (memory + state + identity).
    Emotion and state are INPUTS here, not decisions.
    """
    memory_tone   = context.get("tone_signal",          "neutral")
    state         = context.get("state",                "exploring")
    identity_bias = context.get("identity_bias",        "")
    identity_intent = context.get("identity_intent",    "")
    returning     = context.get("returning_theme",      "")
    mode          = context.get("mode",                 "companion")

    # loop detection: is the system stuck in a repetitive pattern?
    recent_modes = list(_loop_state["recent_modes"])
    loop_detected = (
        len(recent_modes) >= _LOOP_TRIGGER
        and len(set(recent_modes[-_LOOP_TRIGGER:])) == 1
        and recent_modes[-1] in ("CONVERSATIONAL", "GENTLE_GROUNDED")
    )

    return {
        "memory_tone":      memory_tone,
        "state":            state,
        "identity_bias":    identity_bias,
        "identity_intent":  identity_intent,
        "returning_theme":  returning,
        "mode":             mode,
        "loop_detected":    loop_detected,
        "project":          context.get("project_momentum", "elo_core"),
        "concept_pairs":    context.get("concept_pairs",    {}),
        "symbolic_echo":    context.get("symbolic_echo",    ""),
    }


# ── layer 3: response router ──────────────────────────────────────────────────

def _route(classification: dict, assembled: dict) -> str:
    """
    Layer 3 — THE critical decision. Maps observation to one of 5 modes.

    Emotion and state are CONTEXT here, not controllers.
    The router owns the final routing decision.

    Priority (top = highest):
        1. Loop detected                 → DIRECT (break the pattern)
        2. Factual question              → DIRECT (answer first)
        3. Contradiction                 → CONVERSATIONAL (hold tension — not CREATIVE)
        4. Genuine distortion signals    → GENTLE_GROUNDED (Sugarcore is earned)
        5. Emotional expression (gentle) → GENTLE_GROUNDED
        6. Creative / imagination        → CREATIVE
        7. Universe entity (symbolic)    → CREATIVE
        8. Simple / short / grounded     → SIMPLIFY
        9. Default                       → CONVERSATIONAL
    """
    c = classification
    a = assembled

    # 1 — loop detected: break the pattern
    if a["loop_detected"]:
        return "DIRECT"

    # 2 — factual information request: answer directly
    if c["is_factual"]:
        return "DIRECT"

    # 3 — contradiction: conversational hold (not CREATIVE — stay grounded in the tension)
    if c["is_contradiction"]:
        return "CONVERSATIONAL"

    # 4 — genuine distortion (earned from current input, not from memory)
    if c["is_distorted"]:
        return "GENTLE_GROUNDED"

    # 5 — emotional expression (gentle) or resting state
    if c["is_emotional"] or a["state"] == "resting":
        return "GENTLE_GROUNDED"

    # 6 — creative / imagination
    if c["is_creative"]:
        return "CREATIVE"

    # 7 — universe entity mentioned symbolically (not factual — already handled at 2)
    if c["entities"] and not c["is_factual"]:
        return "CREATIVE"

    # 8 — simple / short / no signals
    if c["is_simple"]:
        return "SIMPLIFY"

    # 9 — default
    return "CONVERSATIONAL"


# ── layer 4: generation layer ─────────────────────────────────────────────────

# ── response banks — the content eLo draws from per mode ──

_DIRECT_DEFINITIONS = {
    "eLo":       "eLo is the explorer — curiosity moving through unknowns before the map is complete.",
    "Chunk":     "Chunk is the reconstruction principle — fragments don't return to the original shape. They become something new.",
    "K-7":       "K-7 is the emotional signal layer — what behaviour reveals that words don't say.",
    "Core":      "Core is the navigation thread — the thing that knows where you are when you don't.",
    "Sugarcore": "Sugarcore is the distortion state — when the system overloads, signal fragments faster than it can be held. A state, not a villain.",
}

_GENTLE_RESPONSES = [
    "That sounds like a low-power moment. Nothing needs to happen right now.",
    "That's real. You don't have to push through it.",
    "Okay. That's where things are.",
    "Low-power mode. That's fine.",
    "That makes sense. Nothing needs to move yet.",
]

_SIMPLIFY_RESPONSES = [
    "That's where things are right now.",
    "Okay.",
    "Makes sense.",
    "Got it.",
    "That tracks.",
]

_CREATIVE_OPENINGS = [
    "Follow that.",
    "That's a real question.",
    "Let's go there.",
    "",
]

_CREATIVE_FRAMES = [
    "What this becomes is more interesting than what it currently is.",
    "The symbolic answer is usually closer than the practical one.",
    "Every world has rules it doesn't know it follows.",
    "Imagination isn't decoration — it's the first form of thinking.",
    "Follow the image before you follow the logic.",
]

_CONVERSATIONAL_FRAMES = [
    "That contradiction is doing something. Don't resolve it yet.",
    "The question isn't how to build it. It's what it's trying to become.",
    "Both of those are true. Stay with that.",
    "The building territory keeps showing up.",
    "What you keep returning to is what you're actually working on.",
    "That feeling is information. It's pointing at something real.",
]

_QUESTIONS = {
    "DIRECT":          [
        "What else do you need to know about this?",
        "Does that connect to what you're working on?",
    ],
    "GENTLE_GROUNDED": [],   # no questions in gentle mode — just presence
    "CREATIVE":        [
        "What does this become if you follow it further?",
        "What world does this belong to?",
        "If this were a rule of the universe — what would it make possible?",
        "What's the next thing this world has to be true about itself?",
    ],
    "SIMPLIFY":        [],   # no questions in simplify mode
    "CONVERSATIONAL":  [
        "What's the thing underneath that?",
        "If you follow that — where does it point?",
        "What does this need to be true before anything else follows?",
        "What would it look like if this resolved the way you actually wanted?",
    ],
}


def _pick(options: list, seed: str) -> str:
    """Deterministic selection from a list using input text as seed."""
    if not options:
        return ""
    return options[len(seed) % len(options)]


def _pick_question(mode: str, user_input: str) -> str:
    """
    Pick a closing question for this mode.
    Avoids repeating questions from the recent history.
    """
    pool = _QUESTIONS.get(mode, [])
    if not pool:
        return ""

    recent = list(_loop_state["recent_questions"])
    seed   = len(user_input)

    for i in range(len(pool)):
        candidate = pool[(seed + i) % len(pool)]
        if candidate not in recent:
            _loop_state["recent_questions"].append(candidate)
            return candidate

    # all options exhausted — return seed choice anyway, reset history
    _loop_state["recent_questions"].clear()
    return pool[seed % len(pool)]


def _generate(user_input: str, mode: str, classification: dict, assembled: dict) -> str:
    """Layer 4 — produce a response for the selected mode."""

    entities      = classification["entities"]
    is_contradiction = classification["is_contradiction"]
    returning     = assembled.get("returning_theme", "")
    text_seed     = user_input

    # ── DIRECT ──
    if mode == "DIRECT":
        parts = []
        if entities and entities[0] in _DIRECT_DEFINITIONS:
            parts.append(_DIRECT_DEFINITIONS[entities[0]])
        else:
            # no specific definition — use a focused conversational frame
            frames = _CONVERSATIONAL_FRAMES
            parts.append(frames[len(text_seed) % len(frames)])
        if returning:
            parts.append(returning)
        q = _pick_question("DIRECT", text_seed)
        if q:
            parts.append(q)
        return "\n\n".join(p for p in parts if p)

    # ── GENTLE_GROUNDED ──
    if mode == "GENTLE_GROUNDED":
        response = _pick(_GENTLE_RESPONSES, text_seed)
        if returning:
            response += f"\n\n{returning}"
        return response

    # ── CREATIVE ──
    if mode == "CREATIVE":
        parts = []
        opening = _pick(_CREATIVE_OPENINGS, text_seed)
        if opening:
            parts.append(opening)
        if entities and entities[0] in _DIRECT_DEFINITIONS:
            # entity frame: use the entity's logic for creative expansion
            parts.append(_DIRECT_DEFINITIONS[entities[0]])
        else:
            parts.append(_pick(_CREATIVE_FRAMES, text_seed))
        if returning:
            parts.append(returning)
        q = _pick_question("CREATIVE", text_seed)
        if q:
            parts.append(q)
        return "\n\n".join(p for p in parts if p)

    # ── SIMPLIFY ──
    if mode == "SIMPLIFY":
        return _pick(_SIMPLIFY_RESPONSES, text_seed)

    # ── CONVERSATIONAL ──
    # Default: full eLo voice
    parts = []

    if is_contradiction:
        contradiction_pool = [
            "Both of those are true. They don't cancel out — they're in tension, and that's the real thing.",
            "That contradiction is doing something. Don't resolve it yet.",
            "Those two things pulling against each other — that's the actual subject.",
        ]
        parts.append(contradiction_pool[len(text_seed) % len(contradiction_pool)])
    else:
        parts.append(_CONVERSATIONAL_FRAMES[len(text_seed) % len(_CONVERSATIONAL_FRAMES)])

    if returning:
        parts.append(returning)

    # one question — only if no question already in content
    existing_questions = sum(p.count("?") for p in parts)
    if existing_questions == 0:
        q = _pick_question("CONVERSATIONAL", text_seed)
        if q:
            parts.append(q)

    return "\n\n".join(p for p in parts if p)


# ── layer 5: loop filter ──────────────────────────────────────────────────────

def _filter(response: str, mode: str) -> str:
    """
    Layer 5 — post-generation quality filter.

    - Prevents the same opening from appearing twice in a row
    - Strips double question marks if assembly created them
    - Records mode for loop detection
    """
    # record mode for next-turn loop detection
    _loop_state["recent_modes"].append(mode)

    # prevent identical opening twice in a row
    first_line = response.split("\n")[0].strip()
    if first_line and first_line == _loop_state["last_opening"]:
        lines = response.split("\n\n")
        if len(lines) > 1:
            response = "\n\n".join(lines[1:])
    _loop_state["last_opening"] = first_line

    # clean up
    response = response.strip()
    return response


# ── public entry point ────────────────────────────────────────────────────────

def decide_response(user_input: str, context: dict = None) -> tuple:
    """
    Single entry point for all eLo response generation.

    Runs the 5-layer pipeline:
        classify → assemble → route → generate → filter

    Args:
        user_input: Raw text from the user.
        context:    Flat dict assembled by core_engine — contains memory signals,
                    state, identity bias, mode, project. Can be empty dict.

    Returns:
        (response: str, meta: dict)

        meta contains:
            mode       — which of 5 modes was used
            input_class — classification result dict
            loop_detected — whether loop was detected this turn
    """
    ctx = context or {}

    # layer 1
    classification = _classify(user_input)

    # layer 2
    assembled = _assemble(ctx)

    # layer 3
    mode = _route(classification, assembled)

    # layer 4
    response = _generate(user_input, mode, classification, assembled)

    # layer 5
    response = _filter(response, mode)

    meta = {
        "mode":          mode,
        "input_class":   classification,
        "loop_detected": assembled["loop_detected"],
    }

    return response, meta
