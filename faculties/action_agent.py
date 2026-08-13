"""
faculties/action_agent.py — eLo acts on what he knows.

When eLo has found something worth surfacing — a link from the vault,
a search result, a bookmark connection — this module sequences the action:

  1. Jump to the target window (intent → Unity handles animation)
  2. Open the URL in Chrome (osascript)
  3. Read what's there (screen_reader)
  4. Report back to conversation with what was found

This is the "magic tap" — eLo moves, opens, reads, connects, speaks.
Unity owns the how-it-looks. Python owns the what-to-do.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Optional

_ROOT         = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BSTATE_PATH  = os.path.join(_ROOT, "blender", "blender_state.json")


@dataclass
class ActionResult:
    url:         str
    title:       str
    summary:     str          # from screen_reader after page loads
    topics:      list[str]
    spoken:      str          # what eLo says about it


# ── Intent writing ─────────────────────────────────────────────────────────────

def _write_intent(intent: dict) -> None:
    """Patch movement intent into blender_state.json without clobbering other keys."""
    try:
        try:
            with open(_BSTATE_PATH, encoding="utf-8") as f:
                state = json.load(f)
        except Exception:
            state = {}
        state["intent"]  = intent
        state["_ts"]     = time.time()
        tmp = _BSTATE_PATH + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        os.replace(tmp, _BSTATE_PATH)
    except Exception as e:
        import sys
        print(f"[action_agent] intent write failed: {e}", file=sys.stderr)


def jump_to_app(app_name: str) -> None:
    """Tell Unity to animate eLo jumping to a specific app's window."""
    _write_intent({"name": "jump_to_app", "target": app_name})


def sit_on_window(app_name: str) -> None:
    """Tell Unity to settle eLo on a specific window after arriving."""
    _write_intent({"name": "sit_on_window", "target": app_name})


# ── Core action: open URL ────────────────────────────────────────────────────

def open_and_read(
    url: str,
    topic: str = "",
    jump: bool = True,
) -> ActionResult:
    """
    Full sequence: jump to Chrome → open URL → wait → read screen → return result.

    Args:
        url   — the URL to open
        topic — the concept that triggered this action (for the spoken line)
        jump  — whether to send a jump intent to Unity first
    """
    # Step 1 — jump to Chrome (Unity handles animation)
    if jump:
        jump_to_app("Google Chrome")
        time.sleep(0.3)   # give Unity a moment to start the animation

    # Step 2 — open the URL
    from desktop.chrome_reader import open_url
    opened = open_url(url)

    # Step 3 — brief pause for page to load, then read
    time.sleep(2.0)

    # Step 4 — read the screen
    title   = ""
    summary = ""
    topics: list[str] = []

    try:
        from desktop.screen_reader import read as _sr_read
        content = _sr_read(force=True)
        if content:
            title   = content.app or url[:60]
            summary = content.summary
            topics  = content.topics
    except Exception:
        pass

    # Step 5 — settle on the Chrome window
    if jump:
        sit_on_window("Google Chrome")

    # Step 6 — build what eLo says
    spoken = _build_spoken(url, title, summary, topic)

    return ActionResult(
        url=url,
        title=title,
        summary=summary,
        topics=topics,
        spoken=spoken,
    )


def _build_spoken(url: str, title: str, summary: str, topic: str) -> str:
    domain = url.split("/")[2].replace("www.", "") if "//" in url else url[:40]
    if summary:
        return f"Pulled it up — {summary}"
    if title:
        return f"Got it open — {title}."
    return f"Opened {domain}."


# ── Vault-driven action: find a link and open it ─────────────────────────────

def act_on_topic(topic: str) -> Optional[ActionResult]:
    """
    Find the most relevant URL for a topic (vault → bookmarks → search)
    and open it. Returns None if nothing found.
    """
    url = _find_url_for_topic(topic)
    if not url:
        return None
    return open_and_read(url, topic=topic)


def _find_url_for_topic(topic: str) -> Optional[str]:
    """Check vault, bookmarks, and search — return best URL."""

    # 1. Obsidian vault — any URL in relevant notes
    try:
        from memory.vault_layer import lookup as vlookup
        import re
        entries = vlookup(topic, max_results=5)
        for e in entries:
            content = e.get("content", "") or e.get("text", "")
            urls = re.findall(r'https?://[^\s\)\]\"]+', content)
            if urls:
                return urls[0]
    except Exception:
        pass

    # 2. Chrome bookmarks
    try:
        from desktop.chrome_reader import find_bookmark
        bm = find_bookmark(topic)
        if bm:
            return bm[0].url
    except Exception:
        pass

    # 3. Web search — get first result
    try:
        from tools.web_search import search
        results = search(topic, max_results=1)
        if results:
            return results[0].url
    except Exception:
        pass

    return None


# ── Trigger detection ─────────────────────────────────────────────────────────

_ACTION_TRIGGERS = (
    "pull that up",
    "open that",
    "show me that",
    "jump to",
    "go find",
    "find and open",
    "look it up and show me",
    "open it",
    "go open",
    "show me the link",
    "open the link",
    "go there",
    "take me there",
)


def is_action_intent(text: str) -> bool:
    t = text.lower()
    return any(p in t for p in _ACTION_TRIGGERS)
