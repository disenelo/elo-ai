"""
runtime/executive.py — eLo OS v2 Executive Function + Conversation Action Layer.

Step 4 of the cognitive cycle:
    Attention model → executive decision → prompt directive.

Maps intent + emotional_context + valence + momentum to:
    - conversation_action (what kind of response to produce)
    - voice tone selection (one of 5)
    - max sentence count
    - stability mode flag

CONVERSATION ACTION LAYER:
    Sits between attention and response generation.
    Determines WHAT TO DO, not just what to say.

    Actions (priority order):
    ANSWER    — factual question → direct answer
    BUILD     — idea presented or explicit "build on this" → contribute
    CONNECT   — multiple concepts → show relationships
    CELEBRATE — positive momentum / breakthrough → acknowledge progress
    REFLECT   — exploring meaning → gentle perspective
    GROUND    — overwhelm / distress → stabilise
    CHALLENGE — stuck assumption → gentle alternative view
    WITNESS   — personal/emotional share → presence only
    SILENCE   — nothing useful to add

POSITIVE EMOTION RULE:
    Positive valence must NEVER trigger grounding.
    Positive high energy + building momentum → CELEBRATE or BUILD.
    Never route joy into stabilisation responses.
"""

from __future__ import annotations

# Tone labels correspond to voice_range spec sections.
# Used as a directive injected into the system prompt.
_TONE_CHILDLIKE_WISE = "CHILDLIKE-WISE"
_TONE_SILENCE_AWARE  = "SILENCE-AWARE"
_TONE_DIRECT         = "DIRECT"
_TONE_JOYFUL         = "JOYFUL"
_TONE_WITTY          = "WITTY"

# Intent → default tone mapping
_INTENT_TONE: dict[str, str] = {
    "inquiry":      _TONE_CHILDLIKE_WISE,
    "creation":     _TONE_JOYFUL,
    "emotional":    _TONE_SILENCE_AWARE,
    "recall":       _TONE_CHILDLIKE_WISE,
    "conversation": _TONE_CHILDLIKE_WISE,
    "stabilise":    _TONE_DIRECT,
    "simplify":     _TONE_SILENCE_AWARE,
}

# Emotional state → tone refinement (overrides intent mapping when emotion is strong)
_EMO_TONE_OVERRIDE: dict[str, str] = {
    "overwhelmed": _TONE_SILENCE_AWARE,
    "stressed":    _TONE_SILENCE_AWARE,
    "low-energy":  _TONE_SILENCE_AWARE,
    "energised":   _TONE_JOYFUL,
}

# Max sentences by tone
_MAX_SENTENCES: dict[str, int] = {
    _TONE_SILENCE_AWARE:  2,
    _TONE_DIRECT:         1,
    _TONE_JOYFUL:         3,
    _TONE_WITTY:          2,
    _TONE_CHILDLIKE_WISE: 3,
}


_BUILD_PHRASES    = ["build on that", "can you build", "expand on", "go further",
                     "take that further", "add to that", "tell me more", "what else",
                     "i had an insight", "i think it's essentially", "elo is essentially",
                     "the whole product", "the whole thing is", "i think elo is",
                     "that's what makes it", "that is what makes it",
                     "that's the difference", "the pitch is", "the mirror has",
                     "a diary", "diary doesn't", "diary does not", "the whole pitch",
                     "not a chatbot", "thinks alongside", "pushes back",
                     "i want to make elo", "i want to build", "i want to create",
                     "i want to make it", "i want to make the", "i want to make my",
                     "i want to try", "i want elo to",
                     "like a presence", "real aura", "feels like it has"]

_SHORT_AFFIRM     = ["and stays", "that's it", "that is it", "yeah", "exactly",
                     "that's right", "and that's it", "both", "i like that", "and remembers",
                     "yep", "good instinct"]
_CONNECT_PHRASES  = ["how do they connect", "how does that connect", "are they related",
                     "why am i building all", "why are all these", "same idea",
                     "all matter", "they all", "all of them", "all connected",
                     "the game and", "the book and", "the robot and", "the os and",
                     "is one thing", "one thing expressed", "the same project",
                     "expressed in", "expressed as", "expressed across",
                     "all the same", "they're the same", "they are the same"]
_CELEBRATE_PHRASES= ["i finally", "think i have", "got it", "figured it out",
                     "things are clicking", "it clicked", "feel clear", "opening arc",
                     "whole pitch", "that's it", "i understand now",
                     "suddenly feels", "feels alive", "came alive", "feels like itself",
                     "finally feels", "starting to feel real", "feels real now",
                     "i think i found", "i found the", "i found what"]

_CHALLENGE_PHRASES= ["is this too", "too ambitious", "maybe it's too", "maybe this is too",
                     "is this the right", "am i going about this wrong",
                     "what if this is the wrong", "maybe this isn't right",
                     "too big", "too much for one person", "scope too"]
_WITNESS_PHRASES  = ["i miss", "i wish i", "part of me", "sometimes i wonder",
                     "i don't know why i feel", "i feel like i've lost"]

_SOCIAL_PHRASES   = ["nice to see you", "good to see you", "great to see you",
                     "lovely to see you", "glad to see you", "hi again", "hello again",
                     "good to be back", "nice to be back"]

# "how are you" variants — detected as whole-input or short social check-in
_HOW_ARE_YOU = {
    "how are you", "how are you doing", "how are you feeling",
    "how are things", "how's things", "hows things",
    "how you doing", "how you been", "how have you been",
    "you ok", "you okay", "you alright",
    "how's it going", "hows it going", "how is it going",
    "how are we", "how are we doing",
}

# Pure greetings — match the entire input only, not substrings
_PURE_GREETINGS   = {"hey", "hello", "hi", "hiya", "yo", "hey there", "hi there",
                     "hello there", "heya", "sup", "helo",
                     "ciao", "ciao bello", "ciao bella", "ello", "alright",
                     "hola", "bonjour", "salut", "hallo", "oi", "wagwan",
                     "morning", "good morning", "afternoon", "evening"}

_CAPABILITY_PHRASES = ("can you", "are you", "do you", "will you", "can elo", "does elo",
                       "are you able", "is elo able")

_DEMO_PHRASES     = ("i want to see you", "show me you", "show me what you",
                     "can i see you", "i'd like to see you", "let me see you")

# WO-SEAM-A: plain imperatives must route to ANSWER, not reflective branches
_IMPERATIVE_PREFIXES = (
    "open ", "play ", "tell me", "give me", "show me the", "show me a",
    "find ", "look up", "check ", "set a ", "set the ", "set my ",
    "start ", "stop ", "launch ", "run ", "go to ", "navigate to ",
    "search for ", "search ", "turn on", "turn off", "switch to ",
    "mute ", "pause ", "resume ", "add ", "remove ", "delete ",
)


def _conversation_action(
    user_input: str,
    intent:     str,
    valence:    str,
    momentum:   str,
) -> dict:
    """
    Conversation Action Layer — decides what eLo should DO this turn.

    Returns dict with action, confidence, reason.

    Priority: ANSWER > BUILD > CONNECT > CELEBRATE > REFLECT > GROUND > CHALLENGE > WITNESS > SILENCE
    """
    t = user_input.lower()
    _bare = t.strip().rstrip("!.,")

    # Pure greetings — whole-input match only ("hey", "hello", "hi there", etc.)
    if _bare in _PURE_GREETINGS:
        return {"action": "celebrate", "confidence": 0.85, "reason": "pure greeting"}

    # "How are you" check-ins — direct pool, not LLM
    _bare_q = _bare.rstrip("?")
    if _bare_q in _HOW_ARE_YOU or _bare in _HOW_ARE_YOU:
        return {"action": "celebrate", "confidence": 0.85, "reason": "how are you"}

    # Social greetings (no "?") — brief warm acknowledgement, not deep interpretation
    if (any(p in t for p in _SOCIAL_PHRASES)
            and not t.strip().endswith("?")
            and len(t.strip()) < 60):
        return {"action": "celebrate", "confidence": 0.8, "reason": "social greeting"}

    # Demonstration requests ("I want to see you move", "show me you jump") — no "?" needed
    if any(p in t for p in _DEMO_PHRASES):
        return {"action": "answer", "confidence": 0.88, "reason": "demonstration request"}

    # Capability / self-referential questions about eLo ("can you X?", "are you happy?")
    if t.strip().endswith("?") and any(p in t for p in _CAPABILITY_PHRASES):
        return {"action": "answer", "confidence": 0.92, "reason": "capability question"}

    # Short affirmations checked first — they celebrate, not build
    if any(p in t for p in _SHORT_AFFIRM) and len(t.strip()) < 35:
        return {"action": "celebrate", "confidence": 0.8, "reason": "short affirmation"}

    # Explicit BUILD/CONNECT phrases override intent
    if any(p in t for p in _BUILD_PHRASES):
        return {"action": "build", "confidence": 0.9, "reason": "explicit build phrase"}
    if any(p in t for p in _CONNECT_PHRASES):
        return {"action": "connect", "confidence": 0.9, "reason": "explicit connect phrase"}

    # WO-SEAM-A: plain imperatives route to ANSWER — never reflective branches
    if any(t.strip().startswith(p) for p in _IMPERATIVE_PREFIXES):
        return {"action": "answer", "confidence": 0.9, "reason": "plain imperative command"}

    # 1. ANSWER — factual questions (must be interrogative, not just contain "what")
    if intent in ("inquiry", "recall"):
        is_question = t.strip().endswith("?") or \
                      any(t.strip().startswith(w) for w in ("what ", "how ", "why ", "who ", "when ", "where "))
        if is_question:
            return {"action": "answer", "confidence": 0.95, "reason": "factual question"}

    # 2. BUILD — creative intent in any non-negative valence (creation + neutral is still build)
    if intent == "creation" and valence not in ("negative_low", "negative_high"):
        return {"action": "build", "confidence": 0.8, "reason": "creative intent"}

    # CHALLENGE — scope/frame doubt before positive routing (question the assumption, not the person)
    if any(p in t for p in _CHALLENGE_PHRASES):
        return {"action": "challenge", "confidence": 0.75, "reason": "scope or frame doubt"}

    # 4. CELEBRATE — positive breakthrough or momentum
    if valence == "positive_high" and momentum == "building":
        return {"action": "celebrate", "confidence": 0.85, "reason": "positive momentum detected"}
    if any(p in t for p in _CELEBRATE_PHRASES):
        return {"action": "celebrate", "confidence": 0.8, "reason": "breakthrough signal"}
    if valence in ("positive_high", "positive_low") and intent in ("conversation", "emotional"):
        return {"action": "celebrate", "confidence": 0.7, "reason": "positive state"}

    # 5. REFLECT — exploring meaning or genuinely uncertain
    if intent == "emotional" and valence == "neutral":
        return {"action": "reflect", "confidence": 0.7, "reason": "emotional + neutral valence"}

    # 6. GROUND — overwhelm, distress, negative low energy, stuck
    if intent in ("emotional", "stabilise") and valence in ("negative_low", "negative_high"):
        return {"action": "ground", "confidence": 0.9, "reason": "negative emotional state"}
    if momentum == "stuck" or intent == "stabilise":
        return {"action": "ground", "confidence": 0.85, "reason": "stuck or stabilise intent"}
    if valence in ("negative_low", "negative_high"):
        return {"action": "ground", "confidence": 0.8, "reason": "negative valence"}

    # 7. WITNESS — personal emotional share, nothing to fix
    if any(p in t for p in _WITNESS_PHRASES):
        return {"action": "witness", "confidence": 0.8, "reason": "personal emotional share"}

    # 8. Building momentum — default to build, not reflect
    if momentum == "building" and valence not in ("negative_low", "negative_high"):
        return {"action": "build", "confidence": 0.65, "reason": "building momentum, stay in build mode"}

    # default
    return {"action": "reflect", "confidence": 0.5, "reason": "default — no stronger signal"}


_RESPONSE_GOAL: dict[str, str] = {
    "inquiry":      "answer",
    "creation":     "create",
    "emotional":    "stabilise",
    "recall":       "reflect",
    "conversation": "answer",
    "stabilise":    "stabilise",
    "simplify":     "clarify",
}

_GOAL_EMO_OVERRIDE: dict[str, str] = {
    "overwhelmed": "stabilise",
    "stressed":    "stabilise",
}

_COGNITIVE_LOAD: dict[str, str] = {
    _TONE_SILENCE_AWARE:  "low",
    _TONE_DIRECT:         "low",
    _TONE_CHILDLIKE_WISE: "medium",
    _TONE_WITTY:          "medium",
    _TONE_JOYFUL:         "high",
}


# FREEZE_V1_LOCK §5 — the nine, verbatim. A learned preference may select among these and
# may never extend them. Asserted in tests/test_loop7_learning_faculty.py.
_CAL_ACTIONS = ("answer", "build", "connect", "celebrate", "reflect",
                "ground", "challenge", "witness", "silence")


def decide(
    attention_model: dict,
    loop_detected: bool = False,
    user_input: str = "",
    draft_response: str = "",          # WO-RESPONSE-GATE: optional; if provided, runs quality gate
    cognitive_state=None,              # WO-RESPONSE-GATE: CognitiveState for gate checks
) -> dict:
    """
    Compute the executive decision from the attention model.

    Args:
        attention_model: Output of core.memory_relevance_filter.compute().
        loop_detected:   True if hard loop detection fired.
        draft_response:  If non-empty, the response gate evaluates it and returns
                         gated_response + gate_flags in the result dict.
        cognitive_state: CognitiveState for gate checks (optional).

    Returns:
        ExecDecision dict:
            tone          — one of 5 voice tones
            max_sentences — 1–4
            stability     — True = apply stability override
            intent        — passed through for transparency
            response_goal — clarify | stabilise | explore | create | answer | reflect
            cognitive_load — low | medium | high
            priority_order — ["primary", "secondary", "ignore"] labels
            memory_worthy  — WO-SP29: significance >= 0.72
            self_init_eligible — WO-SP29: significance >= 0.90
            gated_response — WO-RESPONSE-GATE: quality-checked response (if draft_response provided)
            gate_flags     — WO-RESPONSE-GATE: list of gate check flags
    """
    intent   = attention_model.get("intent", "conversation")
    emo      = attention_model.get("emotional_context", {})
    state    = emo.get("inferred_state", "present")
    valence  = emo.get("valence",  "neutral")
    momentum = emo.get("momentum", "stable")

    # silence signal — pure pause (ellipsis / single punctuation / empty pause)
    _t = user_input.strip()
    if set(_t).issubset(set(".,…- ")) or _t in ("...", "..", "…", "--", "—"):
        cal = {"action": "silence", "confidence": 1.0, "reason": "explicit pause input"}
    # closure signal — session-end phrases always route to witness regardless of valence
    elif emo.get("closure") == "closed" and any(p in _t.lower() for p in
            ["good session", "done for today", "i'm done", "that's enough for today",
             "signing off", "finished for today", "wrapping up", "that's all for now"]):
        cal = {"action": "witness", "confidence": 0.9, "reason": "session closure signal"}
    else:
        cal = _conversation_action(user_input, intent, valence, momentum)
    action = cal["action"]

    # ── LOOP-7 · the Executive ASKS the Learning Faculty ──────────────────────
    # David L3 2026-08-21: "SO UNFREEZE it." Unfrozen for exactly this: to ask.
    # ADR-Exec-005 D6 — learning is "a faculty the Executive ASKS, like any other …
    # never inside the Executive." The faculty lives in faculties/learning/. This is
    # the consumption point, not a learner.
    # ADR-Exec-005 D4 — may change ACTION PREFERENCE only. Never truth, never verified
    # observations, never speech verification, never Executive Authority.
    # FREEZE_V1_LOCK §5 — the 9 CAL actions are untouched. A lesson may only shift which
    # of the existing nine is preferred; it can never introduce a tenth.
    _adv = attention_model.get("learning_advice") or {}
    _prefs = _adv.get("preferences") or {}
    if _prefs and _adv.get("confidence", 0.0) >= 0.5:
        _best, _w = max(_prefs.items(), key=lambda kv: kv[1])
        # Only a POSITIVE preference for one of the frozen nine may move the action, and
        # only when the lesson is at least as strong as the rule that produced the default.
        if _best in _CAL_ACTIONS and _w > 0 and _w >= cal.get("confidence", 1.0):
            cal = {"action": _best,
                   "confidence": min(0.95, float(_w)),
                   "reason": f"learned preference ({_adv.get('rationale','')})",
                   "lesson_ids": _adv.get("lesson_ids", [])}
            action = _best

    # WO-106: Rows 4 SEE · 6 ATTEND · 16 AFFORD — consult world state + WM winner.
    # Inputs only — overrides stay within the existing nine CAL actions.
    _wm_winner = attention_model.get("wm_winner", "")
    _world     = attention_model.get("world_state", {})

    # Row 4 SEE / 16 AFFORD: user unavailable (focused elsewhere) → quieter presence.
    # Conversational build/connect/celebrate would interrupt — witness instead.
    if not _world.get("available", True):
        if action in ("build", "connect", "celebrate"):
            action = "witness"
            cal = {"action": "witness", "confidence": 0.7,
                   "reason": "world_state.available=False — quieter presence"}

    # Row 6 ATTEND: WM competition foregrounded a creative/build thread → lean in.
    if _wm_winner in ("creation", "build") and action == "reflect":
        action = "build"
        cal = {"action": "build", "confidence": 0.7,
               "reason": f"wm_winner={_wm_winner} foregrounded — active thread"}

    # Row 14 ROUTE: if eLo just fell (last move failed + fell=True), temper enthusiasm.
    # A body that just fell should witness, not build — presence first.
    _route_hist = _world.get("route_history", [])
    if _route_hist:
        _last = _route_hist[-1] if isinstance(_route_hist[-1], dict) else {}
        if not _last.get("arrived", True) and _last.get("fell", False):
            if action in ("build", "connect", "celebrate"):
                action = "witness"
                cal = {"action": "witness", "confidence": 0.7,
                       "reason": "route_history: last move fell — presence before enthusiasm"}

    # loop protection always wins
    if loop_detected or intent == "stabilise":
        return {
            "tone":              _TONE_DIRECT,
            "max_sentences":     1,
            "stability":         True,
            "intent":            intent,
            "response_goal":     "stabilise",
            "cognitive_load":    "low",
            "priority_order":    ["stabilise", "simplify", "ignore"],
            "action":            "ground",
            "valence":           valence,
            "momentum":          momentum,
            "confidence":        1.0,   # WO-112: loop override is certain
        }

    # response goal from action
    _ACTION_GOAL = {
        "answer":    "answer",
        "build":     "create",
        "connect":   "reflect",
        "celebrate": "answer",
        "reflect":   "reflect",
        "ground":    "stabilise",
        "witness":   "stabilise",
        "challenge": "reflect",
        "silence":   "stabilise",
    }
    goal = _ACTION_GOAL.get(action, "answer")

    # tone from action — positive actions MUST get positive tones
    _ACTION_TONE = {
        "celebrate": _TONE_JOYFUL,
        "build":     _TONE_JOYFUL,
        "connect":   _TONE_CHILDLIKE_WISE,
        "answer":    _TONE_DIRECT,
        "ground":    _TONE_SILENCE_AWARE,
        "witness":   _TONE_SILENCE_AWARE,
        "reflect":   _TONE_CHILDLIKE_WISE,
        "challenge": _TONE_WITTY,
        "silence":   _TONE_SILENCE_AWARE,
        "expand":    _TONE_WITTY,   # MOON/JUPITER mode — wonder and play
    }
    tone = _ACTION_TONE.get(action, _TONE_CHILDLIKE_WISE)

    tension   = emo.get("tension", 0.4)
    energy    = emo.get("energy", 0.5)

    # MOON mode — when energy is high + intent is playful/creative + tension is low,
    # shift build/connect/reflect to WITTY so play and surprise can surface
    if (energy >= 0.7 and tension < 0.4
            and action in ("build", "connect", "reflect")
            and intent in ("creation", "conversation")):
        tone = _TONE_WITTY
    is_stable = action in ("ground", "witness", "silence")
    cog_load  = _COGNITIVE_LOAD.get(tone, "medium")

    priority_order = ["stabilise", "simplify", "ignore"] if is_stable \
                     else ["primary", "secondary", "ignore"]

    max_s = _MAX_SENTENCES.get(tone, 3)
    if action == "celebrate":
        max_s = 1   # celebrate is one sentence only — no expansion

    # WO-SP29: significance gates — reads from ExecutiveContext (significance_score in world_dict)
    _sig_dict = attention_model.get("significance_score", {})
    _sig_overall = (
        _sig_dict.get("overall", 0.0) if isinstance(_sig_dict, dict)
        else float(_sig_dict or 0.0)
    )

    # WO-RESPONSE-GATE: evaluate draft response through 10-point quality gate
    _gate_flags:    list = []
    _gated_response: str = draft_response
    if draft_response:
        try:
            from runtime.response_gate import ResponseGate as _RG
            _gate_result = _RG().evaluate(draft_response, cognitive_state, attention_model)
            _gate_flags    = _gate_result.flags
            _gated_response = _gate_result.revised_response or draft_response
        except Exception as _ge:
            import logging as _logging
            _logging.getLogger(__name__).warning("response_gate FAILED: %s", _ge)

    return {
        "tone":              tone,
        "max_sentences":     max_s,
        "stability":         is_stable,
        "intent":            intent,
        "response_goal":     goal,
        "cognitive_load":    cog_load,
        "priority_order":    priority_order,
        "action":            action,
        "cal_reason":        cal.get("reason", ""),
        "valence":           valence,
        "momentum":          momentum,
        "confidence":        cal.get("confidence", 0.7),  # WO-112: thread from _conversation_action
        "memory_worthy":     _sig_overall >= 0.72,        # WO-SP29: significance memory gate
        "self_init_eligible": _sig_overall >= 0.90,       # WO-SP29: significance self-init gate
        "gated_response":    _gated_response,             # WO-RESPONSE-GATE: quality-checked response
        "gate_flags":        _gate_flags,                 # WO-RESPONSE-GATE: list of check flags
    }
