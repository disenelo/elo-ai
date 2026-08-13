"""
desktop/app_context.py — rich content context from active app + browser tab.

Extracts WHAT is happening, not just which app is open.
Used by desktop_presence.shadow_context() to give eLo situational awareness.

Output examples:
  "You're watching Joe Budden Podcast on YouTube."
  "You're in Claude right now."
  "You're working in Blender."
  "You're on YouTube — looks like music."
  "You're in Sketchbook."
"""
from __future__ import annotations
import re


# ── YouTube content classifier ────────────────────────────────────────────────
# Parses the Chrome/Safari tab title (format: "[Video Title] - YouTube")
# and classifies what kind of content is playing.

_PODCAST_SIGNALS = [
    r"\bpodcast\b", r"\bpod\b", r"\bepisode\b", r"\bep\.?\s*\d+",
    r"\binterview\b", r"\btalk show\b", r"\bshow\b.*\bep\b",
    # named podcasts
    r"joe budden", r"drink champs", r"breakfast club", r"hot 97",
    r"brilliant idiots", r"no jumper", r"akademiks", r"complex",
    r"hot take", r"pivot", r"call her daddy", r"impaulsive",
    r"rogan", r"diary of a ceo",
]

_MUSIC_SIGNALS = [
    r"\bofficial (video|music video|lyric video|audio)\b",
    r"\b(ft\.|feat\.)\s+\w+", r"\blyrics?\b", r"\baudio\b",
    r"\bvevo\b", r"\balbum\b", r"\bsingle\b", r"\bmv\b",
    r"\bremix\b", r"\bcover\b",
]

_LOFI_SIGNALS = [
    r"\blo[- ]?fi\b", r"\bchill\b.*\b(beats?|mix|vibes?)\b",
    r"\blate night\b", r"\bstudy (beats?|music|playlist)\b",
    r"\bsleep (music|beats?|sounds?)\b", r"\brelax(ing)?\b.*\bmusic\b",
    r"\bjazz\b.*\bhiphop\b", r"\bbeats? to\b",
    r"\bnight drive\b", r"\brainy? playlist\b",
]

_PLAYLIST_SIGNALS = [
    r"\bplaylist\b", r"\bmix\b", r"\bcompilation\b", r"\balbum stream\b",
    r"\bhour(s?) of\b", r"\b\d+ hour\b",
]


def classify_youtube(tab_title: str) -> dict:
    """
    Parse a Chrome tab title and return content classification.

    Returns:
        {
          "type":  "podcast" | "music" | "lofi" | "playlist" | "video",
          "title": str,           # the video title, stripped of "- YouTube"
          "label": str,           # human-readable context for eLo
        }
    """
    # Strip "- YouTube" suffix
    title = re.sub(r"\s*-\s*YouTube\s*$", "", tab_title, flags=re.IGNORECASE).strip()

    if not title:
        return {"type": "video", "title": "", "label": "watching something on YouTube"}

    t = title.lower()

    for pattern in _PODCAST_SIGNALS:
        if re.search(pattern, t):
            return {
                "type":  "podcast",
                "title": title,
                "label": f"watching {title} — sounds like a podcast",
            }

    for pattern in _LOFI_SIGNALS:
        if re.search(pattern, t):
            return {
                "type":  "lofi",
                "title": title,
                "label": f"listening to lo-fi — {title}",
            }

    for pattern in _MUSIC_SIGNALS:
        if re.search(pattern, t):
            return {
                "type":  "music",
                "title": title,
                "label": f"watching a music video — {title}",
            }

    for pattern in _PLAYLIST_SIGNALS:
        if re.search(pattern, t):
            return {
                "type":  "playlist",
                "title": title,
                "label": f"listening to a playlist — {title}",
            }

    return {
        "type":  "video",
        "title": title,
        "label": f"watching {title}",
    }


def classify_browser(tab_title: str, tab_url: str = "") -> dict:
    """
    Given an active browser tab title + URL, classify what's happening.

    Returns:
        {
          "type":  str,    # "youtube", "claude", "github", "notion", "general"
          "content": dict, # additional content-specific data
          "label": str,    # human-readable context string
        }
    """
    url  = (tab_url or "").lower()
    title = (tab_title or "").strip()

    # YouTube
    if "youtube.com" in url or "- youtube" in title.lower():
        yt = classify_youtube(title)
        return {"type": "youtube", "content": yt, "label": yt["label"]}

    # Claude
    if "claude.ai" in url or title.lower().startswith("claude"):
        return {"type": "claude", "content": {}, "label": "working in Claude right now"}

    # GitHub
    if "github.com" in url:
        repo = re.search(r"github\.com/([^/]+/[^/?\s]+)", url)
        label = f"on GitHub — {repo.group(1)}" if repo else "on GitHub"
        return {"type": "github", "content": {}, "label": label}

    # Notion
    if "notion.so" in url or "notion.site" in url:
        return {"type": "notion", "content": {}, "label": "in Notion"}

    # Figma
    if "figma.com" in url:
        return {"type": "figma", "content": {}, "label": "in Figma"}

    # Google Docs/Drive
    if "docs.google.com" in url:
        return {"type": "docs", "content": {}, "label": "in Google Docs"}

    # Reddit
    if "reddit.com" in url:
        return {"type": "reddit", "content": {}, "label": "on Reddit"}

    # Generic browser
    label = f"in the browser{(' — ' + title[:40]) if title else ''}"
    return {"type": "general", "content": {}, "label": label}


def spotify_search_hint(youtube_title: str) -> str | None:
    """
    If the YouTube content looks like a music video, extract a search query
    for Spotify. Returns None if not music.

    "Drake - God's Plan (Official Video)" → "Drake God's Plan"
    """
    yt = classify_youtube(youtube_title)
    if yt["type"] not in ("music",):
        return None

    title = yt["title"]
    # Strip common suffixes
    title = re.sub(
        r"\s*[\(\[].*(official|lyric|audio|video|mv|vevo|hd|4k).*[\)\]]",
        "", title, flags=re.IGNORECASE
    ).strip()
    title = re.sub(r"\s*(ft\.|feat\.)\s+", " ", title, flags=re.IGNORECASE).strip()
    return title if title else None
