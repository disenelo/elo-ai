"""
tools/draft_agent.py — eLo creative writing agent.

Generates actual content (pitch, email, scene, copy, brief, brainstorm)
using the available LLM backend with a focused creative writing prompt.

The draft is returned as a data string so tool_router can inject it as
[CONTEXT] and eLo presents it in his own voice.

Modes detected from query:
    pitch       — Kickstarter / product pitch paragraph
    email       — professional or personal email
    scene       — narrative story scene or screenplay beat
    copy        — social media caption, product description, marketing copy
    brief       — design brief, creative brief, project brief
    outline     — structured outline or plan
    brainstorm  — generates 5 distinct options/directions
    refine      — edits/polishes pasted or referenced content
    bio         — short bio or profile text
    caption     — image caption / social post
"""

from __future__ import annotations
import os
import re
import logging
try:
    import httpx as _httpx
except ImportError:
    _httpx = None  # httpx not installed; agent() will raise at call-time

_logger = logging.getLogger(__name__)
_logger.addHandler(logging.NullHandler())
_logger.propagate = False

_OPENAI_KEY  = os.environ.get("OPENAI_API_KEY",  "").strip()
_GOOGLE_KEY  = os.environ.get("GOOGLE_API_KEY",  "").strip()
_GEMINI_MODEL = os.environ.get("ELO_GEMINI_MODEL", "gemini-2.0-flash")

# ── mode detection ─────────────────────────────────────────────────────────────

_MODE_MAP = [
    ("brainstorm", [r"\bbrainstorm\b", r"\bgive me (?:5|five|some|a few|options|ideas)\b",
                    r"\bwhat are (?:some|the)\b.*\bideas\b", r"\blist.*(?:options|ideas|directions)\b",
                    r"\b(?:ideas?|options?)\s+for\b"]),
    ("refine",     [r"\bpolish\b", r"\brefine\b", r"\bedit\b", r"\bimprove\b", r"\bmake.*better\b",
                    r"\bfix\s+(?:this|my)\b", r"\brewrite\b", r"\bclean\s+(?:this|up)\b"]),
    ("pitch",      [r"\bpitch\b", r"\bkickstarter\b", r"\belevator\b", r"\bproduct.*(?:desc|overview)\b",
                    r"\bsell\s+(?:this|it|elo)\b", r"\binvestor\b"]),
    ("email",      [r"\bemail\b", r"\bmessage\s+to\b", r"\bwrite\s+to\b", r"\bdraft.*(?:email|message)\b",
                    r"\breach\s+out\b", r"\bcontact\b.*\babout\b"]),
    ("scene",      [r"\bscene\b", r"\bchapter\b", r"\bact\b", r"\bstory\b", r"\bnarrative\b",
                    r"\bwrite.*(?:story|scene|chapter)\b", r"\bbook\b.*\bwrite\b"]),
    ("bio",        [r"\bbio\b", r"\babout\s+(?:me|us|elo)\b", r"\bprofile\b", r"\bwho\s+(?:am\s+i|is|are)\b.*\bwrite\b"]),
    ("outline",    [r"\boutline\b", r"\bstructure\b", r"\bplan\b.*\bwrite\b", r"\bbreak\s+down\b",
                    r"\bsections?\s+for\b"]),
    ("copy",       [r"\bcaption\b", r"\bpost\b.*\bwrite\b", r"\bsocial\b.*\b(?:copy|post|write)\b",
                    r"\btweet\b", r"\binstagram\b.*\bwrite\b", r"\bmarketing\b.*\bcopy\b",
                    r"\bproduct\s+description\b", r"\bcopy\s+for\b"]),
    ("brief",      [r"\bbrief\b", r"\bspec\b.*\bwrite\b", r"\bdesign\s+doc\b", r"\bproject\s+summary\b",
                    r"\bwrite\s+a\s+brief\b"]),
]

_WRITE_TRIGGERS = [
    r"\bwrite\b", r"\bdraft\b", r"\bcreate\b.*\b(?:text|copy|content)\b",
    r"\bcompose\b", r"\bgenerate\b.*\b(?:text|copy|content|draft)\b",
    r"\bcan you (?:write|draft|create|compose|generate)\b",
    r"\bbrainstorm\b", r"\bpolish\b", r"\brefine\b", r"\bedit\s+this\b",
]

def _detect_mode(text: str) -> str:
    t = text.lower()
    for mode, patterns in _MODE_MAP:
        for pat in patterns:
            if re.search(pat, t):
                return mode
    return "draft"


def _extract_topic(query: str, mode: str) -> str:
    """Strip write/draft verbs to get the core topic."""
    t = query.strip()
    t = re.sub(
        r"^(?:write|draft|create|compose|generate|give me|can you write|help me write|"
        r"brainstorm|polish|refine|edit|improve|outline|make)\s+(?:a\s+|an\s+|me\s+a\s+|me\s+)?",
        "", t, flags=re.IGNORECASE
    ).strip()
    t = re.sub(
        r"^(?:pitch|email|scene|story|caption|copy|brief|bio|outline|brainstorm)\s+(?:for\s+|about\s+)?",
        "", t, flags=re.IGNORECASE
    ).strip()
    return t or query.strip()


# ── LLM call (direct, bypasses eLo personality) ────────────────────────────────

def _call_llm(system: str, user: str, max_tokens: int = 600) -> str:
    """Call OpenAI or Gemini directly for content generation."""

    if _httpx is None:
        raise RuntimeError("draft_agent requires httpx — pip install httpx")
    # OpenAI
    if _OPENAI_KEY:
        resp = _httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {_OPENAI_KEY}", "Content-Type": "application/json"},
            json={
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user",   "content": user},
                ],
                "max_tokens": max_tokens,
                "temperature": 0.75,
            },
            timeout=20.0,
        )
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"].strip()

    # Gemini
    if _GOOGLE_KEY:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{_GEMINI_MODEL}:generateContent"
        payload = {
            "contents": [{"parts": [{"text": f"{system}\n\n{user}"}]}],
            "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.75},
        }
        resp = _httpx.post(url, json=payload, params={"key": _GOOGLE_KEY}, timeout=20.0)
        if resp.status_code == 200:
            return resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()

    raise ValueError("no LLM backend available for draft agent")


# ── mode prompts ───────────────────────────────────────────────────────────────

_SYSTEM_BASE = (
    "You are a skilled creative writer working for DISENELO — a brand built around eLo, "
    "a curious, quietly adventurous character. The work spans a game, a book, physical products, "
    "and a creative OS. Writing should be direct, warm, and slightly surprising. "
    "No fluff. No corporate speak. No unnecessary length. "
    "Output ONLY the requested content — no preamble, no 'Here is your draft:' opener."
)

_MODE_PROMPTS = {
    "pitch":      "Write a compelling, human pitch paragraph. Clear problem, clear solution, emotional hook. Under 100 words.",
    "email":      "Write a clear, direct, professional email. Warm but efficient. Subject line first, then body.",
    "scene":      "Write a vivid narrative scene. Show, don't tell. eLo has no eyes — expression through posture, movement, sound, light.",
    "copy":       "Write punchy social copy. Under 50 words. Voice: curious, slightly wry, direct. No hashtags unless asked.",
    "brief":      "Write a clear creative brief. Sections: What / Why / Who / Tone / Deliverables. Bullet points under each.",
    "outline":    "Write a clear structured outline. Numbered sections with one-line descriptions. Hierarchy where needed.",
    "bio":        "Write a short, honest, engaging bio. First person or third person based on context. Under 80 words.",
    "brainstorm": "Generate 5 distinct, genuinely different directions. Number each. One sentence description + one sentence why it's interesting. No overlap.",
    "refine":     "Polish the following content. Keep the author's voice. Improve clarity, rhythm, and impact. Output the refined version only.",
    "draft":      "Write the requested content clearly and directly. Appropriate length for the format.",
}


# ── public API ─────────────────────────────────────────────────────────────────

def agent(query: str) -> str:
    """
    Generate creative content based on the query.
    Returns a string starting with the mode label, followed by the content.
    """
    mode  = _detect_mode(query)
    topic = _extract_topic(query, mode)

    mode_instruction = _MODE_PROMPTS.get(mode, _MODE_PROMPTS["draft"])
    system = f"{_SYSTEM_BASE}\n\n{mode_instruction}"

    if mode == "refine":
        user_prompt = f"Content to refine:\n\n{topic}"
    elif mode == "brainstorm":
        user_prompt = f"Brainstorm 5 distinct directions for: {topic}"
    else:
        user_prompt = f"Write a {mode} for: {topic}"

    content = _call_llm(system, user_prompt)
    label   = mode.upper()
    return f"{label}:\n\n{content}"


def is_draft_intent(text: str) -> bool:
    """Quick check used by tool_router to detect draft intent."""
    t = text.lower()
    return any(re.search(pat, t) for pat in _WRITE_TRIGGERS)
