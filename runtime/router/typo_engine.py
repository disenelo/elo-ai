"""
runtime/router/typo_engine.py — Stage 02: Typo + Spell Repair

Recover meaning from malformed input. Never forces a correction.
Returns candidates with confidence so the gate can decide to auto-interpret or confirm.

Output: {interpretation, confidence, candidates, changed}
"""
from __future__ import annotations
import re

# ── Hard-coded typo dictionary ────────────────────────────────────────────────
# Covers the highest-frequency real typos seen in voice/fast-typing contexts.
_KNOWN_TYPOS: dict[str, str] = {
    # Spotify
    "spotfy":   "spotify",
    "spottfy":  "spotify",
    "spotifty": "spotify",
    "soptify":  "spotify",
    # Remind / Reminder
    "rmind":    "remind",
    "remid":    "remind",
    "remidner": "reminder",
    "remidn":   "remind",
    "remaind":  "remind",
    # Timer
    "tmer":     "timer",
    "timre":    "timer",
    # Calendar
    "calander": "calendar",
    "calender": "calendar",
    # Weather
    "weatha":   "weather",
    "wheather": "weather",
    "weathr":   "weather",
    "weater":   "weather",
    "wetha":    "weather",
    "wether":   "weather",
    "whts":     "what's",
    "wht":      "what",
    "wuts":     "what's",
    # Notes / Obsidian
    "nots":     "notes",
    "noets":    "notes",
    # Messages
    "mesage":   "message",
    "messge":   "message",
    # Volume
    "volum":    "volume",
    "voume":    "volume",
    # Play
    "pla":      "play",
    "paly":     "play",
    "plya":     "play",
    # Open
    "opne":     "open",
    "oebn":     "open",
    # Search
    "serach":   "search",
    "saerch":   "search",
    # Clipboard
    "clipbord": "clipboard",
    # Translate
    "translat": "translate",
    "tranlsate":"translate",
    # Calculator
    "calcuator":"calculator",
    "calculatr":"calculator",
    # Brightness
    "brigthness":"brightness",
    "brigtness": "brightness",
    # Screenshot
    "sceenshot": "screenshot",
    "screnshot": "screenshot",
    # Common fast-typing word errors
    "liek":     "like",
    "lke":      "like",
    "teh":      "the",
    "taht":     "that",
    "thta":     "that",
    "jsut":     "just",
    "juts":     "just",
    "fro":      "from",
    "frmo":     "from",
    "fo":       "for",
    "ot":       "to",
    "nad":      "and",
    "adn":      "and",
    "od":       "do",
    "dont":     "don't",
    "cant":     "can't",
    "wont":     "won't",
    "wotn":     "won't",
    "yoru":     "your",
    "wiht":     "with",
    "tath":     "that",
    "hte":      "the",
}

# ── Routing vocabulary — words eLo knows as commands or subjects ───────────────
_VOCAB = [
    "play", "pause", "skip", "stop", "next", "previous",
    "spotify", "music", "song", "track", "playlist",
    "remind", "reminder", "reminders", "timer", "alarm",
    "weather", "forecast", "temperature",
    "calendar", "schedule", "meeting", "event",
    "notes", "obsidian", "vault", "journal",
    "message", "send", "text", "imessage",
    "search", "find", "look", "google", "wiki",
    "translate", "language",
    "time", "date", "day",
    "calculator", "calculate", "math",
    "news", "headlines",
    "clipboard", "copy", "paste",
    "volume", "brightness", "dark", "light", "screenshot",
    "open", "launch", "close", "quit", "focus",
    "blender", "unity", "vscode", "safari", "chrome", "finder",
    "github", "repo", "commit",
    "read", "file", "folder",
    "write", "draft", "compose",
    "remember", "save", "note",
    # Common words that appear in command sentences
    "like", "from", "just", "that", "with", "your", "into",
    # Common verbs and words that fuzzy-match vocab items incorrectly
    # e.g. "needs" → "news" (dist 2), "session" → "search" (dist 3), etc.
    "needs", "need", "needed", "needing",
    "feels", "feel", "seems", "looks", "works", "helps", "makes", "takes",
    "tells", "means", "comes", "goes", "says", "shows", "knows",
    "something", "nothing", "anything", "everything",
    "session", "sessions", "debug", "debugging",
    "hows", "hmm", "hm", "yeah", "yep", "nope", "nah",
]


# ── Protected words — never "repair" these, they are valid ───────────────────
# Slang, common words, and anything that fuzzy-matches something wrong
_PROTECTED: frozenset[str] = frozenset({
    # south London / patois slang
    "safe", "peak", "buff", "nang", "leng", "peng", "bare", "ends", "mandem",
    "wagwan", "irie", "nuff", "blud", "fam", "bruv", "innit", "aight",
    # common words that have close vocab neighbours
    "today", "copy", "move", "note", "file", "open", "dark", "light",
    "time", "day", "now", "play", "stop", "set", "get", "put", "run",
    "good", "next", "last", "more", "less", "back", "just", "some",
    "like", "from", "that", "with", "your", "into", "this", "there",
    "then", "than", "what", "when", "where", "which", "while",
    # system/volume words that fuzzy-match incorrectly
    "louder", "quieter", "softer", "dimmer", "brighter", "muted", "unmute",
    "lower", "higher", "louder", "volume", "screenshot", "darkmode", "lightmode",
    # WO-039: past-tense and present-tense English verbs that fuzzy-match to
    # command words (e.g. "built" → "quit" at edit-distance 2, confidence 0.80)
    # — never repair these, they are valid conversational words
    "built", "build", "builds", "building",
    "related", "relate", "relates", "relating",
    "called", "calls", "calling",
    "filled", "fills", "filling",
    "killed", "kills", "killing",
    "billed", "bills", "billing",
    "chilled", "chills", "chilling",
    "skilled", "skills",
    "willed", "spilled", "spills",
    "told", "held", "felt", "dealt",
    "closed", "closes", "closing",
    "used", "uses", "using",
    "cued", "cues", "cueing",
    "queued", "queues", "queuing",
    "quit", "quits", "quitting",  # also protect "quit" itself as a conversational word
    "close", "closes",            # protect so "close" in prose isn't re-repaired
})


def _edit_distance(a: str, b: str) -> int:
    """Levenshtein distance — used for fuzzy matching against vocabulary."""
    if a == b:
        return 0
    la, lb = len(a), len(b)
    if la == 0:
        return lb
    if lb == 0:
        return la
    prev = list(range(lb + 1))
    for i, ca in enumerate(a):
        curr = [i + 1] + [0] * lb
        for j, cb in enumerate(b):
            curr[j + 1] = min(
                prev[j + 1] + 1,
                curr[j] + 1,
                prev[j] + (0 if ca == cb else 1),
            )
        prev = curr
    return prev[lb]


# WO-039: command words require a near-exact (distance=0 or 1) match to avoid
# coercing prose words like "built" → "quit".  Any edit-distance-2 match to a
# command word gets rejected even if it would otherwise pass the threshold.
_COMMAND_WORDS: frozenset[str] = frozenset({"quit", "close", "kill", "open", "stop", "exit"})


def _fuzzy_match(word: str) -> tuple[str, float] | None:
    """
    Return (best_match, confidence) from _VOCAB if close enough.
    Only applies to words >= 4 chars to avoid false positives on short words.
    """
    if len(word) < 4 or word in _PROTECTED:
        return None
    best_word = ""
    best_dist = 999
    for v in _VOCAB:
        d = _edit_distance(word, v)
        if d < best_dist:
            best_dist = d
            best_word = v
    # Accept if edit distance <= 2 for words of length 5+, or <= 1 for shorter
    threshold = 2 if len(word) >= 5 else 1
    # WO-039: command words require distance=0 (exact) to avoid prose coercion
    if best_word in _COMMAND_WORDS and best_dist > 0:
        return None
    if best_dist <= threshold:
        confidence = 1.0 - (best_dist / max(len(word), 1)) * 0.5
        return best_word, confidence
    return None


def repair(text: str) -> dict:
    """
    Stage 02 — attempt typo repair on cleaned input.

    Returns:
        interpretation — repaired text (best guess)
        confidence     — 0.0–1.0
        candidates     — list of plausible interpretations
        changed        — True if any word was repaired
    """
    words = text.lower().split()
    repaired: list[str] = []
    candidates_per_word: list[list[str]] = []
    changed = False

    for w in words:
        if w in _PROTECTED:
            repaired.append(w)
            candidates_per_word.append([w])
            continue
        if w in _KNOWN_TYPOS:
            fix = _KNOWN_TYPOS[w]
            repaired.append(fix)
            candidates_per_word.append([fix])
            changed = True
        else:
            match = _fuzzy_match(w)
            if match:
                best, conf = match
                repaired.append(best)
                candidates_per_word.append([best, w])
                changed = True
            else:
                repaired.append(w)
                candidates_per_word.append([w])

    interpretation = " ".join(repaired).strip()
    # If nothing changed, confidence is 1.0; every repair lowers it slightly
    confidence = 1.0 if not changed else 0.82

    # Build flat candidate list — primary interpretation + alternatives
    candidates = [interpretation]
    if changed:
        candidates.append(text)  # original as fallback

    return {
        "interpretation": interpretation,
        "confidence":     confidence,
        "candidates":     candidates,
        "changed":        changed,
    }
