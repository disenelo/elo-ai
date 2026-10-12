"""
tools/tuya_agent.py — WO-B3-0016: direct local (LAN) control of Tuya lights.

No Alexa, no voice, no cloud at run time: tinytuya sends an encrypted packet on
the local network (TCP 6668). Each device needs its id, IP, protocol version and
local_key, fetched ONCE with a free Tuya developer sign-in
(`python -m tinytuya wizard`) and saved in data/tuya_devices.json:

    {"lights": [{"name": "Studio lights", "id": "...", "ip": "192.168.1.x",
                 "key": "...", "version": 3.5, "type": "bulb"}]}

Not configured → configured() is False and device_control keeps its other
routes. Status 2026-10-12: no Tuya device found on David's LAN (scan + TCP 6668
probe), so nothing is configured yet.

    configured() -> bool
    lights_on() / lights_off() / lights_brightness(pct) -> result standard
"""
from __future__ import annotations

import json
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CONFIG = os.path.join(_ROOT, "data", "tuya_devices.json")


def _lights() -> list[dict]:
    try:
        with open(_CONFIG, encoding="utf-8") as f:
            items = json.load(f).get("lights") or []
        return [d for d in items if d.get("id") and d.get("key") and d.get("ip")]
    except Exception:
        return []


def configured() -> bool:
    return bool(_lights())


def _device(d: dict):
    import tinytuya
    cls = tinytuya.BulbDevice if d.get("type", "bulb") == "bulb" else tinytuya.OutletDevice
    dev = cls(d["id"], d["ip"], d["key"])
    dev.set_version(float(d.get("version", 3.3)))
    dev.set_socketTimeout(3)
    return dev


def _each(action: str, fn) -> dict:
    """Run fn(device) on every configured light; success only if every light answered."""
    from tools.capability_status import tool_result, record_result
    lights = _lights()
    if not lights:
        return record_result("devices", tool_result(False, {"line": "No lights are set up for direct control yet."},
                                                    "data/tuya_devices.json not configured"))
    errors, names = [], []
    for d in lights:
        try:
            r = fn(_device(d))
            if isinstance(r, dict) and r.get("Error"):
                errors.append(f"{d.get('name', d['ip'])}: {r.get('Error')}")
            else:
                names.append(d.get("name", d["ip"]))
        except Exception as e:
            errors.append(f"{d.get('name', d['ip'])}: {type(e).__name__}")
    if errors:
        return record_result("devices", tool_result(False, {"via": "tuya", "line":
                             f"The lights didn't all answer — {'; '.join(errors)[:160]}."}, "; ".join(errors)[:300]))
    # The light answered on the LAN; that is a real acknowledgement from the device.
    return record_result("devices", tool_result(True, {"via": "tuya", "lights": names, "line": action}))


def lights_on() -> dict:
    return _each("Lights on.", lambda dev: dev.turn_on())


def lights_off() -> dict:
    return _each("Lights off.", lambda dev: dev.turn_off())


def lights_brightness(pct: int) -> dict:
    pct = max(1, min(100, int(pct)))
    return _each(f"Lights at {pct}%.",
                 lambda dev: dev.set_brightness_percentage(pct) if hasattr(dev, "set_brightness_percentage")
                 else dev.set_value(22, int(10 + pct * 9.9)))
