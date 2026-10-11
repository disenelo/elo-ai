"""
tools/device_control.py — WO-B3-0011 Company Control, v1: eLo runs David's
device Shortcuts.

Anything David can control from the Home app (lights, plugs, speakers, Hue,
HomeKit…) can be a macOS Shortcut; eLo runs it locally with `shortcuts run`.
No cloud, no brand-specific API. The existing Hue agent (capabilities/
lights_agent.py) has no bridge configured, so it never ran a light.

Only shortcuts on the allow-list can be run by eLo (data/device_shortcuts.json,
default: the device shortcuts found on this Mac 2026-10-10). A sentence can
never trigger an unrelated shortcut ("Download file").

    match(text)        -> command name or None
    run(name)          -> {success, result: {shortcut, line}, error}
    controllable()     -> commands eLo can run now

v2 (David 2026-10-10: the lights are "controlled via Alexa"): a command can go
to an Alexa Routine through Voice Monkey (voicemonkey.io: free Alexa skill +
HTTP API, https://voicemonkey.io/docs/api/trigger). Set VOICE_MONKEY_TOKEN in
.env and create Voice Monkey "Routine Trigger" devices with the IDs in
_ALEXA_DEVICES (or data/alexa_devices.json); each starts an Alexa Routine
("turn off the lights"…). When Voice Monkey isn't set up, the macOS Shortcut
is used as before.  [PARKED by David 2026-10-10: "I don't want more APIs for no
reason." Dormant without VOICE_MONKEY_TOKEN.]

v3, DEFAULT (David 2026-10-10: "I need eLo to talk to Alexa, then Alexa turns the
lights off"): eLo SAYS it out loud through the Mac speakers ("Alexa … turn off
the lights") and the Echo hears it, like David asking. No account, no API, no
cost. Always the Mac speakers: an Echo ignores its own wake word from its own
speaker, so this never goes to the Echo even when eLo's voice is set to it.
Phrases: data/alexa_phrases.json overrides _SPOKEN. ELO_DEVICE_ROUTE=shortcut
uses the macOS Shortcuts instead.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ALLOW_FILE = os.path.join(_ROOT, "data", "device_shortcuts.json")
_DEFAULT_ALLOW = ["Lights On", "Lights Out", "Design Mode", "Living Room Sounds"]

# Command → Voice Monkey Routine Trigger device ID (David creates devices with these IDs).
_ALEXA_FILE = os.path.join(_ROOT, "data", "alexa_devices.json")
_ALEXA_DEVICES = {"Lights On": "elo-lights-on", "Lights Out": "elo-lights-off",
                  "Design Mode": "elo-design-mode", "Living Room Sounds": "elo-living-room-sounds"}
_VM_URL = "https://api-v3.voicemonkey.io/trigger"

# What eLo says to Alexa for each command (after "Alexa").
_PHRASE_FILE = os.path.join(_ROOT, "data", "alexa_phrases.json")
_SPOKEN = {"Lights On": "turn on the lights", "Lights Out": "turn off the lights",
           "Design Mode": "design mode", "Living Room Sounds": "living room sounds"}
_MAC_SPEAKERS = os.environ.get("ELO_MAC_SPEAKERS", "Mac Studio Speakers")

# Spoken forms → the shortcut they mean (lower-case, after normalising).
_ALIASES = {
    "lights on": ("turn on the lights", "turn the lights on", "lights on", "switch the lights on",
                  "switch on the lights", "put the lights on"),
    "lights out": ("turn off the lights", "turn the lights off", "lights off", "lights out",
                   "switch the lights off", "switch off the lights", "kill the lights"),
    "design mode": ("design mode",),
    "living room sounds": ("living room sounds",),
}
_ACT = re.compile(r"\b(?:turn|switch|put|kill|run|start|do|set|activate|trigger|lights?|mode|sounds?)\b")

_QUESTION_WORDS = {"what", "which", "why", "how", "when", "did", "is", "are", "were", "was", "does"}

_cache = {"ts": 0.0, "names": []}


def _all_shortcuts() -> list[str]:
    if time.time() - _cache["ts"] < 60 and _cache["names"]:
        return _cache["names"]
    try:
        out = subprocess.run(["shortcuts", "list"], capture_output=True, text=True, timeout=10).stdout
        names = [l.strip() for l in out.splitlines() if l.strip()]
    except Exception:
        names = []
    _cache.update(ts=time.time(), names=names)
    return names


def allow_list() -> list[str]:
    try:
        with open(_ALLOW_FILE, encoding="utf-8") as f:
            names = json.load(f).get("shortcuts")
        if isinstance(names, list) and names:
            return [str(n) for n in names]
    except Exception:
        pass
    return list(_DEFAULT_ALLOW)


def alexa_devices() -> dict[str, str]:
    """Command → Voice Monkey device ID, only when VOICE_MONKEY_TOKEN is set."""
    if not os.environ.get("VOICE_MONKEY_TOKEN"):
        return {}
    try:
        with open(_ALEXA_FILE, encoding="utf-8") as f:
            m = json.load(f)
        if isinstance(m, dict) and m:
            return {str(k): str(v) for k, v in m.items()}
    except Exception:
        pass
    return dict(_ALEXA_DEVICES)


def _route() -> str:
    return "shortcut" if os.environ.get("ELO_DEVICE_ROUTE", "speak").lower() == "shortcut" else "speak"


def phrases() -> dict[str, str]:
    try:
        with open(_PHRASE_FILE, encoding="utf-8") as f:
            m = json.load(f)
        if isinstance(m, dict) and m:
            return {str(k): str(v) for k, v in m.items()}
    except Exception:
        pass
    return dict(_SPOKEN)


def controllable() -> list[str]:
    if _route() == "speak":
        said = {k.lower(): k for k in phrases()}
        return [said[a.lower()] for a in allow_list() if a.lower() in said]
    have = {n.lower(): n for n in _all_shortcuts()}
    out = [have[a.lower()] for a in allow_list() if a.lower() in have]
    for cmd in alexa_devices():
        if cmd.lower() not in {o.lower() for o in out}:
            out.append(cmd)
    return out


def _norm(text: str) -> str:
    t = re.sub(r"[^\w\s']", " ", (text or "").lower())
    t = re.sub(r"\b(?:please|elo|can you|could you|would you|for me|now|the shortcut|shortcut)\b", " ", t)
    return " ".join(t.split())


def match(text: str) -> str | None:
    """The allow-listed shortcut this sentence asks eLo to run, else None."""
    t = _norm(text)
    first = t.split()[0].split("'")[0] if t else ""          # "what's" → "what"
    if not t or not _ACT.search(t) or first in _QUESTION_WORDS:  # "are the lights on?" isn't a command
        return None
    names = controllable()
    by_lower = {n.lower(): n for n in names}
    for key, phrases in _ALIASES.items():
        if key in by_lower and any(p in t for p in phrases):
            return by_lower[key]
    for n in sorted(names, key=len, reverse=True):          # "run Design Mode", "do living room sounds"
        if n.lower() in t:
            return n
    return None


def _run_alexa(name: str, device: str) -> dict:
    """Start the Alexa Routine behind this command (Voice Monkey trigger device)."""
    from tools.capability_status import tool_result, record_result
    import urllib.parse
    import urllib.request
    q = urllib.parse.urlencode({"token": os.environ["VOICE_MONKEY_TOKEN"], "device": device})
    try:
        with urllib.request.urlopen(f"{_VM_URL}?{q}", timeout=10) as r:
            body = r.read().decode("utf-8", "replace")
            ok = r.status == 200 and '"success":false' not in body.replace(" ", "").lower()
    except Exception as e:
        return record_result("devices", tool_result(False, {"shortcut": name,
                             "line": f"Alexa didn't take “{name}” — {type(e).__name__}."}, str(e)[:200]))
    if not ok:
        return record_result("devices", tool_result(False, {"shortcut": name,
                             "line": f"Alexa didn't take “{name}”."}, body[:200]))
    # Alexa accepted the trigger; eLo can't see the lights, so he says what he did.
    return record_result("devices", tool_result(True, {"shortcut": name, "via": "alexa",
                         "line": f"Asked Alexa: {name.lower()}."}))


def _mac_index() -> int | None:
    """CoreAudio index of the Mac's own speakers (ffmpeg AudioToolbox)."""
    try:
        err = subprocess.run(["ffmpeg", "-hide_banner", "-f", "lavfi", "-i", "anullsrc", "-t", "0.01",
                              "-f", "audiotoolbox", "-list_devices", "true", "-"],
                             capture_output=True, text=True, timeout=8).stderr
    except Exception:
        return None
    for line in err.splitlines():
        m = re.search(r"\[(\d+)\]\s+(.+?),\s", line)
        if m and m.group(2).strip() == _MAC_SPEAKERS:
            return int(m.group(1))
    return None


def _say_on_mac(text: str) -> bool:
    """Say text out loud on the Mac speakers only, in eLo's voice (ElevenLabs) when
    available, else macOS `say`. Blocks until finished."""
    import tempfile
    idx = _mac_index()
    audio = None
    try:
        from voice.voice_engine import _fetch_elevenlabs_audio
        audio = _fetch_elevenlabs_audio(text)
    except Exception:
        audio = None
    if audio:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            f.write(audio)
            path = f.name
        try:
            cmd = (["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", path, "-f", "audiotoolbox",
                    "-audio_device_index", str(idx), "-"] if idx is not None else ["afplay", path])
            return subprocess.run(cmd, capture_output=True, timeout=30).returncode == 0
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass
    cmd = ["say"] + (["-a", _MAC_SPEAKERS] if idx is not None else []) + [text]
    return subprocess.run(cmd, capture_output=True, timeout=30).returncode == 0


def _run_speak(name: str) -> dict:
    """eLo asks Alexa out loud: 'Alexa' … pause … '<command>'."""
    from tools.capability_status import tool_result, record_result
    phrase = phrases().get(name) or {k.lower(): v for k, v in phrases().items()}.get(name.lower(), name.lower())
    try:
        ok = _say_on_mac("Alexa.")
        time.sleep(0.8)                      # let the Echo wake before the command
        ok = _say_on_mac(phrase) and ok
    except Exception as e:
        return record_result("devices", tool_result(False, {"shortcut": name,
                             "line": f"I couldn't say it to Alexa — {type(e).__name__}."}, str(e)[:200]))
    if not ok:
        return record_result("devices", tool_result(False, {"shortcut": name,
                             "line": "I couldn't play that out loud for Alexa."}, "playback failed"))
    # eLo can't hear whether Alexa understood; he says what he did.
    return record_result("devices", tool_result(True, {"shortcut": name, "via": "spoken",
                         "line": f"Asked Alexa: “{phrase}”."}))


# ── awareness ─────────────────────────────────────────────────────────────────
# Live 2026-10-11: "can you control the lights?" and "do you control the lights?"
# got None from match() — the LLM then guesses, often denying a capability eLo has.
# Pattern mirrors tools/spotify_play.capability_answer / awareness_context.

_DEV_MENTION_RE = re.compile(r"\b(?:lights?|lamp|lamps|alexa|smart\s*(?:home|plug|socket)|"
                             r"living\s+room\s+sounds?|design\s+mode|shortcuts?)\b", re.I)
_DEV_ABILITY_RE = re.compile(
    r"\b(?:can\s+you|could\s+you|you\s+can|you\s+could|are\s+you\s+able|you(?:'re|\s+are)\s+able|"
    r"do\s+you(?:\s+know\s+how\s+to)?|able\s+to)\b"
    r".{0,40}\b(?:control|run|operate|work|handle|use|turn|switch|put|dim|kill|flip)\b"
    r"|\bwhat\s+(?:lights|devices|shortcuts|smart[^?.]{0,20})\s+(?:can|do)\s+you\b", re.I)

_ABILITY_LINES = (
    "Yeah, I can — {where}: {names}.",
    "I can, yeah — {where}: {names}.",
    "Yep, that's mine to run {where}: {names}.",
)
_ability_i = -1


def _where() -> str:
    return "by asking Alexa out loud through the Mac speakers" if _route() == "speak" \
        else "through macOS Shortcuts"


def _names_phrase(names: list[str]) -> str:
    if not names:
        return "nothing allow-listed yet"
    low = [n.lower() for n in names]
    if len(low) == 1:
        return low[0]
    return ", ".join(low[:-1]) + f" and {low[-1]}"


def capability_answer(text: str) -> str | None:
    """eLo's own answer when David asks whether he can control the lights /
    devices, so the LLM never gets a chance to deny it. None when the text
    is not an ability question about devices."""
    global _ability_i
    t = text or ""
    if not (_DEV_MENTION_RE.search(t) and _DEV_ABILITY_RE.search(t)):
        return None
    names = controllable()
    _ability_i = (_ability_i + 1) % len(_ABILITY_LINES)
    line = _ABILITY_LINES[_ability_i].format(where=_where(), names=_names_phrase(names))
    if _route() == "speak":
        try:
            from tools import echo_speaker as es
            if es.device_index() is None:
                line += " Echo isn't on Bluetooth right now, so Alexa won't hear me — flip it on and ask again."
        except Exception:
            pass
    return line


def awareness_context(text: str) -> str | None:
    """[CAPABILITY_RESULT: Devices — …] fact for the prompt when devices are
    mentioned but it isn't a direct run request (match() handles those).
    Keeps parity with spotify_play.awareness_context so Builder 1's missing-fact
    exception can carry it through to Executive without LLM paraphrase."""
    t = text or ""
    if not _DEV_MENTION_RE.search(t) or match(t):
        return None
    names = controllable()
    route = _route()
    where = ("via Mac-speakers → Alexa (" + ("Echo connected" if (
        _ability_i_echo_connected()) else "Echo offline, nothing will reach Alexa") + ")"
             if route == "speak" else "via macOS Shortcuts")
    return ("[CAPABILITY_RESULT: Devices — eLo controls David's smart home "
            f"{where}. Allow-listed right now: {', '.join(names) or 'none'}. "
            "Never say you can't control a device that is in that list.]")


def _ability_i_echo_connected() -> bool:
    try:
        from tools import echo_speaker as es
        return es.device_index() is not None
    except Exception:
        return False


def run(name: str) -> dict:
    from tools.capability_status import tool_result, record_result
    if name not in controllable():
        return record_result("devices", tool_result(False, {"line": f"“{name}” isn't one I'm allowed to run."},
                                                    "not allow-listed"))
    alexa = {k.lower(): v for k, v in alexa_devices().items()}
    if name.lower() in alexa:
        return _run_alexa(name, alexa[name.lower()])
    if _route() == "speak":
        return _run_speak(name)
    try:
        r = subprocess.run(["shortcuts", "run", name], capture_output=True, text=True, timeout=45)
    except subprocess.TimeoutExpired:
        return record_result("devices", tool_result(False, {"shortcut": name,
                             "line": f"Your “{name}” shortcut didn't finish in time."}, "timeout"))
    if r.returncode != 0:
        err = (r.stderr or r.stdout or f"exit {r.returncode}").strip()[:200]
        return record_result("devices", tool_result(False, {"shortcut": name,
                             "line": f"Your “{name}” shortcut didn't run — {err}."}, err))
    # The shortcut ran; eLo can't see the lights, so he says what he did, not what happened.
    return record_result("devices", tool_result(True, {"shortcut": name, "line": f"Ran your “{name}” shortcut."}))
