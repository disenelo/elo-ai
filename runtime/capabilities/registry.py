"""
runtime/capabilities/registry.py — Central capability registry.

Every capability eLo possesses or will possess is described here.
Add `future=True` for capabilities not yet implemented.
The router queries this — it never imports agents directly.
"""
from __future__ import annotations
from runtime.capabilities.capability import (
    Capability, UNKNOWN,
    CAT_UTILITY, CAT_KNOWLEDGE, CAT_MEMORY, CAT_COMMUNICATION,
    CAT_MEDIA, CAT_SYSTEM, CAT_CREATIVE, CAT_DEVELOPMENT,
    CAT_DESKTOP, CAT_ROBOT, CAT_STUDIO,
    ACK_SYNC_RETURN, ACK_UNITY_ACK, ACK_NONE, ACK_UNKNOWN, ACK_SOURCES,
    SCOPE_PERSON, SCOPE_COMPANY, SCOPE_RESERVED,
)

# ── UTILITY ───────────────────────────────────────────────────────────────────
_UTILITY: list[Capability] = [
    Capability(
        id="time", display_name="Time", category=CAT_UTILITY,
        description="Current time and date",
        verbs=["time", "date", "day", "what time", "what day", "clock"],
        execution_priority=1, agent_module="tools.tool_router",
        ack_source=ACK_SYNC_RETURN,
    ),
    Capability(
        id="calculator", display_name="Calculator", category=CAT_UTILITY,
        description="Math and unit conversion",
        verbs=["calculate", "convert", "sum", "multiply", "divide", "plus", "minus",
               "math", "how much is", "what is"],
        synonyms=["compute", "work out"],
        execution_priority=1, agent_module="tools.tool_router",
        ack_source=ACK_SYNC_RETURN,
    ),
    Capability(
        id="weather", display_name="Weather", category=CAT_UTILITY,
        description="Current weather and forecast",
        verbs=["weather", "forecast", "rain", "temperature", "hot", "cold",
               "sunny", "cloudy", "snow", "wind"],
        requires_api=True, execution_priority=2,
        agent_module="tools.tool_router",
        ack_source=ACK_SYNC_RETURN,
    ),
    Capability(
        id="sun_events", display_name="Sun Events", category=CAT_UTILITY,
        description="Sunrise, sunset, dawn and dusk times for a location",
        verbs=["sunrise", "sunset", "dawn", "dusk", "golden hour", "solar noon",
               "when does the sun", "sun event", "sun time"],
        requires_api=False, execution_priority=2,
        agent_module="tools.tool_router",
        ack_source=ACK_SYNC_RETURN,
    ),
    Capability(
        id="news", display_name="News", category=CAT_UTILITY,
        description="Current headlines and news",
        verbs=["news", "headlines", "what's happening", "current events"],
        requires_api=True, execution_priority=3,
        agent_module="tools.tool_router",
        ack_source=ACK_SYNC_RETURN,
    ),
    Capability(
        id="translate", display_name="Translate", category=CAT_UTILITY,
        description="Language translation",
        verbs=["translate", "how do you say", "in spanish", "in french", "in japanese",
               "in arabic", "in portuguese", "in korean", "in mandarin"],
        execution_priority=3, agent_module="tools.tool_router",
        ack_source=ACK_SYNC_RETURN,
    ),
    Capability(
        id="timer", display_name="Timer", category=CAT_UTILITY,
        description="Timers and countdowns",
        verbs=["timer", "countdown", "pomodoro", "set timer", "remind me in",
               "alarm", "in 5 minutes", "in 10 minutes"],
        execution_priority=2, agent_module="tools.timer_agent",
        ack_source=ACK_SYNC_RETURN,
    ),
]

# ── KNOWLEDGE ─────────────────────────────────────────────────────────────────
_KNOWLEDGE: list[Capability] = [
    Capability(
        id="search", display_name="Search", category=CAT_KNOWLEDGE,
        description="Web search and summarisation",
        verbs=["search", "find", "look up", "google", "what is", "who is",
               "tell me about", "explain", "define"],
        requires_api=True, execution_priority=4,
        agent_module="tools.web_agent",
        ack_source=ACK_SYNC_RETURN,
    ),
    Capability(
        id="wikipedia", display_name="Wikipedia", category=CAT_KNOWLEDGE,
        description="Wikipedia article lookup",
        verbs=["wikipedia", "wiki", "article on"],
        requires_api=True, execution_priority=4,
        agent_module="tools.tool_router",
        ack_source=ACK_SYNC_RETURN,
    ),
    Capability(
        id="draft", display_name="Draft", category=CAT_KNOWLEDGE,
        description="Writing, brainstorming, and creative composition",
        verbs=["write", "draft", "compose", "brainstorm", "pitch", "email",
               "scene", "brief", "bio", "outline", "post", "story", "help me write"],
        execution_priority=5, agent_module="tools.draft_agent",
        ack_source=ACK_SYNC_RETURN,
    ),
]

# ── MEMORY ────────────────────────────────────────────────────────────────────
_MEMORY: list[Capability] = [
    Capability(
        id="obsidian", display_name="Obsidian", category=CAT_MEMORY,
        description="User's Obsidian notes vault",
        verbs=["my notes", "obsidian", "vault", "journal", "what did i write",
               "what did i note", "read notes"],
        execution_priority=2, agent_module="tools.file_reader_agent",
        ack_source=ACK_SYNC_RETURN,
    ),
    Capability(
        id="vault_write", display_name="Vault Write", category=CAT_MEMORY,
        description="Save things to memory",
        verbs=["remember this", "save this", "note this", "note that", "write this down",
               "add this to my notes", "save that"],
        execution_priority=2, agent_module="tools.vault_writer",
        ack_source=ACK_SYNC_RETURN,
        authority_scope=SCOPE_COMPANY,  # sole writer D-F; routes through Executive + David L3
    ),
    Capability(
        id="file_read", display_name="File Reader", category=CAT_MEMORY,
        description="Read files and documents",
        verbs=["read", "open file", "what's in", "read my", "tracker", "brief"],
        execution_priority=3, agent_module="tools.file_reader_agent",
        ack_source=ACK_SYNC_RETURN,
    ),
    Capability(
        id="clipboard", display_name="Clipboard", category=CAT_MEMORY,
        description="Access clipboard content",
        verbs=["clipboard", "what did i copy", "what's copied", "what have i copied"],
        execution_priority=1, agent_module="tools.clipboard_agent",
        ack_source=ACK_SYNC_RETURN,
    ),
]

# ── COMMUNICATION ─────────────────────────────────────────────────────────────
_COMMUNICATION: list[Capability] = [
    Capability(
        id="messages", display_name="Messages", category=CAT_COMMUNICATION,
        description="Send iMessages",
        verbs=["message", "text", "send", "iMessage", "tell", "let them know"],
        requires_confirmation=True, execution_priority=2,
        response_style="confirm", agent_module="tools.messages_agent",
        ack_source=ACK_SYNC_RETURN,
    ),
    Capability(
        id="calendar", display_name="Calendar", category=CAT_COMMUNICATION,
        description="View calendar events",
        verbs=["calendar", "schedule", "meeting", "event", "today", "tomorrow",
               "this week", "what's on", "coming up", "any meetings"],
        execution_priority=2, agent_module="tools.calendar_agent",
        ack_source=ACK_SYNC_RETURN,
    ),
    Capability(
        id="reminders", display_name="Reminders", category=CAT_COMMUNICATION,
        description="Set and read reminders",
        verbs=["remind me", "reminder", "reminders", "to-do", "to do"],
        execution_priority=2, agent_module="tools.reminders_agent",
        ack_source=ACK_SYNC_RETURN,
    ),
    Capability(
        id="create_document", display_name="Documents", category=CAT_CREATIVE,
        description="Write a text or markdown document into ~/Documents/eLo (WO-B3-0009)",
        verbs=["write that up", "make me a list", "create a doc", "write me a summary", "save that as a document"],
        execution_priority=3, agent_module="tools.document_writer",
        ack_source=ACK_SYNC_RETURN,
    ),
    Capability(
        id="notes", display_name="Apple Notes", category=CAT_COMMUNICATION,
        description="Create Apple Notes entries",
        verbs=["make a note", "new note", "apple notes", "add note"],
        execution_priority=3, agent_module="tools.notes_agent",
        ack_source=ACK_SYNC_RETURN,
    ),
    Capability(
        id="email", display_name="Email", category=CAT_COMMUNICATION,
        description="Send and read email",
        verbs=["email", "send email", "check email", "inbox", "mail"],
        requires_confirmation=True, future=True,
        response_style="confirm",
        ack_source=ACK_NONE,
    ),
]

# ── MEDIA ─────────────────────────────────────────────────────────────────────
_MEDIA: list[Capability] = [
    Capability(
        id="spotify", display_name="Spotify", category=CAT_MEDIA,
        description="Music playback via Spotify",
        verbs=["play", "pause", "resume", "skip", "next", "previous", "music",
               "song", "playlist", "shuffle", "what's playing"],
        requires_api=True, execution_priority=2,
        agent_module="tools.spotify_agent",
        ack_source=ACK_SYNC_RETURN,
    ),
    Capability(
        id="vision", display_name="Vision", category=CAT_MEDIA,
        description="Screen and camera vision",
        verbs=["what's on screen", "what do you see", "look at my screen",
               "read this", "what's this"],
        execution_priority=3, agent_module="tools.vision_agent",
        ack_source=ACK_SYNC_RETURN,
    ),
    Capability(
        id="camera", display_name="Camera", category=CAT_MEDIA,
        description="Physical camera input",
        verbs=["camera", "take photo", "capture", "look at this"],
        future=True,
        requires_authentication=True,   # macOS camera OS grant (D-PRESENCE gating)
        ack_source=ACK_NONE,
    ),
]

# ── DEVELOPMENT ───────────────────────────────────────────────────────────────
_DEVELOPMENT: list[Capability] = [
    Capability(
        id="github", display_name="GitHub", category=CAT_DEVELOPMENT,
        description="GitHub repository queries",
        verbs=["github", "repo", "repository", "pull request", "last commit",
               "branch", "pr", "commit"],
        requires_api=True, execution_priority=4,
        agent_module="tools.github_agent",
        ack_source=ACK_SYNC_RETURN,
    ),
    Capability(
        id="terminal", display_name="Terminal", category=CAT_DEVELOPMENT,
        description="Run shell commands",
        verbs=["terminal", "run", "execute", "shell", "bash", "command"],
        requires_confirmation=True, future=True,
        response_style="confirm",
        ack_source=ACK_NONE,
    ),
    Capability(
        id="computer_control", display_name="Computer Control", category=CAT_DEVELOPMENT,
        description="Control mouse, keyboard, and screen via macOS Accessibility (requires ELO_COMPUTER_CONTROL=1)",
        verbs=["click", "right click", "double click", "type", "press", "scroll",
               "move cursor", "move mouse", "take a screenshot", "keyboard shortcut"],
        requires_confirmation=True, execution_priority=1,
        response_style="confirm", agent_module="tools.computer_control_agent",
        ack_source=ACK_SYNC_RETURN,
    ),
    Capability(
        id="truth_sync", display_name="Truth Sync", category=CAT_DEVELOPMENT,
        description="Memory arbitration, drift detection, and commit draft generation",
        verbs=["check drift", "drift check", "sync memory", "save memory", "compress memory",
               "validate structure", "commit draft", "generate commit", "obsidian sync",
               "truth sync", "sync to github"],
        execution_priority=3,
        agent_module="tools.truth_sync",
        ack_source=ACK_SYNC_RETURN,
    ),
]

# ── SYSTEM ────────────────────────────────────────────────────────────────────
_SYSTEM: list[Capability] = [
    Capability(
        id="volume", display_name="Volume", category=CAT_SYSTEM,
        description="System audio volume control",
        verbs=["volume", "louder", "quieter", "mute", "unmute", "sound",
               "a bit louder", "bit quieter", "not so loud", "turn it up", "turn it down"],
        execution_priority=1, response_style="direct",
        agent_module="tools.system_agent",
        ack_source=ACK_SYNC_RETURN,
    ),
    Capability(
        id="brightness", display_name="Brightness", category=CAT_SYSTEM,
        description="Screen brightness control",
        verbs=["brightness", "dim", "brighter", "darker screen", "screen brightness"],
        execution_priority=1, response_style="direct",
        agent_module="tools.system_agent",
        ack_source=ACK_SYNC_RETURN,
    ),
    Capability(
        id="dark_mode", display_name="Dark Mode", category=CAT_SYSTEM,
        description="System dark/light mode toggle",
        verbs=["dark mode", "darkmode", "light mode", "lightmode", "dark theme"],
        execution_priority=1, response_style="direct",
        agent_module="tools.system_agent",
        ack_source=ACK_SYNC_RETURN,
    ),
    Capability(
        id="app_launch", display_name="App Launch", category=CAT_SYSTEM,
        description="Open applications",
        verbs=["open", "launch", "start", "open blender", "open unity", "open spotify"],
        requires_confirmation=False, execution_priority=2,
        response_style="direct", agent_module="tools.system_agent",
        ack_source=ACK_SYNC_RETURN,
    ),
    Capability(
        id="window_focus", display_name="Window Focus", category=CAT_SYSTEM,
        description="Focus application windows",
        verbs=["focus", "bring to front", "switch to"],
        execution_priority=2, response_style="direct",
        agent_module="tools.system_agent",
        ack_source=ACK_SYNC_RETURN,
    ),
    Capability(
        id="screenshot", display_name="Screenshot", category=CAT_SYSTEM,
        description="Take a screenshot",
        verbs=["screenshot", "screen capture", "capture screen", "take a screenshot"],
        execution_priority=1, response_style="direct",
        agent_module="tools.system_agent",
        ack_source=ACK_SYNC_RETURN,
    ),
    Capability(
        id="media_control", display_name="Media Control", category=CAT_SYSTEM,
        description="System media playback controls",
        verbs=["play pause", "stop media", "next track", "previous track"],
        execution_priority=2, response_style="direct",
        future=True,
        ack_source=ACK_NONE,
    ),
    Capability(
        id="sleep", display_name="Sleep", category=CAT_SYSTEM,
        description="System sleep",
        verbs=["sleep", "sleep the mac", "put to sleep"],
        requires_confirmation=True, future=True,
        response_style="confirm",
        ack_source=ACK_NONE,
    ),
]

# ── CREATIVE ─────────────────────────────────────────────────────────────────
_CREATIVE: list[Capability] = [
    Capability(
        id="image_gen", display_name="Image Gen", category=CAT_CREATIVE,
        description="Generate images from text prompts (DALL-E 3 → DALL-E 2 → SD local)",
        verbs=["generate image", "create image", "make image", "draw", "paint",
               "illustrate", "make a picture", "generate a picture", "create art",
               "make art", "design", "visualise", "visualize"],
        requires_api=True, execution_priority=2,
        agent_module="tools.image_gen_agent",
        ack_source=ACK_SYNC_RETURN,
    ),
    Capability(
        id="model_gen", display_name="3D Model Gen", category=CAT_CREATIVE,
        description="Generate 3D models from text (Hyper3D → Meshy → Tripo → Shap-E)",
        verbs=["generate 3d model", "create 3d model", "make a 3d model", "3d model of",
               "generate model", "create model", "make me a model", "build a 3d"],
        requires_api=True, execution_priority=2,
        agent_module="tools.model_gen_agent",
        ack_source=ACK_SYNC_RETURN,
    ),
    Capability(
        id="blender", display_name="Blender", category=CAT_CREATIVE,
        description="3D modelling and animation in Blender",
        verbs=["blender", "3D", "render", "animation", "rig", "model", "mesh",
               "sculpt", "material", "shader"],
        future=True,
        ack_source=ACK_NONE,
    ),
    Capability(
        id="unity", display_name="Unity", category=CAT_CREATIVE,
        description="Game development in Unity",
        verbs=["unity", "game", "scene", "play mode", "prefab", "component",
               "asset", "animator"],
        future=True,
        ack_source=ACK_NONE,
    ),
    Capability(
        id="substance", display_name="Substance", category=CAT_CREATIVE,
        description="Material and texture creation",
        verbs=["substance", "texture", "material", "pbr"],
        future=True,
        ack_source=ACK_NONE,
    ),
]

# ── DESKTOP ───────────────────────────────────────────────────────────────────
_DESKTOP: list[Capability] = [
    Capability(
        id="desktop_presence", display_name="Desktop Presence", category=CAT_DESKTOP,
        description="eLo desktop avatar and presence",
        verbs=["avatar", "desktop buddy", "elo avatar", "where are you"],
        execution_priority=1, agent_module="desktop.desktop_presence",
        ack_source=ACK_UNITY_ACK,
    ),
    Capability(
        id="file_drop", display_name="File Drop", category=CAT_DESKTOP,
        description="Drag and drop files onto eLo in the Presence window — images, PDFs, 3D models, text files. eLo reads and responds.",
        verbs=["drag", "drop", "drag a file", "drop a file", "drag to you",
               "drag and drop", "view this file", "view files", "files dragged",
               "can you view", "can you read a file"],
        execution_priority=1,
        ack_source=ACK_UNITY_ACK,
    ),
    Capability(
        id="window_observer", display_name="Window Observer", category=CAT_DESKTOP,
        description="Observe active window and application context",
        verbs=["what are you looking at", "what app", "active window"],
        future=True,
        ack_source=ACK_NONE,
    ),
]

# ── ROBOT ─────────────────────────────────────────────────────────────────────
_ROBOT: list[Capability] = [
    Capability(
        id="robot_runtime", display_name="Robot Runtime", category=CAT_ROBOT,
        description="eLo physical robot OS connection",
        verbs=["robot", "elo robot", "physical elo"],
        future=True,
        ack_source=ACK_NONE,
        authority_scope=SCOPE_RESERVED,  # hardware RESERVED: David L3 + separate LG-2 required
    ),
    Capability(
        id="robot_motion", display_name="Robot Motion", category=CAT_ROBOT,
        description="Robot servo and motion control",
        verbs=["walk", "move", "servo", "wave", "look", "turn"],
        future=True,
        ack_source=ACK_NONE,
        authority_scope=SCOPE_RESERVED,  # force/motion = RESERVED per LAW-017 B4 hardware split
    ),
    Capability(
        id="robot_camera", display_name="Robot Camera", category=CAT_ROBOT,
        description="Robot camera feed",
        verbs=["robot camera", "what does the robot see"],
        future=True,
        ack_source=ACK_NONE,
        authority_scope=SCOPE_RESERVED,  # hardware lane — RESERVED
    ),
]

# ── STUDIO ────────────────────────────────────────────────────────────────────
_STUDIO: list[Capability] = [
    Capability(
        id="3d_printer", display_name="3D Printer", category=CAT_STUDIO,
        description="3D printing control",
        verbs=["print", "3d print", "slice", "slicer", "print this"],
        future=True,
        ack_source=ACK_NONE,
    ),
    Capability(
        id="plotter", display_name="Plotter", category=CAT_STUDIO,
        description="Plotter and cutting machine control",
        verbs=["plot", "plotter", "cut", "vinyl cutter"],
        future=True,
        ack_source=ACK_NONE,
    ),
    Capability(
        id="heat_press", display_name="Heat Press", category=CAT_STUDIO,
        description="Heat press control",
        verbs=["heat press", "transfer", "press"],
        future=True,
        ack_source=ACK_NONE,
    ),
    Capability(
        id="laser", display_name="Laser Cutter", category=CAT_STUDIO,
        description="Laser cutter/engraver control",
        verbs=["laser", "engrave", "laser cut"],
        future=True,
        ack_source=ACK_NONE,
    ),
]

# ── Master registry ───────────────────────────────────────────────────────────
ALL_CAPABILITIES: list[Capability] = (
    _UTILITY + _KNOWLEDGE + _MEMORY + _COMMUNICATION +
    _MEDIA + _DEVELOPMENT + _SYSTEM + _CREATIVE +
    _DESKTOP + _ROBOT + _STUDIO
)

# ── PHONE EMBODIMENT SCOPE ────────────────────────────────────────────────────
# DAVID L3, 2026-08-28: "7. 20 genuinely work do those" — his ruling on which capabilities
# eLo can ACTUALLY perform on an iPhone. His condition, verbatim: "It would only be good if
# he can actually do it on the iPhone."
#
# Before this, every capability carried the dataclass default frozenset({"desktop"}), so
# `embodiment="mobile"` yielded 0 of 48 and eLo on the phone could not even `respond`
# (MT verification 2026-08-28, WO-MOBILE-001 AT-2 FAIL).
#
# Listed here as ONE auditable decision set rather than scattered across 48 declarations,
# so Board can review or amend the ruling in one place.
#
# EXCLUDED and why — recorded so the absence is a decision, not an oversight:
#   window/desktop-bound  app_launch · window_focus · window_observer · desktop_presence
#                         file_drop · screenshot · computer_control · terminal
#   no iOS API            volume (apps cannot set system volume) · dark_mode (cannot set
#                         system appearance) · sleep · clipboard (prompts on every read)
#   partial only          messages / email (compose sheet only — the USER presses send)
#                         notes (no public iOS API) · vision (camera yes, SCREEN no)
#                         file_read / obsidian (sandboxed)
#   desktop apps          unity · blender · substance
#   needs a Mac bridge    3d_printer · laser · plotter · heat_press
#                         robot_camera · robot_motion · robot_runtime  (also RESERVED)
_PHONE_CAPABLE: frozenset[str] = frozenset({
    "time", "timer", "calculator", "translate", "weather", "news",
    "search", "wikipedia", "draft", "image_gen", "model_gen", "github",
    "spotify", "calendar", "reminders", "camera", "truth_sync",
    "brightness",       # UIScreen.main.brightness IS settable while the app is foreground
    "media_control",    # own-app audio only
    "vault_write",
})

for _c in ALL_CAPABILITIES:
    if _c.id in _PHONE_CAPABLE:
        _c.embodiment_scope = frozenset(_c.embodiment_scope | {"mobile"})

_BY_ID: dict[str, Capability] = {c.id: c for c in ALL_CAPABILITIES}


def get(capability_id: str) -> Capability | None:
    return _BY_ID.get(capability_id)


def by_category(category: str) -> list[Capability]:
    return [c for c in ALL_CAPABILITIES if c.category == category]


def all_enabled() -> list[Capability]:
    return [c for c in ALL_CAPABILITIES if c.enabled and not c.future]


# ── WO-111 card 05a: ACK-path coverage ────────────────────────────────────────

def capabilities_missing_ack_path() -> list[str]:
    """
    Return ids of capabilities that have not declared an ack_source.

    Any capability with `ack_source == ACK_UNKNOWN` (the default) is one someone
    added without deciding how outcomes get confirmed — a Verified Speech breach
    waiting to happen. The registry-level test in test_wo111_ack_contract fails
    when this list is non-empty.
    """
    return [c.id for c in ALL_CAPABILITIES
            if c.ack_source == ACK_UNKNOWN
            or c.ack_source not in ACK_SOURCES]


# ── WO-CANON-XXIII §A: authority scope helpers ─────────────────────────────────

def get_scope(capability_id: str) -> str:
    """
    Return the authority scope for a capability ID.
    Defaults to SCOPE_PERSON if capability is not in the registry.
    Router calls this before offering to act.
    """
    cap = _BY_ID.get(capability_id)
    return cap.authority_scope if cap else SCOPE_PERSON


def permission_manifest() -> list[dict]:
    """
    Return the permission manifest — one row per capability with its authority scope.
    Emitted by the registry as the Audit's single view of what eLo can do and at what scope.
    """
    return [
        {
            "id":              c.id,
            "display_name":    c.display_name,
            "category":        c.category,
            "authority_scope": c.authority_scope,
            "available":       c.is_available(),
            "future":          c.future,
        }
        for c in ALL_CAPABILITIES
    ]
