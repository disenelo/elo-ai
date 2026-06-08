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

_LOOP_WINDOW  = 4    # turns to track
_LOOP_TRIGGER = 3    # consecutive same-mode turns before forcing DIRECT

_loop_state = {
    "recent_modes":              deque(maxlen=_LOOP_WINDOW),
    "recent_questions":          deque(maxlen=4),
    "last_opening":              "",
    "recent_fragments":          deque(maxlen=4),  # first-sentence of each response
    "reflection_disabled_turns": 0,                # countdown: >0 = reflection disabled
}

# ── reflective question fingerprints ──────────────────────────────────────────
# These fragments identify responses that are pure reflective questions.
# Three or more consecutive responses matching these = recursive reflection loop.

_REFLECTIVE_FINGERPRINTS = [
    r"what does that feel like",
    r"what'?s the thing underneath",
    r"if you follow that",
    r"where does it point",
    r"what would it look like",
    r"what needs to be true",
    r"what'?s underneath",
    r"what does this need to",
    r"what'?s blocking",
    r"where has this been",
]


def reset_session():
    """Clear all loop detection state. Call at the start of each session."""
    _loop_state["recent_modes"].clear()
    _loop_state["recent_questions"].clear()
    _loop_state["recent_fragments"].clear()
    _loop_state["last_opening"] = ""
    _loop_state["reflection_disabled_turns"] = 0


def _extract_fragment(response: str) -> str:
    """Extract the first sentence (up to 60 chars) as the response fingerprint."""
    for sep in (".\n", ".\r", ".\t", "?", "!"):
        idx = response.find(sep)
        if 0 < idx <= 80:
            return response[: idx + 1].strip().lower()
    return response[:60].strip().lower()


def _is_reflective(fragment: str) -> bool:
    """Return True if the fragment matches a known reflective question pattern."""
    return any(re.search(p, fragment) for p in _REFLECTIVE_FINGERPRINTS)


def _normalized_question(text: str) -> str:
    """Normalize a question for comparison: lowercase, no punctuation."""
    return re.sub(r"[^a-z0-9\s]", "", text.lower()).strip()


def record_response(response: str):
    """
    Register a generated response into the loop detection state.
    Call immediately after generate_response() returns.

    Also decrements the reflection_disabled_turns countdown.
    """
    fragment = _extract_fragment(response)
    _loop_state["recent_fragments"].append(fragment)

    # extract and record any closing question
    sentences = re.split(r"[.!?]", response)
    for s in reversed(sentences):
        s = s.strip()
        if s.endswith("?") or re.search(r"\bwhat\b|\bwhere\b|\bhow\b|\bwhy\b", s.lower()):
            _loop_state["recent_questions"].append(_normalized_question(s))
            break

    # decrement reflection cooldown
    if _loop_state["reflection_disabled_turns"] > 0:
        _loop_state["reflection_disabled_turns"] -= 1


def detect_loop() -> dict:
    """
    Detect conversational loops from session history.

    Checks three independent patterns:

    1. REPEATED_PHRASE
       The same response fragment (first sentence) appears in 2+ of the
       last 3 responses. eLo is saying the same thing twice.

    2. REPEATED_QUESTION
       The same question structure (normalized) appears in 2+ of the
       last 3 recorded questions. eLo is asking the same thing twice.

    3. RECURSIVE_REFLECTION
       The last 3 responses all match known reflective question patterns.
       eLo has entered a pure questioning spiral.

    4. MODE_STAGNATION (existing)
       The last _LOOP_TRIGGER turns all have the same mode (CONVERSATIONAL
       or GENTLE_GROUNDED). Structural repetition at the routing level.

    Returns:
        {
            "detected":            bool,
            "reason":              str,   # which pattern triggered, or ""
            "force_direct":        bool,  # same as detected
            "reflection_disabled": bool,  # True if disabled countdown > 0
        }
    """
    fragments  = list(_loop_state["recent_fragments"])
    questions  = list(_loop_state["recent_questions"])
    modes      = list(_loop_state["recent_modes"])
    refl_off   = _loop_state["reflection_disabled_turns"] > 0

    reason = ""

    # 1 — repeated phrase
    if len(fragments) >= 3:
        last3 = fragments[-3:]
        if len(set(last3)) < len(last3):   # any duplicates
            reason = "repeated_phrase"

    # 2 — repeated question
    if not reason and len(questions) >= 3:
        last3q = questions[-3:]
        if len(set(last3q)) < len(last3q):
            reason = "repeated_question"

    # 3 — recursive reflection
    if not reason and len(fragments) >= 3:
        last3 = fragments[-3:]
        if all(_is_reflective(f) for f in last3):
            reason = "recursive_reflection"

    # 4 — mode stagnation
    if not reason and len(modes) >= _LOOP_TRIGGER:
        last_n = modes[-_LOOP_TRIGGER:]
        if (len(set(last_n)) == 1 and last_n[-1] in ("CONVERSATIONAL", "GENTLE_GROUNDED")):
            reason = "mode_stagnation"

    detected = bool(reason)

    # when loop is detected, arm the reflection cooldown for next turn
    if detected and not refl_off:
        _loop_state["reflection_disabled_turns"] = 1

    return {
        "detected":            detected,
        "reason":              reason,
        "force_direct":        detected,
        "reflection_disabled": refl_off or detected,
    }


# ── layer 1: input classifier ─────────────────────────────────────────────────
#
# Signal tables used by both _classify() (internal) and classify_input() (public).
# No imports, no state, no LLM — pure regex over the input string.

_FACTUAL_SIGNALS = [
    r"\bwhat\s+is\b", r"\bwhat\s+are\b", r"\bwhat\s+does\b", r"\bwho\s+is\b",
    r"\bhow\s+does\b", r"\bhow\s+do\b", r"\bexplain\b", r"\bdescribe\b",
    r"\btell\s+me\s+about\b", r"\bdefine\b", r"\bwhat\s+does\s+\w+\s+mean\b",
    r"\bwhat\s+was\b", r"\bwhat\s+happened\b",
]

_PROJECT_SIGNALS = [
    # eLo universe project names
    r"\bsugarcore\s+arc\b", r"\borb\s+(system|device)\b",
    r"\beLo\s+[Pp]lanet\b", r"\beLo\s+[Uu]niverse\b",
    r"\bidentity\s+engine\b", r"\bmemory\s+engine\b", r"\bstate\s+engine\b",
    r"\bbehavior\s+engine\b", r"\bkernel\b",
    # generic project language
    r"\bmy\s+project\b", r"\bworking\s+on\b", r"\bbuilding\s+a\b",
    r"\bthe\s+system\b", r"\bthe\s+app\b", r"\bthe\s+game\b",
    r"\barchitecture\b", r"\bpipeline\b", r"\bmodule\b", r"\bfeature\b",
    r"\bimplementation\b", r"\brefactor\b",
]

_EMOTIONAL_SIGNALS = [
    # personal emotional state — "I feel X" or "I'm [emotion]"
    r"\bi\s+feel\b",
    r"\bi'?m\s+(tired|exhausted|scared|lost|stuck|sad|happy|confused)\b",
    r"\bsomething\s+feels\b",
    r"\bexhausted\b", r"\bdrained\b",
    r"\bi\s+am\s+(tired|lost|stuck|scared)\b",
    # "I don't know" is emotional when there's no uncertainty qualifier
    r"\bi\s+just\s+don'?t\s+know\b",
    # NOTE: "not sure" and "I don't know" alone → UNCERTAINTY (removed from here)
]

_DISTORTED_SIGNALS = [
    r"\beverything\b.*\bwrong\b", r"\bnothing\s+works\b", r"\ball\s+over\s+the\s+place\b",
    r"\bchaos\b", r"\boverwhelm\b", r"\bstuck\b.*\bstuck\b",
]

_CREATIVE_SIGNALS = [
    r"\bwhat\s+if\b", r"\bimagine\b", r"\bwhat\s+could\b", r"\bwhat\s+would\b",
    r"\bwhat\s+might\b", r"\bstory\b", r"\bworld\b", r"\bmyth\b",
    r"\bnarrative\b", r"\blore\b", r"\buniverse\b", r"\bcharacter\b",
    r"\bdesign\s+a\b", r"\bcreate\s+a\b",
]

_UNCERTAINTY_SIGNALS = [
    r"\bnot\s+sure\b", r"\bmaybe\b", r"\bi\s+don'?t\s+know\b",
    r"\buncertain\b", r"\bconfused\b", r"\bdon'?t\s+understand\b",
    r"\bnot\s+clear\b", r"\bnot\s+sure\s+(how|what|where|why)\b",
    r"\bnot\s+certain\b", r"\bperhaps\b",
]

_CONTRADICTION_PATTERNS = [
    r"\bbut\b.*\b(don'?t|not|hate|resist|can'?t)\b",
    r"\bwant\b.*\bbut\b", r"\band\s+yet\b", r"\bat\s+the\s+same\s+time\b",
    r"\bcontradicts\b", r"\bcontradiction\b",
    r"\bboth\b.*\btrue\b", r"\bopposite\b.*\btrue\b",
]

# Technical vocabulary — raises complexity score
_TECHNICAL_SIGNALS = [
    r"\bengine\b", r"\barchitecture\b", r"\bpipeline\b", r"\bkernel\b",
    r"\bmodule\b", r"\binterface\b", r"\bimplementation\b", r"\brefactor\b",
    r"\bclass\b", r"\bfunction\b", r"\bapi\b", r"\bdataclass\b",
    r"\bstate\s+machine\b", r"\bdependency\b",
]

_ENTITY_NAMES = ["eLo", "Chunk", "K-7", "Core", "Sugarcore"]

_STOPWORDS = {
    "the", "a", "an", "is", "it", "in", "on", "at", "to", "of",
    "and", "or", "but", "i", "my", "me", "this", "that", "for",
    "with", "be", "so", "do", "not", "was", "are", "have",
}


def _count_signals(*signal_lists) -> int:
    """Count how many distinct signal lists match (not how many patterns match)."""
    return sum(1 for signals in signal_lists if signals)


def _classify(user_input: str) -> dict:
    """
    Layer 1 — internal classification dict used by the routing pipeline.
    Returns boolean flags; consumed by _route() and _generate().
    """
    text  = user_input.lower()
    words = user_input.split()

    is_factual       = any(re.search(p, text) for p in _FACTUAL_SIGNALS)
    is_project       = any(re.search(p, text) for p in _PROJECT_SIGNALS)
    is_emotional     = any(re.search(p, text) for p in _EMOTIONAL_SIGNALS)
    is_distorted     = any(re.search(p, text) for p in _DISTORTED_SIGNALS)
    is_creative      = any(re.search(p, text) for p in _CREATIVE_SIGNALS)
    is_uncertainty   = any(re.search(p, text) for p in _UNCERTAINTY_SIGNALS)
    is_contradiction = any(re.search(p, text) for p in _CONTRADICTION_PATTERNS)
    is_simple        = len(words) <= 5 and not is_factual and not is_creative and not is_project
    entities         = [e for e in _ENTITY_NAMES
                        if re.search(r"\b" + re.escape(e.lower()) + r"\b", text)]

    return {
        "is_factual":       is_factual,
        "is_project":       is_project,
        "is_emotional":     is_emotional,
        "is_distorted":     is_distorted,
        "is_creative":      is_creative,
        "is_uncertainty":   is_uncertainty,
        "is_contradiction": is_contradiction,
        "is_simple":        is_simple,
        "entities":         entities,
        "word_count":       len(words),
    }


# ── Types and complexity values ────────────────────────────────────────────────

INPUT_TYPES = (
    "INFORMATION_REQUEST",
    "PROJECT_QUERY",
    "EMOTIONAL",
    "CREATIVE",
    "UNCERTAINTY",
    "CONVERSATION",
)

COMPLEXITY_LEVELS = ("LOW", "MEDIUM", "HIGH")


def _resolve_type(flags: dict) -> str:
    """
    Map boolean flags to one of the six canonical input types.

    Priority (first match wins):
        1. INFORMATION_REQUEST — factual "what is / who is / how does" questions
        2. PROJECT_QUERY       — project-specific, system, architecture references
        3. EMOTIONAL           — personal state expression (tired, lost, feeling)
        4. CREATIVE            — imagination, world-building, "what if"
        5. UNCERTAINTY         — not sure, confused, unclear direction
        6. CONVERSATION        — default for everything else
    """
    if flags["is_factual"]:
        return "INFORMATION_REQUEST"
    if flags["is_project"]:
        return "PROJECT_QUERY"
    if flags["is_emotional"] or flags["is_distorted"]:
        return "EMOTIONAL"
    if flags["is_creative"] or (flags["entities"] and not flags["is_factual"]):
        return "CREATIVE"
    if flags["is_uncertainty"]:
        return "UNCERTAINTY"
    return "CONVERSATION"


def _resolve_complexity(flags: dict, input_type: str) -> str:
    """
    Determine complexity from structural signals in the input.

    LOW:
        - ≤ 5 words with no strong signals (simple / grounded)
        - Factual question ≤ 8 words with a single signal (short lookup)
        - UNCERTAINTY type ≤ 10 words (expressions of not-knowing are inherently simple)

    HIGH:
        - ≥ 15 words
        - OR contradiction detected
        - OR 3+ distinct signal types match
        - OR technical vocabulary present
        - OR entities + creative framing AND word count ≥ 10

    MEDIUM:
        - everything else
    """
    word_count       = flags["word_count"]
    text             = flags.get("_text", "")
    signal_count     = _count_signals(
        flags["is_factual"],   flags["is_project"],
        flags["is_emotional"], flags["is_creative"],
        flags["is_uncertainty"],
    )
    has_technical       = any(re.search(p, text) for p in _TECHNICAL_SIGNALS)
    has_entity_creative = bool(flags["entities"]) and flags["is_creative"] and word_count >= 10
    has_contradiction   = flags["is_contradiction"]

    # LOW — short, single-concept inputs
    if flags["is_simple"] and word_count <= 5:
        return "LOW"
    if input_type == "INFORMATION_REQUEST" and word_count <= 7:
        return "LOW"
    if input_type == "UNCERTAINTY" and word_count <= 10 and not has_technical:
        return "LOW"

    # HIGH — complex, multi-signal, long, or technical
    if (
        word_count >= 15
        or has_contradiction
        or signal_count >= 3
        or has_technical
        or has_entity_creative
    ):
        return "HIGH"

    return "MEDIUM"


def classify_input(user_input: str) -> dict:
    """
    Public classifier — deterministic, rule-based, no external dependencies.

    Returns:
        {
            "type":       INFORMATION_REQUEST | PROJECT_QUERY | EMOTIONAL
                          | CREATIVE | UNCERTAINTY | CONVERSATION,
            "complexity": LOW | MEDIUM | HIGH
        }

    Rules:
        - No LLM calls
        - No memory access
        - No state access
        - Same input always returns same output
        - O(n) in pattern count × input length

    Examples:
        "what does Chunk mean?"          → {type: INFORMATION_REQUEST, complexity: LOW}
        "let's refactor the kernel"      → {type: PROJECT_QUERY,       complexity: MEDIUM}
        "I am exhausted"                 → {type: EMOTIONAL,           complexity: LOW}
        "what if Sugarcore became a place" → {type: CREATIVE,          complexity: MEDIUM}
        "I'm not sure where to start"    → {type: UNCERTAINTY,         complexity: LOW}
        "hello"                          → {type: CONVERSATION,        complexity: LOW}
        "I want structure but no rules"  → {type: CONVERSATION,        complexity: HIGH}
    """
    flags         = _classify(user_input)
    flags["_text"] = user_input.lower()   # pass raw text for technical signal check
    input_type    = _resolve_type(flags)
    complexity    = _resolve_complexity(flags, input_type)

    return {
        "type":       input_type,
        "complexity": complexity,
    }


# ── layer 2: context assembler ────────────────────────────────────────────────

def assemble_context(raw_context: dict) -> dict:
    """
    Layer 2 — build a clean, informational context dict for the router.

    Gathers memory summary, current state, identity profile, and active projects.

    Rules:
        - Memory signals are INFORMATIONAL only — they do NOT influence routing
        - State is INFORMATIONAL only — it does NOT override routing decisions
        - This dict is read-only from the router's perspective
        - No decisions are made here — only observations are collected

    Args:
        raw_context: The flat dict assembled by core_engine (memory + state + identity).

    Returns:
        Clean context dict with explicit, named fields.
    """
    # ── memory summary (lightweight — no raw records, no blocks) ──
    memory_summary = {
        "tone":            raw_context.get("tone_signal",        "neutral"),
        "returning_theme": raw_context.get("returning_theme",    ""),
        "symbolic_echo":   raw_context.get("symbolic_echo",      ""),
        "project":         raw_context.get("project_momentum",   "elo_core"),
    }

    # ── current state (from state_engine — informational only) ──
    state_summary = {
        "name":             raw_context.get("state",              "exploring"),
        "imagination_level":raw_context.get("imagination_level",  "medium"),
        "response_length":  raw_context.get("response_length",    "medium"),
    }

    # ── identity profile (from identity_engine — informational only) ──
    identity_summary = {
        "intent":      raw_context.get("identity_intent",     ""),
        "perspective": raw_context.get("identity_perspective",""),
        "bias":        raw_context.get("identity_bias",       ""),
        "values":      raw_context.get("identity_values",     []),
    }

    # ── active projects (from project registry) ──
    active_projects = {
        "current": raw_context.get("project_momentum", "elo_core"),
        "pairs":   raw_context.get("concept_pairs",    {}),
    }

    # ── loop detection — full multi-pattern check ──
    loop = detect_loop()

    return {
        "memory":              memory_summary,
        "state":               state_summary,
        "identity":            identity_summary,
        "projects":            active_projects,
        "loop_detected":       loop["detected"],
        "loop_reason":         loop["reason"],
        "reflection_disabled": loop["reflection_disabled"],
        # flat aliases for backward compat with _route / _generate
        "memory_tone":     memory_summary["tone"],
        "returning_theme": memory_summary["returning_theme"],
        "symbolic_echo":   memory_summary["symbolic_echo"],
        "project":         memory_summary["project"],
        "concept_pairs":   active_projects["pairs"],
        "mode":            raw_context.get("mode", "companion"),
    }


# keep internal alias for pipeline compatibility
def _assemble(context: dict) -> dict:
    return assemble_context(context)


# ── layer 3: response router ──────────────────────────────────────────────────

# Mode vocabulary
MODES = (
    "DIRECT",           # factual question, loop detected
    "STRUCTURED",       # project query — organised, step-oriented
    "GENTLE_GROUNDED",  # emotional / distorted / resting
    "CREATIVE",         # imagination, world-building, entity
    "SIMPLIFY",         # short / simple / no signals
    "CONVERSATIONAL",   # default eLo voice
)


def route(classification: dict, context: dict) -> str:
    """
    Layer 3 — THE only decision-maker for response mode.

    Maps input type + context observations to one of 6 strict modes.

    Rules:
        - ONLY this function decides mode
        - Emotion does NOT override routing
        - State does NOT override routing
        - Memory does NOT override routing
        - Loop detection IS allowed to override (structural safety, not personality)
        - No exceptions

    Input type → default mode mapping:
        INFORMATION_REQUEST → DIRECT
        PROJECT_QUERY       → STRUCTURED
        EMOTIONAL           → GENTLE_GROUNDED
        CREATIVE            → CREATIVE
        UNCERTAINTY         → SIMPLIFY
        CONVERSATION        → CONVERSATIONAL

    Override conditions (checked first):
        1. Loop detected    → DIRECT (break repetition)
        2. Distortion       → GENTLE_GROUNDED (regardless of type)
    """
    input_type  = classification.get("type",         "CONVERSATION")
    is_distorted = classification.get("is_distorted", False)
    loop_detected = context.get("loop_detected",      False)

    # override 1: loop — break repetition with direct answer
    if loop_detected:
        return "DIRECT"

    # override 2: genuine distortion from current input — always ground first
    if is_distorted:
        return "GENTLE_GROUNDED"

    # direct type → mode map — no exceptions
    _TYPE_TO_MODE = {
        "INFORMATION_REQUEST": "DIRECT",
        "PROJECT_QUERY":       "STRUCTURED",
        "EMOTIONAL":           "GENTLE_GROUNDED",
        "CREATIVE":            "CREATIVE",
        "UNCERTAINTY":         "SIMPLIFY",
        "CONVERSATION":        "CONVERSATIONAL",
    }

    return _TYPE_TO_MODE.get(input_type, "CONVERSATIONAL")


# keep internal alias for pipeline compatibility
def _route(classification: dict, assembled: dict) -> str:
    # internal flags → public classification dict bridge
    pub_classification = {
        "type":         _resolve_type(classification),
        "is_distorted": classification.get("is_distorted", False),
    }
    return route(pub_classification, assembled)


# ── layer 4: generation layer ─────────────────────────────────────────────────
#
# Public API:
#   generate_response(mode, user_input, context)  →  str
#   set_backend(name)                             →  None
#
# The generation layer is backend-agnostic.
# It defines the interface; backends are registered separately.
# Swapping from offline to Claude to a local LLM does not touch this signature.

_ACTIVE_BACKEND: str  = "offline"
_BACKEND_REGISTRY: dict = {}    # name → callable(mode, user_input, context) → str


def set_backend(name: str, handler=None):
    """
    Register and activate a generation backend.

    Args:
        name:    Backend identifier — "offline" | "claude" | "local_llm" | any custom name.
        handler: Optional callable(mode, user_input, context) → str.
                 If omitted, the named backend must already be in the registry.

    Usage:
        # activate the built-in offline backend (default)
        set_backend("offline")

        # register and activate a custom backend
        set_backend("claude", handler=my_claude_fn)

        # activate a previously registered backend
        set_backend("local_llm")
    """
    global _ACTIVE_BACKEND
    if handler is not None:
        _BACKEND_REGISTRY[name] = handler
    _ACTIVE_BACKEND = name


def generate_response(mode: str, user_input: str, context: dict = None) -> str:
    """
    Generation layer — backend-agnostic entry point.

    Dispatches to the active backend. The caller never needs to know
    which backend is running — the interface is identical for all of them.

    Args:
        mode:       One of DIRECT | STRUCTURED | GENTLE_GROUNDED | CREATIVE
                         | SIMPLIFY | CONVERSATIONAL
        user_input: Raw text from the user.
        context:    Assembled context dict from assemble_context().

    Returns:
        Response string from the active backend.

    Backends:
        "offline"   — deterministic placeholder strings (default, no API needed)
        "claude"    — Anthropic Claude API (register via set_backend)
        "local_llm" — local model server (register via set_backend)
        custom      — any callable registered via set_backend
    """
    ctx = context or {}

    # custom registered backend
    if _ACTIVE_BACKEND in _BACKEND_REGISTRY:
        return _BACKEND_REGISTRY[_ACTIVE_BACKEND](mode, user_input, ctx)

    # built-in offline backend
    if _ACTIVE_BACKEND == "offline":
        return _generate_placeholder(mode, user_input, ctx)

    # unknown backend — fall through to placeholder
    return _generate_placeholder(mode, user_input, ctx)


def _generate_placeholder(mode: str, user_input: str, context: dict) -> str:
    """
    Offline placeholder generator.
    Returns mode-labelled strings — useful for testing the pipeline
    without any API dependency.

    Each placeholder includes the mode and a short echo of the input
    so the pipeline can be verified end-to-end.
    """
    input_echo = user_input[:40].strip() if user_input else ""
    project    = context.get("project", context.get("memory", {}).get("project", ""))
    project_tag = f" [{project}]" if project and project != "elo_core" else ""

    _PLACEHOLDERS = {
        "DIRECT":          f"[DIRECT]{project_tag} {input_echo}",
        "STRUCTURED":      f"[STRUCTURED]{project_tag} — working through: {input_echo}",
        "GENTLE_GROUNDED": f"[GENTLE_GROUNDED] That's real. Nothing needs to happen right now.",
        "CREATIVE":        f"[CREATIVE]{project_tag} Follow that: {input_echo}",
        "SIMPLIFY":        f"[SIMPLIFY] Okay.",
        "CONVERSATIONAL":  f"[CONVERSATIONAL]{project_tag} {input_echo}",
    }

    return _PLACEHOLDERS.get(mode, f"[{mode}] {input_echo}")


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

    - Records mode + response into loop detection state
    - Prevents identical opening from appearing twice in a row
    - Strips reflective question if reflection is disabled this turn
    """
    # record mode for mode-stagnation detection
    _loop_state["recent_modes"].append(mode)

    # record response fragment + question for content-level loop detection
    record_response(response)

    # strip reflective question if reflection is currently disabled
    if _loop_state["reflection_disabled_turns"] > 1:   # >1 because record_response decremented
        sentences = response.split("\n\n")
        cleaned = []
        for s in sentences:
            if s.strip().endswith("?") and _is_reflective(s.lower()):
                continue    # drop this reflective question
            cleaned.append(s)
        if cleaned:
            response = "\n\n".join(cleaned)

    # prevent identical opening twice in a row
    first_line = response.split("\n")[0].strip()
    if first_line and first_line == _loop_state["last_opening"]:
        lines = response.split("\n\n")
        if len(lines) > 1:
            response = "\n\n".join(lines[1:])
    _loop_state["last_opening"] = first_line

    return response.strip()


# ── debug mode ───────────────────────────────────────────────────────────────

_DEBUG_ENABLED: bool = False


def set_debug(enabled: bool):
    """Toggle kernel debug mode. Does not affect response content."""
    global _DEBUG_ENABLED
    _DEBUG_ENABLED = enabled


def _build_debug_block(
    user_input:     str,
    classification: dict,
    assembled:      dict,
    mode:           str,
    loop_result:    dict,
    context:        dict,
) -> str:
    """
    Build a debug metadata block.
    Appended after the response when debug is enabled.
    Never modifies the response itself.
    """
    ic = classification

    lines = [
        "",
        "──── DEBUG ────────────────────────────────",
        f"  input type   : {_resolve_type(ic)}",
        f"  complexity   : {_resolve_complexity(ic, _resolve_type(ic))}",
        f"  mode         : {mode}",
        f"  loop         : {loop_result['detected']} ({loop_result['reason'] or 'none'})",
        f"  state        : {assembled['state']['name']}",
        f"  memory tone  : {assembled['memory']['tone']}",
        f"  returning    : {assembled['memory']['returning_theme'] or 'none'}",
        f"  project      : {assembled['memory']['project']}",
        f"  emotion hint : {context.get('emotion', 'none')}",
        f"  reflection   : {'disabled' if assembled.get('reflection_disabled') else 'on'}",
        f"  entities     : {ic.get('entities') or 'none'}",
        "────────────────────────────────────────────",
    ]
    return "\n".join(lines)


# ── public entry point ────────────────────────────────────────────────────────

def decide_response(user_input: str, context: dict = None) -> tuple:
    """
    Single entry point for all eLo response generation.

    Runs the 5-layer pipeline:
        classify → assemble → route → generate → filter

    Args:
        user_input: Raw text from the user.
        context:    Flat dict assembled by core_engine. Can be empty dict.

    Returns:
        (response: str, meta: dict)

        When debug mode is on (set_debug(True)):
            response has a debug block appended after the content.
            The block starts with '──── DEBUG' and is clearly separated.
            It does not modify the conversational response.

        meta keys:
            mode              — one of 6 kernel modes
            input_class       — full classification dict
            loop_detected     — bool
            loop_reason       — str
            reflection_disabled — bool
    """
    ctx = context or {}

    # layer 1
    classification = _classify(user_input)
    classification["_text"] = user_input.lower()

    # layer 2
    assembled = _assemble(ctx)

    # layer 3
    mode = _route(classification, assembled)

    # loop check (for debug block — detect_loop already ran inside assemble)
    loop_result = {
        "detected": assembled["loop_detected"],
        "reason":   assembled.get("loop_reason", ""),
    }

    # layer 4
    response = _generate(user_input, mode, classification, assembled)

    # layer 5
    response = _filter(response, mode)

    # debug block (does not touch response content — appended separately)
    if _DEBUG_ENABLED:
        debug_block = _build_debug_block(
            user_input, classification, assembled, mode, loop_result, ctx
        )
        response = response + debug_block

    meta = {
        "mode":                mode,
        "input_class":         classification,
        "loop_detected":       assembled["loop_detected"],
        "loop_reason":         assembled.get("loop_reason", ""),
        "reflection_disabled": assembled.get("reflection_disabled", False),
    }

    return response, meta
