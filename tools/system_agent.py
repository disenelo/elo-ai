"""
tools/system_agent.py — macOS system control agent for eLo OS.

Gives eLo the ability to control windows, open apps, and organise files
on macOS. All actions are confirmed before execution — eLo describes what
he's about to do and waits for user approval.

RULE: Never auto-executes destructive or hard-to-reverse actions (move/delete files).
Always returns a description of the proposed action so eLo can confirm with the user.

Capabilities:
    window_fullscreen  — make a named app full screen
    window_focus       — bring a named app to front
    window_close       — close front window of a named app
    app_open           — launch a named app
    app_quit           — quit a named app
    folder_open        — reveal a folder in Finder
    folder_list        — list contents of a folder (read-only, safe)
    folder_organise    — propose an organisation plan for a folder (plan only, no write)

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


# ── Action registry ────────────────────────────────────────────────────────────

_ACTIONS = {
    "window_fullscreen": _do_window_fullscreen,
    "window_focus":      _do_window_focus,
    "window_close":      _do_window_close,
    "app_open":          _do_app_open,
    "app_quit":          _do_app_quit,
    "folder_open":       _do_folder_open,
    "folder_list":       _do_folder_list,
    "folder_organise":   _do_folder_organise,
    "file_copy":         _do_file_copy,
    "file_move":         _do_file_move,
    "file_rename":       _do_file_rename,
    "file_delete":       _do_file_delete,
}

# read-only actions — execute immediately without confirmation
_SAFE_ACTIONS = {"folder_list", "folder_organise"}


# ── Intent detection ───────────────────────────────────────────────────────────

# (pattern, action, arg_extractor)
_SYSTEM_INTENTS = [
    (r"\b(full.?screen|fullscreen)\b.*\b(\w+)\b",        "window_fullscreen", 2),
    (r"\bmake\s+(\w[\w\s]*?)\s+(full.?screen|fullscreen)", "window_fullscreen", 1),
    (r"\bopen\s+([\w\s]+?)\s+(?:app|application)\b",     "app_open",          1),
    (r"\blaunch\s+([\w\s]+?)\b",                         "app_open",          1),
    (r"\bquit\s+([\w\s]+?)\b",                           "app_quit",          1),
    (r"\bclose\s+([\w\s]+?)\b",                          "window_close",      1),
    (r"\bfocus\s+on\s+([\w\s]+?)\b",                     "window_focus",      1),
    (r"\bbring\s+([\w\s]+?)\s+to\s+(?:the\s+)?front\b",  "window_focus",      1),
    (r"\bopen\s+(~?[\w\/\.\-]+)\s+(?:folder|directory)", "folder_open",       1),
    (r"\bshow\s+(?:me\s+)?(~?[\w\/\.\-]+)\s+(?:folder|in finder)", "folder_open", 1),
    (r"\bwhat'?s?\s+in\s+(~?[\w\/\.\-]+)\b",             "folder_list",       1),
    (r"\blist\s+(~?[\w\/\.\-]+)\b",                      "folder_list",       1),
    (r"\borgan(?:ise|ize)\s+(~?[\w\/\.\-]+)\b",                                 "folder_organise", 1),
    (r"\btidy\s+(?:up\s+)?(~?[\w\/\.\-]+)\b",                                   "folder_organise", 1),
    (r"\bcp\s+(~?[\w\/\.\- ]+(?:->|–>|→)[\w\/\.\- ]+)\b",                       "file_copy",       1),
    (r"\bcopy\s+(~?[\w\/\.\-]+)\s+(?:to|into)\s+(~?[\w\/\.\-]+)",               "file_copy",       0),
    (r"\bmove\s+(~?[\w\/\.\-]+)\s+(?:to|into)\s+(~?[\w\/\.\-]+)",               "file_move",       0),
    (r"\bmv\s+(~?[\w\/\.\- ]+(?:->|–>|→)[\w\/\.\- ]+)\b",                       "file_move",       1),
    (r"\brename\s+(~?[\w\/\.\-]+)\s+(?:to|as)\s+([\w\.\-]+)",                   "file_rename",     0),
    (r"\bdelete\s+(~?[\w\/\.\-]+)\b",                                            "file_delete",     1),
    (r"\btrash\s+(~?[\w\/\.\-]+)\b",                                             "file_delete",     1),
]


def detect(user_input: str) -> Optional[tuple[str, str]]:
    """
    Detect a system action intent. Returns (action_name, arg) or None.
    The caller should confirm with the user before calling execute().
    """
    text = user_input.lower().strip()
    for pattern, action, group in _SYSTEM_INTENTS:
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
        "window_fullscreen": f"make {_resolve_app(arg)} full screen",
        "window_focus":      f"bring {_resolve_app(arg)} to the front",
        "window_close":      f"close the front window of {_resolve_app(arg)}",
        "app_open":          f"open {_resolve_app(arg)}",
        "app_quit":          f"quit {_resolve_app(arg)}",
        "folder_open":       f"open {arg} in Finder",
        "folder_list":       f"show you what's in {arg}",
        "folder_organise":   f"suggest how to organise {arg}",
    }
    return descriptions.get(action, f"{action} {arg}")


def execute(action: str, arg: str) -> str:
    """Run the action. Returns a result string for eLo to relay. Raises on failure."""
    fn = _ACTIONS.get(action)
    if fn is None:
        raise ValueError(f"Unknown system action: {action}")
    return fn(arg)
