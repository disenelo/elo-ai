"""
desktop/chrome_reader.py — Read-only Chrome observation layer.

What eLo can actually see:
  - All open Chrome tabs (title + URL) across all windows
  - Bookmarks (title + URL, flattened)
  - Recent browser history (last N visits)

Shadow mode — observe only, never control.
All reads are best-effort; partial failure returns what's available.
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import subprocess
import shutil
import tempfile
from dataclasses import dataclass
from typing import Optional


_CHROME_PROFILE = os.path.expanduser(
    "~/Library/Application Support/Google/Chrome/Default"
)
_BOOKMARKS_PATH = os.path.join(_CHROME_PROFILE, "Bookmarks")
_HISTORY_PATH   = os.path.join(_CHROME_PROFILE, "History")


@dataclass
class ChromeTab:
    title: str
    url:   str
    window_index: int = 0
    tab_index:    int = 0

    def domain(self) -> str:
        m = re.search(r"https?://(?:www\.)?([^/]+)", self.url)
        return m.group(1) if m else self.url[:40]

    def matches(self, query: str) -> bool:
        q = query.lower()
        return q in self.title.lower() or q in self.url.lower()


@dataclass
class Bookmark:
    title: str
    url:   str
    folder: str = ""

    def matches(self, query: str) -> bool:
        q = query.lower()
        return q in self.title.lower() or q in self.url.lower()


@dataclass
class HistoryEntry:
    title: str
    url:   str
    visit_count: int = 1


# ── All open Chrome tabs ──────────────────────────────────────────────────────

def all_tabs() -> list[ChromeTab]:
    """Return every open Chrome tab across all windows via AppleScript."""
    script = """
tell application "Google Chrome"
    set result to {}
    set wi to 0
    repeat with w in windows
        set wi to wi + 1
        set ti to 0
        repeat with t in tabs of w
            set ti to ti + 1
            set end of result to (wi as string) & "|||" & (ti as string) & "|||" & (title of t) & "|||" & (URL of t)
        end repeat
    end repeat
    return result
end tell
"""
    try:
        r = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=5,
        )
        if r.returncode != 0:
            return []
        tabs: list[ChromeTab] = []
        # AppleScript returns comma-separated list items
        for line in r.stdout.strip().split(", "):
            parts = line.split("|||")
            if len(parts) == 4:
                wi, ti, title, url = parts
                tabs.append(ChromeTab(
                    title=title.strip(),
                    url=url.strip(),
                    window_index=int(wi.strip()),
                    tab_index=int(ti.strip()),
                ))
        return tabs
    except Exception:
        return []


def find_tab(query: str) -> Optional[ChromeTab]:
    """Find the first tab whose title or URL contains query."""
    for tab in all_tabs():
        if tab.matches(query):
            return tab
    return None


def focus_tab(tab: ChromeTab) -> bool:
    """Bring a specific Chrome tab to front."""
    script = f"""
tell application "Google Chrome"
    set index of window {tab.window_index} to 1
    set active tab index of window {tab.window_index} to {tab.tab_index}
    activate
end tell
"""
    try:
        r = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, timeout=5,
        )
        return r.returncode == 0
    except Exception:
        return False


def open_url(url: str) -> bool:
    """Open a URL in Chrome."""
    try:
        script = f'tell application "Google Chrome" to open location "{url}"'
        r = subprocess.run(["osascript", "-e", script], capture_output=True, timeout=5)
        subprocess.run(["osascript", "-e", 'tell application "Google Chrome" to activate'],
                       capture_output=True, timeout=3)
        return r.returncode == 0
    except Exception:
        return False


# ── Bookmarks ─────────────────────────────────────────────────────────────────

def _flatten_bookmarks(node: dict, folder: str = "") -> list[Bookmark]:
    results: list[Bookmark] = []
    node_type = node.get("type", "")
    if node_type == "url":
        results.append(Bookmark(
            title=node.get("name", ""),
            url=node.get("url", ""),
            folder=folder,
        ))
    elif node_type == "folder":
        name = node.get("name", "")
        for child in node.get("children", []):
            results.extend(_flatten_bookmarks(child, folder=name))
    else:
        # Root node — iterate children
        for child in node.get("children", []):
            results.extend(_flatten_bookmarks(child, folder=folder))
    return results


def bookmarks() -> list[Bookmark]:
    """Return all Chrome bookmarks, flattened."""
    try:
        with open(_BOOKMARKS_PATH, encoding="utf-8") as f:
            data = json.load(f)
        roots = data.get("roots", {})
        result: list[Bookmark] = []
        for root_node in roots.values():
            result.extend(_flatten_bookmarks(root_node))
        return result
    except Exception:
        return []


def find_bookmark(query: str) -> list[Bookmark]:
    """Return bookmarks matching query."""
    q = query.lower()
    return [b for b in bookmarks() if b.matches(q)]


# ── Browser history ───────────────────────────────────────────────────────────

def recent_history(limit: int = 50) -> list[HistoryEntry]:
    """
    Return the most recently visited URLs from Chrome's History SQLite DB.
    Copies the DB to a temp file first — Chrome holds a lock on the original.
    """
    if not os.path.exists(_HISTORY_PATH):
        return []
    try:
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            tmp_path = tmp.name
        shutil.copy2(_HISTORY_PATH, tmp_path)
        conn = sqlite3.connect(tmp_path)
        cur  = conn.execute(
            """
            SELECT urls.title, urls.url, urls.visit_count
            FROM urls
            ORDER BY last_visit_time DESC
            LIMIT ?
            """,
            (limit,),
        )
        entries = [
            HistoryEntry(title=row[0] or "", url=row[1] or "", visit_count=row[2])
            for row in cur.fetchall()
        ]
        conn.close()
        os.unlink(tmp_path)
        return entries
    except Exception:
        return []


def search_history(query: str, limit: int = 10) -> list[HistoryEntry]:
    """Return history entries matching query."""
    q = query.lower()
    return [
        e for e in recent_history(200)
        if q in e.title.lower() or q in e.url.lower()
    ][:limit]


# ── Connection summary ─────────────────────────────────────────────────────────
# Used by the Connection Surface to describe what eLo currently observes.

def observe(query: str = "") -> dict:
    """
    Return a structured snapshot of Chrome's state.
    If query is given, filter tabs/bookmarks/history to matches.
    """
    tabs_all = all_tabs()

    if query:
        tabs_matched      = [t for t in tabs_all if t.matches(query)]
        bookmarks_matched = find_bookmark(query)
        history_matched   = search_history(query, limit=5)
    else:
        tabs_matched      = tabs_all[:10]
        bookmarks_matched = []
        history_matched   = recent_history(10)

    return {
        "open_tabs":  [{"title": t.title, "url": t.url, "window": t.window_index, "tab": t.tab_index} for t in tabs_matched],
        "bookmarks":  [{"title": b.title, "url": b.url, "folder": b.folder} for b in bookmarks_matched],
        "history":    [{"title": h.title, "url": h.url, "visits": h.visit_count} for h in history_matched],
        "tab_count":  len(tabs_all),
    }
