"""
core/attention.py — eLo OS v2 Attention Layer.

Computes BEFORE every response. Determines what is relevant RIGHT NOW.
Filters memory through intent and relevance scoring before prompt assembly.

eLo does NOT respond based on full memory.
eLo responds based on: WHAT IS RELEVANT RIGHT NOW.

Output (AttentionModel dict):
    {
        "intent":                 str,   one of 7 intents
        "high_priority_memory":   list,  score >= 8
        "medium_priority_memory": list,  score 4–7
        "low_priority_memory":    list,  score < 4  (excluded from prompt)
        "emotional_context":      dict,  energy / tension / closure / inferred_state
    }
"""

from __future__ import annotations
import re

# ── intent patterns ────────────────────────────────────────────────────────────

_INTENT_PATTERNS: dict[str, list] = {
    "inquiry":   [r"\bwhat\b", r"\bhow\b", r"\bwhy\b", r"\bexplain\b",
                  r"\btell\s+me\b", r"\bwhat\s+is\b", r"\bwhat\s+are\b",
                  r"\bshould\s+i\b", r"\bdo\s+i\b", r"\bcan\s+i\b"],
    "creation":  [r"\bbuild\b", r"\bdesign\b", r"\bmake\b", r"\bcreate\b",
                  r"\bimplement\b", r"\bwhat\s+if\b", r"\bcould\s+we\b", r"\blet'?s\b"],
    "emotional": [r"\bfeel\b", r"\btired\b", r"\bsad\b", r"\boverwhel\b",
                  r"\bconfused\b", r"\bscared\b", r"\bstuck\b", r"\bworried\b"],
    "recall":    [r"\bremember\b", r"\blast\s+time\b", r"\bbefore\b",
                  r"\bwe\s+talked\b", r"\bwe\s+said\b", r"\byou\s+said\b"],
    "simplify":  [r"\btoo\s+much\b", r"\boverload\b", r"\bsimplify\b",
                  r"\bcan'?t\s+think\b", r"\bjust\b.{1,20}\bsimple\b"],
}

# ── emotional spectrum keywords ────────────────────────────────────────────────

_ENERGY_LOW   = ["tired", "exhaust", "drain", "slow", "stuck", "low", "drained"]
_ENERGY_HIGH  = ["excited", "energetic", "fast", "rush", "flying", "can't stop"]
_TENSION_HIGH = ["overwhelm", "stress", "anxious", "worried", "scared", "panic", "too much"]
_TENSION_LOW  = ["calm", "relax", "okay", "fine", "good", "peaceful", "alright"]
_CLOSED_CUES  = ["done", "finished", "enough", "stop", "no more", "closed", "end"]
_OPEN_CUES    = ["what if", "explore", "let's", "could", "maybe", "wondering", "curious"]

# ── helpers ────────────────────────────────────────────────────────────────────

def _matches(text: str, patterns: list) -> bool:
    t = text.lower()
    return any(re.search(p, t) for p in patterns)


def _content_words(text: str) -> set:
    _STOP = {"the", "a", "an", "is", "it", "in", "on", "at", "to", "of",
             "and", "or", "but", "i", "my", "me", "this", "that", "for", "with"}
    return {w.lower() for w in re.findall(r"\b\w{4,}\b", text)
            if w.lower() not in _STOP}


# ── intent classifier ─────────────────────────────────────────────────────────

def _classify_intent(user_input: str, loop_detected: bool = False) -> str:
    """Classify the user's intent. Loop detection overrides to 'stabilise'."""
    if loop_detected:
        return "stabilise"
    for intent in ("emotional", "simplify", "recall", "creation", "inquiry"):
        if _matches(user_input, _INTENT_PATTERNS.get(intent, [])):
            return intent
    return "conversation"


# ── memory scoring ─────────────────────────────────────────────────────────────

def _score(item_text: str, user_input: str, source: str) -> int:
    """
    Score a memory item for relevance to the current input.

    Scoring:
        +5  semantically related (3+ shared content words)
        +2  lightly related (1–2 shared words)
        +3  emotionally significant keyword in item
        +1  recent (all pack items are recent — always awarded)
        +3  identity or session anchor (critical sources always get a bump)
        -2  irrelevant (no shared words, low base score)

    Thresholds:
        8+  → HIGH
        4–7 → MEDIUM
        <4  → LOW
    """
    score = 1  # +1 recency, always

    if source in ("identity", "session_anchor"):
        score += 3

    user_words = _content_words(user_input)
    item_words = _content_words(item_text)
    shared     = user_words & item_words

    if len(shared) >= 3:
        score += 5
    elif shared:
        score += 2

    emo_markers = ["important", "strong", "overwhelm", "critical", "core", "identity", "key"]
    if any(m in item_text.lower() for m in emo_markers):
        score += 3

    if not shared and score < 3:
        score -= 2

    return score


def _bucket(score: int) -> str:
    if score >= 8:
        return "high"
    if score >= 4:
        return "medium"
    return "low"


# ── emotional valence + momentum signals ──────────────────────────────────────

_POSITIVE_HIGH = ["clicking", "excited", "inspired", "finally", "figured it out",
                   "got it", "energy is high", "feeling good", "feeling great",
                   "feel great", "feel good today", "feel amazing", "great today",
                   "amazing", "breakthrough", "things are clicking", "it clicked",
                   "clear now", "understand now", "makes sense now", "i think i have",
                   "opening arc", "whole pitch", "things clicking", "feel clear",
                   "feel really good", "feeling really good", "slept well",
                   "energy is", "high energy", "really good today",
                   "feel real", "feels real", "feel genuine", "is working",
                   "are working", "actually working", "conversations feel", "starting to work"]
_POSITIVE_LOW  = ["content", "peaceful", "satisfied", "feeling okay", "settled",
                   "calm today", "good today", "doing well", "all good"]
_NEGATIVE_HIGH = ["frustrated", "angry", "stressed", "furious", "annoyed",
                   "irritated", "fed up", "can't take", "so angry"]
_BUILDING_MOM  = ["clicking", "figured", "understand", "makes sense", "coming together",
                   "think i have", "got it", "opening arc", "i think i", "progress",
                   "moving forward", "starting to see", "finally", "feel clear",
                   "everything clicking", "things are clicking", "whole pitch",
                   "that's it", "found it", "landed on"]
_DECLINING_MOM = ["falling behind", "losing", "wrong direction", "can't find",
                   "going backwards", "nothing working", "lost the thread"]


# ── emotional spectrum ─────────────────────────────────────────────────────────

def _emotional_context(user_input: str, emotional_history: list) -> dict:
    """
    Infer user emotional state as Energy / Tension / Closure / Valence / Momentum.

    eLo mirrors at 30% intensity only — 70% stays stable identity.
    """
    t = user_input.lower()

    energy = 0.2 if any(w in t for w in _ENERGY_LOW) \
        else 0.85 if any(w in t for w in _ENERGY_HIGH) \
        else 0.5

    # positive high energy overrides the base energy reading
    if any(w in t for w in _POSITIVE_HIGH):
        energy = max(energy, 0.8)

    tension = 0.8 if any(w in t for w in _TENSION_HIGH) \
         else 0.2 if any(w in t for w in _TENSION_LOW) \
         else 0.4

    closure = "closed" if any(w in t for w in _CLOSED_CUES) \
         else "open"

    if tension > 0.6 and energy < 0.4:
        inferred = "overwhelmed"
    elif tension > 0.6:
        inferred = "stressed"
    elif energy > 0.7:
        inferred = "energised"
    elif energy < 0.3:
        inferred = "low-energy"
    else:
        inferred = "present"

    # light history adjustment — only when input is neutral
    if emotional_history and energy == 0.5:
        last = emotional_history[-1].get("tone", "neutral")
        if last == "low-energy":
            energy = 0.4

    # ── valence ────────────────────────────────────────────────────────────────
    if any(w in t for w in _POSITIVE_HIGH):
        valence = "positive_high"
    elif any(w in t for w in _POSITIVE_LOW):
        valence = "positive_low"
    elif any(w in t for w in _NEGATIVE_HIGH):
        valence = "negative_high"
    elif tension > 0.5 or energy < 0.3:
        valence = "negative_low"
    else:
        valence = "neutral"

    # ── momentum ───────────────────────────────────────────────────────────────
    if any(w in t for w in _BUILDING_MOM):
        momentum = "building"
    elif any(w in t for w in _DECLINING_MOM):
        momentum = "declining"
    elif tension > 0.6 and energy < 0.3:
        momentum = "stuck"
    else:
        momentum = "stable"

    return {
        "energy":           round(energy, 2),
        "tension":          round(tension, 2),
        "closure":          closure,
        "inferred_state":   inferred,
        "valence":          valence,
        "momentum":         momentum,
        "mirror_intensity": 0.3,
    }


# ── public API ─────────────────────────────────────────────────────────────────

def compute(
    user_input:    str,
    memory_pack:   dict,
    session_state: dict,
    loop_detected: bool = False,
) -> dict:
    """
    Compute the AttentionModel for this turn.

    Args:
        user_input:    Raw user message.
        memory_pack:   Output of memory_pack_builder.load() or build().
        session_state: Output of state_manager.load().
        loop_detected: True if hard loop detection fired.

    Returns:
        AttentionModel with intent, memory buckets, emotional_context.
        Only HIGH + MEDIUM memory should reach the prompt.
        LOW memory is returned for logging but excluded from generation.
    """
    intent = _classify_intent(user_input, loop_detected)

    # collect all scoreable memory items
    candidates: list[tuple[str, str]] = []

    identity = memory_pack.get("identity", "")
    if identity:
        candidates.append((identity, "identity"))

    anchor = session_state.get("session_anchor", {})
    anchor_text = anchor.get("current_session_summary", "")
    if anchor_text:
        candidates.append((anchor_text, "session_anchor"))

    for entity in memory_pack.get("entities", []):
        if entity.strip():
            candidates.append((entity, "entity"))

    for exchange in memory_pack.get("recent_context", []):
        text = f"{exchange.get('user', '')} {exchange.get('elo', '')}".strip()
        if text:
            candidates.append((text, "exchange"))

    topics = session_state.get("last_topics", [])
    if topics:
        candidates.append((" ".join(topics[-5:]), "topics"))

    # score and sort
    scored = sorted(
        [(_score(text, user_input, src), text) for text, src in candidates if text.strip()],
        key=lambda x: x[0],
        reverse=True,
    )

    high: list[str]   = []
    medium: list[str] = []
    low: list[str]    = []

    for score, text in scored:
        tier = _bucket(score)
        if tier == "high":
            high.append(text)
        elif tier == "medium":
            medium.append(text)
        else:
            low.append(text)

    # loop/stabilise override — clear all except identity anchors
    if loop_detected or intent == "stabilise":
        medium = []
        low    = []
        high   = [t for t in high if "elo" in t.lower() or "identity" in t.lower()][:2]

    emo_ctx = _emotional_context(user_input, session_state.get("emotional_history", []))

    return {
        "intent":                 intent,
        "high_priority_memory":   high[:4],     # cap: keep prompt lean
        "medium_priority_memory": medium[:3],
        "low_priority_memory":    low,
        "emotional_context":      emo_ctx,
    }
