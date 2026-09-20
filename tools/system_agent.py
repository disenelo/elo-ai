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


def _do_folder_open(path: str) -> str:
    expanded = os.path.expanduser(path)
    if not os.path.isdir(expanded):
        raise ValueError(f"Folder not found: {expanded}")
    subprocess.run(["open", expanded], check=True)
    return f"Opened {expanded} in Finder."


def _do_folder_list(path: str) -> str:
    expanded = os.path.expanduser(path)
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
}

# safe actions — execute immediately without confirmation gate
_SAFE_ACTIONS = {
    "folder_list",
    "folder_organise",
    "volume_set",
    "volume_mute",
    "windows_minimise_all",
    "windows_restore_all",
}


# ── Intent detection ───────────────────────────────────────────────────────────

# (pattern, action, arg_capture_group)
# group=0 means full match (used when no capture group is needed for the arg)
_SYSTEM_INTENTS = [
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
    (r"\bwhat'?s?\s+in\s+(~?[\w\/\.\-]+)\b",                                                   "folder_list",          1),
    (r"\blist\s+(~?[\w\/\.\-]+)\b",                                                            "folder_list",          1),
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
            try:
                arg = m.group(group).strip()
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
