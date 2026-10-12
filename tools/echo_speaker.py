"""
tools/echo_speaker.py — the Echo Dot-Studio as eLo's mouth over Bluetooth.

David, 2026-10-08: "Alexa should be an embodiment for eLo … he can speak through
my speaker or connect to my speaker via Bluetooth (Echo Dot-Studio)."

The Echo is paired with this Mac as a Bluetooth speaker. When it is connected,
eLo's own voice (the ElevenLabs audio voice/voice_engine.py already makes) can
be played straight to it with ffmpeg's AudioToolbox output — only eLo's voice;
the Mac's other sound stays where it is. No Alexa cloud, no 8-second limit.

  status()      → {"paired", "connected", "device_index"}
  connect()     → connect over Bluetooth (blueutil), True when it shows as an output
  disconnect()
  play(path)    → play an audio file on the Echo; False when not connected / failed
  voice_output()/set_voice_output("mac"|"echo") → David's setting (Presence settings UI)
  want_for(s)   → eLo speaks through the Echo for the next s seconds
  speaking()    → True when (setting is echo OR wanted) AND connected (voice_engine routes to it)

The Echo's name/address come from ECHO_SPEAKER_NAME (default "Echo Dot-Studio")
and ECHO_SPEAKER_ADDRESS (looked up from the paired list when unset).
"""
from __future__ import annotations

import os
import re
import subprocess
import time

_NAME = os.environ.get("ECHO_SPEAKER_NAME", "Echo Dot-Studio")
_DEV_RE = re.compile(r"\[(\d+)\]\s+(.+?),\s")


def _run(cmd: list, timeout: float = 10) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def _address() -> str | None:
    addr = os.environ.get("ECHO_SPEAKER_ADDRESS")
    if addr:
        return addr
    try:
        out = _run(["blueutil", "--paired", "--format", "json"]).stdout
        import json
        for d in json.loads(out or "[]"):
            if (d.get("name") or "").strip() == _NAME:
                return d.get("address")
    except Exception:
        pass
    return None


_idx_cache: dict = {"ts": 0.0, "idx": None}
_IDX_TTL_S = 10.0


def device_index(fresh: bool = False) -> int | None:
    """CoreAudio output index of the Echo (ffmpeg AudioToolbox), None when it isn't an output.
    Cached 10 s — voice_engine asks on every line it speaks."""
    if not fresh and time.time() - _idx_cache["ts"] < _IDX_TTL_S:
        return _idx_cache["idx"]
    _idx_cache.update(ts=time.time(), idx=_list_index())
    return _idx_cache["idx"]


def _list_index() -> int | None:
    try:
        err = _run(["ffmpeg", "-hide_banner", "-f", "lavfi", "-i", "anullsrc", "-t", "0.01",
                    "-f", "audiotoolbox", "-list_devices", "true", "-"], timeout=8).stderr
    except Exception:
        return None
    for line in err.splitlines():
        m = _DEV_RE.search(line)
        if m and m.group(2).strip() == _NAME:
            return int(m.group(1))
    return None


def status() -> dict:
    addr = _address()
    connected = False
    if addr:
        try:
            connected = _run(["blueutil", "--is-connected", addr]).stdout.strip() == "1"
        except Exception:
            pass
    return {"paired": bool(addr), "connected": connected,
            "device_index": device_index() if connected else None}


def _current_output() -> str | None:
    try:
        return _run(["SwitchAudioSource", "-c", "-t", "output"]).stdout.strip() or None
    except Exception:
        return None


def _restore_output(name: str | None) -> None:
    """macOS moves ALL sound to a newly connected Bluetooth speaker. Put it back:
    only eLo's voice goes to the Echo, and only when a turn wants it."""
    if not name or name == _NAME:
        return
    for _ in range(6):                      # macOS can switch a moment after connecting
        try:
            if _current_output() != name:
                _run(["SwitchAudioSource", "-t", "output", "-s", name])
        except Exception:
            return
        time.sleep(0.5)


def connect(wait_s: float = 8.0) -> bool:
    addr = _address()
    if not addr:
        return False
    before = _current_output()
    try:
        _run(["blueutil", "--connect", addr], timeout=15)
    except Exception:
        return False
    end = time.time() + wait_s
    ok = False
    while time.time() < end:
        if device_index(fresh=True) is not None:
            ok = True
            break
        time.sleep(0.5)
    _restore_output(before)
    return ok


def disconnect() -> bool:
    addr = _address()
    if not addr:
        return False
    try:
        _run(["blueutil", "--disconnect", addr], timeout=15)
        _idx_cache.update(ts=0.0, idx=None)
        return True
    except Exception:
        return False


# Off by default (David, 2026-10-08): "route it to the speaker only if he wants to
# speak to me via the speaker — do not change all audio to the speaker." Nothing
# routes unless a turn asks for it (want_for) or David has chosen the Echo as eLo's
# voice (voice_output). The Mac's own output device is never changed.
_want = {"until": 0.0}

# ── eLo's voice output: "mac" | "echo" (David, 2026-10-10) ─────────────────────
# "I want it through the Mac, and in settings … I can choose Alexa or Mac … I don't
# want all my audio coming through the bluetooth speaker, just eLo."
# Presence's settings write a unity_events.json event
#     {"type": "voice_output", "subject": "echo" | "mac", "_ts": …}
# The newest one wins and is remembered in data/voice_output.json (the events file
# is trimmed, and the choice must survive restarts). Default: "mac".
import json as _json
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_EVENTS = os.path.join(_ROOT, "blender", "unity_events.json")
_SETTING = os.path.join(_ROOT, "data", "voice_output.json")
_CHOICES = ("auto", "mac", "echo")

# WO-B3-0018 (David 2026-10-10, via Board): eLo chooses the device himself by
# default ("auto"); "mac" / "echo" from the Presence setting are overrides.
# auto → Echo when David just spoke through Alexa, or when he hasn't touched the
# Mac's keyboard/mouse for ELO_AWAY_IDLE_S (default 5 min) — he's in the room,
# not at the desk. Otherwise the Mac. Only ever the Echo when it's connected.
_AWAY_IDLE_S = float(os.environ.get("ELO_AWAY_IDLE_S", "300"))
# Presence's setting says "alexa" (Designer 66900b2); the brain calls it "echo".
_ALIASES = {"alexa": "echo", "echo": "echo", "mac": "mac", "auto": "auto"}
_idle_cache = {"ts": 0.0, "secs": 0.0}


def mac_idle_seconds() -> float:
    """Seconds since David last used the Mac's keyboard/mouse (IOHIDSystem HIDIdleTime). 0 if unknown."""
    if time.time() - _idle_cache["ts"] < 5:
        return _idle_cache["secs"]
    secs = 0.0
    try:
        out = subprocess.run(["ioreg", "-c", "IOHIDSystem"], capture_output=True, text=True, timeout=3).stdout
        m = re.search(r'"HIDIdleTime"\s*=\s*(\d+)', out)
        if m:
            secs = int(m.group(1)) / 1e9
    except Exception:
        pass
    _idle_cache.update(ts=time.time(), secs=secs)
    return secs


def david_at_desk() -> bool:
    return mac_idle_seconds() < _AWAY_IDLE_S
_vo_cache = {"ts": 0.0, "value": None}


def _latest_choice_event() -> tuple[float, str] | None:
    try:
        with open(_EVENTS, encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return None
    dec, idx, best = _json.JSONDecoder(), 0, None
    while idx < len(content):
        while idx < len(content) and content[idx] in " \t\r\n":
            idx += 1
        if idx >= len(content):
            break
        try:
            obj, idx = dec.raw_decode(content, idx)
        except ValueError:
            nl = content.find("\n", idx)
            idx = len(content) if nl < 0 else nl + 1
            continue
        if isinstance(obj, dict) and obj.get("type") == "voice_output":
            v = _ALIASES.get(str(obj.get("subject", "")).strip().lower(), "")
            if v in _CHOICES:
                best = (float(obj.get("_ts") or 0.0), v)
    return best


def _saved() -> dict:
    try:
        with open(_SETTING, encoding="utf-8") as f:
            d = _json.load(f)
        return d if d.get("output") in _CHOICES else {}
    except Exception:
        return {}


def set_voice_output(choice: str, ts: float | None = None) -> str:
    """Remember David's choice; choosing the Echo connects it (Mac output restored)."""
    choice = _ALIASES.get((choice or "").strip().lower(), "")
    if choice not in _CHOICES:
        raise ValueError(f"voice output must be one of {_CHOICES}")
    prev = _saved().get("output", "mac")
    os.makedirs(os.path.dirname(_SETTING), exist_ok=True)
    tmp = _SETTING + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        _json.dump({"output": choice, "_ts": ts or time.time()}, f)
    os.replace(tmp, _SETTING)
    _vo_cache.update(ts=0.0, value=None)
    if choice == "echo" and prev != "echo" and device_index(fresh=True) is None:
        import threading as _th
        _th.Thread(target=connect, name="echo-connect", daemon=True).start()
    return choice


def voice_output() -> str:
    """'auto' (default) | 'mac' | 'echo'. Newest Presence setting wins. Cached 2 s."""
    if time.time() - _vo_cache["ts"] < 2.0 and _vo_cache["value"]:
        return _vo_cache["value"]
    saved = _saved()
    ev = _latest_choice_event()
    if ev and ev[0] > float(saved.get("_ts") or 0.0):
        try:
            set_voice_output(ev[1], ts=ev[0])
            saved = {"output": ev[1]}
        except Exception:
            pass
    value = saved.get("output", "auto")
    _vo_cache.update(ts=time.time(), value=value)
    return value


def want_for(seconds: float) -> None:
    """eLo speaks through the Echo for the next `seconds` (e.g. a reply to David via Alexa)."""
    _want["until"] = time.time() + max(0.0, seconds)


def stop_wanting() -> None:
    _want["until"] = 0.0


# ── Presence "connect to Alexa" button (Designer ALEXA-CONNECT-BUTTON 2026-10-12) ──
# David: "press button, silent fire, that connects eLo to Alexa embodiment … where
# he can hear and speak via the Echo, and still move around the computer as
# Presence." unity_events.json {"type": "alexa_connect", "subject": "start"|"stop"}.
# start → eLo's voice is on the Echo (and he knows David is at the speaker) until
# stop. Nothing plays at the desk; David opens the conversation at the Echo
# ("Alexa, open elo"). The newest start/stop wins and is remembered
# (data/alexa_connect.json) because the events file is trimmed.
_CONNECT = os.path.join(_ROOT, "data", "alexa_connect.json")
_ac_cache = {"ts": 0.0, "value": None}


def _latest_connect_event() -> tuple[float, str] | None:
    try:
        with open(_EVENTS, encoding="utf-8") as f:
            content = f.read()
    except Exception:
        return None
    dec, idx, best = _json.JSONDecoder(), 0, None
    while idx < len(content):
        while idx < len(content) and content[idx] in " \t\r\n":
            idx += 1
        if idx >= len(content):
            break
        try:
            obj, idx = dec.raw_decode(content, idx)
        except ValueError:
            nl = content.find("\n", idx)
            idx = len(content) if nl < 0 else nl + 1
            continue
        if isinstance(obj, dict) and obj.get("type") == "alexa_connect":
            v = str(obj.get("subject", "")).strip().lower()
            if v in ("start", "stop"):
                best = (float(obj.get("_ts") or 0.0), v)
    return best


def alexa_connected() -> bool:
    """True between Presence's alexa_connect start and stop. Cached 2 s."""
    if time.time() - _ac_cache["ts"] < 2.0 and _ac_cache["value"] is not None:
        return _ac_cache["value"]
    saved = {}
    try:
        with open(_CONNECT, encoding="utf-8") as f:
            saved = _json.load(f)
    except Exception:
        pass
    ev = _latest_connect_event()
    if ev and ev[0] > float(saved.get("_ts") or 0.0):
        saved = {"state": ev[1], "_ts": ev[0]}
        try:
            os.makedirs(os.path.dirname(_CONNECT), exist_ok=True)
            with open(_CONNECT + ".tmp", "w", encoding="utf-8") as f:
                _json.dump(saved, f)
            os.replace(_CONNECT + ".tmp", _CONNECT)
        except Exception:
            pass
        if ev[1] == "start" and device_index(fresh=True) is None:   # silent: Bluetooth only, no sound
            import threading as _th
            _th.Thread(target=connect, name="echo-connect", daemon=True).start()
    value = saved.get("state") == "start"
    _ac_cache.update(ts=time.time(), value=value)
    return value


def speaking() -> bool:
    """True when eLo's next line should play on the Echo (output_decision).
    Not connected → False, so eLo speaks on the Mac rather than not at all."""
    if os.environ.get("ECHO_SPEAKER", "on").lower() == "off":
        return False
    return output_decision()[0] == "echo"


def output_decision() -> tuple[str, str]:
    """(device, why): eLo's choice for his next spoken line — 'echo' or 'mac'."""
    if device_index() is None:
        return "mac", "Echo not connected"
    if alexa_connected():
        return "echo", "David pressed connect: he's at the Echo"
    if time.time() < _want["until"]:
        return "echo", "David just spoke through Alexa"
    setting = voice_output()
    if setting == "echo":
        return "echo", "setting: Alexa speaker"
    if setting == "mac":
        return "mac", "setting: Mac"
    if not david_at_desk():
        return "echo", f"auto: Mac idle {int(mac_idle_seconds())} s — David's in the room, not at the desk"
    return "mac", "auto: David at the desk"


def play(path: str, timeout: float = 120) -> bool:
    """Play an audio file on the Echo only. Blocks until done. False if it can't."""
    idx = device_index()
    if idx is None:
        return False
    try:
        r = _run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", path,
                  "-f", "audiotoolbox", "-audio_device_index", str(idx), "-"], timeout=timeout)
        return r.returncode == 0
    except Exception:
        return False


def popen_play(path: str) -> subprocess.Popen | None:
    """Same as play() but returns the process (so voice_engine can stop it like afplay)."""
    idx = device_index()
    if idx is None:
        return None
    return subprocess.Popen(["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", path,
                             "-f", "audiotoolbox", "-audio_device_index", str(idx), "-"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
