"""
tools/system_primitives.py — WO-B3-0007: deterministic facts from macOS. No LLM.

The Tier-0 instrument panel: things macOS can answer exactly (time, dates,
arithmetic, battery, disk, files, processes) are answered here, never invented
by a model. No confirmation gates: read-only or output-only actions.

Sources: docs/architecture/_intake/SOURCE_SYSTEM-FACULTY-FAST-LANE_2026-10-08.md,
SOURCE_ELO-COMMAND-LAYER_2026-10-08.md, SOURCE_CAPABILITY-AUTHORITY-MODEL_2026-10-08.md.

Every call returns
    {"value": ..., "source": "macOS", "authority": "definitive",
     "confidence": 1.0, "freshness": "live"}
and on failure the same shape with value None, confidence 0.0 and an "error".

    from tools.system_primitives import system
    system.time.now()["value"]            # "13:25:42"
    system.math.calculate("28 * 74")      # {"value": "2072", ...}
    system.run("CALC", "10 / 3")          # via COMMAND_VOCAB

tools/system_agent.py (window/app control with confirmation) sits above this;
nothing here duplicates it. Builder 1 wires COMMAND_VOCAB into the fast router.
"""
from __future__ import annotations

import datetime
import subprocess

_TIMEOUT = 5


# ── result shape ──────────────────────────────────────────────────────────────

def _ok(value, freshness: str = "live") -> dict:
    return {"value": value, "source": "macOS", "authority": "definitive",
            "confidence": 1.0, "freshness": freshness}


def _fail(error: str) -> dict:
    return {"value": None, "source": "macOS", "authority": "definitive",
            "confidence": 0.0, "freshness": "live", "error": error}


def _sh(args: list, input_text: str | None = None, timeout: float = _TIMEOUT) -> str:
    """Run a command without a shell (args list), return stdout. Raises on failure."""
    r = subprocess.run(args, input=input_text, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout or f"exit {r.returncode}").strip()[:200])
    return r.stdout.strip()


def _safe(fn):
    """Every primitive returns the result shape, never raises."""
    def wrapper(*a, **k):
        try:
            return fn(*a, **k)
        except Exception as e:
            return _fail(f"{type(e).__name__}: {e}")
    wrapper.__name__ = fn.__name__
    wrapper.__doc__ = fn.__doc__
    return wrapper


def _date(fmt: str, offset_days: int | None = None) -> str:
    args = ["date"]
    if offset_days:
        args.append(f"-v{offset_days:+d}d")
    return _sh(args + [fmt])


_DAY_FMT = "+%A %-d %B %Y"     # "Thursday 8 October 2026"


# ── namespaces ────────────────────────────────────────────────────────────────

class _Time:
    @staticmethod
    @_safe
    def now():
        return _ok(_sh(["date", "+%H:%M:%S"]))

    @staticmethod
    @_safe
    def utc_now():
        return _ok(_sh(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"]))

    @staticmethod
    @_safe
    def timestamp():
        return _ok(int(_sh(["date", "+%s"])))

    @staticmethod
    @_safe
    def timezone():
        return _ok(_sh(["date", "+%Z"]))


class _Calendar:
    @staticmethod
    @_safe
    def today():
        return _ok(_date(_DAY_FMT))

    @staticmethod
    @_safe
    def tomorrow():
        return _ok(_date(_DAY_FMT, 1))

    @staticmethod
    @_safe
    def yesterday():
        return _ok(_date(_DAY_FMT, -1))

    @staticmethod
    @_safe
    def date_offset(days: int = 0):
        return _ok(_date(_DAY_FMT, int(days)))

    @staticmethod
    @_safe
    def day_of_week():
        return _ok(_sh(["date", "+%A"]))


# Arithmetic only: digits, operators, brackets, decimal point, spaces.
# Words ("times", "x", "×") are normalised first; anything else is refused —
# the python3 fallback must never run arbitrary text.
_MATH_OK = set("0123456789+-*/%^(). ")
_MATH_WORDS = (("×", "*"), ("÷", "/"), (" x ", " * "), ("times", "*"), ("multiplied by", "*"),
               ("divided by", "/"), ("plus", "+"), ("minus", "-"), ("to the power of", "^"),
               ("squared", "^2"), ("cubed", "^3"), (",", ""))


import re as _re   # parsing only (percent-of); no shell, no eval
_PCT_OF = _re.compile(r"(\d+(?:\.\d+)?)\s*(?:%|percent|per\s+cent)\s+of\s+(\d+(?:\.\d+)?)")


def _clean_expr(expression: str) -> str:
    e = expression.lower().strip().rstrip("?=").strip()
    for lead in ("what's", "what is", "whats", "how much is", "calculate", "work out", "eval"):
        if e.startswith(lead):
            e = e[len(lead):].strip()
            break
    # "15% of 80" / "15 percent of 80" → (15/100)*80
    e = _PCT_OF.sub(lambda m: f"({m.group(1)}/100)*{m.group(2)}", e)
    e = f" {e} "
    for word, op in _MATH_WORDS:
        e = e.replace(word, op)
    e = " ".join(e.split())
    if not e or any(c not in _MATH_OK for c in e):
        raise ValueError(f"not arithmetic: {expression!r}")
    return e


def _tidy_number(s: str) -> str:
    s = s.replace("\\\n", "").strip()
    if "." in s:
        s = s.rstrip("0").rstrip(".")
        if s.startswith("."):
            s = "0" + s
        elif s.startswith("-."):
            s = "-0" + s[1:]
    return s or "0"


class _Math:
    @staticmethod
    @_safe
    def calculate(expression: str, scale: int = 4):
        """Exact arithmetic via bc (scale 4); python3 fallback for what bc rejects."""
        e = _clean_expr(expression)
        try:
            out = _sh(["bc", "-l"], input_text=f"scale={int(scale)}\n{e}\n")
            if out and "error" not in out.lower():
                return _ok(_tidy_number(out))
        except Exception:
            pass
        py = e.replace("^", "**")
        out = _sh(["python3", "-c", f"r = {py}\nprint(round(r, {int(scale)}) if isinstance(r, float) else r)"])
        return _ok(_tidy_number(out))


class _Computer:
    @staticmethod
    @_safe
    def hostname():
        return _ok(_sh(["hostname"]))

    @staticmethod
    @_safe
    def os_version():
        return _ok(_sh(["sw_vers", "-productVersion"]))

    @staticmethod
    @_safe
    def uptime():
        """'up 1 day, 1:44' (the uptime command without users/load averages)."""
        raw = _sh(["uptime"])
        m = _re.search(r"\bup\s+(.*?),\s+\d+\s+users?\b", raw)
        return _ok("up " + " ".join(m.group(1).split()) if m else raw)

    @staticmethod
    @_safe
    def battery():
        """{percent, charging, power_source, has_battery}. A Mac on mains with no
        battery (Mac Studio) → has_battery False, percent None."""
        out = _sh(["pmset", "-g", "batt"])
        source = "AC" if "AC Power" in out else ("battery" if "Battery Power" in out else "unknown")
        percent, charging = None, None
        for line in out.splitlines()[1:]:
            if "%" in line:
                pct = line.split("%")[0].split()[-1]
                if pct.isdigit():
                    percent = int(pct)
                low = line.lower()
                charging = ("charging" in low and "discharging" not in low and "not charging" not in low) \
                    or "charged" in low
        return _ok({"percent": percent, "charging": charging, "power_source": source,
                    "has_battery": percent is not None})

    @staticmethod
    @_safe
    def disk(path: str = "/"):
        """{total, free, used} for the volume holding path (human sizes, df -h)."""
        line = _sh(["df", "-h", path]).splitlines()[-1].split()
        return _ok({"total": line[1], "used": line[2], "free": line[3], "capacity": line[4]})

    @staticmethod
    @_safe
    def cpu_info():
        return _ok(_sh(["sysctl", "-n", "machdep.cpu.brand_string"]))


_home: list = []


def _expand(path: str) -> str:
    """Leading ~ → the home folder (no shell expansion of anything else)."""
    if path == "~" or path.startswith("~/"):
        if not _home:
            _home.append(_sh(["/bin/sh", "-c", 'printf %s "$HOME"']))
        return _home[0] + path[1:]
    return path


class _Files:
    @staticmethod
    @_safe
    def list(path: str = "~"):
        return _ok([x for x in _sh(["ls", "-1", _expand(path)]).splitlines() if x])

    @staticmethod
    @_safe
    def search(query: str, scope: str = "~", limit: int = 50):
        """Spotlight (mdfind) by name or content, within scope. First `limit` paths."""
        out = _sh(["mdfind", "-onlyin", _expand(scope), query], timeout=10)
        return _ok([p for p in out.splitlines() if p][:limit])

    @staticmethod
    @_safe
    def exists(path: str):
        r = subprocess.run(["test", "-e", _expand(path)], timeout=_TIMEOUT)
        return _ok(r.returncode == 0)

    @staticmethod
    @_safe
    def open(path: str):
        _sh(["open", _expand(path)])
        return _ok(None)


class _MacOS:
    @staticmethod
    @_safe
    def speak(text: str, voice: str | None = None):
        _sh(["say"] + (["-v", voice] if voice else []) + [text], timeout=60)
        return _ok(None)

    @staticmethod
    @_safe
    def notify(title: str, message: str):
        def q(s):  # AppleScript string literal
            return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'
        _sh(["osascript", "-e", f"display notification {q(message)} with title {q(title)}"])
        return _ok(None)

    @staticmethod
    @_safe
    def open_app(name: str):
        _sh(["open", "-a", name])
        return _ok(None)

    @staticmethod
    @_safe
    def open_url(url: str):
        if not url.lower().startswith(("http://", "https://")):
            raise ValueError("only http(s) URLs")
        _sh(["open", url])
        return _ok(None)


class _Process:
    @staticmethod
    @_safe
    def list_running():
        rows = []
        for line in _sh(["ps", "-axo", "pid=,comm="]).splitlines():
            parts = line.strip().split(None, 1)
            if len(parts) == 2 and parts[0].isdigit():
                rows.append({"pid": int(parts[0]), "name": parts[1].rsplit("/", 1)[-1]})
        return _ok(rows)

    @staticmethod
    @_safe
    def is_running(name: str):
        r = subprocess.run(["pgrep", "-ix", name], capture_output=True, timeout=_TIMEOUT)
        if r.returncode == 0:
            return _ok(True)
        procs = _Process.list_running()["value"] or []
        return _ok(any(p["name"].lower() == name.lower() for p in procs))


class _Env:
    @staticmethod
    @_safe
    def whoami():
        return _ok(_sh(["whoami"]))

    @staticmethod
    @_safe
    def current_dir():
        return _ok(_sh(["pwd"]))


# ── capability metadata (kernel dispatcher) ───────────────────────────────────

def _cap(latency: str = "instant", side_effect: bool = False) -> dict:
    return {"deterministic": True, "latency": latency, "reasoning_required": False,
            "authority": "definitive", "freshness": "live", "side_effect": side_effect}


CAPABILITIES: dict[str, dict] = {
    "time.now": _cap(), "time.utc_now": _cap(), "time.timestamp": _cap(), "time.timezone": _cap(),
    "calendar.today": _cap(), "calendar.tomorrow": _cap(), "calendar.yesterday": _cap(),
    "calendar.date_offset": _cap(), "calendar.day_of_week": _cap(),
    "math.calculate": _cap(),
    "computer.hostname": _cap(), "computer.os_version": _cap(), "computer.uptime": _cap(),
    "computer.battery": _cap(), "computer.disk": _cap(), "computer.cpu_info": _cap(),
    "files.list": _cap("fast"), "files.search": _cap("fast"), "files.exists": _cap(),
    "files.open": _cap("fast", side_effect=True),
    "macos.speak": _cap("fast", side_effect=True), "macos.notify": _cap("fast", side_effect=True),
    "macos.open_app": _cap("fast", side_effect=True), "macos.open_url": _cap("fast", side_effect=True),
    "process.list_running": _cap("fast"), "process.is_running": _cap(),
    "env.whoami": _cap(), "env.current_dir": _cap(),
}

COMMAND_VOCAB: dict[str, str] = {
    "TIME":    "time.now",
    "DATE":    "calendar.today",
    "CALC":    "math.calculate",
    "BATTERY": "computer.battery",
    "DISK":    "computer.disk",
    "FIND":    "files.search",
    "OPEN":    "macos.open_app",
    "SPEAK":   "macos.speak",
    "NOTIFY":  "macos.notify",
    "PROCESS": "process.list_running",
    "SYSTEM":  "computer.os_version",
    "UPTIME":  "computer.uptime",
}


class SystemPrimitives:
    time = _Time
    calendar = _Calendar
    math = _Math
    computer = _Computer
    files = _Files
    macos = _MacOS
    process = _Process
    env = _Env

    def call(self, name: str, *args, **kwargs) -> dict:
        """call("math.calculate", "2+2") — only names in CAPABILITIES."""
        if name not in CAPABILITIES:
            return _fail(f"unknown primitive {name!r}")
        ns, fn = name.split(".", 1)
        return getattr(getattr(self, ns), fn)(*args, **kwargs)

    def run(self, command: str, *args, **kwargs) -> dict:
        """run("CALC", "28 * 74") — eLo command vocabulary."""
        name = COMMAND_VOCAB.get(command.upper())
        return self.call(name, *args, **kwargs) if name else _fail(f"unknown command {command!r}")


system = SystemPrimitives()
