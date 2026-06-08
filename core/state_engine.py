"""
core/state_engine.py — eLo AI conversational state.

Tracks per-session state that persists across turns:
    - active mode (studio / companion / adventure)
    - turn count
    - recent emotion arc
    - recently used question patterns (for deduplication)
    - active project tag

This is the memory of the conversation itself — not what was said,
but how the conversation has been moving.
"""


class ConversationState:
    """Mutable state container for a single eLo session."""

    def __init__(self, default_mode: str = "companion"):
        self.mode:              str   = default_mode
        self.turn_count:        int   = 0
        self.active_project:    str   = "elo_core"
        self._emotion_arc:      list  = []   # last N detected emotions
        self._recent_questions: list  = []   # closing questions used recently
        self._arc_max:          int   = 8
        self._question_max:     int   = 3

    # ── mode ──────────────────────────────────────────────────────────────────

    def set_mode(self, mode: str) -> bool:
        """Set mode. Returns True if mode changed, False if already set."""
        if mode in ("studio", "companion", "adventure") and mode != self.mode:
            self.mode = mode
            return True
        return False

    # ── turn lifecycle ─────────────────────────────────────────────────────────

    def start_turn(self, emotion: str, project: str):
        """Called at the start of each turn to update running state."""
        self.turn_count      += 1
        self.active_project   = project
        self._emotion_arc.append(emotion)
        if len(self._emotion_arc) > self._arc_max:
            self._emotion_arc.pop(0)

    def record_question(self, question: str):
        """Track a closing question that was used this session."""
        self._recent_questions.append(question)
        if len(self._recent_questions) > self._question_max:
            self._recent_questions.pop(0)

    # ── queries ────────────────────────────────────────────────────────────────

    def dominant_emotion(self) -> str:
        """Return the most frequent emotion in the recent arc, or 'neutral'."""
        if not self._emotion_arc:
            return "neutral"
        from collections import Counter
        return Counter(self._emotion_arc).most_common(1)[0][0]

    def question_was_recent(self, question: str) -> bool:
        return question in self._recent_questions

    def turns_since_mode_change(self) -> int:
        """Approximate — returns total turn count as proxy for mode age."""
        return self.turn_count

    def to_dict(self) -> dict:
        return {
            "mode":            self.mode,
            "turn_count":      self.turn_count,
            "active_project":  self.active_project,
            "dominant_emotion": self.dominant_emotion(),
        }
