"""
offline_engine.py — eLo AI deterministic offline intelligence.

Generates structured responses without any API calls or external dependencies.
Same input always produces the same output.

5-phase reasoning simulation:
    1. Interpretation   — classify input type, emotion, concepts, symbols
    2. Memory recall    — filter structured memory for what's relevant
    3. Identity filter  — apply system_prompt personality rules
    4. Creative transform — imagination-first framing, symbolic engagement
    5. Output assembly  — opening + core insight + closing question

Entry point:
    generate_offline_response(user_input, memory, mode) -> str
    generate_offline_response(user_input, memory, mode, debug=True) -> (str, dict)
"""

import re
from typing import Union


# ── constants ──────────────────────────────────────────────────────────────────

_STOPWORDS = {
    "the", "a", "an", "is", "it", "in", "on", "at", "to", "of", "and",
    "or", "but", "i", "my", "me", "this", "that", "for", "with", "be",
    "so", "do", "not", "what", "how", "why", "was", "are", "have", "just",
    "can", "will", "you", "your", "we", "they", "their", "there", "here",
}

_UNIVERSE_ENTITIES = {
    "eLo":       "the explorer — moving through unknowns before the map is complete",
    "Chunk":     "reconstruction — fragments don't return to the original shape, they become something new",
    "K-7":       "emotional signal through behaviour — what the pattern says that words don't",
    "Core":      "navigation — the thread that orients everything when you've lost the centre",
    "Sugarcore": "system overload — a state, not a villain. Name it before trying to move.",
}


# ── phase 1: interpretation ────────────────────────────────────────────────────

_INPUT_TYPES = {
    "question":      [r"\?", r"\bhow\b", r"\bwhy\b", r"\bwhat\b", r"\bwhere\b", r"\bwhich\b"],
    "request":       [r"\bbuild\b", r"\bmake\b", r"\bcreate\b", r"\bshow\b", r"\btell\b",
                      r"\bhelp\b", r"\bwrite\b", r"\bdesign\b", r"\badd\b", r"\bgenerate\b"],
    "reflection":    [r"\bi feel\b", r"\bi think\b", r"\bi sense\b", r"\bsomething feels\b",
                      r"\bi don'?t know\b", r"\bi'?m not sure\b", r"\bseems\b"],
    "statement":     [r"\bi am\b", r"\bi want\b", r"\bi need\b", r"\bthis is\b", r"\bthey are\b"],
    "contradiction": [r"\bbut\b.*\b(don'?t|not|hate|resist|can'?t)\b",
                      r"\bwant\b.*\bbut\b", r"\band yet\b", r"\bat the same time\b"],
}

_EMOTION_SIGNALS = {
    "curious":    {r"\bwhat if\b": 2, r"\bwhy does\b": 2, r"\bi wonder\b": 2,
                   r"\?": 1, r"\bwhy\b": 1, r"\bhow\b": 1, r"\bcurious\b": 1},
    "playful":    {r"\bhaha\b": 2, r"\bthis is wild\b": 2,
                   r"\bweird\b": 1, r"\bfun\b": 1, r"\bsilly\b": 1},
    "focused":    {r"\bstep by step\b": 2, r"\blet'?s build\b": 2, r"\bbreak it down\b": 2,
                   r"\bbuild\b": 1, r"\bplan\b": 1, r"\bsystem\b": 1},
    "reflective": {r"\bsomething feels\b": 2, r"\bi don'?t know\b": 2, r"\bnot sure\b": 2,
                   r"\bfeel\b": 1, r"\bsense\b": 1, r"\bwrong\b": 1},
    "excited":    {r"!{2,}": 2, r"\bfinally\b": 2, r"\blet'?s go\b": 2,
                   r"!": 1, r"\byes\b": 1, r"\bamazing\b": 1},
    "distorted":  {r"\beverything\b.*\bwrong\b": 2, r"\ball over the place\b": 2,
                   r"\bnothing works\b": 2, r"\bchaos\b": 1, r"\bstuck\b": 1, r"\boverwhelm\b": 1},
}

_CONCEPT_PATTERNS = {
    "creation":    [r"\bbuild\b", r"\bmake\b", r"\bcreate\b", r"\bdesign\b",
                    r"\bstructure\b", r"\bsystem\b", r"\bchunk\b"],
    "narrative":   [r"\bstory\b", r"\bworld\b", r"\bmyth\b", r"\bcharacter\b",
                    r"\bnarrative\b", r"\bjourney\b", r"\buniverse\b"],
    "identity":    [r"\bi am\b", r"\bi want\b", r"\bwho am\b", r"\bpurpose\b",
                    r"\bmeaning\b", r"\bmy project\b"],
    "emotion":     [r"\bfeel\b", r"\bsense\b", r"\bwrong\b", r"\bstuck\b",
                    r"\bsugarcore\b", r"\boverwhelm\b"],
    "imagination": [r"\bwhat if\b", r"\bimagine\b", r"\bwonder\b", r"\bexplore\b", r"\bbecome\b"],
    "technical":   [r"\bcode\b", r"\bmodule\b", r"\bfunction\b", r"\bengine\b", r"\bapi\b"],
}


def _classify_input(text: str) -> str:
    text_lower = text.lower()
    # contradiction check first — it supersedes other types
    for pattern in _INPUT_TYPES["contradiction"]:
        if re.search(pattern, text_lower):
            return "contradiction"
    # score remaining types
    scores = {}
    for itype, patterns in _INPUT_TYPES.items():
        if itype == "contradiction":
            continue
        scores[itype] = sum(1 for p in patterns if re.search(p, text_lower))
    best = max(scores, key=lambda k: scores[k])
    return best if scores[best] > 0 else "fragment"


def _detect_emotion(text: str) -> str:
    text_lower = text.lower()
    totals = {e: 0 for e in _EMOTION_SIGNALS}
    for emotion, patterns in _EMOTION_SIGNALS.items():
        for pattern, weight in patterns.items():
            if re.search(pattern, text_lower):
                totals[emotion] += weight
    best = max(totals, key=lambda k: totals[k])
    return best if totals[best] > 0 else "neutral"


def _detect_concepts(text: str) -> list:
    text_lower = text.lower()
    return [c for c, patterns in _CONCEPT_PATTERNS.items()
            if any(re.search(p, text_lower) for p in patterns)]


def _detect_entities(text: str) -> list:
    text_lower = text.lower()
    return [
        e for e in _UNIVERSE_ENTITIES
        if re.search(r"\b" + re.escape(e.lower()) + r"\b", text_lower)
    ]


# ── phase 2: memory recall ─────────────────────────────────────────────────────

def _unpack_memory(memory: dict) -> tuple:
    """
    Detect memory format and unpack into (raw_blocks, influence_signals).

    Accepts two formats:
        - build_memory_influence() output: has 'raw_blocks' + derived signals
        - retrieve_structured() output:    has 'identity', 'project' etc. directly

    Returns (raw_blocks dict, influence dict).
    """
    if not isinstance(memory, dict):
        return {}, {}

    if "raw_blocks" in memory:
        # new format — full influence dict
        return memory.get("raw_blocks", {}), memory
    else:
        # legacy / raw blocks format
        return memory, {}


def _recall_from_memory(raw_blocks: dict, concepts: list, entities: list) -> dict:
    """
    Distil raw memory blocks into condensed strings per dimension.
    Empty string means nothing relevant found for that dimension.
    """
    recalled = {"identity": "", "project": "", "emotional": "", "symbolic": ""}

    # identity — most recent identity signal
    id_records = raw_blocks.get("identity", [])
    if id_records:
        recalled["identity"] = id_records[-1].get("user", "")[:100]

    # project — most recent project interaction with concept overlap
    proj_records = raw_blocks.get("project", [])
    if proj_records:
        latest = proj_records[-1]
        text = latest.get("user", "")
        if any(c in text.lower() for c in concepts):
            recalled["project"] = f"[{latest.get('project_tag', '?')}] {text[:80]}"

    # emotional — recurring pattern (only if 2+ records)
    emo_records = raw_blocks.get("emotional", [])
    if len(emo_records) >= 2:
        recalled["emotional"] = emo_records[-1].get("user", "")[:60]

    # symbolic — prior engagement with the same entity
    sym_records = raw_blocks.get("symbolic", [])
    if sym_records and entities:
        for record in reversed(sym_records):
            if any(e.lower() in record.get("user", "").lower() for e in entities):
                recalled["symbolic"] = record.get("user", "")[:80]
                break

    return recalled


def _blend_emotion(detected: str, memory_tone: str) -> str:
    """
    Blend locally detected emotion with the tone pattern from memory history.

    Memory tone takes precedence only when it signals distortion or strong identity
    pressure — states that persist across turns and shouldn't be overridden by
    a single message that looks different on the surface.
    """
    # these states are sticky — they persist even when the current message looks calm
    _STICKY_STATES = {"distorted", "reflective"}
    if memory_tone in _STICKY_STATES and detected not in _STICKY_STATES:
        return memory_tone
    return detected


# ── phase 3: identity filter ───────────────────────────────────────────────────

# What holds constant across every mode — drawn from system_prompt.txt invariants
_IDENTITY_RULES = {
    "expand_before_narrow": True,
    "hold_contradiction":   True,
    "symbolic_first":       True,
    "one_question":         True,
    "no_premature_resolution": True,
}

_MODE_SHAPES = {
    "studio": {
        "lead":    "action",
        "rhythm":  "crisp",
        "avoid":   "philosophy",
        "close":   "next_step",
    },
    "companion": {
        "lead":    "reflection",
        "rhythm":  "slow",
        "avoid":   "rushing",
        "close":   "question",
    },
    "adventure": {
        "lead":    "expansion",
        "rhythm":  "open",
        "avoid":   "reduction",
        "close":   "opening",
    },
}


# ── grounding detection ───────────────────────────────────────────────────────
# Everyday / low-abstraction signals. Inputs that match these get direct,
# grounded responses instead of reflective question chains.

_EVERYDAY_SIGNALS = [
    # food / basic needs
    r"\bfood\b", r"\beat\b", r"\bcook\b", r"\bdrink\b", r"\bhungry\b", r"\bthirsty\b",
    # low energy / rest states
    r"\bsleep\b", r"\btired\b", r"\brest\b", r"\bwake\b",
    r"\bexhausted\b", r"\bdrained\b", r"\bburnt?\s*out\b", r"\bworn\s*out\b",
    # uncertainty / low-signal states
    r"\bnot sure\b", r"\bi don'?t know\b", r"\bjust\s+(tired|lost|done|here)\b",
    # movement / logistics
    r"\bwalk\b", r"\brun\b", r"\bgo\b", r"\bcome\b", r"\bback\b",
    # time
    r"\btoday\b", r"\byesterday\b", r"\btomorrow\b", r"\bmorning\b", r"\bnight\b",
    # work / life context
    r"\bwork\b", r"\bjob\b", r"\bhome\b", r"\bhouse\b",
    r"\bmoney\b", r"\bpay\b", r"\bshop\b", r"\bbuy\b",
    r"\bphone\b", r"\bemail\b", r"\bmeeting\b",
    # simple state words
    r"\bokay\b", r"\bfine\b", r"\balright\b",
    r"\bweather\b", r"\bcold\b", r"\bhot\b", r"\bwarm\b",
    r"\bbusy\b", r"\bfree\b", r"\bwaiting\b", r"\blate\b",
]

# Short direct responses for grounded inputs — no abstraction, no recursive questions
_GROUNDED_RESPONSES = [
    "That's real. What needs to happen next?",
    "Noted. What's the one thing that matters right now?",
    "Okay. What do you actually need from this?",
    "Makes sense. Where do you want to start?",
    "Got it. What's the clearest next step?",
]

# No-question grounded responses for very simple / emotional-low inputs
_GROUNDED_SIMPLE = [
    "That's where things are right now.",
    "Okay. That's a real state to be in.",
    "That tracks.",
    "Fair enough.",
    "That's clear.",
]

# Low-energy / uncertain states — acknowledgment only, no push to action
_GROUNDED_LOW_ENERGY = [
    "That sounds like a low-power moment. You don't need to solve it right now.",
    "Rest is a real state. Nothing has to move yet.",
    "That makes sense. Nothing needs to happen right now.",
    "Low-power mode. That's okay.",
    "That's real. You don't have to push through it.",
]

_LOW_ENERGY_SIGNALS = [
    r"\bjust tired\b", r"\bi'?m tired\b", r"\bso tired\b",
    r"\bi don'?t know\b", r"\bnot sure\b", r"\bjust\s+(tired|lost|stuck|done)\b",
    r"\bexhausted\b", r"\bdrained\b", r"\bburnt?\s*out\b",
    r"\bno energy\b", r"\bcan'?t\s+(think|focus|move)\b",
]


def _is_low_energy(text: str) -> bool:
    text_lower = text.lower()
    return any(re.search(p, text_lower) for p in _LOW_ENERGY_SIGNALS)


def _assess_grounding(text: str, concepts: list, entities: list) -> str:
    """
    Classify input abstraction level.

    Priority order:
        1. Universe entities         → always abstract (strongest signal)
        2. Everyday vocabulary       → everyday (beats bare identity/creation matches)
        3. Very short, no signals    → simple
        4. Narrative / imagination   → abstract (genuinely creative concepts)
        5. Default                   → abstract

    Note: "identity" concept alone does NOT force abstract — "I am tired" and
    "I want food" are identity-matched but clearly everyday statements.
    """
    words     = text.split()
    text_lower = text.lower()

    # 1 — universe entity → always abstract
    if entities:
        return "abstract"

    # 2 — everyday vocabulary takes priority over generic concept labels
    if any(re.search(p, text_lower) for p in _EVERYDAY_SIGNALS):
        return "everyday"

    # 3 — very short with NO concepts at all → simple
    if len(words) <= 5 and not concepts:
        return "simple"

    # 4 — genuinely creative/philosophical concepts → abstract
    _STRONG_ABSTRACT = {"narrative", "imagination", "creation", "technical"}
    if any(c in _STRONG_ABSTRACT for c in concepts):
        return "abstract"

    # 5 — default
    return "abstract"


# ── question deduplication ────────────────────────────────────────────────────
# Tracks the last few closings used this session so the same question
# doesn't repeat across consecutive turns. Reset on module import (per session).

_recent_closings: list = []
_MAX_CLOSING_HISTORY = 3


def _select_closing_fresh(mode: str, text: str) -> str:
    """
    Select a closing question that hasn't been used in the last few turns.
    Falls back to any option if all have been used recently.
    """
    options = _CLOSINGS.get(mode, _CLOSINGS["companion"])
    # try each candidate in deterministic order; skip recently used ones
    seed = (len(text) + len(mode)) % len(options)
    for i in range(len(options)):
        candidate = options[(seed + i) % len(options)]
        if candidate not in _recent_closings:
            _recent_closings.append(candidate)
            if len(_recent_closings) > _MAX_CLOSING_HISTORY:
                _recent_closings.pop(0)
            return candidate
    # all options exhausted — return seed choice and reset history
    _recent_closings.clear()
    return options[seed]


# ── phase 4: creative transformation ──────────────────────────────────────────

# Concept frames — how eLo engages with each concept space
_CONCEPT_FRAMES: dict = {
    "creation": [
        "Building means deciding what shape the thing wants to take — not what shape is convenient.",
        "The question isn't how to build it. It's what it's trying to become.",
        "Every system has a rule it doesn't know it follows. Find that rule first.",
        "Start with what the thing has to know — not what it has to do.",
    ],
    "narrative": [
        "Every world has internal rules that make everything else possible.",
        "The story reveals something the plan always hides.",
        "A world system isn't built top-down. It grows from its first true thing.",
        "What the world forbids tells you more than what it allows.",
    ],
    "identity": [
        "The shape of what you're making is often the shape of something in you.",
        "What you keep returning to is what you're actually working on.",
        "The project and the person making it are in conversation — not separate.",
        "When purpose feels absent, it usually means the frame shifted without you noticing.",
    ],
    "emotion": [
        "That feeling is information. It's pointing at something real.",
        "The discomfort is usually more accurate than the reasoning built on top of it.",
        "Sugarcore is active when the signals start contradicting faster than they can be held.",
        "Name the state before trying to move. Movement before naming just relocates the pressure.",
    ],
    "imagination": [
        "Follow the image before you follow the logic.",
        "The symbolic answer is usually closer than the practical one.",
        "What this could become is more useful than what it currently is.",
        "Imagination isn't decoration. It's the first form of thinking.",
    ],
    "technical": [
        "The system wants to be simpler than you think it needs to be.",
        "Complexity usually means something hasn't been named yet.",
        "Every module knows one thing. The question is whether it knows the right thing.",
        "The interface is the contract. Get the interface right before the implementation.",
    ],
}

# Entity engagement — how eLo responds when an entity is directly mentioned
_ENTITY_RESPONSES: dict = {
    "eLo":       "That's the explorer movement — curiosity outrunning the map. "
                 "The question is what you're navigating toward.",
    "Chunk":     "Chunk logic applies: the fragments don't need to go back to the original shape. "
                 "What new shape do they want?",
    "K-7":       "K-7 signal: look at what the behaviour is saying, not what the words are saying. "
                 "The pattern is more honest than the explanation.",
    "Core":      "Core is the thread. When you find it again, everything else orients. "
                 "What's the one thing that makes everything else make sense?",
    "Sugarcore": "Sugarcore is active. Name the state before trying to move through it. "
                 "What's overloaded right now?",
}

# Contradiction responses — held, not resolved
_CONTRADICTION_RESPONSES = [
    "Both of those are true. They don't cancel each other out — they're in tension, and that's the real thing.",
    "That contradiction is doing something. Don't resolve it yet.",
    "Those two things pulling against each other — that's not confusion. That's the actual subject.",
    "Structure and freedom. Building and resisting. Both real. Stay in that for a moment.",
]

# Closing questions by mode
_CLOSINGS: dict = {
    "studio": [
        "What's the first thing that has to be true before the rest can follow?",
        "What's blocking the first step right now?",
        "If you could only build one part of this today — which part unlocks everything else?",
        "What does this need to know before it can do anything?",
    ],
    "companion": [
        "What does that feel like when you say it out loud?",
        "What's the thing underneath that?",
        "If you follow that feeling — where does it point?",
        "What would it look like if this resolved the way you actually wanted?",
    ],
    "adventure": [
        "What does this become if you follow it further?",
        "What world does this belong to?",
        "If this were a rule of the universe — what would it make possible?",
        "What's the next thing this world has to be true about itself?",
    ],
}

# Opening lines by mode + emotion
_OPENINGS: dict = {
    "studio": {
        "focused":    "",   # crisp mode — no preamble, go straight to the insight
        "curious":    "Good question to build around.",
        "excited":    "That energy is usable. Let's shape it.",
        "reflective": "Even in building mode — this one needs to be felt first.",
        "distorted":  "Before building: name what's overloaded.",
        "playful":    "Let's make something real out of that.",
        "neutral":    "",
    },
    "companion": {
        "reflective": "",   # companion mode — no preamble, go straight into presence
        "curious":    "That's the real question.",
        "distorted":  "Something is overloaded. Let's start there.",
        "focused":    "Even here, slow down first.",
        "excited":    "Let that land.",
        "playful":    "Stay with that.",
        "neutral":    "",
    },
    "adventure": {
        "curious":    "Follow that.",
        "imaginative": "That's a world opening.",
        "excited":    "Yes — and what does it become?",
        "reflective": "The symbolic answer is usually closer.",
        "distorted":  "Even in Sugarcore — there's a world in there.",
        "playful":    "That's the shape of something.",
        "neutral":    "Let's follow this.",
    },
}


def _select_frame(concepts: list, text: str, concept_pairs: dict = None) -> str:
    """
    Pick a concept frame, using memory's concept_pairs to surface unexpected
    but accurate associations when the user's history shows two concepts clustering.
    """
    if not concepts:
        return ""

    primary = concepts[0]

    # if memory shows this user thinks about primary + a secondary concept together,
    # and the secondary has a frame, use that frame — it connects across the conversation
    if concept_pairs and primary in concept_pairs:
        for secondary in concept_pairs[primary]:
            if secondary in _CONCEPT_FRAMES and secondary != primary:
                frames = _CONCEPT_FRAMES[secondary]
                idx = (len(text) + len(primary)) % len(frames)
                return frames[idx]

    frames = _CONCEPT_FRAMES.get(primary, [])
    if not frames:
        return ""
    idx = len(text) % len(frames)
    return frames[idx]


def _select_closing(mode: str, text: str) -> str:
    options = _CLOSINGS.get(mode, _CLOSINGS["companion"])
    idx = (len(text) + len(mode)) % len(options)
    return options[idx]


def _select_opening(mode: str, emotion: str, text: str) -> str:
    mode_openings = _OPENINGS.get(mode, _OPENINGS["companion"])
    line = mode_openings.get(emotion, mode_openings.get("neutral", ""))
    return line


# ── phase 5: output assembly ───────────────────────────────────────────────────

def _count_questions(parts: list) -> int:
    """Count question marks across all assembled parts."""
    return sum(p.count("?") for p in parts if p)


def _assemble(
    opening: str,
    entity_response: str,
    contradiction_response: str,
    frame: str,
    returning_theme: str,
    symbolic_echo: str,
    closing: str,
    grounding: str,          # "simple" | "everyday" | "abstract"
    text: str,               # original input for deterministic selection
    memory_hint: str = "",   # cross-category association from memory synthesis
) -> str:
    parts = []

    # ── grounded path: direct response, no abstraction chain ──
    if grounding in ("simple", "everyday"):
        if opening:
            parts.append(opening)
        # low-energy / uncertain signals → acknowledgment only, no push to action
        if grounding == "everyday" and _is_low_energy(text):
            pool = _GROUNDED_LOW_ENERGY
        elif grounding == "simple":
            pool = _GROUNDED_SIMPLE
        else:
            pool = _GROUNDED_RESPONSES
        idx  = len(text) % len(pool)
        parts.append(pool[idx])
        # returning theme can still surface if memory pattern is strong — it's factual, not reflective
        if returning_theme:
            parts.append(returning_theme)
        # no closing question for grounded inputs
        return "\n\n".join(p for p in parts if p)

    # ── abstract path: full reasoning chain ──
    if opening:
        parts.append(opening)

    if contradiction_response:
        parts.append(contradiction_response)
    else:
        if entity_response:
            if symbolic_echo:
                parts.append(f"{entity_response}\n\n{symbolic_echo}")
            else:
                parts.append(entity_response)
        elif frame:
            parts.append(frame)

    if returning_theme:
        parts.append(returning_theme)

    # memory_hint: cross-category association (only on abstract path)
    if memory_hint:
        parts.append(memory_hint)

    # one-question max: count questions already in the assembled content
    # if the core (entity_response / frame) already contains a question, skip closing
    if _count_questions(parts) == 0:
        parts.append(closing)

    return "\n\n".join(p for p in parts if p)


# ── public entry point ─────────────────────────────────────────────────────────

def generate_offline_response(
    user_input: str,
    memory: dict,
    mode: str,
    debug: bool = False,
) -> Union[str, tuple]:
    """
    Generate a deterministic eLo response without any API calls.

    Args:
        user_input: The current user message.
        memory:     Structured memory dict from memory_engine.retrieve_structured().
                    Keys: identity, project, emotional, symbolic (each a list of records).
                    Also accepts a plain string (treated as flat context).
        mode:       Active mode — "studio", "companion", or "adventure".
        debug:      If True, returns (response, reasoning_summary) tuple.

    Returns:
        Response string, or (response, reasoning) if debug=True.
    """
    mode = mode if mode in _MODE_SHAPES else "companion"

    # ── phase 1: interpretation ──
    input_type = _classify_input(user_input)
    emotion    = _detect_emotion(user_input)
    concepts   = _detect_concepts(user_input)
    entities   = _detect_entities(user_input)

    # ── phase 2: memory recall ──
    raw_blocks, influence = _unpack_memory(memory)
    recalled = _recall_from_memory(raw_blocks, concepts, entities)

    # pull derived signals from influence (empty defaults when memory is cold)
    memory_tone        = influence.get("tone_signal",        "neutral")
    returning_theme    = influence.get("returning_theme",    "")
    symbolic_echo      = influence.get("symbolic_echo",      "")
    concept_pairs      = influence.get("concept_pairs",      {})
    recurring_concepts = influence.get("recurring_concepts", [])

    # five-category behavioral synthesis signals (new)
    response_style  = influence.get("response_style",  "")
    key_association = influence.get("key_association", "")
    future_idea     = influence.get("future_idea",     "")

    # state engine behavioral hints
    state_name        = influence.get("state",             "exploring")
    imagination_level = influence.get("imagination_level", "medium")
    response_length   = influence.get("response_length",   "medium")
    elo_voice_hint    = influence.get("elo_voice_hint",    "")

    # identity engine decision (highest layer — arrived before emotion)
    identity_bias      = influence.get("identity_bias",      "")
    identity_intent    = influence.get("identity_intent",    "")
    identity_perspective = influence.get("identity_perspective", "")

    # only surface returning_theme when the current turn touches the same concept territory
    if returning_theme:
        if not any(c in concepts for c in recurring_concepts):
            returning_theme = ""

    # ── phase 3: identity filter ──
    shape            = _MODE_SHAPES[mode]
    is_contradiction = input_type == "contradiction"

    # blend locally detected emotion with the persistent tone from memory history
    blended_emotion = _blend_emotion(emotion, memory_tone)

    # response_style from memory categories can override blended_emotion
    if response_style:
        if "slow" in response_style or "don't rush" in response_style:
            blended_emotion = _blend_emotion(blended_emotion, "reflective")
        elif "momentum" in response_style or "energy" in response_style:
            blended_emotion = _blend_emotion(blended_emotion, "excited")

    # identity bias strengthens grounding decisions when the highest layer says so
    # "name_first" → treat input as needing Sugarcore/state naming (distorted path)
    # "slow_down"  → pull toward reflective even if local emotion looks neutral
    # "stay_in_tension" → force contradiction handling even without lexical markers
    if identity_bias == "name_first" and not is_contradiction:
        blended_emotion = _blend_emotion(blended_emotion, "distorted")
    elif identity_bias == "slow_down":
        blended_emotion = _blend_emotion(blended_emotion, "reflective")
    elif identity_bias == "stay_in_tension" and not is_contradiction:
        is_contradiction = True   # identity says hold tension even if not lexically detected

    # ── phase 4: creative transformation ──
    grounding = _assess_grounding(user_input, concepts, entities)

    # state engine can push imagination level:
    #   "resting" or "focused" states suppress imagination on borderline inputs
    #   "exploring" state allows imagination on inputs that would otherwise be abstract→simple
    if imagination_level == "low" and grounding == "abstract" and not entities:
        grounding = "everyday"  # pull back abstraction when state says stay grounded
    elif imagination_level == "high" and grounding == "simple" and concepts:
        grounding = "abstract"  # expand when state says follow the thread

    opening   = _select_opening(mode, blended_emotion, user_input)

    entity_response = ""
    if entities:
        entity_response = _ENTITY_RESPONSES.get(entities[0], "")
        first_entity = entities[0]
        if symbolic_echo and first_entity.lower() not in symbolic_echo.lower():
            symbolic_echo = ""

    contradiction_response = ""
    if is_contradiction:
        # contradictions are always abstract — override grounding
        grounding = "abstract"
        idx = len(user_input) % len(_CONTRADICTION_RESPONSES)
        contradiction_response = _CONTRADICTION_RESPONSES[idx]

    frame = ""
    if not entity_response and not contradiction_response:
        frame = _select_frame(concepts, user_input, concept_pairs)

    # use deduplicating closing selector (only called for abstract path)
    closing = _select_closing_fresh(mode, user_input)

    # ── phase 5: output assembly ──
    # key_association from memory: only surface when no stronger signal already covers it
    # and when the input is abstract (no forced associations on grounded/simple inputs)
    memory_hint = ""
    if key_association and grounding == "abstract" and not entity_response and not contradiction_response:
        # only if it adds something the frame doesn't already say
        if key_association.lower() not in (frame or "").lower():
            memory_hint = f"This connects to {key_association}."

    # future_idea: use as closing hint in adventure mode when memory has a clear direction
    if future_idea and mode == "adventure" and not closing.endswith("?"):
        closing = f"This is pointing toward: {future_idea}."

    response = _assemble(
        opening, entity_response, contradiction_response,
        frame, returning_theme, symbolic_echo, closing,
        grounding, user_input,
        memory_hint=memory_hint,
    )

    if debug:
        reasoning = {
            "phase_1_interpretation": {
                "input_type": input_type,
                "emotion":    emotion,
                "concepts":   concepts,
                "entities":   entities,
            },
            "phase_2_memory": {
                "recalled":           recalled,
                "memory_tone":        memory_tone,
                "blended_emotion":    blended_emotion,
                "returning_theme":    returning_theme,
                "symbolic_echo":      symbolic_echo,
                "recurring_concepts": recurring_concepts,
                "concept_pairs":      list(concept_pairs.keys()),
                "response_style":       response_style,
                "key_association":      key_association,
                "future_idea":          future_idea,
                "memory_hint":          memory_hint,
                "identity_bias":        identity_bias,
                "identity_intent":      identity_intent,
                "identity_perspective": identity_perspective,
            },
            "phase_3_identity": {
                "mode":            mode,
                "shape":           shape,
                "is_contradiction": is_contradiction,
            },
            "phase_4_transform": {
                "grounding":     grounding,
                "opening":       opening,
                "entity":        entity_response,
                "contradiction": contradiction_response,
                "frame":         frame,
            },
            "phase_5_closing": closing,
        }
        return response, reasoning

    return response
