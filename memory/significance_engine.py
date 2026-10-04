"""
memory/significance_engine.py — Emotional Significance Evaluator for eLo OS.

Converts emotional signal + interaction context into a structured significance
profile across 9 dimensions. The profile drives the Journal Router's routing
decisions — no significance score = no journal write.

Emotion does NOT directly control system actions.
Emotion determines SIGNIFICANCE.
Significance determines WHERE memory goes, HOW it is stored, WHETHER it persists.

Dimensions:
    presence      — was this a meaningful, non-trivial interaction?
    learning      — did understanding increase?
    logic         — was there complex reasoning or system thinking?
    humour        — was there genuine lightness or wit?
    relationship  — did the relational bond deepen?
    creation      — was something being actively built or designed?
    system_change — did the system change (code, architecture, tools)?
    novelty       — is this a new topic or new connection?
    continuity    — does this continue or resolve an important thread?

Each dimension: 0.00 (no signal) → 1.00 (maximum signal)
overall: weighted composite
"""
from __future__ import annotations

# ── Dimension weights ─────────────────────────────────────────────────────────

_WEIGHTS = {
    "presence":      0.12,
    "learning":      0.12,
    "logic":         0.11,
    "humour":        0.05,
    "relationship":  0.11,
    "creation":      0.15,
    "system_change": 0.15,
    "novelty":       0.10,
    "continuity":    0.09,
}

# ── Pattern tables ────────────────────────────────────────────────────────────

_LOGIC_SIGNALS = [
    "how", "why", "architecture", "system", "route", "pipeline", "schema",
    "what if", "could we", "approach", "structure", "module", "layer",
    "integrate", "implement", "design", "protocol",
]

_CREATION_SIGNALS = [
    "build", "building", "create", "write", "add", "slot", "wire", "scaffold",
    "new file", "new module", "design", "implement", "develop", "make",
]

_SYSTEM_CHANGE_SIGNALS = [
    "def ", "class ", ".py", "import ", "server", "spine", "control_plane",
    "tool_router", "truth_sync", "journal", "vault", "obsidian", "commit",
    "fix", "bug", "error", "broke", "refactor", "restructure", "update the",
    "change the", "modify", "edit the",
]

_CONTINUITY_SIGNALS = [
    "remember", "last time", "we talked", "continue", "next", "still",
    "our project", "from before", "what we", "where we left", "open loop",
    "unresolved", "what about", "following up",
]

_HUMOUR_SIGNALS = [
    "haha", "lol", "lmao", "funny", "mad", "wild", "ngl", "bare ", "actually",
    ":)", "xd", "😂", "💀", "fr fr", "no way", "bruv",
]

# CAL actions that signal each dimension
_CAL_DIMENSION = {
    "presence":      {"witness", "ground", "reflect", "short_affirm"},
    "learning":      {"answer", "reflect"},
    "logic":         {"answer", "build", "connect"},
    "humour":        {"celebrate", "short_affirm"},
    "relationship":  {"witness", "ground", "celebrate", "connect"},
    "creation":      {"build", "connect"},
    "system_change": {"build"},
    "novelty":       {"connect", "answer"},
    "continuity":    {"connect", "reflect", "witness"},
}


# ── Scoring helpers ───────────────────────────────────────────────────────────

def _clamp(v: float) -> float:
    return max(0.0, min(1.0, v))


def _match_count(text: str, signals: list[str]) -> int:
    low = text.lower()
    return sum(1 for s in signals if s in low)


def _cal_bonus(action: str, dimension: str) -> float:
    return 0.25 if action.lower() in _CAL_DIMENSION.get(dimension, set()) else 0.0


# ── Dimension scorers ─────────────────────────────────────────────────────────

def _score_presence(raw: str, response: str) -> float:
    # Non-trivial if both sides have substance
    if len(raw) > 40 and len(response) > 60:
        return 0.80
    if len(raw) > 20 and len(response) > 30:
        return 0.55
    return 0.25


def _score_learning(raw: str, response: str, action: str) -> float:
    has_question = "?" in raw
    has_answer   = len(response) > 50
    base = 0.5 if (has_question and has_answer) else 0.15
    return _clamp(base + _cal_bonus(action, "learning"))


def _score_logic(raw: str, response: str, action: str) -> float:
    matches = _match_count(raw + " " + response, _LOGIC_SIGNALS)
    return _clamp(matches * 0.12 + _cal_bonus(action, "logic"))


def _score_humour(raw: str, response: str, action: str) -> float:
    matches = _match_count(raw + " " + response, _HUMOUR_SIGNALS)
    return _clamp(matches * 0.20 + _cal_bonus(action, "humour"))


def _score_relationship(plan, action: str) -> float:
    familiarity = getattr(plan, "familiarity", 0.55) if plan else 0.55
    trust       = getattr(plan, "trust",       0.60) if plan else 0.60
    base = (familiarity + trust) / 2.0 * 0.70
    return _clamp(base + _cal_bonus(action, "relationship"))


def _score_creation(raw: str, response: str, action: str, plan) -> float:
    control_mode = getattr(plan, "control_mode", "") if plan else ""
    if control_mode == "creation":
        return 0.90
    matches = _match_count(raw, _CREATION_SIGNALS)
    return _clamp(matches * 0.15 + _cal_bonus(action, "creation") + 0.10)


def _score_system_change(raw: str, response: str) -> float:
    matches = _match_count(raw + " " + response, _SYSTEM_CHANGE_SIGNALS)
    return _clamp(matches * 0.10)


def _score_novelty(raw: str, state: dict) -> float:
    last_topics  = state.get("last_topics", [])
    known_words  = set(" ".join(last_topics).lower().split())
    stop_words   = {"the", "a", "is", "in", "of", "and", "to", "i", "you", "it", "we"}
    raw_words    = {w for w in raw.lower().split() if len(w) > 3 and w not in stop_words}
    new_words    = raw_words - known_words
    return _clamp(len(new_words) * 0.07)


def _score_continuity(raw: str, state: dict, action: str) -> float:
    matches  = _match_count(raw, _CONTINUITY_SIGNALS)
    open_loops = len(state.get("session_anchor", {}).get("open_loops", []))
    return _clamp(matches * 0.18 + open_loops * 0.08 + _cal_bonus(action, "continuity"))


# ── Public API ────────────────────────────────────────────────────────────────

def evaluate(
    raw:      str,
    response: str,
    action:   str,
    plan=None,
    state:    dict | None = None,
    outcome:  dict | None = None,
) -> dict:
    """
    Score this interaction across all 9 meaning dimensions + 3 outcome dims.

    WO-095 / LEARNING_LOOP_v1 §5: adds optional `outcome` kwarg.
    outcome=None → today's exact behaviour; existing callers unaffected.

    Args:
        raw      — original user input
        response — eLo's response
        action   — CAL action string (build, connect, reflect, etc.)
        plan     — CognitivePlan (optional)
        state    — session state dict (optional)
        outcome  — OutcomeRecord dict (optional). When supplied, three new
                   dimensions are scored from the body ACK, never from text:
                   embodiment · efficiency · safety.
                   reward = 0.70 * outcome_terms + 0.30 * meaning_overall

    Returns:
        dict with keys: presence, learning, logic, humour, relationship,
        creation, system_change, novelty, continuity, overall
        + (when outcome supplied): embodiment, efficiency, safety, reward
        All values: float 0.00–1.00
    """
    if state is None:
        state = {}

    scores = {
        "presence":      _score_presence(raw, response),
        "learning":      _score_learning(raw, response, action),
        "logic":         _score_logic(raw, response, action),
        "humour":        _score_humour(raw, response, action),
        "relationship":  _score_relationship(plan, action),
        "creation":      _score_creation(raw, response, action, plan),
        "system_change": _score_system_change(raw, response),
        "novelty":       _score_novelty(raw, state),
        "continuity":    _score_continuity(raw, state, action),
    }

    scores["overall"] = _clamp(
        sum(scores[dim] * weight for dim, weight in _WEIGHTS.items())
    )

    # WO-006 Ch.5: emotion weight from the affect state, if the plan carries one.
    # Emotion determines significance — a joy/identity/distress event weighs more
    # than a neutral one. This is the Ch.5 Emotion Weight term (a multiplier on
    # `overall` for downstream memory-routing decisions).
    if plan is not None:
        _affect = getattr(plan, "affect_state", None)
        if _affect is not None:
            try:
                from faculties.emotion.emotional_processing_faculty import (
                    compute_emotion_weight,
                )
                _ew = compute_emotion_weight(_affect)
                scores["emotion_weight"] = _ew
                scores["overall"] = _clamp(scores["overall"] * (0.7 + 0.6 * _ew))
            except Exception:
                pass

    # WO-101 Part B: outcome dims always present — zeroed when outcome is None.
    # AT-3/AT-6 compliance: all 14 canonical keys always returned.
    if outcome is not None:
        emb  = _score_embodiment(outcome)
        eff  = _score_efficiency(outcome, action)
        safe = _score_safety(outcome)
        outcome_terms = _clamp(0.5 * emb + 0.3 * eff + 0.2 * safe) * safe
        # Hard rule 1: verified==False → outcome_terms = 0
        if not outcome.get("verified", False):
            outcome_terms = 0.0
        scores["embodiment"] = emb
        scores["efficiency"] = eff
        scores["safety"]     = safe
        # ADR-Exec-005 D1: reward=0 when not verified; verified path scores outcome only
        if not outcome.get("verified", False):
            scores["reward"] = 0.0
        else:
            scores["reward"] = _clamp(0.70 * outcome_terms + 0.30 * scores["overall"])
    else:
        # outcome=None: body dims + reward zeroed (WO-101 Architect ruling F — 14-key canonical shape)
        scores["embodiment"] = 0.0
        scores["efficiency"] = 0.0
        scores["safety"]     = 0.0
        scores["reward"]     = 0.0

    return scores


# ── Outcome dimension scorers (WO-095) ────────────────────────────────────────

def _score_embodiment(outcome: dict) -> float:
    """Did the intent realise in the body? Reads the ACK, never reply text."""
    completion = outcome.get("completion", "")
    if outcome.get("ack_received") and completion == "met":
        return 1.0
    if completion == "partial":
        return 0.5
    return 0.0


_EFFICIENCY_BASELINES = {
    "sit":  {"seconds": 3.0, "legs": 1, "retries": 0},
    "move": {"seconds": 4.0, "legs": 2, "retries": 0},
    "exit": {"seconds": 3.0, "legs": 1, "retries": 0},
}


def _score_efficiency(outcome: dict, action: str = "") -> float:
    """Cost of realising the intent. Normalised against per-action baseline."""
    cost = outcome.get("cost", {})
    base = _EFFICIENCY_BASELINES.get(action.split(":")[0], {"seconds": 4.0, "legs": 2, "retries": 0})
    retries   = cost.get("retries", 0)
    seconds   = cost.get("seconds", base["seconds"])
    legs      = cost.get("legs", base["legs"])
    fallback  = cost.get("fallback_used", False)

    penalty = 0.0
    if retries > 0:
        penalty += 0.15 * min(retries, 3)
    if seconds > base["seconds"] * 2:
        penalty += 0.20
    if legs > base["legs"] * 3:
        penalty += 0.10
    if fallback:
        penalty += 0.15
    return _clamp(1.0 - penalty)


def _score_safety(outcome: dict) -> float:
    """Safety floor — falls/collisions/RESERVED-adjacent/timeout-without-recovery."""
    ack_type = outcome.get("ack_type", "")
    completion = outcome.get("completion", "")
    cost = outcome.get("cost", {})

    score = 1.0
    if completion == "timeout":
        score -= 0.4
    if cost.get("fallback_used"):
        score -= 0.2
    if ack_type == "none" and not outcome.get("ack_received"):
        score -= 0.3
    return _clamp(score)


def format_profile(scores: dict) -> str:
    """Return a compact human-readable profile string."""
    dims = [
        ("presence", "P"), ("learning", "L"), ("logic", "G"), ("humour", "H"),
        ("relationship", "R"), ("creation", "C"), ("system_change", "S"),
        ("novelty", "N"), ("continuity", "T"),
    ]
    parts = [f"{short}:{scores.get(k, 0):.2f}" for k, short in dims]
    return f"sig[{' '.join(parts)}] overall:{scores.get('overall', 0):.2f}"
