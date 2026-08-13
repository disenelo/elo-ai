"""
tools/llm_file_agent.py — LLM-backed natural language file operations agent.

Understands contextual requests like "take all screenshots off my Desktop and
put them in a Screenshots folder" and turns them into a confirmed, executable plan.

Flow:
  1. is_file_ops_intent(text) — keyword check, called by tool_router
  2. agent(query) — gathers directory context, calls LLM, stores pending plan,
                    returns a [FILE_PLAN: ...] context string for the LLM response
  3. server.py detects user confirmation ("do it", "yes", etc.)
  4. execute_pending() — runs the stored ops via glob-expanded shutil/osascript
  5. cancel_pending() — discards the plan cleanly

Module-level _PENDING_PLAN survives across HTTP turns in the same server process.
Since _process_turn runs under _lock, no separate lock is needed here.
"""

from __future__ import annotations

import os
import re
import glob
import json
import shutil
import logging
import subprocess
from typing import Optional

_logger = logging.getLogger(__name__)
_logger.addHandler(logging.NullHandler())
_logger.propagate = False

_PENDING_PLAN: Optional[dict] = None   # {"summary": str, "ops": list}


# ── Intent detection ──────────────────────────────────────────────────────────

_TRIGGER_PHRASES = {
    "organise", "organize", "tidy", "sort", "group", "arrange", "clean up",
    "move all", "copy all", "take all", "put all", "grab all", "pull all",
    "make a folder", "create a folder", "make folder", "new folder", "archive",
    "screenshots", "all files", "all the files", "all my",
}

# ── Tracker / document creation triggers ─────────────────────────────────────

_TRACKER_TRIGGERS = (
    "create a tracker",
    "create tracker",
    "make a tracker",
    "build a tracker",
    "write a tracker",
    "create a markdown",
    "make a markdown",
    "write a markdown",
    "create a md",
    "make a md",
    "create a file",
    "make a file",
    "write a file",
    "document what we",
    "document what we've",
    "document our session",
    "summarise what we",
    "summarize what we",
    "write up what we",
    "write up our",
    "log what we",
    "tracker for what",
    "tracker of what",
    "can you complete one",
    "complete one for what",
)


def is_tracker_intent(text: str) -> bool:
    """Return True if the user is asking eLo to create a file or tracker document."""
    t = text.lower()
    return any(phrase in t for phrase in _TRACKER_TRIGGERS)

_OP_VERBS = {
    "move", "copy", "take", "put", "send", "archive", "organise", "organize",
    "sort", "group", "tidy", "clean", "gather", "collect", "create", "make",
}

_LOCATIONS = {
    "desktop", "downloads", "documents", "pictures", "folder", "files",
    "screenshots", "photos", "pdfs", "videos", "movies", "music",
}


def is_file_ops_intent(text: str) -> bool:
    """
    Return True if the input is a natural language file operation that is too
    contextual for regex matching — i.e. it describes intent without explicit
    paths ("take all screenshots off Desktop", not "mv ~/Desktop/x.png ~/Shots/").
    """
    t = text.lower()

    # Explicit shell-style paths → already handled by system_agent, skip here
    if re.search(r"[~/][\w/.\-]+\s*(?:->|–>|→)\s*[~/][\w/.\-]+", t):
        return False

    words = set(t.split())
    has_phrase   = any(ph in t for ph in _TRIGGER_PHRASES)
    has_verb     = bool(words & _OP_VERBS)
    has_location = any(loc in t for loc in _LOCATIONS)

    return (has_phrase or has_verb) and has_location


# ── Directory context ─────────────────────────────────────────────────────────

def _gather_context(query: str) -> str:
    q = query.lower()
    dirs_to_scan: list[str] = []

    if "desktop" in q:
        dirs_to_scan.append("~/Desktop")
    if "download" in q:
        dirs_to_scan.append("~/Downloads")
    if "document" in q:
        dirs_to_scan.append("~/Documents")
    if "picture" in q or "photo" in q:
        dirs_to_scan.append("~/Pictures")
    if not dirs_to_scan:
        dirs_to_scan = ["~/Desktop", "~/Downloads"]

    parts: list[str] = []
    for d in dirs_to_scan:
        expanded = os.path.expanduser(d)
        if not os.path.isdir(expanded):
            continue
        try:
            items = sorted(os.listdir(expanded), key=str.lower)[:80]
            parts.append(f"DIRECTORY: {d}/\n" + "\n".join(f"  {i}" for i in items))
        except Exception:
            pass

    return "\n\n".join(parts) or "No directory context available."


# ── LLM planner ───────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
You are eLo's file operation planner for macOS.

The user made a natural-language file request. Using the directory listing below,
determine exactly what operations are needed and return raw JSON — no markdown.

AVAILABLE OPERATIONS (all paths use ~/ for home):
  mkdir  → {"op": "mkdir",  "path": "~/path/to/dir"}
  move   → {"op": "move",   "src": "~/Desktop/glob*.ext", "dst": "~/Dest/"}
  copy   → {"op": "copy",   "src": "~/Desktop/glob*.ext", "dst": "~/Dest/"}
  rename → {"op": "rename", "src": "~/old/path",          "dst": "~/new/name"}
  delete → {"op": "delete", "path": "~/file/to/trash"}

RULES:
- Use glob patterns in src where the user said "all" or a file type
- mkdir must always come before any move/copy into that directory
- Never propose delete unless the user explicitly said delete or trash
- For macOS screenshots, typical Desktop names are: "Screen Shot*", "Screenshot*", "Capture*"
- Be precise — only operate on what the user described
- Destination folder in move/copy should end with /

RETURN FORMAT — raw JSON only:
{
  "summary": "One sentence in eLo's voice describing what you will do",
  "ops": [ ... ]
}

If the request is ambiguous or you cannot determine safe operations, return:
{
  "summary": "Not sure exactly what to do — can you say a bit more?",
  "ops": []
}
"""


def _call_llm(context: str, query: str) -> dict:
    import httpx

    user_message = f"DIRECTORY CONTEXT:\n{context}\n\nUSER REQUEST:\n{query}"

    # OpenAI primary (json_object response format forces valid JSON)
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    if openai_key:
        try:
            resp = httpx.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {openai_key}",
                         "Content-Type": "application/json"},
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": _SYSTEM_PROMPT},
                        {"role": "user",   "content": user_message},
                    ],
                    "response_format": {"type": "json_object"},
                    "max_tokens": 600,
                    "temperature": 0.1,
                },
                timeout=15.0,
            )
            resp.raise_for_status()
            return json.loads(resp.json()["choices"][0]["message"]["content"])
        except Exception as e:
            _logger.debug("OpenAI file plan failed: %s", e)

    # Claude fallback (Haiku — fast, cheap, good at structured output)
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if anthropic_key:
        try:
            resp = httpx.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": anthropic_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-haiku-4-5-20251001",
                    "max_tokens": 600,
                    "system": _SYSTEM_PROMPT + "\n\nIMPORTANT: Return ONLY raw JSON, no markdown.",
                    "messages": [{"role": "user", "content": user_message}],
                },
                timeout=15.0,
            )
            resp.raise_for_status()
            raw = resp.json()["content"][0]["text"].strip()
            # Strip any markdown fences
            raw = re.sub(r"^```\w*\n?", "", raw)
            raw = re.sub(r"\n?```$", "", raw)
            return json.loads(raw)
        except Exception as e:
            _logger.debug("Claude file plan failed: %s", e)

    raise RuntimeError("No LLM backend available for file planning")


# ── Execution ─────────────────────────────────────────────────────────────────

def _execute_plan(ops: list) -> list[str]:
    results: list[str] = []

    for op in ops:
        kind = op.get("op", "")
        try:
            if kind == "mkdir":
                path = os.path.expanduser(op["path"])
                os.makedirs(path, exist_ok=True)
                results.append(f"Created {op['path']}")

            elif kind in ("move", "copy"):
                src_pattern = os.path.expanduser(op["src"])
                dst         = os.path.expanduser(op["dst"])
                matches     = glob.glob(src_pattern)
                if not matches:
                    results.append(f"No files matched {op['src']}")
                    continue
                os.makedirs(dst, exist_ok=True)
                for src in matches:
                    if kind == "move":
                        shutil.move(src, dst)
                    else:
                        shutil.copy2(src, dst)
                verb = "Moved" if kind == "move" else "Copied"
                results.append(f"{verb} {len(matches)} file(s) to {op['dst']}")

            elif kind == "rename":
                src = os.path.expanduser(op["src"])
                dst = os.path.expanduser(op["dst"])
                shutil.move(src, dst)
                results.append(f"Renamed to {op['dst']}")

            elif kind == "write":
                path    = os.path.expanduser(op["path"])
                content = op.get("content", "")
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w", encoding="utf-8") as _wf:
                    _wf.write(content)
                results.append(f"Written to {op['path']}")

            elif kind == "delete":
                path_pattern = os.path.expanduser(op["path"])
                matches      = glob.glob(path_pattern)
                if not matches:
                    results.append(f"Nothing found at {op['path']}")
                    continue
                # Batch Finder Trash — single AppleScript call for all matched files
                posix_list = ", ".join(f'POSIX file "{f}"' for f in matches)
                subprocess.run(
                    ["osascript", "-e",
                     f'tell application "Finder" to delete {{{posix_list}}}'],
                    capture_output=True, timeout=15,
                )
                results.append(f"Sent {len(matches)} item(s) to Trash")

        except Exception as exc:
            results.append(f"Error ({kind}): {exc}")

    return results


# ── Public API ────────────────────────────────────────────────────────────────

def agent(query: str) -> str:
    """
    Plan a file operation from natural language. Stores the plan for later
    execution and returns a [FILE_PLAN: ...] context string.
    """
    global _PENDING_PLAN

    try:
        context = _gather_context(query)
        plan    = _call_llm(context, query)
    except Exception as exc:
        _logger.debug("llm_file_agent.agent failed: %s", exc)
        return "[FILE_PLAN: Not sure where those files are — can you say a bit more?]"

    summary = plan.get("summary", "")
    ops     = plan.get("ops", [])

    if not ops:
        return f"[FILE_PLAN: {summary}]"

    _PENDING_PLAN = {"summary": summary, "ops": ops}
    return (
        f"[FILE_PLAN: {summary} "
        f"Tell the user what you'll do and ask them to say 'do it' to confirm or 'cancel' to stop.]"
    )


_TRACKER_SYSTEM = """\
You are eLo's session tracker writer. Given a conversation log, produce a clean
markdown tracker document summarising what was discussed, decided, and what's next.

FORMAT — use this exact structure:
# Session Tracker — [topic derived from conversation]

## What We Covered
- bullet per topic discussed

## Decisions Made
- bullet per concrete decision (skip if none)

## Built / Wired
- bullet per thing that was actually created or changed (skip if none)

## Outstanding
- bullet per open thread, bug, or next step

---
*Generated by eLo OS*

RULES:
- Be specific — use actual names, file paths, feature names from the conversation
- Skip sections that have nothing to put in them
- Keep bullets tight — one line each
- Do not add commentary or preamble — just the document
"""


def tracker_agent(query: str, session_context: str = "") -> str:
    """
    Generate a markdown tracker from the current session and store it as a
    pending write plan. Returns a [FILE_PLAN: ...] context string for the LLM.

    Args:
        query           — the user's original request
        session_context — conversation history string (turns from _SESSION_WINDOW)
    """
    global _PENDING_PLAN

    import httpx, datetime

    ctx = session_context or "No session context available."
    user_msg = f"CONVERSATION:\n{ctx}\n\nUSER REQUEST:\n{query}"

    content = ""

    openai_key = os.environ.get("OPENAI_API_KEY", "")
    if openai_key:
        try:
            resp = httpx.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {openai_key}",
                         "Content-Type": "application/json"},
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": _TRACKER_SYSTEM},
                        {"role": "user",   "content": user_msg},
                    ],
                    "max_tokens": 1000,
                    "temperature": 0.2,
                },
                timeout=20.0,
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            _logger.debug("tracker_agent OpenAI failed: %s", e)

    if not content:
        anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if anthropic_key:
            try:
                resp = httpx.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": anthropic_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": "claude-haiku-4-5-20251001",
                        "max_tokens": 1000,
                        "system": _TRACKER_SYSTEM,
                        "messages": [{"role": "user", "content": user_msg}],
                    },
                    timeout=20.0,
                )
                resp.raise_for_status()
                content = resp.json()["content"][0]["text"].strip()
            except Exception as e:
                _logger.debug("tracker_agent Claude failed: %s", e)

    if not content:
        return "Couldn't write the tracker right now — LLM unavailable."

    date_str  = datetime.datetime.now().strftime("%Y-%m-%d")
    filename  = f"session_tracker_{date_str}.md"
    save_path = os.path.expanduser(
        os.path.join("~/Documents/DISENELO/trackers", filename)
    )

    try:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "w", encoding="utf-8") as _f:
            _f.write(content)
    except Exception as _write_err:
        return f"Generated it but couldn't save — {_write_err}"

    return f"Done. Tracker saved to Documents/DISENELO/trackers/{filename}"


def has_pending() -> bool:
    return _PENDING_PLAN is not None


def execute_pending() -> str:
    global _PENDING_PLAN
    if _PENDING_PLAN is None:
        return "No pending operation."

    ops     = _PENDING_PLAN.get("ops", [])
    _PENDING_PLAN = None

    if not ops:
        return "Nothing to execute."

    results = _execute_plan(ops)
    done    = [r for r in results if not r.startswith("Error")]
    errors  = [r for r in results if r.startswith("Error")]

    if errors:
        return "Done — with some issues. " + " ".join(done + errors)
    return "Done. " + " ".join(done)


def cancel_pending() -> None:
    global _PENDING_PLAN
    _PENDING_PLAN = None
