"""
tools/capability_status.py — what eLo can do right now, as data.

Source: blender/agent_bus/builder3/FROM_ARCHITECT_2026-10-06_IS-ELO-VERDICTS-BUILDER3.md
  "a system that knows what tools it has? NO … Make capability_registry
   queryable by Builder 1's capabilities block. Your job: expose an API or
   structured dict that Builder 1 reads into the anchor." — registry must carry
   ACTIVE/INACTIVE per capability.
  "every tool call in your domain must return {success: bool, result: any,
   error: str}."
Live 2026-10-06: eLo denied controlling Spotify while a playlist he started
was playing — the LLM answered from training, not from state.

API (read by Builder 1 — this module never touches the prompt):
  get_active_capabilities() -> {cap_id: {...}}   registry + live probes
  capabilities_block()      -> str               compact anchor text
  spotify_status()          -> tool_result       structured, not prose
  tool_result(...)          -> {success, result, error}
  record_result(tool, r) / last_results()        every B3 tool call, newest last
"""
from __future__ import annotations

import os
import re
import subprocess
import threading
import time

_CACHE_S = 5.0
_cache: dict = {"ts": 0.0, "data": None}
_lock = threading.Lock()
_results: list[dict] = []
_RESULTS_MAX = 20


# ── result standard ───────────────────────────────────────────────────────────

def tool_result(success: bool, result=None, error: str | None = None) -> dict:
    """The one return shape for every Builder 3 tool call."""
    return {"success": bool(success), "result": result, "error": error}


def record_result(tool: str, r: dict) -> dict:
    """Log a tool call's outcome where the execution-confirmation gate can read it."""
    with _lock:
        _results.append({"tool": tool, "ts": time.time(), **r})
        del _results[:-_RESULTS_MAX]
    return r


def last_results(since_ts: float = 0.0) -> list[dict]:
    with _lock:
        return [dict(x) for x in _results if x["ts"] >= since_ts]


# ── live probes (Builder 3 capabilities) ──────────────────────────────────────

def spotify_status() -> dict:
    """{success, result: {state, track, artist, device, can}, error} — what
    Spotify is doing, from the Web API, else the app itself."""
    can = ["open", "play playlist/artist/track by name", "list playlists",
           "pause", "resume", "skip", "previous"]
    try:
        from tools import spotify_web as sw
        if not sw.is_available():
            return tool_result(False, {"state": "unconfigured", "can": []}, "no Spotify credentials")
        from tools import spotify_play as sp
        st = sp._player()
        it = st.get("item") or {}
        if it:
            return tool_result(True, {
                "state": "playing" if st.get("is_playing") else "paused",
                "track": it.get("name", ""),
                "artist": ", ".join(a["name"] for a in it.get("artists", [])),
                "device": (st.get("device") or {}).get("name", ""),
                "can": can,
            })
        from tools.spotify_agent import _spotify_running, get_current_track
        if not _spotify_running():
            return tool_result(True, {"state": "closed", "can": can})
        cur = get_current_track() or ""          # "Artist — Track (playing|paused)"
        if " — " in cur:
            artist, rest = cur.split(" — ", 1)
            track, _, state = rest.rpartition(" (")
            return tool_result(True, {"state": state.rstrip(")"), "track": track, "artist": artist,
                                      "device": "this Mac (app)", "can": can})
        return tool_result(True, {"state": "open, nothing loaded", "can": can})
    except Exception as e:
        return tool_result(False, {"state": "unknown", "can": can}, f"{type(e).__name__}: {e}")


def _presence_running() -> bool:
    try:
        return subprocess.run(["pgrep", "-f", "DISENELO Presence"], capture_output=True,
                              timeout=2).returncode == 0
    except Exception:
        return False


def devices_status() -> dict:
    """{success, result: {route, controllable, echo_connected, can}, error} —
    smart-home control eLo can run right now (WO-B3-0011): the shortcuts /
    phrases that are allow-listed AND actually reachable on this Mac, plus
    which route is live (speak-to-Alexa by default; macOS Shortcuts under
    ELO_DEVICE_ROUTE=shortcut) and whether the Echo is in Bluetooth range
    for the speak route."""
    try:
        from tools import device_control as dc
        route = dc._route()
        names = dc.controllable()
        echo_connected = False
        if route == "speak":
            try:
                from tools import echo_speaker as es
                echo_connected = es.device_index() is not None
            except Exception:
                pass
        can = [n.lower() for n in names] or []
        return tool_result(bool(names), {"route": route, "controllable": names,
                                         "echo_connected": echo_connected, "can": can})
    except Exception as e:
        return tool_result(False, {"route": "unknown", "controllable": [], "echo_connected": False,
                                   "can": []}, f"{type(e).__name__}: {e}")


def _b3_live() -> dict:
    out: dict = {}
    sp = spotify_status()
    s = sp["result"] or {}
    out["spotify"] = {
        "status": "ACTIVE" if sp["success"] else "INACTIVE",
        "can": s.get("can", []),
        "live": {k: v for k, v in s.items() if k != "can"},
        "reason": sp["error"],
    }
    serp = bool(os.environ.get("SERPAPI_KEY"))
    out["search"] = {
        "status": "ACTIVE",
        "can": ["look things up on the web when asked", "summaries from Wikipedia"],
        "live": {"provider": "SerpAPI (Google)" if serp else "DuckDuckGo fallback"},
        "reason": None,
    }
    out["research"] = {
        "status": "ACTIVE",
        "can": ["notice what he doesn't know and look it up", "remember what he looked up",
                "say whether a fact is known, retrieved or verified"],
        "live": {"ledger": "data/research/ledger.json"},
        "reason": None,
    }
    alexa = bool(os.environ.get("ALEXA_SKILL_ID"))
    out["alexa_ingress"] = {
        "status": "ACTIVE" if alexa else "INACTIVE",
        "can": ["hear David through an Echo and answer there"] if alexa else [],
        "live": {"port": os.environ.get("ALEXA_PORT", "5051")} if alexa else {},
        "reason": None if alexa else "Alexa skill not set up yet (capabilities/alexa/ALEXA_SETUP.md)",
    }
    pres = _presence_running()
    out["show_brain"] = {
        "status": "ACTIVE" if pres else "INACTIVE",
        "can": ["open his brain / health view on David's screen"] if pres else [],
        "live": {"presence": "running" if pres else "not running"},
        "reason": None if pres else "DISENELO Presence is not open",
    }
    dv = devices_status()
    dr = dv["result"] or {}
    route = dr.get("route") or "speak"
    active = bool(dv["success"]) and (route == "shortcut" or dr.get("echo_connected"))
    reason = None if active else (
        "nothing allow-listed to control" if not dr.get("controllable")
        else "Echo isn't connected over Bluetooth (speak-to-Alexa route)" if route == "speak"
        else None)
    out["devices"] = {
        "name": "Devices",
        "status": "ACTIVE" if active else "INACTIVE",
        "can": dr.get("can", []),
        "live": {"route": route, "echo_connected": dr.get("echo_connected")},
        "reason": dv["error"] or reason,
    }
    return out


# ── the whole picture ─────────────────────────────────────────────────────────

def get_active_capabilities(refresh: bool = False) -> dict:
    """{cap_id: {name, status: ACTIVE|INACTIVE, can, live, reason}} — registry
    entries (health_state ONLINE → ACTIVE; future/offline → INACTIVE) overlaid
    with live probes for the capabilities Builder 3 owns. Cached 5 s."""
    with _lock:
        if not refresh and _cache["data"] is not None and time.time() - _cache["ts"] < _CACHE_S:
            return _cache["data"]
    caps: dict = {}
    try:
        from runtime.capabilities.registry import ALL_CAPABILITIES
        for c in ALL_CAPABILITIES:
            future = bool(getattr(c, "future", False))
            online = str(getattr(c, "health_state", "")).upper() == "ONLINE"
            caps[c.id] = {
                "name": getattr(c, "display_name", c.id),
                "status": "ACTIVE" if online and not future else "INACTIVE",
                "can": list(getattr(c, "verbs", []) or [])[:8],
                "live": {},
                "reason": "not built yet" if future else (None if online else "offline"),
            }
    except Exception as e:
        caps["_registry"] = {"name": "registry", "status": "INACTIVE", "can": [], "live": {},
                             "reason": f"registry unreadable: {e}"}
    # Registered but not implemented here (system_agent can't read or set this
    # Mac's display brightness) — never offered as something he can do.
    if "brightness" in caps:
        caps["brightness"].update(status="INACTIVE", reason="can't reach this Mac's display brightness")
    for cid, info in _b3_live().items():
        base = caps.get(cid, {"name": cid.replace("_", " ").title()})
        caps[cid] = {**base, **info}
    with _lock:
        _cache.update(ts=time.time(), data=caps)
    return caps


_LIVE_FIRST = ("spotify", "search", "research", "devices", "show_brain", "alexa_ingress")


def capabilities_block(max_chars: int = 1600) -> str:
    """Compact anchor text. Live-probed capabilities first, with what they're
    doing now (so a cut can never drop Spotify — that was the bug); the other
    active ones by name; then what he can't do right now and why."""
    caps = get_active_capabilities()
    live, names, off = [], [], []
    for cid in _LIVE_FIRST:
        c = caps.get(cid)
        if not c:
            continue
        if c["status"] != "ACTIVE":
            off.append(f"{c['name']} ({c.get('reason') or 'inactive'})")
            continue
        lv = c.get("live") or {}
        now = ""
        if cid == "spotify" and lv.get("state"):
            now = f" — now {lv['state']}" + (f": {lv['track']} by {lv['artist']}" if lv.get("track") else "")
        elif cid == "devices":
            now = " — via Alexa over the Mac speakers" if lv.get("route") == "speak" else " — via macOS Shortcuts"
        live.append(f"{c['name']}{now} ({', '.join(c.get('can', [])[:7])})")
    for cid, c in sorted(caps.items()):
        if cid in _LIVE_FIRST:
            continue
        if c["status"] == "ACTIVE":
            names.append(c["name"])
        else:
            off.append(f"{c['name']} ({c.get('reason') or 'inactive'})")
    text = ("[WHAT YOU CAN DO — live state, not memory]\n"
            "You CAN: " + "; ".join(live) + "\n"
            "Also: " + ", ".join(names) + "\n"
            "Not right now: " + "; ".join(off) + "\n"
            "Never say you can't do something you CAN.")
    return text if len(text) <= max_chars else text[:max_chars - 1] + "…"


# ── honest no for what isn't built ────────────────────────────────────────────
# Capability demo 2026-10-06: "can you open a scene in Blender and render it" →
# "Shall I…?"; "what does the robot camera see" → an invented description; "can you
# start the heat press" → filler. Registry marks these future (not built).
_NOT_BUILT_NOUNS = {
    "blender": r"\bblender\b", "unity": r"\bunity\b", "substance": r"\bsubstance\b",
    "robot_camera": r"\brobot(?:'s)?\s+camera\b", "robot_motion": r"\brobot\b.{0,30}\b(?:wave|walk|move)\b",
    "robot_runtime": r"\brobot\s+body\b|\byour\s+robot\b|\bphysical\s+(?:elo|body)\b",
    "3d_printer": r"\b3d\s*print", "plotter": r"\bplotter\b", "heat_press": r"\bheat\s*press\b",
    "laser": r"\blaser(?:\s*cutter)?\b", "email": r"\b(?:e-?mails?|inbox)\b",
    "terminal": r"\b(?:terminal|shell\s+command)\b", "camera": r"\b(?:the|your)\s+camera\b",
    "sleep": r"\b(?:put|send)\s+(?:the\s+)?mac\s+to\s+sleep\b|\bsleep\s+the\s+mac\b",
}
_ASK_RE = re.compile(r"\b(?:can|could|will|would)\s+you\b|\bare\s+you\s+able\b|^(?:please\s+)?(?:open|start|run|connect|"
                     r"render|print|check|send|make|take|put|cut|plot|engrave)\b|\bwhat\s+does\b.{0,30}\bsee\b|"
                     r"\bconnect\s+to\b", re.I)
_no_i = -1


def not_built_answer(text: str) -> str | None:
    """'Not yet — …' when the request clearly targets a capability the registry
    marks as not built; None otherwise (built tools and chat untouched)."""
    global _no_i
    t = (text or "").strip()
    if not _ASK_RE.search(t):
        return None
    caps = get_active_capabilities()
    for cid, pat in _NOT_BUILT_NOUNS.items():
        c = caps.get(cid)
        if c and c["status"] != "ACTIVE" and re.search(pat, t, re.I):
            _no_i = (_no_i + 1) % 2
            lead = ("Not yet — " if _no_i == 0 else "Can't do that one yet — ")
            spoken = {"robot_runtime": "my robot body", "robot_motion": "my robot body",
                      "robot_camera": "the robot's camera", "sleep": "sleeping the Mac",
                      "camera": "a camera", "terminal": "the terminal"}.get(cid, c["name"])
            return f"{lead}{spoken[0].upper() + spoken[1:]} isn't connected to me" + (
                f" ({c['reason']})." if c.get("reason") and c["reason"] != "not built yet" else ".")
    return None
