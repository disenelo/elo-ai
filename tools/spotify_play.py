"""
tools/spotify_play.py — B3-SPOTIFY-001: David asks eLo to open / play / list on Spotify.

Source: blender/agent_bus/builder3/FROM_ARCHITECT_2026-10-05_CAPABILITY-PROCESSING.md
David, verbatim (2026-10-05 session):
  "Can you open spotify for me?"
  "Can you start Jitwam Radio Playlist in spotify?"
  "List me a few [playlists] and choose one"
  "Can you play Four Brothers Soundtrack in Spotify"

Gap found 2026-10-06 (read, not assumed): spotify_agent.agent() answers every
"play X" with AppleScript `play` — it resumes whatever was loaded and reports
that track as if it were X. spotify_web's find_playlist / search_track /
play_uri were never called, and play_uri only takes track URIs.

This module resolves the thing David named and starts it on a real device via
the Web API. Every line eLo says reports what actually happened.
"""
from __future__ import annotations

import random
import re
import subprocess
import time

from tools import spotify_web as sw

# ── request parsing ───────────────────────────────────────────────────────────

_SPOTIFY_RE = re.compile(r"\bspotify\b", re.I)
_OPEN_RE = re.compile(r"\b(?:open|launch|start\s+up|fire\s+up)\s+(?:up\s+)?spotify\b", re.I)
_LIST_RE = re.compile(
    r"\b(?:list|show|tell|name|what(?:'s|\s+are)?)\b.{0,30}\bplaylists?\b"
    r"|\bplaylists?\s+(?:do\s+)?i\s+have\b"
    r"|\blist\s+(?:me\s+)?(?:a\s+few|some)\b",
    re.I,
)
_CHOOSE_RE = re.compile(r"\b(?:choose|pick|select)\s+(?:one|something|a\s+playlist)\b", re.I)
_PLAY_RE = re.compile(
    r"\b(?:play|start|put\s+on|shuffle|queue\s+up)\s+(?:me\s+)?(?:the\s+|my\s+|some\s+)?(.+)$", re.I
)
# What David says around the name — stripped to leave the name.
_TAIL_RE = re.compile(r"\s+(?:in|on|from|with|through)\s+(?:the\s+)?spotify\b.*$|\s+(?:for\s+me|please)\b.*$", re.I)
_HEAD_RE = re.compile(r"^(?:can|could|will|would)\s+you\s+(?:please\s+)?", re.I)
# Bare controls stay with the existing spotify_agent path.
_GENERIC = re.compile(
    r"^(?:it|that|this|music|some\s+music|something|anything|a\s+song|the\s+music|again|next|previous)$", re.I
)


# When the last Spotify turn was this recent, "list me a few and choose one"
# needs no "playlist" / "Spotify" — the conversation already says it.
_CONTEXT_WINDOW_S = 180.0
_last_spotify_ts = 0.0


def parse(text: str) -> tuple[str, str] | None:
    """("open"|"list"|"play", target) for a Spotify request, else None.
    Only claims a turn when it names Spotify or a playlist (or follows a
    Spotify turn), so "play" alone and game/music chatter keep their routes."""
    t = (text or "").strip()
    low = t.lower()
    in_context = time.time() - _last_spotify_ts < _CONTEXT_WINDOW_S
    if not (_SPOTIFY_RE.search(t) or re.search(r"\bplaylists?\b", low) or in_context):
        return None
    if not (_SPOTIFY_RE.search(t) or re.search(r"\bplaylists?\b", low)):
        # Context only: just the list / choose follow-ups.
        if _LIST_RE.search(t) or _CHOOSE_RE.search(t):
            return ("list", "choose" if _CHOOSE_RE.search(t) else "")
        return None
    if _LIST_RE.search(t) or (_CHOOSE_RE.search(t) and "playlist" in low):
        return ("list", "choose" if _CHOOSE_RE.search(t) else "")
    body = _HEAD_RE.sub("", t).rstrip("?.! ")
    m = _PLAY_RE.search(body)
    if m:
        target = _TAIL_RE.sub("", m.group(1)).strip(" ,.'\"")
        target = re.sub(r"\s+playlist$", "", target, flags=re.I).strip()
        if target and not _GENERIC.match(target) and target.lower() != "spotify":
            return ("play", target)
    if _OPEN_RE.search(t):
        return ("open", "")
    return None


# ── device ────────────────────────────────────────────────────────────────────

def _devices() -> list[dict]:
    r = sw._get(f"{sw._API}/me/player/devices", headers=sw._h(), timeout=8.0)
    r.raise_for_status()
    return r.json().get("devices", [])


def _ensure_app() -> None:
    subprocess.run(["open", "-a", "Spotify"], capture_output=True, timeout=5)


def _device_id() -> str | None:
    """The active device, else this Mac. Opens Spotify and waits for it to
    register when no computer is listed."""
    for attempt in range(6):
        devs = _devices()
        for d in devs:
            if d.get("is_active"):
                return d["id"]
        for d in devs:
            if d.get("type", "").lower() == "computer":
                return d["id"]
        if attempt == 0:
            _ensure_app()
        time.sleep(1.5)
    return None


_last_started = ""


def _start(device_id: str, *, context_uri: str = "", uris: list[str] | None = None) -> None:
    global _last_started
    _last_started = context_uri or (uris or [""])[0]
    body = {"context_uri": context_uri} if context_uri else {"uris": uris or []}
    r = sw._put(f"{sw._API}/me/player/play", headers=sw._h(),
                params={"device_id": device_id}, json=body, timeout=8.0)
    if r.status_code not in (200, 202, 204):
        raise ValueError(f"Spotify refused playback ({r.status_code}): {r.text[:160]}")


# ── resolution ────────────────────────────────────────────────────────────────

def _all_playlists() -> list[dict]:
    url, params, out = f"{sw._API}/me/playlists", {"limit": 50}, []
    while url:
        r = sw._get(url, headers=sw._h(), params=params, timeout=8.0)
        r.raise_for_status()
        d = r.json()
        out += [{"name": p["name"], "uri": p["uri"]} for p in d.get("items", []) if p]
        url, params = d.get("next"), None
    return out


def _words(s: str) -> list[str]:
    return [w for w in re.findall(r"[a-z0-9]+", s.lower()) if w not in {"the", "a", "my", "playlist"}]


def _own_playlist(name: str, mine: list[dict]) -> dict | None:
    nl = name.lower().strip()
    for p in mine:
        if p["name"].lower().strip() == nl:
            return p
    want = set(_words(name))
    for p in mine:
        if want and want <= set(_words(p["name"])):
            return p
    return None


def _search(q: str, kind: str, limit: int = 5) -> list[dict]:
    r = sw._get(f"{sw._API}/search", headers=sw._h(),
                params={"q": q, "type": kind, "limit": limit}, timeout=8.0)
    r.raise_for_status()
    return [x for x in (r.json().get(kind + "s", {}).get("items") or []) if x]


def _catalogue_playlist(name: str) -> dict | None:
    want = set(_words(name))
    for p in _search(name, "playlist"):
        if want and want <= set(_words(p["name"])):
            return {"name": p["name"], "uri": p["uri"]}
    return None


def _artist(name: str) -> dict | None:
    bare = re.sub(r"\s+radio$", "", name, flags=re.I).strip().lower()
    for a in _search(bare, "artist"):
        if a["name"].lower() == bare:
            return {"name": a["name"], "uri": a["uri"]}
    return None


def _track(name: str) -> dict | None:
    items = _search(name, "track", limit=1)
    if not items:
        return None
    t = items[0]
    return {"name": t["name"], "artist": t["artists"][0]["name"], "uri": t["uri"]}


# ── actions ───────────────────────────────────────────────────────────────────

def open_app() -> str:
    _ensure_app()
    return "Opening Spotify."


def play(target: str) -> str:
    dev = _device_id()
    if not dev:
        return "Spotify isn't showing up as a device yet — give it a second and ask again."
    mine = _all_playlists()
    p = _own_playlist(target, mine)
    if p:
        _start(dev, context_uri=p["uri"])
        return f"Playing your {p['name']} playlist."
    p = _catalogue_playlist(target)
    if p:
        _start(dev, context_uri=p["uri"])
        return f"Playing {p['name']}."
    a = _artist(target)
    if a:
        _start(dev, context_uri=a["uri"])
        if a["name"].lower() != target.lower():
            return f"There's no {target} playlist I can reach — playing {a['name']} instead."
        return f"Playing {a['name']}."
    t = _track(target)
    if t:
        _start(dev, uris=[t["uri"]])
        return f"Playing {t['name']} by {t['artist']}."
    return f"Couldn't find {target} on Spotify."


def list_playlists(choose: bool) -> str:
    mine = _all_playlists()
    if not mine:
        return "You don't have any playlists I can see."
    few = mine[:5]
    names = ", ".join(p["name"] for p in few[:-1]) + f" and {few[-1]['name']}" if len(few) > 1 else few[0]["name"]
    if not choose:
        return f"A few of yours: {names}. Want one on?"
    pick = random.choice(few)
    dev = _device_id()
    if not dev:
        return f"A few of yours: {names}. I'd go {pick['name']} — but Spotify isn't showing up as a device yet."
    _start(dev, context_uri=pick["uri"])
    return f"A few of yours: {names}. Going with {pick['name']}."


# ── playback controls ─────────────────────────────────────────────────────────
# Live 2026-10-06 David: "Can you pause Spotify" → eLo: "I can't control Spotify
# directly". Controls now act through the Web API and eLo reports the player
# state Spotify gives back — never a claim the player doesn't confirm.

_MUSIC_WORDS = r"(?:spotify|music|song|track|tune|playlist|playing|playback|it|that|this)"
_CONTROL_RES = [
    # A request, not a mention: imperative at the start, or "can you stop/pause"
    # with the music named ("I can't stop thinking about that song" is not one).
    ("pause", re.compile(
        r"^(?:please\s+)?(?:pause|stop|kill|turn\s+off|shut\s+off|mute)\b.{0,30}\b" + _MUSIC_WORDS + r"\b"
        r"|\b(?:can|could|will|would)\s+you\s+(?:please\s+)?(?:pause|stop|turn\s+off|mute)\b"
        r"(?=.*\b(?:spotify|music|song|track|playing|playback)\b)"
        r"|(?=.*\b(?:spotify|music|song|track|playing|playback)\b).*\b(?:can|could|will|would)\s+you\s+(?:please\s+)?(?:pause|stop)\b"
        r"|\bstop\s+playing\b|\bpause\s+(?:spotify|the\s+music|music)\b"
        r"|^(?:pause|stop|stop\s+it|pause\s+it)$", re.I)),
    ("resume", re.compile(
        r"\b(?:resume|unpause|un-pause|carry\s+on\s+playing|keep\s+playing)\b"
        r"|\bplay\s+(?:it|the\s+music|music|spotify)\s+again\b"
        r"|\b(?:start|turn)\s+(?:the\s+)?(?:music|spotify)\s+(?:back\s+)?(?:on|up|again)\b", re.I)),
    ("next", re.compile(r"\b(?:skip|next)\s+(?:this\s+|the\s+)?(?:song|track|one|tune)\b|^(?:skip|next)(?:\s+it)?$", re.I)),
    ("previous", re.compile(
        r"\b(?:previous|last)\s+(?:song|track|one)\b|\bgo\s+back\s+a\s+(?:song|track)\b"
        r"|\bplay\s+(?:the\s+)?(?:previous|last)\s+(?:song|track|one)\b", re.I)),
]


def control_for(text: str) -> str | None:
    t = re.sub(r"[?!.]+$", "", (text or "").strip().lower())
    t = _HEAD_RE.sub("", t)
    for name, rx in _CONTROL_RES:
        if rx.search(t):
            return name
    return None


def _player() -> dict:
    r = sw._get(f"{sw._API}/me/player", headers=sw._h(), timeout=8.0)
    if r.status_code == 204:
        return {}
    r.raise_for_status()
    return r.json() or {}


def _now(state: dict) -> str:
    it = state.get("item") or {}
    if not it:
        return ""
    who = ", ".join(a["name"] for a in it.get("artists", []))
    return f"{it.get('name', '')} by {who}" if who else it.get("name", "")


def _control_app(action: str) -> str:
    """No Web API device but the app is open — drive the app itself, then
    report what its own player state says."""
    from tools import spotify_agent as sa
    before = _status()
    if action == "pause" and not before.startswith("playing"):
        return "Spotify isn't playing anything — nothing to pause."
    if action == "resume" and before.startswith("playing"):
        return f"It's already {before}."
    sa.control({"resume": "play"}.get(action, action))
    time.sleep(1.0)
    after = _status()
    if action == "pause":
        return "Paused." if not after.startswith("playing") else "I tried to pause it, but Spotify's still playing."
    if action == "resume":
        return f"Back on — {after[len('playing '):]}." if after.startswith("playing") \
            else "I tried to resume it, but Spotify's still paused."
    return f"Done — Spotify's {after} now." if after != before else "Spotify didn't move to another track."


def control(action: str) -> str:
    before = _player()
    if not before:
        from tools.spotify_agent import _spotify_running
        if _spotify_running():
            return _control_app(action)
    playing = bool(before.get("is_playing"))
    if action == "pause":
        if not before or not playing:
            return "Spotify isn't playing anything — nothing to pause."
        sw.pause()
    elif action == "resume":
        if playing:
            return f"It's already playing — {_now(before)}." if _now(before) else "It's already playing."
        if not before:
            return "There's nothing loaded in Spotify to resume."
        sw.resume()
    elif action == "next":
        if not before:
            return "Spotify isn't playing anything to skip."
        sw.skip()
    elif action == "previous":
        if not before:
            return "Spotify isn't playing anything to go back on."
        sw.previous()
    time.sleep(1.0)
    after = _player()
    now = _now(after)
    if action == "pause":
        return "Paused." if not after.get("is_playing") else "I tried to pause it, but Spotify's still playing."
    if action == "resume":
        return (f"Back on — {now}." if now else "Back on.") if after.get("is_playing") \
            else "I tried to resume it, but Spotify's still paused."
    if now and now != _now(before):
        return f"Skipped — now {now}." if action == "next" else f"Went back — {now}."
    return "Spotify didn't move to another track."


# ── awareness ─────────────────────────────────────────────────────────────────
# A Spotify mention that isn't a command still reaches the LLM, whose prompt
# lists no capabilities — so it guessed "I can't control Spotify". Handed this
# fact (prefix recognised by backend_router's missing-fact exception).

_MENTION_RE = re.compile(r"\b(?:spotify|playlists?|the\s+music|music\s+playing|what'?s\s+playing|song|track)\b", re.I)


def _status() -> str:
    """What Spotify is doing, in words. Web API first; when it has no device,
    the app itself (AppleScript) — live 2026-10-06 the API had no device while
    the app sat paused on a track."""
    try:
        st = _player()
        now = _now(st)
        if now:
            return f"playing {now}" if st.get("is_playing") else f"paused on {now}"
    except Exception:
        pass
    try:
        from tools.spotify_agent import get_current_track, _spotify_running
        if not _spotify_running():
            return "not open"
        cur = get_current_track()  # "Artist — Track (playing|paused)"
        if cur:
            m = re.match(r"(.+?) — (.+) \((playing|paused)\)$", cur)
            if m:
                verb = "playing" if m.group(3) == "playing" else "paused on"
                return f"{verb} {m.group(2)} by {m.group(1)}"
            return cur
        return "open, nothing loaded"
    except Exception:
        return "status unavailable"


def awareness_context(text: str) -> str | None:
    if not _MENTION_RE.search(text or ""):
        return None
    return ("[CAPABILITY_RESULT: Spotify — eLo controls Spotify on David's Mac himself: "
            "launch the app, start any playlist / artist / track by name, list David's playlists, "
            f"pause, resume, skip, go back. Right now Spotify is {_status()}. "
            "Never say you can't control Spotify — if David says you can, he is right.]")


# Asked, or told, whether he can control Spotify. Answered here: live
# 2026-10-06 the LLM, given the fact above as the first line of the message,
# still said "I don't have that recorded".
_ABILITY_RE = re.compile(
    r"\b(?:can\s+you|could\s+you|you\s+can|you\s+could|are\s+you\s+able|you(?:'re|\s+are)\s+able|"
    r"do\s+you\s+know\s+how\s+to|able\s+to)\b"
    r".{0,40}\b(?:control|use|run|operate|work|access|handle|play|pause|skip|manage)\b", re.I)


# Rotated: elo_response_gate blanks a reply identical to the previous one
# (live 2026-10-06 the second "can you control spotify?" came back "").
_ABILITY_LINES = [
    "Yeah, I can — I open it, play any playlist, artist or track you name, list your playlists, pause, skip and go back.",
    "I can, yeah — open it, start whatever playlist, artist or track you name, list your playlists, pause, skip, go back.",
    "Yep, that's mine to run — opening it, playing what you name, listing your playlists, pausing, skipping, going back.",
]
_ability_i = -1


def capability_answer(text: str) -> str | None:
    global _ability_i
    if not (_SPOTIFY_RE.search(text or "") and _ABILITY_RE.search(text or "")):
        return None
    _ability_i = (_ability_i + 1) % len(_ABILITY_LINES)
    return f"{_ABILITY_LINES[_ability_i]} Right now Spotify's {_status()}."


def _handle_line(text: str) -> tuple[str, str, str] | None:
    """(kind, detail, eLo's line) for a Spotify request, after doing it.
    kind: control | open | list | choose | play | ability. None when not one."""
    global _last_spotify_ts
    act = control_for(text)
    if act:
        _last_spotify_ts = time.time()
        try:
            return ("control", act, control(act))
        except Exception as e:
            return ("control", act, f"I couldn't {act} Spotify — it gave me an error.", f"{type(e).__name__}: {e}")
    req = parse(text)
    if not req:
        ans = capability_answer(text)
        if ans:
            _last_spotify_ts = time.time()
            return ("ability", "", ans)
        return None
    _last_spotify_ts = time.time()
    kind, target = req
    try:
        if kind == "open":
            return ("open", "", open_app())
        if kind == "list":
            return ("choose" if target == "choose" else "list", "", list_playlists(choose=(target == "choose")))
        return ("play", target, play(target))
    except Exception as e:
        return (kind, target, "Spotify didn't take that — something went wrong on its side.",
                f"{type(e).__name__}: {e}")


# Control lines that mean Spotify confirmed the change (control() only says
# these after reading the player state back).
_CONFIRMED = ("Paused.", "Back on", "Skipped —", "Went back —", "Done — Spotify's")


def _verify_started() -> tuple[bool, str | None]:
    """Did what we just started actually start? Read the player back."""
    for _ in range(4):
        time.sleep(0.75)
        try:
            st = _player()
        except Exception as e:
            return False, f"player unreadable: {e}"
        uri = ((st.get("context") or {}).get("uri") or (st.get("item") or {}).get("uri") or "")
        if st.get("is_playing") and _last_started and (uri == _last_started
                                                       or _last_started.startswith("spotify:artist:")):
            return True, None
    return False, f"Spotify isn't playing {_last_started or 'it'} after the request"


def execute(text: str) -> dict | None:
    """{success, result: {kind, detail, line, state}, error} for a Spotify
    request — success from what Spotify reports afterwards, never from having
    sent a command. Recorded for the execution-confirmation gate. None when
    the text isn't a Spotify request."""
    from tools.capability_status import tool_result, record_result
    got = _handle_line(text)
    if not got:
        return None
    kind, detail, line = got[0], got[1], got[2]
    error = got[3] if len(got) > 3 else None
    if error:
        ok = False
    elif kind == "control":
        ok = line.startswith(_CONFIRMED)
        error = None if ok else line
    elif kind in ("play", "choose") and not error:
        if line.startswith(("Couldn't find", "Spotify isn't showing up", "You don't have")) \
                or "isn't showing up" in line:
            ok, error = False, line
        else:
            ok, error = _verify_started()
            if not ok:
                # Never claim playback Spotify doesn't show (Board Bug 3: execute or say why).
                line = (f"I asked Spotify to play {detail or 'that'}, but it isn't playing — "
                        "might need a tap on the Spotify app.")
    elif kind == "open":
        from tools.spotify_agent import _spotify_running
        time.sleep(1.0)
        ok = _spotify_running()
        error = None if ok else "Spotify app didn't open"
    elif kind == "list":
        ok = not line.startswith("You don't have")
        error = None if ok else line
    else:  # ability — an answer about himself, true by construction
        ok = True
    try:
        state = _status()
    except Exception:
        state = "unknown"
    return record_result("spotify", tool_result(ok, {"kind": kind, "detail": detail, "line": line,
                                                     "state": state}, error))


def handle(text: str) -> str | None:
    """eLo's line for a Spotify request, after doing it. None when not one."""
    r = execute(text)
    return r["result"]["line"] if r else None
