"""
tools/project_knowledge.py — Live project awareness for eLo OS.

Reads DISENELO project trackers, Studio Bibles, and Engineering status.
Provides two surfaces:
  - get_context()  → str injected into g_ctx as [STUDIO BRIEF] (permanent ambient)
  - get_tokens()   → set[str] registered as a Connection Surface stream

Auto-refreshes every 5 minutes. Never crashes — all failures are silent.
Config: config/project_paths.json
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import threading
import time

_ROOT       = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CFG_PATH   = os.path.join(_ROOT, "config", "project_paths.json")

_lock        = threading.Lock()
_context_str = ""         # current g_ctx payload
_tokens_set  = set()      # current Connection Surface token set
_last_load   = 0.0        # time.monotonic() of last refresh

# ── Config ────────────────────────────────────────────────────────────────────

def _cfg() -> dict:
    try:
        with open(_CFG_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _paths(key: str) -> list[str]:
    return [os.path.expanduser(p) for p in _cfg().get(key, [])]

def _int_cfg(key: str, default: int) -> int:
    return int(_cfg().get(key, default))

def _str_cfg(key: str, default: str) -> str:
    return str(_cfg().get(key, default))

# ── Markdown tracker reader ───────────────────────────────────────────────────

def _extract_tracker(path: str) -> tuple[str, set[str]]:
    """
    Read a tracker .md file. Return (summary_str, concept_tokens).
    Extracts: §2 Status Snapshot + most recent Change Log entry.
    """
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except Exception:
        return "", set()

    name = os.path.splitext(os.path.basename(path))[0].replace("_", " ").replace("-", " ")
    lines = []

    # §2 Status Snapshot — grab table rows (up to max_rows)
    max_rows = _int_cfg("tracker_max_status_rows", 30)
    snap_m = re.search(r"##\s*§2\s+Status Snapshot(.*?)(?:^##\s*§|\Z)", text, re.S | re.M)
    if snap_m:
        snap_block = snap_m.group(1)
        table_rows = [l.strip() for l in snap_block.splitlines() if l.strip().startswith("|") and "|---|" not in l]
        lines.append(f"STATUS ({name}):")
        lines.extend(table_rows[:max_rows])

    # Most recent Change Log entry — find section header, then first dated entry inside it
    max_cl = _int_cfg("tracker_max_changelog_chars", 800)
    cl_hdr = re.search(r"##\s*§(?:8|9|10)\s+Change Log", text)
    if cl_hdr:
        rest = text[cl_hdr.end():]
        entry_m = re.search(r"(###\s+\d{4}.*?)(?=^###\s+\d{4}|\Z)", rest, re.S | re.M)
        if entry_m:
            entry = entry_m.group(1).strip()[:max_cl]
            lines.append(f"RECENT ({name}): {entry}")

    summary = "\n".join(lines)

    # Tokens: all words 4+ chars, lowercase, from tracker text
    tokens = _words_from_text(text)

    return summary, tokens

# ── PDF reader ────────────────────────────────────────────────────────────────

def _pdf_to_text(path: str) -> str:
    """Extract text from PDF using pdftotext. Caches result to /tmp."""
    cache_dir = _str_cfg("pdf_cache_dir", "/tmp/elo_pdf_cache")
    os.makedirs(cache_dir, exist_ok=True)
    cache_file = os.path.join(cache_dir, os.path.basename(path) + ".txt")

    # Use cache if PDF hasn't changed
    try:
        pdf_mtime  = os.path.getmtime(path)
        cache_mtime = os.path.getmtime(cache_file)
        if cache_mtime > pdf_mtime:
            with open(cache_file, encoding="utf-8") as f:
                return f.read()
    except OSError:
        pass

    try:
        result = subprocess.run(
            ["pdftotext", "-layout", path, "-"],
            capture_output=True, text=True, timeout=15.0,
        )
        if result.returncode == 0:
            extracted = result.stdout
            with open(cache_file, "w", encoding="utf-8") as f:
                f.write(extracted)
            return extracted
    except Exception:
        pass
    return ""


def _extract_bible(path: str, is_pdf: bool) -> tuple[str, set[str]]:
    """Read a Bible document. Return (summary_str, concept_tokens)."""
    max_chars = _int_cfg("bible_max_chars", 1200)
    try:
        if is_pdf:
            raw = _pdf_to_text(path)
        else:
            with open(path, encoding="utf-8", errors="ignore") as f:
                raw = f.read()
    except Exception:
        return "", set()

    if not raw.strip():
        return "", set()

    name = os.path.splitext(os.path.basename(path))[0].replace("_", " ").replace("-", " ")
    # Take first max_chars of meaningful content
    cleaned = re.sub(r"\s+", " ", raw).strip()
    snippet = cleaned[:max_chars]
    summary = f"BIBLE ({name}):\n{snippet}"
    tokens  = _words_from_text(raw[:4000])  # more text for token extraction

    return summary, tokens

# ── Engineering README reader ─────────────────────────────────────────────────

def _extract_engineering(path: str) -> tuple[str, set[str]]:
    """Read engineering/README.md phase table."""
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except Exception:
        return "", set()

    # Grab the Phase Sequence table
    m = re.search(r"##\s+Phase Sequence(.*?)(?:^---|\Z)", text, re.S | re.M)
    if m:
        table = m.group(1).strip()
        # Just the table rows
        rows = [l for l in table.splitlines() if "|" in l and "---|" not in l]
        summary = "ENGINEERING PHASES:\n" + "\n".join(rows[:25])
    else:
        summary = "ENGINEERING: " + text[:400]

    tokens = _words_from_text(text)
    return summary, tokens

# ── Token extraction ──────────────────────────────────────────────────────────

_STOP = frozenset({
    "the", "and", "for", "are", "was", "with", "this", "that", "from",
    "have", "has", "not", "will", "can", "its", "their", "been", "into",
    "also", "when", "what", "each", "more", "then", "than", "but", "any",
    "all", "one", "two", "three", "some", "they", "were", "would", "could",
})

def _words_from_text(text: str) -> set[str]:
    """Extract lowercase words (4+ chars, not stopwords) from text."""
    return {
        w.lower() for w in re.findall(r"[a-zA-Z]{4,}", text)
        if w.lower() not in _STOP
    }

# ── Main refresh ──────────────────────────────────────────────────────────────

def _refresh() -> None:
    global _context_str, _tokens_set, _last_load

    parts   = []
    all_tok = set()

    # Engineering phase status
    for path in _paths("engineering"):
        if os.path.exists(path):
            s, t = _extract_engineering(path)
            if s:
                parts.append(s)
            all_tok |= t

    # Project trackers
    for path in _paths("trackers"):
        if os.path.exists(path):
            s, t = _extract_tracker(path)
            if s:
                parts.append(s)
            all_tok |= t

    # Bibles (txt)
    for path in _paths("bibles_txt"):
        if os.path.exists(path):
            s, t = _extract_bible(path, is_pdf=False)
            if s:
                parts.append(s)
            all_tok |= t

    # Bibles (pdf)
    for path in _paths("bibles_pdf"):
        if os.path.exists(path):
            s, t = _extract_bible(path, is_pdf=True)
            if s:
                parts.append(s)
            all_tok |= t

    context = "[STUDIO BRIEF]\n" + "\n\n".join(parts) if parts else ""

    with _lock:
        _context_str = context
        _tokens_set  = all_tok
        _last_load   = time.monotonic()


# ── Auto-refresh thread ───────────────────────────────────────────────────────

def _auto_refresh_loop() -> None:
    interval = _int_cfg("refresh_interval_seconds", 300)
    while True:
        try:
            _refresh()
        except Exception:
            pass
        time.sleep(interval)


_refresh_thread: threading.Thread | None = None

def start() -> None:
    """Start background refresh. Safe to call multiple times."""
    global _refresh_thread
    if _refresh_thread and _refresh_thread.is_alive():
        return
    # Do one synchronous load first so context is available immediately
    try:
        _refresh()
    except Exception:
        pass
    _refresh_thread = threading.Thread(
        target=_auto_refresh_loop, daemon=True, name="project-knowledge"
    )
    _refresh_thread.start()
    print(f"[eLo project knowledge] loaded — {len(_tokens_set)} tokens, {len(_context_str)} chars")


# ── Public API ────────────────────────────────────────────────────────────────

def get_context() -> str:
    """Return the current studio brief for g_ctx injection."""
    with _lock:
        return _context_str

def get_tokens() -> set[str]:
    """Return token set for Connection Surface stream registration."""
    with _lock:
        return set(_tokens_set)

def force_refresh() -> None:
    """Force an immediate reload. Call after tracker files change."""
    try:
        _refresh()
    except Exception:
        pass
