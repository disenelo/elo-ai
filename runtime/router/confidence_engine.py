"""
runtime/router/confidence_engine.py — Stage 09: Confidence + Self-Awareness

Aggregate confidence signals and decide: proceed, confirm, or ask.
Tracks uncertainty. Never pretends.

Output: {confidence, action, message, uncertain_about}
"""
from __future__ import annotations

# ── Thresholds ────────────────────────────────────────────────────────────────
_AUTO_THRESHOLD    = 0.82   # proceed without asking
_CONFIRM_THRESHOLD = 0.60   # propose and confirm
# below _CONFIRM_THRESHOLD → ask for clarification


def score(signals: dict[str, float]) -> dict:
    """
    Aggregate confidence signals into a routing decision.

    Args:
        signals — dict of {signal_name: confidence_0_to_1}
                  e.g. {"meaning": 0.9, "typo": 0.8, "intent": 0.75}

    Returns:
        confidence     — weighted average
        action         — "proceed" | "confirm" | "ask"
        message        — human-readable note for eLo to optionally surface
        uncertain_about — which signal drove uncertainty (or "")
    """
    if not signals:
        return {"confidence": 0.5, "action": "confirm", "message": "Low certainty.", "uncertain_about": "all"}

    # Simple mean — all signals equal weight for now
    avg = sum(signals.values()) / len(signals)
    weakest = min(signals, key=signals.get)
    weakest_val = signals[weakest]

    if avg >= _AUTO_THRESHOLD:
        action = "proceed"
        message = ""
        uncertain_about = ""
    elif avg >= _CONFIRM_THRESHOLD:
        action = "confirm"
        message = f"I think I understood — want me to go ahead?"
        uncertain_about = weakest if weakest_val < 0.7 else ""
    else:
        action = "ask"
        message = "I'm not sure what you mean — can you rephrase?"
        uncertain_about = weakest

    return {
        "confidence":     round(avg, 3),
        "action":         action,
        "message":        message,
        "uncertain_about": uncertain_about,
    }


def from_pipeline(meaning: dict, typo: dict, intent: dict) -> dict:
    """
    Convenience wrapper — build signals from pipeline stage outputs.
    """
    signals: dict[str, float] = {}

    if meaning:
        signals["meaning"] = meaning.get("confidence", 0.9)
    if typo:
        signals["typo"] = typo.get("confidence", 1.0)
    if intent:
        signals["intent"] = intent.get("confidence", 0.5)

    return score(signals)
