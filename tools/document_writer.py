"""
tools/document_writer.py — WO-B3-0009: eLo writes documents onto David's Mac.

"Make me a list of…" / "Write that up" / "Create a doc with…" → a real file
David can open, in ~/Documents/eLo/ (ELO_DOCS_DIR overrides), and eLo says
where it is.

Extends what exists (Rule 1): the writing prompt style of tools/draft_agent.py,
its cloud call as the fallback, and the conversation tracker for "write THAT
up". Local model first (David's local-first rule), cloud only if local fails.

    is_document_request(text) -> bool
    write_document(text)      -> {success, result: {path, title, line}, error}
"""
from __future__ import annotations

import datetime
import json
import os
import re
import urllib.request

_DIR = os.path.expanduser(os.environ.get("ELO_DOCS_DIR", "~/Documents/eLo"))

# Things eLo should write as a FILE. Apple Notes ("make a note") and reminders
# have their own tools and are excluded.
_DOC_NOUN = r"(?:doc|document|file|list|checklist|summary|plan|outline|brief|report|write-?up|to-?do\s+list)"
_TRIGGERS = (
    r"\bwrite\s+(?:that|this|it|all\s+(?:that|this))\s+up\b",
    r"\bwrite\s+up\s+(?:what|our|the|a|an|my)\b",
    r"\bmake\s+(?:me\s+)?a\s+(?:quick\s+|short\s+|proper\s+)?(?:list|checklist|to-?do\s+list)\b",
    rf"\b(?:create|make|start|write|draft|put\s+together)\s+(?:me\s+)?(?:a|an|the)\s+(?:quick\s+|short\s+|new\s+|text\s+|markdown\s+)?{_DOC_NOUN}\b",
    rf"\bsave\s+(?:that|this|it|all\s+that)\s+(?:as|to|in(?:to)?)\s+(?:a|an)\s+(?:\w+\s+)?{_DOC_NOUN}\b",
    rf"\bput\s+(?:that|this|it)\s+(?:in(?:to)?)\s+(?:a|an)\s+{_DOC_NOUN}\b",
)
_REFERS_BACK = re.compile(r"\b(?:that|this|it|what\s+we|our\s+(?:chat|conversation|talk)|all\s+that)\b")


def is_document_request(text: str) -> bool:
    t = (text or "").lower()
    if re.search(r"\bmake\s+(?:a\s+)?note\b", t) or re.search(r"\bremind\s+me\b", t):
        return False
    return any(re.search(p, t) for p in _TRIGGERS)


def _format(text: str) -> str:
    return "txt" if re.search(r"\b(?:plain\s+text|text\s+file|\.?txt)\b", text.lower()) else "md"


def _recent_conversation(limit: int = 5) -> str:
    try:
        from faculties.grounding.conversation_tracker import get_tracker
        turns = get_tracker().get_context("default").get("recent_turns") or []
    except Exception:
        return ""
    lines = []
    for t in turns[-limit:]:
        u, e = (t[0], t[1]) if isinstance(t, (list, tuple)) else (t.get("user", ""), t.get("elo", ""))
        if u:
            lines.append(f"David: {u}")
        if e:
            lines.append(f"eLo: {e}")
    return "\n".join(lines)


_SYSTEM = (
    "You write documents for David Charles (founder of DISENELO, creator of eLo). "
    "Write exactly the document asked for: clear, direct, useful, no fluff. "
    "{fmt} Start with a short title line, then the content. "
    "Output ONLY the document — no preamble, no 'Here is…', no sign-off."
)


def _ollama(system: str, user: str, timeout: float = 120) -> str:
    host = os.environ.get("ELO_OLLAMA_HOST", "http://localhost:11434").rstrip("/")
    model = os.environ.get("ELO_DOCS_MODEL") or os.environ.get("ELO_OLLAMA_MODEL", "llama3.1:8b")
    body = json.dumps({"model": model, "stream": False, "options": {"temperature": 0.4},
                       "messages": [{"role": "system", "content": system},
                                    {"role": "user", "content": user}]}).encode()
    req = urllib.request.Request(f"{host}/api/chat", data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return (json.loads(r.read().decode()).get("message") or {}).get("content", "").strip()


def _generate(system: str, user: str) -> str:
    try:
        out = _ollama(system, user)
        if out:
            return out
    except Exception:
        pass
    from tools.draft_agent import _call_llm          # existing cloud path (OpenAI → Gemini)
    return _call_llm(system, user, max_tokens=1200)


def _title_of(content: str, request: str) -> str:
    first = next((l.strip() for l in content.splitlines() if l.strip()), "")
    first = re.sub(r"^[#*\-\s]+|[*_`]+|\s+$", "", first)
    if 3 <= len(first) <= 80:
        return first
    words = re.sub(r"[^\w\s-]", "", request).split()
    return " ".join(words[:8]) or "eLo document"


def _slug(title: str) -> str:
    s = re.sub(r"[^\w\s-]", "", title).strip().lower()
    return re.sub(r"[\s_-]+", "-", s)[:60].strip("-") or "elo-document"


def _unique(path: str) -> str:
    base, ext = os.path.splitext(path)
    n, out = 2, path
    while os.path.exists(out):
        out, n = f"{base}-{n}{ext}", n + 1
    return out


def write_document(request: str) -> dict:
    """Generate the document for `request`, save it, return the result standard."""
    from tools.capability_status import tool_result, record_result
    fmt = _format(request)
    fmt_rule = ("Use Markdown (headings, bullet or numbered lists where they help)." if fmt == "md"
                else "Use plain text only — no Markdown symbols.")
    user = f"Request: {request.strip()}"
    if _REFERS_BACK.search(request.lower()):
        convo = _recent_conversation()
        if convo:
            user += f"\n\nThe conversation it refers to (most recent last):\n{convo}"
    try:
        content = _generate(_SYSTEM.format(fmt=fmt_rule), user).strip()
        if not content:
            raise ValueError("nothing was written")
        title = _title_of(content, request)
        os.makedirs(_DIR, exist_ok=True)
        stamp = datetime.date.today().isoformat()
        path = _unique(os.path.join(_DIR, f"{stamp}-{_slug(title)}.{fmt}"))
        with open(path, "w", encoding="utf-8") as f:
            f.write(content + "\n")
        shown = path.replace(os.path.expanduser("~"), "~", 1)
        line = f"Done — I wrote it up: “{title}”, saved in {os.path.dirname(shown)} as {os.path.basename(path)}."
        return record_result("create_document", tool_result(True, {"path": path, "title": title, "line": line}))
    except Exception as e:
        line = "I couldn't write that one up — the writing model didn't answer. Try me again in a moment?"
        return record_result("create_document", tool_result(False, {"line": line}, f"{type(e).__name__}: {e}"))
