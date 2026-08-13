"""
runtime/router/meaning_engine.py — Stage 01: Input Normalisation

Convert human input into stable meaning without overwriting the original.

Output: {original, cleaned, confidence, social}
"""
from __future__ import annotations
import re

# ── Address/filler prefixes stripped when not the whole message ───────────────
_FILLER_PREFIXES = {
    "yo", "bro", "man", "g", "fam", "bruv", "blud", "mate", "oi",
    "hey", "ok", "okay", "right", "so", "well", "look", "listen",
    "boss", "chief", "king", "queen", "cuz",
}

# ── Abbreviation expansion ────────────────────────────────────────────────────
_ABBREVS = {
    "tmr":   "tomorrow",
    "tmrw":  "tomorrow",
    "2mrw":  "tomorrow",
    "2day":  "today",
    "2nite": "tonight",
    "rn":    "right now",
    "ngl":   "",            # drop — not meaningful for routing
    "imo":   "",
    "tbh":   "",
    "pls":   "please",
    "plz":   "please",
    "u":     "you",
    "ur":    "your",
    "r":     "are",
    "4":     "for",
    "b4":    "before",
    "thx":   "thanks",
    "lmk":   "let me know",
    "asap":  "as soon as possible",
    "yday":  "yesterday",
    "atm":   "at the moment",
    "rn":    "right now",
    "nvm":   "never mind",
}

# ── Repeated character collapse ───────────────────────────────────────────────
_REPEAT_RE = re.compile(r'(.)\1{2,}')  # "sooooo" → "so", "broooo" → "bro"

# ── Social signals — inputs that are pure social acts, not commands ───────────
_SOCIAL_GREETINGS = {
    "yo", "hey", "hi", "hello", "wagwan", "wah gwaan", "safe", "aight",
    "what's good", "what you saying", "you calm", "gang gang",
}
_SOCIAL_AFFIRM = {"safe", "aight", "say less", "gg", "gz", "gang gang"}
_SOCIAL_FAREWELL = {"bye", "later", "peace", "laters", "take care", "good night", "goodnight"}


def normalise(raw: str) -> dict:
    """
    Stage 01 — normalise raw input into stable meaning.

    Returns:
        original   — untouched input
        cleaned    — normalised for routing
        confidence — 1.0 if no changes, lower if significant transforms applied
        social     — "greeting" | "farewell" | "affirmation" | "" if purely social
    """
    original = raw
    t = raw.lower().strip()

    # Detect purely social inputs before any stripping
    social = ""
    if t in _SOCIAL_GREETINGS:
        social = "greeting"
    elif t in _SOCIAL_AFFIRM:
        social = "affirmation"
    elif t in _SOCIAL_FAREWELL:
        social = "farewell"

    # Collapse repeated letters ("sooooo" → "so", "yooo" → "yo")
    t = _REPEAT_RE.sub(r'\1\1', t)  # keep two, drop the rest

    # Strip leading filler words only when input has other content
    words = t.split()
    stripped = False
    while len(words) > 1 and words[0] in _FILLER_PREFIXES:
        if len(words) <= 2 and len(words[-1]) <= 2:
            break  # don't strip to a single short token like "g"
        words.pop(0)
        stripped = True
    t = " ".join(words)

    # Expand abbreviations word by word
    expanded_words = []
    changed = stripped
    for w in t.split():
        if w in _ABBREVS:
            replacement = _ABBREVS[w]
            if replacement:
                expanded_words.append(replacement)
            changed = True
        else:
            expanded_words.append(w)
    t = " ".join(expanded_words).strip()

    # Normalise whitespace and punctuation
    t = re.sub(r'\s{2,}', ' ', t).strip()
    t = re.sub(r'[!]{2,}', '!', t)
    t = re.sub(r'[?]{2,}', '?', t)

    confidence = 1.0 if not changed else 0.9

    return {
        "original":   original,
        "cleaned":    t,
        "confidence": confidence,
        "social":     social,
    }
