"""
faculties/intent_gatekeeper.py — WO-072: Intent Gatekeeper (rules-first, LLM normalizer fallback).

Stage at the front of the Faculty Bus. Turns raw user input into a structured
intent envelope: {intent, confidence, cleaned_text, target}.

Priority:
  1. Rules (deterministic, free) — fast path for most turns
  2. LLM normalizer (fallback, low-confidence only) — via existing backend_router
  3. Honest degrade → "conversation" when uncertain (ADR-Exec-001)
"""

import re
import json
import logging

_log = logging.getLogger(__name__)

# ── Intent taxonomy ───────────────────────────────────────────────────────────

INTENTS = frozenset({
    "conversation", "sit", "stand", "move", "exit_run", "jump",
    "weather", "company", "board", "memory", "cancel",
    "tool:spotify", "tool:search", "tool:file", "tool:github",
})

# ── Rule tables ───────────────────────────────────────────────────────────────

_SIT_PHRASES = frozenset({
    "come sit", "sit with me", "sit beside", "sit next to me",
    "come sit with me", "sit with me while", "come and sit",
    "come sit down", "sit down with", "come join me",
})

_EXIT_RUN_PHRASES = frozenset({
    "exit run", "stop running", "end run", "finish run",
    "exit the run", "done running",
})

# Pure cancel: ONLY fire when the entire input is one of these — never a substring
_CANCEL_EXACT = frozenset({
    "cancel", "never mind", "nevermind", "forget it", "abort",
    "cancel that", "forget that", "stop that", "nvm",
})

_WEATHER_PHRASES = (
    "weather", "temperature", "forecast", "raining", "sunny",
    "how hot", "how cold", "what's the temp", "whats the weather",
    "how's the weather", "weather in", "weather today",
)

_COMPANY_PHRASES = (
    "how's the company", "hows the company", "company update",
    "company news", "how's disenelo", "hows disenelo",
    "what's happening with the company", "company status",
)

_BOARD_PHRASES = (
    "what's on the board", "what is on the board", "board priorities",
    "board update", "board status", "what are my priorities",
    "what's the priority", "what should i focus on", "on the board",
    "board today",
)

# Regex: inputs matching these are conversational regardless of other words present
_CONVERSATIONAL_RE = re.compile(
    r"^no\s+but"                          # "No but it takes time..."
    r"|^not\s+really"
    r"|^not\s+sure"
    r"|^i\s+don.t\s+think"
    r"|^i\s+was\s+thinking"
    r"|^i\s+mean\b"
    r"|^actually\s+no"
    r"|^wait\s+no"
    r"|^hmm\b"
    r"|^hm\b"
    r"|what\s+does\s+that\s+mean"         # "Strange reply what does that mean?"
    r"|strange\s+reply"
    r"|anything\s+we\s+can"              # "anything we can press on with?"
    r"|what\s+can\s+we"
    r"|i.m\s+tired"
    r"|nothing.s\s+working"
    r"|feels\s+like",
    re.I,
)

# Long questions (> 20 chars) starting with reflective words → conversation
_REFLECTIVE_QUESTION_RE = re.compile(
    r"^(why|how come|what if|do you think|should we|could we|"
    r"would it|is it\b|isn.t it|don.t you|can.t we|wouldn.t|"
    r"is there|are there|do we)",
    re.I,
)


# ── Envelope builder ──────────────────────────────────────────────────────────

def _envelope(intent: str, confidence: float, text: str, target: str = "") -> dict:
    return {
        "intent":       intent,
        "confidence":   confidence,
        "cleaned_text": text,
        "target":       target,
    }


# ── Rules classifier (deterministic) ─────────────────────────────────────────

def _rules_classify(text: str) -> dict | None:
    """
    Deterministic rules — fast path, no LLM cost.
    Returns an envelope at high confidence, or None to fall through.
    """
    t = text.strip()
    tl = t.lower()
    bare = tl.rstrip("?!.,; ")

    # ── Conversational override: fire before any command check ────────────────
    if _CONVERSATIONAL_RE.search(tl):
        return _envelope("conversation", 0.92, t)

    if _REFLECTIVE_QUESTION_RE.match(tl) and len(t) > 20:
        return _envelope("conversation", 0.82, t)

    # ── Pure cancel — whole-input only, never a substring ────────────────────
    if bare in _CANCEL_EXACT:
        return _envelope("cancel", 0.92, t)

    # ── Sit ───────────────────────────────────────────────────────────────────
    for phrase in _SIT_PHRASES:
        if phrase in tl:
            return _envelope("sit", 0.93, t)

    # ── Exit run ──────────────────────────────────────────────────────────────
    if bare in _EXIT_RUN_PHRASES or any(p in tl for p in _EXIT_RUN_PHRASES):
        return _envelope("exit_run", 0.90, t)

    # ── Weather ───────────────────────────────────────────────────────────────
    if any(p in tl for p in _WEATHER_PHRASES):
        return _envelope("weather", 0.88, t)

    # ── Company ───────────────────────────────────────────────────────────────
    if any(p in tl for p in _COMPANY_PHRASES):
        return _envelope("company", 0.88, t)

    # ── Board ─────────────────────────────────────────────────────────────────
    if any(p in tl for p in _BOARD_PHRASES):
        return _envelope("board", 0.88, t)

    return None  # uncertain — fall through to LLM normalizer


# ── LLM normalizer (fallback only) ───────────────────────────────────────────

_LLM_SYSTEM = (
    "You are a strict intent classifier for an AI system. "
    "Classify the user message into exactly ONE intent: "
    "conversation, sit, stand, move, exit_run, jump, weather, company, board, "
    "memory, cancel, tool:spotify, tool:search, tool:file, tool:github. "
    "\n\nRules:"
    "\n- 'No but...', 'not really', reflective questions, meta-questions → conversation"
    "\n- Only classify as a command if the input is CLEARLY imperative"
    "\n- When uncertain → always return conversation (never fabricate a command)"
    "\n- Fix obvious typos/STT noise in cleaned_text; otherwise return as-is"
    "\n\nReturn ONLY valid JSON (no other text): "
    '{"intent": "<class>", "confidence": 0.0-1.0, "cleaned_text": "<text>"}'
)


def _llm_normalize(text: str) -> dict | None:
    """Call cheap LLM to classify + clean. Returns envelope or None on failure."""
    try:
        from runtime import backend_router as _br
        raw, _ = _br.route(text, _LLM_SYSTEM, max_sentences=1)
        match = re.search(r'\{[^}]+\}', raw, re.DOTALL)
        if not match:
            return None
        data = json.loads(match.group())
        intent = data.get("intent", "conversation")
        if intent not in INTENTS:
            intent = "conversation"
        conf = float(data.get("confidence", 0.5))
        cleaned = str(data.get("cleaned_text", text))
        return _envelope(intent, conf, cleaned)
    except Exception as e:
        _log.debug("gatekeeper LLM normalizer failed: %s", e)
        return None


# ── Public API ────────────────────────────────────────────────────────────────

def classify(text: str, use_llm: bool = True) -> dict:
    """
    Full gatekeeper: rules first, LLM fallback, confidence gate.
    Always returns a valid intent envelope — never raises.

    use_llm=False: rules-only mode (zero latency, for hot-path server wiring).
    use_llm=True:  falls through to LLM normalizer when rules are uncertain.
    """
    # 1. Rules (deterministic, free)
    result = _rules_classify(text)
    if result and result["confidence"] >= 0.85:
        return result

    # 2. LLM normalizer (fallback — low confidence or uncertain)
    if use_llm:
        llm_result = _llm_normalize(text)
        if llm_result and llm_result["confidence"] >= 0.75:
            return llm_result

    # 3. Honest degrade — uncertain → conversation (ADR-Exec-001)
    return _envelope("conversation", 0.5, text)
