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
  want_for(s)   → eLo speaks through the Echo for the next s seconds (off by default)
  speaking()    → True only while wanted AND connected (voice_engine routes to it)

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
# routes unless a turn asks for it (want_for); the Mac's own output is never changed.
_want = {"until": 0.0}


def want_for(seconds: float) -> None:
    """eLo speaks through the Echo for the next `seconds` (e.g. a reply to David via Alexa)."""
    _want["until"] = time.time() + max(0.0, seconds)


def stop_wanting() -> None:
    _want["until"] = 0.0


def speaking() -> bool:
    """True only while a turn wants the Echo AND it is connected as an output."""
    if os.environ.get("ECHO_SPEAKER", "on").lower() == "off":
        return False
    return time.time() < _want["until"] and device_index() is not None


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
