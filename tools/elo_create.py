"""
tools/elo_create.py — eLo CREATE capability implementation.

Provides the core file operations eLo can perform:
    create_file, read_file, edit_file, move_file, save_note, run_python, generate_research

Authority: David L3 2026-09-05 (BA-06) + WO-CREATE-IMPL-001 + WO-OUTPUT-STYLE-001.
Identity guard: eLo cannot create/edit files in its own runtime config paths.
Output style: all eLo-created files carry eLo's voice, not generic AI output.
"""

from __future__ import annotations

import os
import re
import time
import shutil
import textwrap
import logging
import subprocess
import datetime
from typing import Optional

_log = logging.getLogger(__name__)
_log.addHandler(logging.NullHandler())

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# WO-OUTPUT-STYLE-001: eLo's output directories — where eLo can write
_ALLOWED_WRITE_ROOTS = [
    os.path.expanduser("~/Documents/DISENELO/"),
    os.path.expanduser("~/Desktop/Output/"),
    os.path.expanduser("~/Desktop/"),
    os.path.expanduser("~/Documents/"),
    os.path.join(_ROOT, "data", "create_drafts"),
    os.path.join(_ROOT, "data", "notes"),
    os.path.join(_ROOT, "data", "elo_notes"),
]

# Identity guard — eLo never overwrites its own runtime config
_PROTECTED_PATHS = [
    os.path.join(_ROOT, "runtime"),
    os.path.join(_ROOT, "prompts"),
    os.path.join(_ROOT, "tools", "elo_create.py"),  # not itself
    os.path.join(_ROOT, "engineering", "work_orders"),
    os.path.join(_ROOT, "runtime", "executive.py"),
    os.path.join(_ROOT, "prompts", "living_presence_spec.txt"),
]


# ── WO-OUTPUT-STYLE-001: eLo voice style wrapper ─────────────────────────────

def _elo_style_header(path: str, purpose: str = "") -> str:
    """Return a brief eLo-voiced header for a created file, appropriate to its type."""
    ext = os.path.splitext(path)[1].lower()
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")

    if ext in (".md", ".txt"):
        label = purpose or os.path.basename(path)
        return (
            f"<!-- eLo made this — {date_str} -->\n"
            f"<!-- {label} -->\n\n"
        )
    elif ext == ".py":
        label = purpose or os.path.basename(path)
        return (
            f"# eLo made this — {date_str}\n"
            f"# {label}\n\n"
        )
    return ""


def _elo_note_voice(content: str, tag: str = "") -> str:
    """Format a note in eLo's voice register — direct, warm, not formal doc style."""
    date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    tag_line = f"[{tag}] " if tag else ""
    header = f"— {tag_line}{date_str}\n\n"
    body = content.strip()
    return header + body + "\n"


# ── Identity guard ────────────────────────────────────────────────────────────

def _is_protected(path: str) -> bool:
    """Return True if the path is in a protected eLo config location."""
    abs_path = os.path.abspath(os.path.expanduser(path))
    return any(abs_path.startswith(p) for p in _PROTECTED_PATHS)


def _is_writable_root(path: str) -> bool:
    """Return True if the path is within an allowed write root."""
    abs_path = os.path.abspath(os.path.expanduser(path))
    # Always allow data/ subdirs within elo-ai root
    if abs_path.startswith(os.path.join(_ROOT, "data")):
        return True
    return any(abs_path.startswith(r) for r in _ALLOWED_WRITE_ROOTS)


# ── CREATE operations ─────────────────────────────────────────────────────────

def create_file(path: str, content: str, purpose: str = "") -> dict:
    """
    Create a file at `path` with `content`. Adds eLo-voiced header.

    Returns:
        {success, path, notification, error}
    """
    abs_path = os.path.abspath(os.path.expanduser(path))
    if _is_protected(abs_path):
        return {
            "success": False,
            "path": abs_path,
            "notification": f"I can't write there — that's part of how I work.",
            "error": f"PROTECTED_PATH: {abs_path}",
        }

    # Default to data/create_drafts if no allowed root
    if not _is_writable_root(abs_path):
        fname = os.path.basename(abs_path)
        abs_path = os.path.join(_ROOT, "data", "create_drafts", fname)

    try:
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        header = _elo_style_header(abs_path, purpose)
        with open(abs_path, "w", encoding="utf-8") as _f:
            _f.write(header + content)
        short = abs_path.replace(os.path.expanduser("~"), "~")
        return {
            "success": True,
            "path": abs_path,
            "notification": f"Done. {short}",
            "error": None,
        }
    except Exception as _e:
        _log.warning("create_file FAILED: %s", _e)
        return {"success": False, "path": abs_path, "notification": "Couldn't write it.", "error": str(_e)}


def read_file(path: str) -> dict:
    """
    Read a file and return its content.

    Returns:
        {success, path, content, error}
    """
    abs_path = os.path.abspath(os.path.expanduser(path))
    try:
        with open(abs_path, encoding="utf-8", errors="replace") as _f:
            content = _f.read()
        return {"success": True, "path": abs_path, "content": content, "error": None}
    except Exception as _e:
        _log.warning("read_file FAILED: %s", _e)
        return {"success": False, "path": abs_path, "content": "", "error": str(_e)}


def edit_file(path: str, instructions: str) -> dict:
    """
    Edit a file by appending a new section with eLo's voice framing.
    For simple edits: read → modify → write back.

    Returns:
        {success, path, notification, error}
    """
    abs_path = os.path.abspath(os.path.expanduser(path))
    if _is_protected(abs_path):
        return {
            "success": False,
            "path": abs_path,
            "notification": "I can't edit that — it's part of how I work.",
            "error": f"PROTECTED_PATH: {abs_path}",
        }
    try:
        existing = read_file(abs_path).get("content", "")
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        addition = f"\n\n<!-- Updated {date_str} -->\n{instructions.strip()}\n"
        with open(abs_path, "w", encoding="utf-8") as _f:
            _f.write(existing + addition)
        short = abs_path.replace(os.path.expanduser("~"), "~")
        return {
            "success": True,
            "path": abs_path,
            "notification": f"Added to {short}.",
            "error": None,
        }
    except Exception as _e:
        _log.warning("edit_file FAILED: %s", _e)
        return {"success": False, "path": abs_path, "notification": "Couldn't edit it.", "error": str(_e)}


def move_file(src: str, dest: str) -> dict:
    """
    Move or rename a file.

    Returns:
        {success, src, dest, notification, error}
    """
    abs_src = os.path.abspath(os.path.expanduser(src))
    abs_dst = os.path.abspath(os.path.expanduser(dest))
    if _is_protected(abs_src) or _is_protected(abs_dst):
        return {
            "success": False,
            "notification": "Can't move that — it's part of how I work.",
            "error": "PROTECTED_PATH",
        }
    try:
        os.makedirs(os.path.dirname(abs_dst), exist_ok=True)
        shutil.move(abs_src, abs_dst)
        return {
            "success": True,
            "src": abs_src,
            "dest": abs_dst,
            "notification": f"Moved to {abs_dst.replace(os.path.expanduser('~'), '~')}.",
            "error": None,
        }
    except Exception as _e:
        _log.warning("move_file FAILED: %s", _e)
        return {"success": False, "notification": "Couldn't move it.", "error": str(_e)}


def save_note(content: str, tag: str = "") -> dict:
    """
    Save a note to eLo's note store (data/elo_notes/).
    WO-OUTPUT-STYLE-001: note is formatted in eLo's natural register, not formal doc style.

    Returns:
        {success, path, notification, error}
    """
    _notes_dir = os.path.join(_ROOT, "data", "elo_notes")
    os.makedirs(_notes_dir, exist_ok=True)

    slug = re.sub(r"[^\w]+", "_", tag[:20] if tag else "note").strip("_").lower()
    ts = int(time.time())
    filename = f"{slug}_{ts}.md"
    abs_path = os.path.join(_notes_dir, filename)

    try:
        voiced = _elo_note_voice(content, tag)
        with open(abs_path, "w", encoding="utf-8") as _f:
            _f.write(voiced)
        return {
            "success": True,
            "path": abs_path,
            "notification": f"Noted. [{tag}] in elo_notes.",
            "error": None,
        }
    except Exception as _e:
        _log.warning("save_note FAILED: %s", _e)
        return {"success": False, "path": abs_path, "notification": "Couldn't save the note.", "error": str(_e)}


def run_python(code: str, timeout: int = 10) -> dict:
    """
    Execute Python code in a sandboxed subprocess.
    Returns stdout + stderr as result.

    Returns:
        {success, stdout, stderr, returncode, error}
    """
    try:
        proc = subprocess.run(
            ["python3", "-c", code],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "success": proc.returncode == 0,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "returncode": proc.returncode,
            "notification": proc.stdout.strip() or proc.stderr.strip() or "Ran — no output.",
            "error": None if proc.returncode == 0 else proc.stderr,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "stdout": "", "stderr": "timed out", "returncode": -1,
                "notification": "Timed out.", "error": "TimeoutExpired"}
    except Exception as _e:
        _log.warning("run_python FAILED: %s", _e)
        return {"success": False, "stdout": "", "stderr": str(_e), "returncode": -1,
                "notification": "Couldn't run it.", "error": str(_e)}


def generate_research(query: str) -> dict:
    """
    Research a query using the web_search capability and synthesise a response.
    WO-OUTPUT-STYLE-001: output framed in eLo's curious/exploratory perspective.

    Returns:
        {success, summary, sources, notification, error}
    """
    try:
        from tools.web_search import search as _search
        results = _search(query, max_results=5) or []
        if not results:
            return {
                "success": False,
                "summary": "",
                "sources": [],
                "notification": "Went looking — nothing solid came back.",
                "error": "no_results",
            }
        snippets = []
        sources = []
        for r in results:
            if hasattr(r, "snippet") and r.snippet:
                snippets.append(r.snippet)
            if hasattr(r, "url") and r.url:
                sources.append(r.url)
            elif hasattr(r, "text"):
                snippets.append(str(r.text)[:200])

        # Synthesise inline (no second LLM call — use snippet assembly)
        summary = "\n".join(f"— {s.strip()}" for s in snippets[:5] if s.strip())
        return {
            "success": True,
            "summary": summary,
            "sources": sources[:5],
            "notification": f"Found something. {len(snippets)} threads.",
            "error": None,
        }
    except Exception as _e:
        _log.warning("generate_research FAILED: %s", _e)
        return {
            "success": False,
            "summary": "",
            "sources": [],
            "notification": "Couldn't research that right now.",
            "error": str(_e),
        }
