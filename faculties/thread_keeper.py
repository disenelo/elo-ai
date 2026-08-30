"""
faculties/thread_keeper.py — WO-068: Capture · Prepare · Hold the Thread.

A. CAPTURE  — "write this down / before I lose it" → self/ideas_log.jsonl + honest confirm
B. PREPARE  — "get the invoice ready" → DRAFT_*.md at review path, nothing sent (L3 gate)
C. HOLD     — persist last-state on topic-switch; "where did we leave off" → log answer
"""

from __future__ import annotations
import os
import re
import json
import time
import logging
from datetime import datetime

_log = logging.getLogger(__name__)
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── Paths ─────────────────────────────────────────────────────────────────────

_IDEAS_LOG    = os.path.join(_ROOT, "self", "ideas_log.jsonl")
_LAST_STATE   = os.path.join(_ROOT, "self", "last_state.jsonl")
_INVOICE_DIR  = os.environ.get(
    "ELO_INVOICE_DIR",
    os.path.expanduser("~/Company_Vault/Invoices"),
)


# ─────────────────────────────────────────────────────────────────────────────
# A. CAPTURE
# ─────────────────────────────────────────────────────────────────────────────

_CAPTURE_TRIGGERS = re.compile(
    r"write\s+(?:this\s+|it\s+)?down"
    r"|before\s+i\s+(?:lose|forget)\s+(?:it|this|the\s+thread)"
    r"|before\s+i\s+lose\s+(?:it|this)"
    r"|note\s+this\s+down"
    r"|just\s+note\s+(?:that|this)"
    r"|capture\s+(?:this|that)"
    r"|jot\s+(?:this\s+|that\s+|it\s+)?down"
    r"|don.t\s+let\s+me\s+lose\s+this"
    r"|save\s+this\s+idea",
    re.I,
)

_HOLD_RECALL_TRIGGERS = re.compile(
    r"where\s+did\s+we\s+leave\s+off"
    r"|where\s+were\s+we"
    r"|what\s+were\s+we\s+working\s+on"
    r"|pick\s+up\s+where\s+we\s+left\s+off"
    r"|before\s+i\s+walked\s+away"
    r"|catch\s+me\s+up"
    r"|where\s+did\s+(?:we|i)\s+stop"
    r"|where\s+(?:did\s+)?we\s+get\s+to",
    re.I,
)

_PREPARE_TRIGGERS = re.compile(
    r"(?:get|sort|prepare|make|draft)\s+(?:the\s+|an?\s+)?invoice\s+ready"
    r"|invoice\s+for\s+.+(?:ready|sorted|prepared)"
    r"|get\s+it\s+ready\s+(?:so\s+i\s+can|for\s+me\s+to)\s+(?:look|review|check)"
    r"|prepare\s+(?:a\s+)?(?:the\s+)?invoice"
    r"|sort\s+(?:out\s+)?(?:the\s+)?invoice"
    r"|invoice\s+for\s+client",
    re.I,
)


def is_capture_intent(text: str) -> bool:
    return bool(_CAPTURE_TRIGGERS.search(text))


def is_prepare_intent(text: str) -> bool:
    return bool(_PREPARE_TRIGGERS.search(text))


def is_hold_recall_intent(text: str) -> bool:
    return bool(_HOLD_RECALL_TRIGGERS.search(text))


def capture(text: str) -> str:
    """
    Save the idea verbatim to self/ideas_log.jsonl.
    Returns a short confirmation naming the save path.
    Never just reflects the idea back — always writes first.
    """
    entry = {
        "ts":    time.time(),
        "idea":  text.strip(),
        "saved": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
    }
    try:
        os.makedirs(os.path.dirname(_IDEAS_LOG), exist_ok=True)
        with open(_IDEAS_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        short_path = os.path.relpath(_IDEAS_LOG, _ROOT)
        return f"Got it — saved to `{short_path}`. It's there when you need it."
    except Exception as e:
        _log.warning("capture write failed: %s", e)
        return "Tried to save it but hit a file error. Tell me the idea again and I'll retry."


# ─────────────────────────────────────────────────────────────────────────────
# B. PREPARE (invoice draft — L3 gate: never sends)
# ─────────────────────────────────────────────────────────────────────────────

_NON_CLIENT = frozenset({
    "the", "a", "an", "my", "this", "that", "get", "invoice", "design",
    "work", "project", "job", "done", "ready", "sorted", "prepared",
    "it", "me", "us", "our", "some", "your",
})


def _extract_invoice_fields(text: str) -> dict:
    """Pull client, work, period from a natural language invoice request."""
    fields: dict[str, str] = {}

    # Client — must follow "client <name>" or "for <ProperNoun>" (initial cap, not a noise word)
    m = re.search(
        r"\bclient\s+([A-Z][a-zA-Z0-9 &'.]{1,40}?)(?=\s|,|$|\bfor\b|\bsorted\b|\bready\b)",
        text, re.I,
    )
    if m:
        candidate = m.group(1).strip()
        if candidate.lower() not in _NON_CLIENT:
            fields["client"] = candidate
    else:
        # Fallback: "for <ProperNoun>" — requires title-case first letter (case-sensitive)
        m2 = re.search(
            r"\bfor\s+([A-Z][a-zA-Z0-9 &'.]{1,40}?)(?=\s+(sorted|ready|on|invoice|\b)|,|$)",
            text,  # no re.I — capital required
        )
        if m2:
            candidate = m2.group(1).strip()
            first = candidate.split()[0].lower() if candidate else ""
            if first not in _NON_CLIENT:
                fields["client"] = candidate

    # Work description
    m = re.search(
        r"(?:for the|for)\s+(.+?)\s+(?:work|project|job|done|completed|over|during|in|this|last)\b",
        text, re.I,
    )
    if m:
        fields["work"] = m.group(1).strip()

    # Period
    m = re.search(
        r"(?:over\s+(?:the\s+)?|for\s+(?:the\s+)?|in\s+(?:the\s+)?)"
        r"(last\s+(?:fortnight|week|month|two\s+weeks?|[0-9]+\s+days?)"
        r"|this\s+(?:week|month|fortnight)"
        r"|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\w*(?:\s+\d{4})?)",
        text, re.I,
    )
    if m:
        fields["period"] = m.group(1).strip()

    return fields


def prepare_invoice(text: str) -> str:
    """
    Extract fields, write a DRAFT invoice to the review directory, return the path.
    If a required field is missing, return ONE targeted question — never invent data.
    L3 gate: this function never sends, emails, or finalises anything.
    """
    fields = _extract_invoice_fields(text)

    # Missing-field check — ask exactly ONE question
    if "client" not in fields:
        return "Who's the client for this invoice?"
    if "work" not in fields:
        return f"What work should I put on the invoice for {fields['client']}?"
    if "period" not in fields:
        return f"What time period does this cover — last fortnight, this month?"

    # Build the draft
    ts_str    = datetime.utcnow().strftime("%Y-%m-%d")
    slug      = re.sub(r"[^a-zA-Z0-9]", "_", fields["client"])[:24]
    filename  = f"DRAFT_{slug}_{ts_str}.md"
    filepath  = os.path.join(_INVOICE_DIR, filename)

    draft = (
        f"# DRAFT INVOICE — {fields['client']}\n\n"
        f"**Date:** {ts_str}  \n"
        f"**Client:** {fields['client']}  \n"
        f"**Work:** {fields['work']}  \n"
        f"**Period:** {fields['period']}  \n"
        f"**Status:** DRAFT — awaiting David's review  \n\n"
        f"---\n\n"
        f"*Auto-prepared by eLo OS · WO-068 · NOT sent or finalised*\n"
    )

    try:
        os.makedirs(_INVOICE_DIR, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(draft)
        return (
            f"Draft ready at `{filepath}`. "
            f"{fields['client']} · {fields['work']} · {fields['period']}. "
            f"Nothing sent — your review first."
        )
    except Exception as e:
        _log.warning("prepare_invoice write failed: %s", e)
        return f"Hit a file error saving the draft: {e}. Try again?"


# ─────────────────────────────────────────────────────────────────────────────
# C. HOLD THE THREAD
# ─────────────────────────────────────────────────────────────────────────────

def record_state(topic: str, summary: str, session_id: str = "") -> None:
    """
    Persist a last-state entry to self/last_state.jsonl.
    Called on topic-switch or session end — not on every turn.
    """
    entry = {
        "ts":         time.time(),
        "saved":      datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        "topic":      topic.strip(),
        "summary":    summary.strip(),
        "session_id": session_id,
    }
    try:
        os.makedirs(os.path.dirname(_LAST_STATE), exist_ok=True)
        with open(_LAST_STATE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        _log.warning("record_state write failed: %s", e)


def recall_thread(topic: str = "") -> str:
    """
    Look up last-state entry for topic (or most recent if topic is empty).
    Also checks second_brain/index.jsonl for visual captures (WO-068 Phase 2).
    Returns a direct answer from the log — never fabricates.
    """
    if not os.path.exists(_LAST_STATE):
        return "Nothing logged yet — I haven't recorded a thread for that. Next time you switch topics I'll lock the state."

    try:
        entries: list[dict] = []
        with open(_LAST_STATE, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
    except Exception:
        return "Couldn't read the thread log — file might be corrupted. I'll start fresh from here."

    if not entries:
        return "Nothing logged yet — I haven't recorded a thread for that. Next time you switch topics I'll lock the state."

    def _archive_suffix(q: str) -> str:
        if not q:
            return ""
        hit = search_second_brain(q)
        if hit and "Nothing" not in hit and "Couldn't" not in hit:
            return f"\n\nAlso in archive — {hit}"
        return ""

    # Topic match: find the most recent entry whose topic contains the query
    if topic:
        tl = topic.lower()
        matched = [e for e in entries if tl in e.get("topic", "").lower()]
        if matched:
            best = matched[-1]
            reply = (
                f"Last state on '{best['topic']}' ({best['saved']}): "
                f"{best['summary']}"
            )
            return reply + _archive_suffix(topic)
        # No exact topic match — return most recent with honest caveat
        best = entries[-1]
        reply = (
            f"No exact match for '{topic}'. Most recent thread ({best['saved']}): "
            f"'{best['topic']}' — {best['summary']}"
        )
        return reply + _archive_suffix(topic)

    # No topic specified — most recent
    best = entries[-1]
    return (
        f"Last thread ({best['saved']}): '{best['topic']}' — {best['summary']}"
    )


# ─────────────────────────────────────────────────────────────────────────────
# D. SECOND BRAIN — visual capture + vision-indexed recall (WO-068 Phase 2)
# ─────────────────────────────────────────────────────────────────────────────

_SECOND_BRAIN_DIR   = os.path.join(_ROOT, "self", "second_brain")
_SECOND_BRAIN_INDEX = os.path.join(_SECOND_BRAIN_DIR, "index.jsonl")


def _describe_screenshot(image_bytes: bytes) -> str:
    """Pass image_bytes through vision_loop._analyse() and return the description string."""
    try:
        from tools import vision_loop as _vl
        result = _vl._analyse(image_bytes)
        if result and result.get("description"):
            return result["description"]
    except Exception as e:
        _log.debug("vision describe failed: %s", e)
    return ""


def capture_visual(text: str, image_bytes: bytes | None = None, elo_made: bool = False) -> str:
    """
    Extended capture (WO-068 Phase 2): saves text note to ideas_log.jsonl (Phase 1),
    and if image_bytes is provided, also saves the screenshot to second_brain/ with
    provenance + vision description, and appends to the index.

    Returns confirmation naming both save paths when a screenshot is included.
    """
    # Phase 1: always capture the text note
    text_reply = capture(text)

    if not image_bytes:
        return text_reply

    # Phase 2: save screenshot + index it
    try:
        os.makedirs(_SECOND_BRAIN_DIR, exist_ok=True)
        ts_now   = time.time()
        ts_label = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        img_filename = f"capture_{ts_label}.png"
        img_path     = os.path.join(_SECOND_BRAIN_DIR, img_filename)

        with open(img_path, "wb") as f:
            f.write(image_bytes)

        description = _describe_screenshot(image_bytes)

        entry = {
            "ts":          ts_now,
            "saved":       datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
            "path":        img_path,
            "type":        "screenshot",
            "note":        text.strip(),
            "description": description,
            "tags":        {
                "david_reference": not elo_made,
                "elo_made":        elo_made,
            },
        }
        with open(_SECOND_BRAIN_INDEX, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        rel_img   = os.path.relpath(img_path, _ROOT)
        rel_index = os.path.relpath(_SECOND_BRAIN_INDEX, _ROOT)
        desc_line = f" ({description})" if description else ""
        return (
            f"Got it — text saved to `self/ideas_log.jsonl`, "
            f"screenshot saved to `{rel_img}`{desc_line}. "
            f"Indexed in `{rel_index}`."
        )
    except Exception as e:
        _log.warning("capture_visual write failed: %s", e)
        return text_reply + f" (screenshot save failed: {e})"


def search_second_brain(query: str) -> str:
    """
    Search second_brain/index.jsonl by keyword match on description + note.
    Returns the best matching entry or an honest "nothing found yet" reply.
    """
    if not os.path.exists(_SECOND_BRAIN_INDEX):
        return "Nothing in the archive yet — capture something first and I'll be able to search it."

    try:
        entries: list[dict] = []
        with open(_SECOND_BRAIN_INDEX, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
    except Exception:
        return "Couldn't read the second brain index — file might be corrupted."

    if not entries:
        return "Nothing in the archive yet — capture something first and I'll be able to search it."

    ql = query.lower()
    scored: list[tuple[int, dict]] = []
    for e in entries:
        text_blob = (e.get("description", "") + " " + e.get("note", "")).lower()
        score = sum(1 for word in ql.split() if word in text_blob)
        if score > 0:
            scored.append((score, e))

    if not scored:
        return f"Nothing matching '{query}' in the archive yet."

    scored.sort(key=lambda x: (-x[0], -x[1]["ts"]))
    _, best = scored[0]
    rel_path    = os.path.relpath(best["path"], _ROOT)
    description = best.get("description", "")
    saved       = best.get("saved", "")
    desc_line   = f": {description}" if description else ""
    return (
        f"Found it — `{rel_path}` ({saved}){desc_line}. "
        f"Note: \"{best.get('note', '')}\"."
    )
