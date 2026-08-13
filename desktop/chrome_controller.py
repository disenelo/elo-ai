"""
desktop/chrome_controller.py — Active Chrome control layer.

Complements chrome_reader.py (read-only) with write/control operations.
All JS is injected into specific Chrome tabs via AppleScript.
"""
from __future__ import annotations

import subprocess
from typing import Optional

from desktop.chrome_reader import all_tabs, ChromeTab


def _find_youtube_tab() -> Optional[ChromeTab]:
    """Return the first open YouTube watch tab."""
    for tab in all_tabs():
        if "youtube.com/watch" in tab.url:
            return tab
    return None


def _exec_js(tab: ChromeTab, js: str) -> tuple[bool, str]:
    """Execute JavaScript in a specific Chrome tab. Returns (success, result_string)."""
    js_esc = js.replace("\\", "\\\\").replace('"', '\\"')
    script = (
        f'tell application "Google Chrome"\n'
        f'    execute tab {tab.tab_index} of window {tab.window_index} javascript "{js_esc}"\n'
        f'end tell'
    )
    try:
        r = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=6,
        )
        return r.returncode == 0, r.stdout.strip()
    except Exception:
        return False, ""


def play_video() -> tuple[bool, str]:
    """Play (resume) a paused video in the first open YouTube tab."""
    tab = _find_youtube_tab()
    if not tab:
        return False, "no_tab"
    ok, _ = _exec_js(tab, "document.querySelector('video').play(); 'ok'")
    return ok, tab.title


def pause_video() -> tuple[bool, str]:
    """Pause a playing video in the first open YouTube tab."""
    tab = _find_youtube_tab()
    if not tab:
        return False, "no_tab"
    ok, _ = _exec_js(tab, "document.querySelector('video').pause(); 'ok'")
    return ok, tab.title


def get_youtube_volume() -> Optional[int]:
    """Return current YouTube video volume as 0–100, or None if no tab found."""
    tab = _find_youtube_tab()
    if not tab:
        return None
    ok, result = _exec_js(tab, "Math.round(document.querySelector('video').volume * 100)")
    if ok and result.isdigit():
        return int(result)
    return None


def set_youtube_volume(percent: int) -> tuple[bool, int]:
    """
    Set YouTube's internal video volume to `percent` (0–100).
    Returns (success, actual_percent_set).
    """
    percent = max(0, min(100, percent))
    tab = _find_youtube_tab()
    if not tab:
        return False, percent
    js = (
        f"(function(){{"
        f"var v=document.querySelector('video');"
        f"v.volume={percent / 100.0:.4f};"
        f"v.muted=false;"
        f"return Math.round(v.volume*100);"
        f"}})()"
    )
    ok, result = _exec_js(tab, js)
    actual = int(result) if (ok and result.isdigit()) else percent
    return ok, actual


_YT_APP_NAMES = ["YouTube", "youtube"]


def open_youtube_app(url: str = "") -> tuple[bool, str]:
    """
    Open the YouTube Chrome PWA (installed via Chrome's 'Open in App').
    If `url` is provided, passes it as an argument so the app opens to that video.
    Falls back to youtube.com if the app isn't installed.

    Returns (used_app, message).
    """
    import os
    # Common install locations for Chrome PWAs on macOS
    _app_dirs = [
        os.path.expanduser("~/Applications/Chrome Apps.localized"),
        os.path.expanduser("~/Applications"),
        "/Applications",
    ]
    _app_path = None
    for _d in _app_dirs:
        for _name in _YT_APP_NAMES:
            _candidate = os.path.join(_d, f"{_name}.app")
            if os.path.isdir(_candidate):
                _app_path = _candidate
                break
        if _app_path:
            break

    if _app_path:
        _cmd = ["open", "-a", _app_path]
        if url:
            _cmd.append(url)
        try:
            r = subprocess.run(_cmd, capture_output=True, timeout=6)
            if r.returncode == 0:
                return True, "youtube_app"
        except Exception:
            pass

    # Fallback — open in regular Chrome
    from desktop.chrome_reader import open_url
    _target = url or "https://www.youtube.com"
    open_url(_target)
    return False, "chrome_fallback"


def open_current_video_in_app() -> tuple[bool, str]:
    """
    Grab the URL of the open YouTube tab and open it in the YouTube PWA.
    If no tab is open, opens the YouTube app to its home screen.
    """
    tab = _find_youtube_tab()
    url = tab.url if tab else ""
    return open_youtube_app(url)


def adjust_youtube_volume(delta: int) -> tuple[bool, int]:
    """
    Adjust YouTube's internal volume by `delta` percentage points (+/-).
    Clamps to 0–100. Returns (success, new_percent).
    """
    tab = _find_youtube_tab()
    if not tab:
        return False, 0
    delta_f = delta / 100.0
    clamp = "Math.max(0, Math.min(1, v.volume + (" + f"{delta_f:.4f}" + "))"
    js = (
        f"(function(){{"
        f"var v=document.querySelector('video');"
        f"v.volume={clamp};"
        f"v.muted=false;"
        f"return Math.round(v.volume*100);"
        f"}})()"
    )
    ok, result = _exec_js(tab, js)
    actual = int(result) if (ok and result.isdigit()) else 0
    return ok, actual
