"""
tools/system_agent.py — macOS system control agent for eLo OS.

Gives eLo the ability to control windows, open apps, and organise files
on macOS. All actions are confirmed before execution — eLo describes what
he's about to do and waits for user approval.

RULE: Never auto-executes destructive or hard-to-reverse actions (move/delete files).
Always returns a description of the proposed action so eLo can confirm with the user.

Capabilities:
    window_fullscreen     — make a named app full screen
    window_focus          — bring a named app to front
    window_close          — close front window of a named app
    app_open              — launch a named app
    app_quit              — quit a named app
    folder_open           — reveal a folder in Finder
    folder_list           — list contents of a folder (read-only, safe)
    folder_organise       — propose an organisation plan for a folder (plan only, no write)
    volume_set            — set system output volume (0–100)
    volume_mute           — mute system audio
    windows_minimise_all  — minimise all visible windows
    windows_restore_all   — restore all minimised windows

Adding a new action:
    1. Add a handler function _do_<action>(args) → str
    2. Add an entry to _ACTIONS
    3. Add intent patterns to tool_router.py _INTENT_MAP with agent="system"
"""

from __future__ import annotations

import os
import re
import subprocess
import logging
from typing import Optional

_logger = logging.getLogger(__name__)
_logger.addHandler(logging.NullHandler())
_logger.propagate = False


# ── AppleScript runner ─────────────────────────────────────────────────────────

def _osascript(script: str) -> str:
    """Run an AppleScript snippet. Returns stdout or raises on error."""
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True, text=True, timeout=10
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "osascript error")
    return result.stdout.strip()


# ── App name normaliser ────────────────────────────────────────────────────────

_APP_ALIASES = {
    "chrome":     "Google Chrome",
    "google":     "Google Chrome",
    "safari":     "Safari",
    "firefox":    "Firefox",
    "finder":     "Finder",
    "terminal":   "Terminal",
    "vscode":     "Visual Studio Code",
    "code":       "Visual Studio Code",
    "vs code":    "Visual Studio Code",
    "slack":      "Slack",
    "figma":      "Figma",
    "blender":    "Blender",
    "unity":      "Unity",
    "xcode":      "Xcode",
    "mail":       "Mail",
    "messages":   "Messages",
    "music":      "Music",
    "spotify":    "Spotify",
    "notes":      "Notes",
    "calendar":   "Calendar",
    "photos":     "Photos",
}


def _resolve_app(name: str) -> str:
    """Resolve a casual app name to its macOS display name."""
    return _APP_ALIASES.get(name.lower().strip(), name.strip().title())


# ── Action handlers ────────────────────────────────────────────────────────────

def _do_window_fullscreen(app_name: str) -> str:
    app = _resolve_app(app_name)
    _osascript(f'tell application "{app}" to activate')
    _osascript(f'''
        tell application "System Events"
            tell process "{app}"
                set value of attribute "AXFullScreen" of window 1 to true
            end tell
        end tell
    ''')
    return f"{app} is now full screen."


def _do_window_focus(app_name: str) -> str:
    app = _resolve_app(app_name)
    _osascript(f'tell application "{app}" to activate')
    return f"Brought {app} to the front."


def _do_window_close(app_name: str) -> str:
    app = _resolve_app(app_name)
    _osascript(f'''
        tell application "{app}"
            close front window
        end tell
    ''')
    return f"Closed the front window of {app}."


def _do_app_open(app_name: str) -> str:
    app = _resolve_app(app_name)
    _osascript(f'tell application "{app}" to activate')
    return f"Opened {app}."


def _do_app_quit(app_name: str) -> str:
    app = _resolve_app(app_name)
    _osascript(f'tell application "{app}" to quit')
    return f"Quit {app}."


_HOME_FOLDERS = {"desktop": "~/Desktop", "documents": "~/Documents", "downloads": "~/Downloads",
                 "pictures": "~/Pictures", "music": "~/Music", "movies": "~/Movies", "home": "~"}


def _expand_folder(path: str) -> str:
    """'desktop' means David's Desktop, not a folder of that name wherever the
    server happens to run (B3 2026-10-06: it listed elo-ai/desktop/)."""
    p = path.strip()
    return os.path.expanduser(_HOME_FOLDERS.get(p.lower(), p))


def _do_folder_open(path: str) -> str:
    expanded = _expand_folder(path)
    if not os.path.isdir(expanded):
        raise ValueError(f"Folder not found: {expanded}")
    subprocess.run(["open", expanded], check=True)
    return f"Opened {expanded} in Finder."


def _do_folder_list(path: str) -> str:
    expanded = _expand_folder(path)
    if not os.path.isdir(expanded):
        raise ValueError(f"Folder not found: {expanded}")
    entries = sorted(os.scandir(expanded), key=lambda e: (not e.is_dir(), e.name.lower()))
    lines = []
    for e in entries[:30]:  # cap at 30
        tag = "📁" if e.is_dir() else "📄"
        lines.append(f"{tag} {e.name}")
    summary = "\n".join(lines)
    if len(entries) > 30:
        summary += f"\n… and {len(entries) - 30} more"
    return f"Contents of {expanded}:\n{summary}"


def _do_folder_organise(path: str) -> str:
    """Read-only: propose an organisation plan without moving anything."""
    expanded = os.path.expanduser(path)
    if not os.path.isdir(expanded):
        raise ValueError(f"Folder not found: {expanded}")

    # Group by extension
    groups: dict[str, list[str]] = {}
    for entry in os.scandir(expanded):
        if entry.is_file():
            ext = os.path.splitext(entry.name)[1].lower() or "no extension"
            groups.setdefault(ext, []).append(entry.name)

    if not groups:
        return f"{expanded} appears to be empty or contains only folders."

    lines = [f"Here's how I'd organise {expanded}:", ""]
    for ext, files in sorted(groups.items()):
        folder_name = ext.lstrip(".").upper() + " Files" if ext != "no extension" else "Misc"
        lines.append(f"  → {folder_name}/ ({len(files)} files: {', '.join(files[:3])}{'…' if len(files) > 3 else ''})")
    lines += ["", "Say 'do it' to apply, or tell me a different structure."]
    return "\n".join(lines)


def _do_file_copy(args: str) -> str:
    """Copy a file or folder. args: 'source -> destination'"""
    import shutil
    parts = re.split(r"\s*[-–→>]+\s*", args, maxsplit=1)
    if len(parts) != 2:
        raise ValueError("Need source and destination: 'file -> destination'")
    src, dst = os.path.expanduser(parts[0].strip()), os.path.expanduser(parts[1].strip())
    if not os.path.exists(src):
        raise ValueError(f"Source not found: {src}")
    if os.path.isdir(src):
        shutil.copytree(src, os.path.join(dst, os.path.basename(src)))
    else:
        shutil.copy2(src, dst)
    return f"Copied {os.path.basename(src)} to {dst}."


def _do_file_move(args: str) -> str:
    """Move a file or folder. args: 'source -> destination'"""
    import shutil
    parts = re.split(r"\s*[-–→>]+\s*", args, maxsplit=1)
    if len(parts) != 2:
        raise ValueError("Need source and destination")
    src, dst = os.path.expanduser(parts[0].strip()), os.path.expanduser(parts[1].strip())
    if not os.path.exists(src):
        raise ValueError(f"Source not found: {src}")
    shutil.move(src, dst)
    return f"Moved {os.path.basename(src)} to {dst}."


def _do_file_rename(args: str) -> str:
    """Rename a file or folder. args: 'old_name -> new_name' or 'path/to/file new_name'"""
    import shutil
    parts = re.split(r"\s*[-–→>]+\s*|(?<=\S)\s+(?=\S)", args, maxsplit=1)
    if len(parts) != 2:
        raise ValueError("Need old and new name")
    src  = os.path.expanduser(parts[0].strip())
    new  = parts[1].strip()
    dst  = os.path.join(os.path.dirname(src), new)
    if not os.path.exists(src):
        raise ValueError(f"File not found: {src}")
    shutil.move(src, dst)
    return f"Renamed {os.path.basename(src)} to {new}."


def _do_file_delete(args: str) -> str:
    """Move to Trash via AppleScript — safer than rm."""
    path = os.path.expanduser(args.strip())
    if not os.path.exists(path):
        raise ValueError(f"Not found: {path}")
    _osascript(f'tell application "Finder" to delete POSIX file "{path}"')
    return f"Moved {os.path.basename(path)} to Trash."


def _do_volume_set(level: str) -> str:
    """Set macOS output volume 0–100."""
    m = re.search(r'\d+', level)
    if not m:
        raise ValueError("Need a number 0–100 for volume.")
    vol = max(0, min(100, int(m.group())))
    _osascript(f"set volume output volume {vol}")
    return f"Volume set to {vol}%."


def _do_volume_mute(_arg: str) -> str:
    """Toggle mute on macOS output audio."""
    _osascript("set volume with output muted")
    return "Audio muted."


_MINIMISE_ALL_SCRIPT = """\
tell application "System Events"
    repeat with p in (every application process whose visible is true and name is not "Dock")
        try
            set miniaturized of every window of p to true
        end try
    end repeat
end tell
"""

_RESTORE_ALL_SCRIPT = """\
tell application "System Events"
    repeat with p in (every application process whose visible is true)
        try
            set miniaturized of every window of p to false
        end try
    end repeat
end tell
"""


def _do_windows_minimise_all(_arg: str) -> str:
    """Minimise all visible application windows via System Events."""
    subprocess.run(["osascript"], input=_MINIMISE_ALL_SCRIPT,
                   capture_output=True, text=True, timeout=30)
    return "All windows minimised."


def _do_windows_restore_all(_arg: str) -> str:
    """Restore all minimised windows via System Events."""
    subprocess.run(["osascript"], input=_RESTORE_ALL_SCRIPT,
                   capture_output=True, text=True, timeout=30)
    return "All windows restored."


# ── Action registry ────────────────────────────────────────────────────────────

# ── B3 2026-10-06: capability demo showed these registered but missing ─────────
# Each reads the result back and says only what the Mac reports.

def _dark_mode_state() -> bool:
    return _osascript('tell application "System Events" to tell appearance preferences '
                      'to get dark mode').strip() == "true"


def _do_dark_mode(arg: str) -> str:
    want = arg != "off"
    if _dark_mode_state() == want:
        return f"It's already in {'dark' if want else 'light'} mode."
    _osascript('tell application "System Events" to tell appearance preferences '
               f'to set dark mode to {"true" if want else "false"}')
    if _dark_mode_state() != want:
        raise RuntimeError("the Mac didn't switch")
    return "Dark mode on." if want else "Light mode on."


def _do_screenshot(_arg: str) -> str:
    import datetime as _dt
    path = os.path.expanduser(f"~/Desktop/eLo screenshot {_dt.datetime.now():%Y-%m-%d at %H.%M.%S}.png")
    subprocess.run(["screencapture", "-x", path], capture_output=True, timeout=15)
    if not os.path.exists(path):
        raise RuntimeError("screencapture didn't write a file")
    return "Screenshot saved to your Desktop."


def _volume_now() -> tuple[int, bool]:
    out = _osascript("get volume settings")  # output volume:42, input volume:…, output muted:false
    vol = re.search(r"output volume:(\d+)", out)
    muted = "output muted:true" in out
    return (int(vol.group(1)) if vol else -1), muted


def _do_volume_get(_arg: str) -> str:
    vol, muted = _volume_now()
    if vol < 0:
        raise RuntimeError("couldn't read the volume")
    return f"Volume's at {vol}%" + (" — but it's muted." if muted else ".")


def _do_volume_step(direction: str) -> str:
    vol, _ = _volume_now()
    new = max(0, min(100, vol + (10 if direction == "up" else -10)))
    _osascript(f"set volume output volume {new} without output muted")
    got, _ = _volume_now()
    return f"Volume {'up' if direction == 'up' else 'down'} to {got}%."


def _do_brightness(_arg: str) -> str:
    # No supported way to read or set this Mac's display brightness from here,
    # so nothing is attempted and nothing is claimed.
    return "I can't change your screen's brightness yet — that's not something I can reach on this Mac."


def _app_installed(name: str) -> str | None:
    """The real app name (its case) if it's installed, else None."""
    want = _resolve_app(name).lower() + ".app"
    for base in ("/Applications", "/System/Applications", "/System/Applications/Utilities",
                 os.path.expanduser("~/Applications")):
        try:
            for entry in os.listdir(base):
                if entry.lower() == want:
                    return entry[:-4]
        except OSError:
            continue
    return None


def _do_app_launch(app_name: str) -> str:
    app = _app_installed(app_name)
    if not app:
        raise RuntimeError(f"no app called {app_name} on this Mac")
    subprocess.run(["open", "-a", app], capture_output=True, timeout=15)
    for _ in range(10):
        running = _osascript(f'tell application "System Events" to (name of processes) contains "{app}"')
        if running.strip() == "true":
            return f"{app}'s open."
        import time as _t
        _t.sleep(0.5)
    raise RuntimeError(f"{app} didn't open")


_ACTIONS = {
    "window_fullscreen":    _do_window_fullscreen,
    "window_focus":         _do_window_focus,
    "window_close":         _do_window_close,
    "app_open":             _do_app_open,
    "app_quit":             _do_app_quit,
    "folder_open":          _do_folder_open,
    "folder_list":          _do_folder_list,
    "folder_organise":      _do_folder_organise,
    "file_copy":            _do_file_copy,
    "file_move":            _do_file_move,
    "file_rename":          _do_file_rename,
    "file_delete":          _do_file_delete,
    "volume_set":           _do_volume_set,
    "volume_mute":          _do_volume_mute,
    "windows_minimise_all": _do_windows_minimise_all,
    "windows_restore_all":  _do_windows_restore_all,
    "dark_mode":            _do_dark_mode,
    "screenshot":           _do_screenshot,
    "volume_get":           _do_volume_get,
    "volume_step":          _do_volume_step,
    "brightness":           _do_brightness,
    "app_launch":           _do_app_launch,
}

# safe actions — execute immediately without confirmation gate
_SAFE_ACTIONS = {
    "folder_list",
    "folder_organise",
    "volume_set",
    "volume_mute",
    "windows_minimise_all",
    "windows_restore_all",
    # B3 2026-10-06 — registry says no confirmation; harmless and read back.
    "dark_mode", "screenshot", "volume_get", "volume_step", "brightness", "app_launch",
}


# ── Intent detection ───────────────────────────────────────────────────────────

# (pattern, action, arg_capture_group)
# group=0 means full match (used when no capture group is needed for the arg)
_SYSTEM_INTENTS = [
    # B3 2026-10-06 — dark mode, screenshot, volume read/step, brightness, open <app>
    (r"\b(?:switch|turn|change|go|put)\s+(?:it\s+)?(?:on\s+|to\s+|into\s+)?dark\s*mode\b|\bdark\s*mode\s+on\b|^dark\s*mode$", "dark_mode", "on"),
    (r"\b(?:switch|turn|change|go|put)\s+(?:it\s+)?(?:on\s+|to\s+|into\s+|back\s+to\s+)?light\s*mode\b|\bdark\s*mode\s+off\b|\bturn\s+off\s+dark\s*mode\b", "dark_mode", "off"),
    (r"\b(?:take|grab|capture)\s+(?:a\s+)?screen\s*shot\b|^screen\s*shot$", "screenshot", 0),
    (r"\bwhat(?:'s|\s+is)\s+the\s+volume\b|\bvolume\s+level\b|\bhow\s+loud\s+is\s+it\b", "volume_get", 0),
    (r"\b(?:turn\s+(?:the\s+)?(?:volume|sound)\s+up|volume\s+up|louder)\b", "volume_step", "up"),
    (r"\b(?:turn\s+(?:the\s+)?(?:volume|sound)\s+down|volume\s+down|quieter)\b", "volume_step", "down"),
    (r"\b(?:bright(?:er|ness)|dimm?(?:er)?)\b.{0,30}\bscreen\b|\bscreen\b.{0,30}\b(?:bright(?:er|ness)|dimm?(?:er)?)\b", "brightness", 0),
    (r"^(?:(?:can|could|would)\s+you\s+)?(?:please\s+)?(?:open|launch)\s+(?:up\s+)?(?:the\s+)?([A-Za-z][\w\.]*(?:\s[A-Za-z][\w\.]*){0,2}?)(?:\s+app)?(?:\s+for\s+me)?[\s\?\.!]*$", "app_launch", 1),
    # Volume control — must come before generic window patterns
    (r"\b(?:turn|set|put)\s+(?:the\s+)?(?:volume|audio|sound)\s+(?:to\s+|at\s+)?(\d+)\s*%?", "volume_set",           1),
    (r"\bvolume\s+(?:to\s+|at\s+)?(\d+)\s*%?",                                                "volume_set",           1),
    (r"\b(\d+)\s*%?\s+(?:volume|audio)",                                                       "volume_set",           1),
    (r"\bmute\b",                                                                              "volume_mute",          0),
    # Minimise / restore all windows
    (r"\b(?:minimise|minimize|hide)\s+all\b",                                                  "windows_minimise_all", 0),
    (r"\b(?:minimise|minimize)\s+(?:my\s+)?windows?\b",                                        "windows_minimise_all", 0),
    (r"\b(?:restore|unminimise|unminimize|show\s+all|bring\s+back)\s+(?:all\s+)?(?:my\s+)?windows?\b", "windows_restore_all", 0),
    (r"\bshow\s+my\s+windows?\b",                                                              "windows_restore_all",  0),
    # Window / app operations
    (r"\b(full.?screen|fullscreen)\b.*\b(\w+)\b",                                              "window_fullscreen",    2),
    (r"\bmake\s+(\w[\w\s]*?)\s+(full.?screen|fullscreen)",                                     "window_fullscreen",    1),
    (r"\bopen\s+([\w\s]+?)\s+(?:app|application)\b",                                           "app_open",             1),
    (r"\blaunch\s+([\w\s]+?)\b",                                                               "app_open",             1),
    (r"\bquit\s+([\w\s]+?)\b",                                                                 "app_quit",             1),
    (r"\bclose\s+([\w\s]+?)\b",                                                                "window_close",         1),
    (r"\bfocus\s+on\s+([\w\s]+?)\b",                                                           "window_focus",         1),
    (r"\bbring\s+([\w\s]+?)\s+to\s+(?:the\s+)?front\b",                                        "window_focus",         1),
    # Folder / file operations
    (r"\bopen\s+(~?[\w\/\.\-]+)\s+(?:folder|directory)",                                       "folder_open",          1),
    (r"\bshow\s+(?:me\s+)?(~?[\w\/\.\-]+)\s+(?:folder|in finder)",                             "folder_open",          1),
    # B3 2026-10-06: only a folder-shaped target — "what's in the news" listed a folder "the"
    (r"\bwhat'?s?\s+in\s+(~?/[\w\/\.\-]+|~|(?:my\s+)?(?:desktop|documents|downloads|pictures|music|movies|home)(?:\s+folder)?)(?:\s|$|\?)",  "folder_list",          1),
    (r"\blist\s+(~?/[\w\/\.\-]+|~|(?:my\s+)?(?:desktop|documents|downloads|pictures|music|movies|home)(?:\s+folder)?)(?:\s|$|\?)",            "folder_list",          1),
    (r"\borgan(?:ise|ize)\s+(~?[\w\/\.\-]+)\b",                                                "folder_organise",      1),
    (r"\btidy\s+(?:up\s+)?(~?[\w\/\.\-]+)\b",                                                  "folder_organise",      1),
    (r"\bcp\s+(~?[\w\/\.\- ]+(?:->|–>|→)[\w\/\.\- ]+)\b",                                      "file_copy",            1),
    (r"\bcopy\s+(~?[\w\/\.\-]+)\s+(?:to|into)\s+(~?[\w\/\.\-]+)",                              "file_copy",            0),
    (r"\bmove\s+(~?[\w\/\.\-]+)\s+(?:to|into)\s+(~?[\w\/\.\-]+)",                              "file_move",            0),
    (r"\bmv\s+(~?[\w\/\.\- ]+(?:->|–>|→)[\w\/\.\- ]+)\b",                                      "file_move",            1),
    (r"\brename\s+(~?[\w\/\.\-]+)\s+(?:to|as)\s+([\w\.\-]+)",                                  "file_rename",          0),
    (r"\bdelete\s+(~?[\w\/\.\-]+)\b",                                                          "file_delete",          1),
    (r"\btrash\s+(~?[\w\/\.\-]+)\b",                                                           "file_delete",          1),
]


_LONG_INPUT_SAFE_ACTIONS = frozenset({
    "volume_set", "volume_mute", "windows_minimise_all", "windows_restore_all",
    "dark_mode", "screenshot", "volume_get", "volume_step", "brightness",
})


def detect(user_input: str) -> Optional[tuple[str, str]]:
    """
    Detect a system action intent. Returns (action_name, arg) or None.
    The caller should confirm with the user before calling execute().

    Guard: inputs > 10 words are treated as conversational — only unambiguous
    actions (volume, minimise/restore all) are matched. This prevents command
    verbs like 'close', 'open', 'list', 'launch', 'quit' from firing on
    incidental appearances in natural speech (e.g. "not even close to what
    the datasheet said" triggering window_close).
    """
    text = user_input.lower().strip()
    word_count = len(text.split())
    for pattern, action, group in _SYSTEM_INTENTS:
        if word_count > 10 and action not in _LONG_INPUT_SAFE_ACTIONS:
            continue
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            if isinstance(group, str):          # literal argument ("on", "up", …)
                return action, group
            if action == "app_launch" and not _app_installed(m.group(group).strip()):
                continue                        # "open the door" isn't an app
            try:
                arg = m.group(group).strip()
                if action == "folder_list":
                    arg = re.sub(r"^my\s+|\s+folder$", "", arg)
                return action, arg
            except IndexError:
                continue
    return None


def describe(action: str, arg: str) -> str:
    """Return a human-readable description of what will happen — for eLo to say before doing it."""
    descriptions = {
        "window_fullscreen":    f"make {_resolve_app(arg)} full screen",
        "window_focus":         f"bring {_resolve_app(arg)} to the front",
        "window_close":         f"close the front window of {_resolve_app(arg)}",
        "app_open":             f"open {_resolve_app(arg)}",
        "app_quit":             f"quit {_resolve_app(arg)}",
        "folder_open":          f"open {arg} in Finder",
        "folder_list":          f"show you what's in {arg}",
        "folder_organise":      f"suggest how to organise {arg}",
        "volume_set":           f"set your volume to {arg}%",
        "volume_mute":          "mute the audio",
        "windows_minimise_all": "minimise all open windows",
        "windows_restore_all":  "restore all minimised windows",
    }
    return descriptions.get(action, f"{action} {arg}")


def execute(action: str, arg: str) -> str:
    """Run the action. Returns a result string for eLo to relay. Raises on failure."""
    fn = _ACTIONS.get(action)
    if fn is None:
        raise ValueError(f"Unknown system action: {action}")
    return fn(arg)
