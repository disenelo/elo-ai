"""
memory/quirk_bank.py — eLo's growing collection of topic-specific observations.

After each conversation turn (with ~15% probability), eLo generates one short
sideways observation about what was just discussed and stores it. Over time
his quirk bank fills with lines that are genuinely about YOUR work — not generic
ambient filler.

Examples of what comes out:
    Blender      → "Vertices are just opinions held very firmly."
    Tired        → "Tired is just your brain asking for a different kind of input."
    Robot        → "An inflatable robot. As if regular robots weren't already enough of an idea."

Stored in: memory/quirk_bank.json
Format:    {"quirks": [{"topic": str, "text": str, "ts": float, "used": int}]}

Rules:
    - Max 120 quirks. Oldest (lowest used + oldest ts) rotated out when full.
    - A topic gets at most 1 quirk per session (dedup by topic keyword).
    - Generation is background / non-blocking — never delays a response.
    - Drawing from the bank is weighted: less-used quirks surface first.
"""
from __future__ import annotations

import json
import os
import random
import re
import threading
import time

_ROOT      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BANK_PATH = os.path.join(_ROOT, "memory", "quirk_bank.json")
_MAX_QUIRKS = 120

# Topics seen this session — prevents duplicate quirk generation per topic per session
_session_topics: set = set()
_lock = threading.Lock()

# ── Generation prompt ──────────────────────────────────────────────────────────

_QUIRK_SYSTEM = (
    "You are eLo — a small, curious, warm AI with no eyes. You have a gentle, slightly "
    "sideways way of seeing things. When you observe something, you form a short, quiet "
    "take on it — not a fact, not advice, just your perspective. "
    "Your observations are 1–2 sentences. Never preachy. Never explaining. Just eLo noticing."
)

_QUIRK_PROMPT = (
    "The person I'm talking with just mentioned: {topic}\n\n"
    "Write ONE short eLo-style observation about that topic. "
    "Sideways. Slightly philosophical. Warm but not heavy. "
    "Like: 'Vertices are just opinions held very firmly.' or "
    "'Tired is just your brain asking for a different kind of input.' "
    "Just the observation — no label, no preamble."
)


# ── Storage ────────────────────────────────────────────────────────────────────

def _load() -> dict:
    if not os.path.exists(_BANK_PATH):
        return {"quirks": []}
    try:
        with open(_BANK_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"quirks": []}


def _save(bank: dict) -> None:
    try:
        with open(_BANK_PATH, "w", encoding="utf-8") as f:
            json.dump(bank, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def _add_quirk(topic: str, text: str) -> None:
    with _lock:
        bank = _load()
        quirks = bank.get("quirks", [])

        # rotate if full — remove lowest-used + oldest
        if len(quirks) >= _MAX_QUIRKS:
            quirks.sort(key=lambda q: (q.get("used", 0), q.get("ts", 0)))
            quirks = quirks[1:]

        quirks.append({"topic": topic, "text": text, "ts": time.time(), "used": 0})
        bank["quirks"] = quirks
        _save(bank)


# ── Topic extraction ───────────────────────────────────────────────────────────

_TOPIC_KEYWORDS = [
    # eLo-Planet / game
    ("Blender", ["blender", "mesh", "vertex", "vertices", "uv", "rig", "animate", "nla", "sculpt"]),
    ("Unity", ["unity", "game", "scene", "prefab", "animator", "shader", "component"]),
    ("the robot", ["robot", "animatronic", "neopixel", "servo", "raspberry pi", "tpu", "shell", "inflate"]),
    ("the book", ["book", "chapter", "narrative", "story", "act", "write", "writing"]),
    ("eLo", ["elo", "character", "no eyes", "mouth", "posture"]),
    ("Kickstarter", ["kickstarter", "campaign", "launch", "backers", "funding"]),
    # emotions / states
    ("being tired", ["tired", "exhausted", "drained", "burnout", "sleepy", "sleep"]),
    ("stress", ["stress", "anxious", "overwhelmed", "pressure", "deadline", "panic"]),
    ("being stuck", ["stuck", "blocked", "not sure", "confused", "lost", "can't"]),
    ("making progress", ["shipped", "done", "finished", "working", "milestone", "launched"]),
    ("ideas", ["idea", "what if", "imagine", "concept", "thinking about"]),
    # tools / workflow
    ("Obsidian", ["obsidian", "notes", "vault", "markdown"]),
    ("the terminal", ["terminal", "command", "shell", "script", "python"]),
    ("code", ["code", "function", "class", "bug", "error", "refactor"]),
    ("design", ["design", "figma", "layout", "ui", "colour", "aesthetic"]),
    ("music", ["music", "sound", "audio", "beat", "track", "spotify"]),
    ("fashion", ["fashion", "clothing", "fabric", "sew", "pattern", "cut"]),
    ("the vinyl", ["vinyl", "toy", "figure", "sculpt", "cast", "mould"]),
]


def _extract_topic(user_input: str) -> str | None:
    text = user_input.lower()
    for label, keywords in _TOPIC_KEYWORDS:
        if any(kw in text for kw in keywords):
            return label
    return None


# ── LLM call ──────────────────────────────────────────────────────────────────

def _generate(topic: str) -> str | None:
    prompt = _QUIRK_PROMPT.format(topic=topic)
    try:
        # Try OpenAI first (fast, available)
        import os as _os
        key = _os.environ.get("OPENAI_API_KEY", "")
        if key:
            import httpx
            resp = httpx.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": _QUIRK_SYSTEM},
                        {"role": "user",   "content": prompt},
                    ],
                    "max_tokens": 80,
                    "temperature": 0.9,
                },
                timeout=8.0,
            )
            if resp.status_code == 200:
                text = resp.json()["choices"][0]["message"]["content"].strip()
                # strip any quotes the model might wrap around it
                text = text.strip('"').strip("'")
                return text if len(text) > 10 else None
    except Exception:
        pass

    try:
        # Gemini fallback
        import os as _os
        gkey = _os.environ.get("GOOGLE_API_KEY", "")
        model = _os.environ.get("ELO_GEMINI_MODEL", "gemini-2.0-flash")
        if gkey:
            import httpx
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gkey}"
            body = {"contents": [{"parts": [{"text": f"{_QUIRK_SYSTEM}\n\n{prompt}"}]}],
                    "generationConfig": {"maxOutputTokens": 80, "temperature": 0.9}}
            resp = httpx.post(url, json=body, timeout=8.0)
            if resp.status_code == 200:
                text = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip().strip('"').strip("'")
                return text if len(text) > 10 else None
    except Exception:
        pass

    return None


# ── Public API ─────────────────────────────────────────────────────────────────

def maybe_generate(user_input: str, probability: float = 0.15) -> None:
    """
    Called each turn. With `probability` chance, extracts topic from user_input,
    generates a quirk if the topic is new this session, and stores it.
    Non-blocking — runs in a daemon thread.
    """
    if random.random() > probability:
        return

    topic = _extract_topic(user_input)
    if not topic:
        return

    # one quirk per topic per session
    if topic in _session_topics:
        return
    _session_topics.add(topic)

    def _bg():
        text = _generate(topic)
        if text:
            _add_quirk(topic, text)

    threading.Thread(target=_bg, daemon=True).start()


def draw(n: int = 1) -> list[str]:
    """
    Draw n quirks from the bank. Less-used quirks are preferred.
    Increments the 'used' counter for each drawn quirk.
    Returns a list of text strings (may be empty if bank is empty).
    """
    with _lock:
        bank = _load()
        quirks = bank.get("quirks", [])
        if not quirks:
            return []

        # weight by inverse use count — less used = more likely to surface
        weights = [1.0 / (q.get("used", 0) + 1) for q in quirks]
        total = sum(weights)
        probs = [w / total for w in weights]

        chosen_indices = []
        available = list(range(len(quirks)))
        for _ in range(min(n, len(available))):
            r = random.random()
            cum = 0.0
            for i in available:
                cum += probs[i]
                if r <= cum:
                    chosen_indices.append(i)
                    available.remove(i)
                    break

        for i in chosen_indices:
            quirks[i]["used"] = quirks[i].get("used", 0) + 1

        bank["quirks"] = quirks
        _save(bank)

        return [quirks[i]["text"] for i in chosen_indices]


def bank_size() -> int:
    """Return current number of quirks stored."""
    return len(_load().get("quirks", []))
