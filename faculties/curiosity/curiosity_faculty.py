"""
faculties/curiosity/curiosity_faculty.py — WO-CURIOSITY-001

BECOME CURIOUS + FORM QUESTION causal chain nodes.

eLo detects gaps in working knowledge (WKG entries absent or low-confidence),
forms an internal question to close the gap, prioritises questions by
significance weight, and makes the top question available for the Executive
to optionally surface.

API (consumed by runtime/curiosity_faculty.py re-export):
    detect_gap(context, wkg_state)   → list[dict] gap descriptors
    form_question(gap)               → dict question record
    prioritise(questions)            → list[dict] sorted by weight desc
    curiosity_prompt_block()         → str prompt injection block (may be "")
    store_question(q)                → None  (persists to working memory)
    top_question()                   → dict | None

Placement: read-only re: eLo output. Questions stored to working memory.
Executive decides whether to surface. Never writes to vault or speaks directly.

FREEZE_V1_LOCK: does not touch runtime/executive.py or prompts/.
"""
from __future__ import annotations

import json
import os
import re
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_QUESTIONS_PATH = os.path.join(_ROOT, "self", "state", "open_questions.json")

# Confidence below this in a WKG claim → gap
_CONFIDENCE_GAP_THRESHOLD = 0.55

# Maximum questions kept in the open queue (oldest dropped first)
_MAX_OPEN_QUESTIONS = 20

# Minimum token length of a topic string worth querying
_MIN_TOPIC_LEN = 3


# ── Gap detection ─────────────────────────────────────────────────────────────

def detect_gap(context: str, wkg_state: dict | None = None) -> list[dict]:
    """
    Scan context for noun phrases / topics and check each against WKG.

    Returns a list of gap descriptors:
        {topic, reason, confidence, ts}

    where reason is "absent" or "low_confidence".

    wkg_state is an optional pre-fetched WKG snapshot (for testing); when None
    the live WKG is queried. Fails quietly — returns [] on any error.
    """
    try:
        topics = _extract_topics(context)
        gaps: list[dict] = []
        for topic in topics:
            gap = _check_topic(topic, wkg_state)
            if gap:
                gaps.append(gap)
        return gaps
    except Exception:
        return []


def _extract_topics(text: str) -> list[str]:
    """
    Cheap noun-phrase heuristic — pull capitalised multi-word chunks and
    lowercased single words that look like proper names or concepts.

    Deliberately dumb: the point is to produce candidate topics for WKG
    lookup, not to parse language. False positives are harmless (WKG returns
    None and we skip).
    """
    candidates: list[str] = []

    # Multi-word capitalised runs: "Raspberry Pi", "NeoPixel ring"
    for m in re.finditer(r"(?:[A-Z][a-z]+)(?:\s+[A-Z][a-z]+)+", text):
        candidates.append(m.group(0).strip())

    # Single CamelCase tokens: "TPU", "NLA", "eLo"
    for m in re.finditer(r"\b[A-Z][a-zA-Z]{2,}\b", text):
        candidates.append(m.group(0).strip())

    # Quoted phrases: "forward kinematics"
    for m in re.finditer(r'"([^"]{3,40})"', text):
        candidates.append(m.group(1).strip())

    seen: set[str] = set()
    result: list[str] = []
    for c in candidates:
        lc = c.lower()
        if lc not in seen and len(c) >= _MIN_TOPIC_LEN:
            seen.add(lc)
            result.append(c)
    return result[:30]  # cap to avoid WKG hammering


def _check_topic(topic: str, wkg_state: dict | None) -> dict | None:
    """
    Return a gap descriptor if the topic is absent or low-confidence in WKG.
    Returns None when the topic is well-known.
    """
    try:
        if wkg_state is not None:
            # Test-injected snapshot: {label: confidence_float}
            conf = wkg_state.get(topic.lower())
            if conf is None:
                return {"topic": topic, "reason": "absent", "confidence": 0.0, "ts": time.time()}
            if float(conf) < _CONFIDENCE_GAP_THRESHOLD:
                return {"topic": topic, "reason": "low_confidence", "confidence": float(conf), "ts": time.time()}
            return None

        # Live WKG lookup
        from runtime.wkg_faculty import search_entities, get_claims_about
        entities = search_entities(topic)
        if not entities:
            return {"topic": topic, "reason": "absent", "confidence": 0.0, "ts": time.time()}

        # Check average claim confidence for this entity
        eid = entities[0]["entity_id"]
        claims = get_claims_about(eid)
        if not claims:
            return {"topic": topic, "reason": "low_confidence", "confidence": 0.1, "ts": time.time()}

        confidences = [float(c.get("confidence", 0.5)) for c in claims]
        avg_conf = sum(confidences) / len(confidences)
        if avg_conf < _CONFIDENCE_GAP_THRESHOLD:
            return {"topic": topic, "reason": "low_confidence", "confidence": round(avg_conf, 3), "ts": time.time()}

        return None
    except Exception:
        return None


# ── Question formation ─────────────────────────────────────────────────────────

def form_question(gap: dict) -> dict:
    """
    Convert a gap descriptor into an internal question record.

    Returns:
        {
            question_id,
            topic,
            text,         ← the question as a string
            reason,
            confidence,
            weight,       ← significance weight 0–10
            ts,
            surfaced,     ← False until Executive promotes it
        }

    The question is stored internally, NOT surfaced to David directly.
    """
    topic = gap.get("topic", "")
    reason = gap.get("reason", "absent")
    conf = float(gap.get("confidence", 0.0))

    if reason == "absent":
        text = f"What do I know about {topic}? I have no record of it."
        weight = 6
    else:
        pct = int((1.0 - conf) * 100)
        text = f"What more should I know about {topic}? My confidence is only {pct}%."
        weight = 4 + int((1.0 - conf) * 4)  # 4–8 based on gap size

    qid = f"q-{int(time.time() * 1000)}-{abs(hash(topic)) % 9999:04d}"
    return {
        "question_id": qid,
        "topic": topic,
        "text": text,
        "reason": reason,
        "confidence": conf,
        "weight": min(weight, 10),
        "ts": time.time(),
        "surfaced": False,
    }


# ── Prioritisation ─────────────────────────────────────────────────────────────

def prioritise(questions: list[dict]) -> list[dict]:
    """
    Sort questions by weight descending, then by ts ascending (older first
    among equals). Returns a new sorted list; does not mutate input.
    """
    return sorted(questions, key=lambda q: (-q.get("weight", 0), q.get("ts", 0)))


# ── Persistence ───────────────────────────────────────────────────────────────

def store_question(q: dict) -> None:
    """Append a question to the open_questions queue. Caps at _MAX_OPEN_QUESTIONS."""
    try:
        questions = _load_questions()
        # Deduplicate by topic
        existing_topics = {r.get("topic", "").lower() for r in questions}
        if q.get("topic", "").lower() in existing_topics:
            return
        questions.append(q)
        if len(questions) > _MAX_OPEN_QUESTIONS:
            questions = prioritise(questions)[:_MAX_OPEN_QUESTIONS]
        _save_questions(questions)
    except Exception:
        pass


def top_question() -> dict | None:
    """Return the highest-priority unsurfaced question, or None."""
    try:
        questions = [q for q in _load_questions() if not q.get("surfaced", False)]
        if not questions:
            return None
        return prioritise(questions)[0]
    except Exception:
        return None


def _load_questions() -> list[dict]:
    try:
        with open(_QUESTIONS_PATH, encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (FileNotFoundError, json.JSONDecodeError):
        return []
    except Exception:
        return []


def _save_questions(questions: list[dict]) -> None:
    try:
        os.makedirs(os.path.dirname(_QUESTIONS_PATH), exist_ok=True)
        with open(_QUESTIONS_PATH, "w", encoding="utf-8") as f:
            json.dump(questions, f, indent=2)
    except Exception:
        pass


# ── Prompt injection ──────────────────────────────────────────────────────────

def curiosity_prompt_block() -> str:
    """
    Return a prompt block with the top open question for Executive context.

    Returns "" when there are no open questions — non-blocking.
    The Executive may choose to surface this question or use it to drive a
    WKG lookup. It is never a command to speak.
    """
    try:
        q = top_question()
        if not q:
            return ""
        return (
            f"[CURIOSITY — internal open question (may inform response or WKG lookup)]\n"
            f"  Topic: {q['topic']}\n"
            f"  Question: {q['text']}\n"
            f"  Weight: {q['weight']}/10  Reason: {q.get('reason', 'unknown')}\n"
            f"  This is for eLo's awareness only — not a directive to speak the question aloud."
        )
    except Exception:
        return ""
