"""
blender_bridge/shared_tables.py — Canonical Python↔Unity alias tables (WO-010)

Single source of truth for mood aliases and animation clip aliases.
Both Python (embodiment_publisher.py, animation_driver.py) and Unity (MoodPalette,
AnimatorController) must stay in sync with these tables.

Unity Agent: read shared_tables.json (auto-generated alongside this file)
for the same data in Unity-friendly JSON.

To regenerate shared_tables.json after any edit here:
    python3 blender_bridge/shared_tables.py

No runtime dependencies — safe to import anywhere.
"""

from __future__ import annotations


# ── Mood alias table ─────────────────────────────────────────────────────────
# Maps Python light-engine 20-state vocabulary → Unity MoodPalette vocabulary.
# Unity MoodPalette handles 8 moods; unmapped values pass through (Unity falls to neutral).
#
# Canonical 8 Unity moods (from EloMoodPalette.cs / MoodPalette ScriptableObject):
#   neutral | calm | curious | alert | excited | joy | sad | distress

MOOD_ALIASES: dict[str, str] = {
    # curiosity family
    "curiosity":      "curious",
    "wonder":         "curious",
    "interest":       "curious",
    # alert family
    "challenge":      "alert",
    "focus":          "alert",
    "thinking":       "alert",
    "processing":     "alert",
    "alert":          "alert",
    # calm family
    "comfort":        "calm",
    "reflection":     "calm",
    "repair":         "calm",
    "connection":     "calm",
    "witnessing":     "calm",
    "calm":           "calm",
    "meditative":     "calm",
    # excited family
    "celebration":    "excited",
    "excitement":     "excited",
    # joy family
    "joy":            "joy",
    "love":           "joy",
    "gratitude":      "joy",
    # sad family
    "sadness":        "sad",
    "melancholy":     "sad",
    "longing":        "sad",
    # distress family
    "distress":       "distress",
    "overwhelm":      "distress",
    "fear":           "distress",
    "panic":          "distress",
    # neutral
    "waiting":        "neutral",
    "listening":      "neutral",
    "neutral":        "neutral",
    "resting":        "neutral",
    # music mood labels (from spotify_agent._music_mood_blend)
    "playful":        "excited",
    "focused":        "alert",
    # state_writer legacy vocab (consolidated here; local dict removed from state_writer)
    "open":           "neutral",
    "warm":           "calm",
    "quiet":          "calm",
    "lit":            "joy",
}

UNITY_MOOD_STATES: tuple[str, ...] = (
    "neutral", "calm", "curious", "alert", "excited", "joy", "sad", "distress",
)


# ── Animation clip alias table ────────────────────────────────────────────────
# Maps bare/alias names → canonical eLo_ NLA clip names.
# These must match the retargeter NLA action names exactly (eLo_ prefix).

ANIMATION_ALIASES: dict[str, str] = {
    "idle":      "eLo_Idle",
    "walk":      "eLo_Walk",
    "run":       "eLo_Run",
    "longj":     "eLo_LongJ",
    "longjump":  "eLo_LongJ",
    "jump":      "eLo_LongJ",
    "calm":      "eLo_Calm",
    "meditate":  "eLo_Calm",
    # presence-engine aliases
    "breathe":   "eLo_Idle",
    "settle":    "eLo_Idle",
    "float":     "eLo_Calm",
    "sit":       "eLo_Idle",
    "pace":      "eLo_Walk",
    "wander":    "eLo_Walk",
    "hop":       "eLo_LongJ",
}

KNOWN_CLIPS: frozenset[str] = frozenset({
    "eLo_Idle", "eLo_Walk", "eLo_Run", "eLo_LongJ", "eLo_Calm",
})


# ── Lookup helpers ────────────────────────────────────────────────────────────

def resolve_mood(python_mood: str) -> str:
    """Map a Python light-engine mood → Unity MoodPalette mood."""
    return MOOD_ALIASES.get(python_mood, python_mood)


def resolve_clip(animation: str) -> str:
    """Map an animation alias → canonical eLo_ clip, defaulting to eLo_Idle."""
    name = animation.lower().strip()
    if name.startswith("elo_"):
        name = name[4:]
    return ANIMATION_ALIASES.get(name, "eLo_Idle")


# ── JSON export (run directly to regenerate shared_tables.json) ───────────────

def export_json(path: str | None = None) -> str:
    """Serialise both tables to JSON for Unity Agent consumption."""
    import json, os
    data = {
        "version":           "1.0.0",
        "description":       "Canonical Python↔Unity alias tables. Source: blender_bridge/shared_tables.py",
        "mood_aliases":      MOOD_ALIASES,
        "unity_mood_states": list(UNITY_MOOD_STATES),
        "animation_aliases": ANIMATION_ALIASES,
        "known_clips":       sorted(KNOWN_CLIPS),
    }
    out = json.dumps(data, indent=2, ensure_ascii=False)
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shared_tables.json")
    with open(path, "w", encoding="utf-8") as f:
        f.write(out)
    return path


if __name__ == "__main__":
    path = export_json()
    print(f"Exported: {path}")
