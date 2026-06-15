"""
continuity/identity_state.py — meaning-memory data structure.

Stores what mattered across sessions — not transcripts.
Fields are meaning units: emotion, theme, project, direction.
"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class IdentityState:
    session_theme:       str    = ""      # dominant recurring theme
    confidence:          float  = 0.0    # 0–1, based on session count + consistency
    emotional_direction: str    = ""      # "opening", "building", "contracting", "settling"
    active_project:      str    = ""      # which project was most present
    relationship_shift:  str    = ""      # "closer", "more distant", "same", "uncertain"
    what_changed:        list   = field(default_factory=list)   # new things that appeared
    what_stayed:         list   = field(default_factory=list)   # things that kept returning
    what_matters:        str    = ""      # single most important thread

    def is_empty(self) -> bool:
        return not self.session_theme and not self.what_matters


# emotional direction mapping — from tone history
_TONE_TO_DIRECTION = {
    "energised":    "building",
    "low-energy":   "contracting",
    "overwhelmed":  "contracting",
    "stressed":     "contracting",
    "present":      "settling",
}

# project keywords — used to identify which project was present
_PROJECT_KEYWORDS = {
    "os":      ["os", "cognitive", "language", "prompt", "backend", "llm", "elo os"],
    "game":    ["game", "unity", "player", "enemy", "level", "elo-planet"],
    "robot":   ["robot", "physical", "animatronic", "servo", "raspberry"],
    "book":    ["book", "narrative", "story", "chapter", "writing"],
    "kickstarter": ["kickstarter", "funding", "launch", "backers"],
}

# theme keywords
_THEME_KEYWORDS = {
    "building":    ["build", "create", "make", "design", "implement", "ship"],
    "clarity":     ["clarity", "clear", "figured", "understand", "clicked"],
    "identity":    ["identity", "who", "what is elo", "purpose", "meaning"],
    "connection":  ["connect", "together", "same idea", "converge", "related"],
    "momentum":    ["momentum", "moving", "progress", "forward", "starting"],
    "overwhelm":   ["overwhelm", "too much", "stuck", "blocked", "scattered"],
    "presence":    ["presence", "here", "real", "physical", "alive"],
}
