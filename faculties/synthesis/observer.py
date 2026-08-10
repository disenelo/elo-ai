"""
faculties/synthesis/observer.py — Cross-signal synthesis observer.

Watches across: Chrome tabs, browser history, bookmarks, conversation topics,
Obsidian vault entries, and DISENELO tracker files.

When two or more signals point at the same concept, this module produces a
SynthesisHit — a structured observation that eLo can speak proactively.

Architecture position:
  Ambient cycle → ambient_thought() calls observe() → if hit → speak
  Also runs inline on each turn (injected as context if high confidence).

Rate limiting: one hit per topic per 10 minutes — no nagging.
WO-085: decline tracking, relaxation gate, raised threshold, phrasing fixes.
"""
from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass, field
from typing import Optional

# ── Config ────────────────────────────────────────────────────────────────────

_MIN_CONFIDENCE   = 0.65   # WO-085: raised from 0.45 — only fire on strong signal
_COOLDOWN_SECS    = 600    # 10 min between hits on the same topic
_MAX_KEYWORDS     = 12     # keywords extracted from conversation / tabs

# Words in the user's message that mean "I'm winding down / leave it" — no proposals
_RELAXATION_SIGNALS = frozenset({
    "relax", "relaxing", "unwind", "unwinding", "chill", "chilling",
    "take a break", "nothing to do", "leave it", "not right now",
    "i'm done", "that's enough", "just browsing", "just looking",
})

# Decline phrases — when David says these, suppress all proposals for a cooldown
_DECLINE_PHRASES = frozenset({
    "no need", "i got that", "i've got that", "i have that", "covered",
    "don't need to track", "don't need that", "nothing to do", "i'm relaxing",
    "i'm trying to relax", "thank you", "got it", "i got it", "i'm good",
    "leave it", "that's fine", "all good", "i know", "already have",
})

# ── Cooldown + decline trackers ───────────────────────────────────────────────
_last_fired: dict[str, float] = {}   # topic_key → epoch
_declined_topics: dict[str, float] = {}  # topic_key → decline epoch
_declined_until: float = 0.0             # global proposal cooldown after any decline
_DECLINE_COOLDOWN = 300.0                # 5 min global silence after a decline


def record_decline(topic: str = "") -> None:
    """Call when David declines a proposal. Suppresses that topic + global cooldown."""
    global _declined_until
    _declined_until = time.time() + _DECLINE_COOLDOWN
    if topic:
        _declined_topics[topic.lower()] = time.time() + _DECLINE_COOLDOWN


def is_relaxation_signal(text: str) -> bool:
    """Return True if the user's text signals winding down / leave-me-alone."""
    lower = text.lower()
    return any(phrase in lower for phrase in _RELAXATION_SIGNALS)


# ── Data structures ───────────────────────────────────────────────────────────

@dataclass
class Signal:
    source: str          # "chrome_tab" | "bookmark" | "history" | "vault" | "conversation" | "tracker"
    text:   str          # human-readable label
    keywords: frozenset[str] = field(default_factory=frozenset)
    url:  str = ""
    path: str = ""


@dataclass
class SynthesisHit:
    topic:       str           # the shared concept
    signals:     list[Signal]  # all signals that share this topic
    confidence:  float         # 0–1
    offer:       str           # eLo's natural-language proactive offer
    actions:     list[str]     # what eLo can do: "add_to_tracker" | "set_reminder" | "save_vault" | "bookmark"


# ── Stopwords ─────────────────────────────────────────────────────────────────

_STOPWORDS = frozenset({
    "a","an","the","and","or","but","in","on","at","to","for","of","with",
    "is","it","i","you","he","she","we","they","was","be","do","did","have",
    "has","had","will","would","that","this","what","which","who","how","when",
    "where","why","so","if","as","up","out","about","just","now","also","get",
    "got","can","could","should","something","like","one","two","its","not",
    "are","were","been","into","more","from","by","im","our","your","my","me",
    "us","them","him","her","his","their","really","very","want","need","make",
    "know","think","see","look","go","going","say","said","tell","let","yes",
    "no","okay","ok","sure","right","good","great","nice","fine","cool",
})


def _keywords(text: str) -> frozenset[str]:
    words = re.findall(r"[a-z]{3,}", text.lower())
    return frozenset(w for w in words if w not in _STOPWORDS)


def _overlap(a: frozenset[str], b: frozenset[str]) -> frozenset[str]:
    return a & b


# ── Signal collectors ─────────────────────────────────────────────────────────

def _chrome_signals() -> list[Signal]:
    signals: list[Signal] = []
    try:
        from desktop.chrome_reader import all_tabs, bookmarks as bm_list, recent_history
        for tab in all_tabs()[:15]:
            if not tab.title:
                continue
            signals.append(Signal(
                source="chrome_tab",
                text=tab.title,
                keywords=_keywords(tab.title + " " + tab.url),
                url=tab.url,
            ))
        for bm in bm_list()[:200]:
            if bm.title:
                signals.append(Signal(
                    source="bookmark",
                    text=bm.title,
                    keywords=_keywords(bm.title + " " + bm.url),
                    url=bm.url,
                ))
        for h in recent_history(30):
            if h.title:
                signals.append(Signal(
                    source="history",
                    text=h.title,
                    keywords=_keywords(h.title + " " + h.url),
                    url=h.url,
                ))
    except Exception:
        pass
    return signals


def _vault_signals() -> list[Signal]:
    signals: list[Signal] = []
    try:
        from memory.vault_layer import lookup as vlookup
        # Sample recent vault entries without a specific query
        entries = vlookup("eLo DISENELO project", max_results=10)
        for e in entries:
            content = e.get("content", "") or e.get("text", "")
            title   = e.get("title", "") or e.get("filename", "")
            if content:
                signals.append(Signal(
                    source="vault",
                    text=title or content[:80],
                    keywords=_keywords(content[:400]),
                    path=e.get("path", ""),
                ))
    except Exception:
        pass
    return signals


def _tracker_signals() -> list[Signal]:
    signals: list[Signal] = []
    tracker_dirs = [
        os.path.expanduser("~/Documents/DISENELO/trackers"),
        os.path.expanduser("~/Documents/DISENELO/memory/projects"),
        os.path.expanduser("~/eLo-Planet/projects"),
    ]
    for d in tracker_dirs:
        if not os.path.isdir(d):
            continue
        for fn in os.listdir(d):
            if not fn.endswith(".md"):
                continue
            path = os.path.join(d, fn)
            try:
                with open(path, encoding="utf-8") as f:
                    content = f.read(800)
                signals.append(Signal(
                    source="tracker",
                    text=fn.replace("_", " ").replace("-", " ").replace(".md", ""),
                    keywords=_keywords(content),
                    path=path,
                ))
            except Exception:
                pass
    return signals


def _screen_signal() -> Optional[Signal]:
    """Read the screen via Claude vision and return a Signal if content found."""
    try:
        from desktop.screen_reader import read as _sr_read, as_signal_text as _sr_text
        content = _sr_read()
        if content and (content.raw_text or content.topics):
            text = _sr_text(content)
            return Signal(
                source="screen",
                text=content.summary or content.raw_text[:80],
                keywords=_keywords(text) | frozenset(t.lower() for t in content.topics),
            )
    except Exception:
        pass
    return None


def _conversation_signal(recent_text: str) -> Signal:
    return Signal(
        source="conversation",
        text=recent_text[:80],
        keywords=_keywords(recent_text),
    )


# ── Core observe ──────────────────────────────────────────────────────────────

def observe(
    conversation_text: str = "",
    min_confidence: float = _MIN_CONFIDENCE,
    respect_cooldown: bool = True,
) -> Optional[SynthesisHit]:
    """
    Cross-reference all signals and return the highest-confidence SynthesisHit,
    or None if nothing meaningful found.

    Args:
        conversation_text  — recent conversation text (last few turns combined)
        min_confidence     — minimum overlap score to return a hit
        respect_cooldown   — if True, skip topics fired in last 10 min
    """
    all_signals: list[Signal] = []

    if conversation_text:
        all_signals.append(_conversation_signal(conversation_text))

    all_signals.extend(_chrome_signals())
    all_signals.extend(_vault_signals())
    all_signals.extend(_tracker_signals())

    _screen = _screen_signal()
    if _screen:
        all_signals.append(_screen)

    if not all_signals:
        return None

    # WO-085: global decline cooldown — David said "no need / covered / i'm relaxing"
    if time.time() < _declined_until:
        return None

    # WO-085: relaxation gate — never propose while David is winding down
    if conversation_text and is_relaxation_signal(conversation_text):
        return None

    # Find keyword clusters across signals
    # For each keyword appearing in 2+ signals, score that cluster
    keyword_to_signals: dict[str, list[Signal]] = {}
    for sig in all_signals:
        for kw in sig.keywords:
            keyword_to_signals.setdefault(kw, []).append(sig)

    # Score clusters: prefer keywords from diverse sources
    clusters: dict[str, list[Signal]] = {}
    for kw, sigs in keyword_to_signals.items():
        sources = {s.source for s in sigs}
        if len(sources) < 2:
            continue
        # Prefer cross-source matches (conversation + chrome, vault + tracker, etc.)
        if "conversation" not in sources and len(sources) < 2:
            continue
        clusters[kw] = sigs

    if not clusters:
        return None

    # Score each cluster
    best_kw     = None
    best_score  = 0.0
    best_sigs   = []

    for kw, sigs in clusters.items():
        sources = {s.source for s in sigs}
        # Score: more distinct sources = higher confidence
        score = min(1.0, len(sources) / 3.0)
        # Bonus for conversation involvement
        if "conversation" in sources:
            score = min(1.0, score + 0.2)
        # Bonus for vault involvement (something already filed)
        if "vault" in sources or "tracker" in sources:
            score = min(1.0, score + 0.15)
        if score > best_score:
            best_score = score
            best_kw    = kw
            best_sigs  = sigs

    if best_score < min_confidence or not best_kw:
        return None

    # Cooldown check (per-topic + per-decline)
    topic_key = best_kw.lower()
    if respect_cooldown:
        last = _last_fired.get(topic_key, 0)
        if time.time() - last < _COOLDOWN_SECS:
            return None
        # WO-085: topic-level decline suppression
        if time.time() < _declined_topics.get(topic_key, 0):
            return None
    _last_fired[topic_key] = time.time()

    # Deduplicate signals by source (one per source)
    seen_sources: set[str] = set()
    deduped: list[Signal] = []
    for s in best_sigs:
        if s.source not in seen_sources:
            deduped.append(s)
            seen_sources.add(s.source)

    # Build the offer
    offer = _build_offer(best_kw, deduped)

    # Determine available actions
    actions: list[str] = ["add_to_tracker", "save_vault", "set_reminder"]
    if any(s.source == "chrome_tab" for s in deduped):
        actions.append("bookmark")

    return SynthesisHit(
        topic=best_kw,
        signals=deduped,
        confidence=best_score,
        offer=offer,
        actions=actions,
    )


_OFFER_VARIANTS = [
    "Want me to hold onto that?",
    "Want me to remember this?",
    "I can keep that in mind if you like.",
    "Should I hang onto that?",
    "Worth remembering — want me to?",
]


def _build_offer(topic: str, signals: list[Signal]) -> str:
    """Build eLo's natural proactive offer from the matched signals. WO-085: no vault,
    no fabricated tracker links, natural varied phrasing."""
    import random
    src_map = {s.source: s for s in signals}

    parts: list[str] = []

    if "chrome_tab" in src_map:
        tab = src_map["chrome_tab"]
        parts.append(f"you've got '{tab.text[:50]}' open")
    elif "history" in src_map:
        h = src_map["history"]
        parts.append(f"you were looking at '{h.text[:50]}'")
    elif "screen" in src_map:
        s = src_map["screen"]
        parts.append(f"I can see '{s.text[:50]}' on screen")

    if "conversation" in src_map:
        parts.append("you've mentioned it")

    if "vault" in src_map:
        v = src_map["vault"]
        parts.append(f"I've got something related in memory")

    if not parts:
        return ""

    observation = " — ".join(parts)
    ask = random.choice(_OFFER_VARIANTS)
    return f"Noticed: {observation}. {ask}"


# ── Convenience: text-only context for LLM injection ────────────────────────

def context_block(conversation_text: str = "") -> str:
    """Return a [SYNTHESIS] context string for injection into the system prompt."""
    hit = observe(conversation_text, respect_cooldown=False)
    if not hit:
        return ""
    source_labels = ", ".join(s.source.replace("_", " ") for s in hit.signals)
    return (
        f"[SYNTHESIS SIGNAL — confidence {hit.confidence:.0%}]\n"
        f"Topic: '{hit.topic}' — seen across: {source_labels}.\n"
        f"Offer if natural: {hit.offer}"
    )
