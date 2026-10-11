"""
runtime/capability_dispatcher.py — Kernel truth boundary (WO-B1-0104)

Classifies incoming requests and routes to the lowest-authority tier capable
of answering correctly. No unnecessary LLM escalation.

Tier model:
  FACT      → deterministic system/hardware truth (time, date, math, battery…)
  STATE     → eLo's known world / working memory can answer
  COGNITION → requires faculty interpretation
  UNKNOWN   → requires deep AI synthesis

FACT dispatch requires tools/system_primitives.py (Builder 3, B3-0007).
Until that is delivered, classify() works fully; dispatch_fact() falls through
gracefully (returns None) so existing executive flow is unchanged.

Result metadata shape (all dispatchers return this or None):
  {
      "value":      any,
      "source":     "macOS" | "elo_state" | "memory" | "faculty" | "deep_ai",
      "authority":  "definitive" | "recorded" | "inference",
      "confidence": float,          # 1.0 for deterministic
      "freshness":  "live" | "cached" | int,  # int = seconds since recorded
  }
"""

from __future__ import annotations
import re
import time as _time
from typing import Any

# ── Tier labels ────────────────────────────────────────────────────────────────
TIER_FACT       = "FACT"
TIER_STATE      = "STATE"
TIER_COGNITION  = "COGNITION"
TIER_UNKNOWN    = "UNKNOWN"
# WO-B1-0111: pre-LLM correction / unlearn tier
TIER_CORRECTION = "CORRECTION"

# ── FACT patterns (coarse, fast — no LLM) ─────────────────────────────────────
# Each pattern maps to a string key used in dispatch_fact().
_FACT_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\bwhat(?:'s| is| time)?\s+(?:the\s+)?time\b", re.I),  "time"),
    # bare "time?" or "time" alone
    (re.compile(r"^\s*time\s*\??\s*$", re.I),                           "time"),
    (re.compile(r"\bwhat(?:'s| is| are)?\s+(?:today|the\s+date|today'?s?\s+date)\b", re.I), "date"),
    (re.compile(r"\btomorrow(?:'s)?\s+date\b", re.I),                    "tomorrow"),
    (re.compile(r"\byesterday(?:'s)?\s+date\b", re.I),                   "yesterday"),
    # "battery" alone is eLo's (robot battery / Presence health — David 2026-10-09),
    # handled by tool_router._elo_health_context. The Mac only when named.
    (re.compile(r"\b(?:mac(?:book)?|laptop|computer)'?s?\s+battery\b"
                r"|\bbattery\s+(?:on|of|in)\s+(?:my|the|this)\s+(?:mac(?:book)?|laptop|computer)\b", re.I), "battery"),
    (re.compile(r"\bdisk\s*(?:space|usage|free)?\b", re.I),              "disk"),
    (re.compile(r"\buptime\b",                       re.I),              "uptime"),
    # WO-B1-0117: unit conversions — must come BEFORE arithmetic patterns so
    # "100 km to miles" doesn't fall into the bare-digit arithmetic path first.
    # Full words (celsius, fahrenheit) before single-char °?[CF] in alternation.
    (re.compile(
        r"\b(?:convert\s+)?\d+(?:\.\d+)?\s*"
        r"(?:kilometers?|kilometres?|km|miles?\b|kilograms?|kg|pounds?|lbs?\b|"
        r"centimetres?|centimeters?|cm|inches?\b|feet|ft\b|"
        r"fahrenheit|celsius|°?\s*[CF]\b|litres?|liters?|gallons?|"
        r"km\s*/\s*h|kph|mph)\s*"
        r"(?:to|in|into|as)\s+"
        r"(?:kilometers?|kilometres?|km|miles?\b|kilograms?|kg|pounds?|lbs?\b|"
        r"centimetres?|centimeters?|cm|inches?\b|feet|ft\b|"
        r"fahrenheit|celsius|°?\s*[CF]\b|litres?|liters?|gallons?|"
        r"km\s*/\s*h|kph|mph)",
        re.I,
    ), "convert"),
    # WO-B1-0117: percentage-of — must come BEFORE digit+operator arithmetic pattern
    # so "15% of 340" doesn't get `_extract_math_expr` picking up just "340".
    (re.compile(r"\b\d+(?:\.\d+)?\s*(?:%|percent|per\s+cent)\s+of\s+\d", re.I), "math_pct"),
    # Arithmetic: expression contains digits and operator — e.g. "28 × 74", "5+3*2"
    (re.compile(r"\b\d[\d\s\+\-\*\/\×\÷\^\.]+\d\b"),                    "math"),
    # Explicit "calculate" without complex natural-language structure
    (re.compile(r"\b(?:calculate|compute|what(?:'s| is)\s+)\s*\d",re.I), "math"),
]

# ── STATE patterns ─────────────────────────────────────────────────────────────
_STATE_PATTERNS: tuple[re.Pattern, ...] = tuple(re.compile(p, re.I) for p in (
    r"\bwhat\s+(?:am\s+i|are\s+we)\s+(?:working\s+on|building|doing|making)\b",
    r"\bwhat(?:'s|\s+is)\s+(?:my|our|the)\s+(?:current\s+)?(?:project|task|plan|goal)\b",
    r"\bwhat(?:'s|\s+is)\s+next\b",
    r"\bhow\s+(?:am\s+i|are\s+we)\s+doing\b",
    r"\bmy\s+(?:battery|health|status|state)\b",
    r"\belo(?:'s)?\s+(?:battery|health|status|state)\b",
))

# ── COGNITION patterns ─────────────────────────────────────────────────────────
_COGNITION_PATTERNS: tuple[re.Pattern, ...] = tuple(re.compile(p, re.I) for p in (
    r"\bwhat\s+should\s+(?:i|we)\b",
    r"\bshould\s+i\b",
    r"\bwhy\s+(?:did|is|are|does)\b",
    r"\bexplain\b",
    r"\bhow\s+(?:do\s+i|should\s+i|can\s+i)\b",
    r"\bwhat(?:'s|\s+is)\s+(?:your|elo'?s?)\s+(?:opinion|view|take|thought)\b",
    r"\bwhat\s+do\s+(?:you|elo)\s+think\b",
    r"\bhelp\s+me\s+(?:decide|choose|figure)\b",
))

# ── CORRECTION patterns (WO-B1-0111) — user flagging a wrong WKG claim ────────
_CORRECTION_PATTERNS: tuple[re.Pattern, ...] = tuple(re.compile(p, re.I) for p in (
    r"\bthat(?:'?s|\s+is)\s+(?:not\s+)?(?:wrong|incorrect|false|off|not\s+right|not\s+true)\b",
    r"\bforget\s+(?:that|what\s+you\s+said|what\s+you\s+just\s+said|it)\b",
    r"\byou(?:'?ve|\s+have)\s+got\s+(?:me|it|that|this)\s+wrong\b",
    r"\bgot\s+(?:me|it|that|this)\s+wrong\b",
    r"\bi\s+(?:never|don'?t|didn'?t)\s+(?:have|own|use|said|do|did)\b",
    r"\bthat'?s\s+not\s+(?:me|mine|accurate|correct|right|true)\b",
    r"\bunlearn\s+that\b",
    r"\bno[,\s]+(?:i|that|you)\b.*\bwrong\b",
))


def is_correction(request: str) -> bool:
    """WO-B1-0111: True when the request is correcting a prior WKG recall."""
    low = request.lower()
    return any(p.search(low) for p in _CORRECTION_PATTERNS)


def dispatch_correction(request: str) -> dict[str, Any] | None:
    """
    WO-B1-0111: Deprecate the most recently retrieved WKG profile claims and
    return an in-character acknowledgement. No LLM involved.
    """
    try:
        from runtime.wkg_faculty import deprecate_recent_claims as _deprecate
        count = _deprecate(reason="user_correction")
        if count > 0:
            return {
                "value": "Got it — I had that wrong. I've flagged it. What's the right version?",
                "source": "wkg_correction",
                "authority": "user_instruction",
                "confidence": 1.0,
                "freshness": "live",
                "corrected_count": count,
            }
        return {
            "value": "Noted. Nothing flagged from my last recall to unlearn — tell me what's right and I'll hold it.",
            "source": "wkg_correction",
            "authority": "user_instruction",
            "confidence": 1.0,
            "freshness": "live",
            "corrected_count": 0,
        }
    except Exception:
        return None


def classify(request: str) -> str:
    """
    Classify a user request into a tier without calling any LLM.

    Returns FACT | STATE | COGNITION | UNKNOWN.
    FACT tier answers come from deterministic system calls.
    STATE tier answers come from eLo's known world / working memory.
    COGNITION tier needs faculty interpretation.
    UNKNOWN falls through to deep AI.
    """
    if not request or not request.strip():
        return TIER_UNKNOWN
    low = request.lower()

    for pattern, _ in _FACT_PATTERNS:
        if pattern.search(low):
            return TIER_FACT

    for pattern in _STATE_PATTERNS:
        if pattern.search(low):
            return TIER_STATE

    for pattern in _COGNITION_PATTERNS:
        if pattern.search(low):
            return TIER_COGNITION

    return TIER_UNKNOWN


def dispatch_fact(request: str) -> dict[str, Any] | None:
    """
    Attempt to resolve a FACT-tier request from deterministic system sources.
    Returns a result-metadata dict or None if system_primitives is unavailable
    or the request doesn't match a known FACT pattern.

    Callers: treat None as "fall through to existing executive flow".
    """
    try:
        from tools.system_primitives import SystemPrimitives as _SP
    except ImportError:
        # Builder 3 hasn't delivered system_primitives yet — graceful fallback.
        return _dispatch_fact_builtin(request)

    sp = _SP()
    low = request.lower()

    for pattern, key in _FACT_PATTERNS:
        if not pattern.search(low):
            continue
        try:
            if key == "time":
                val = sp.time.now()
                return _fact_result(_unwrap(val), "macOS")
            if key == "date":
                val = sp.calendar.today()
                return _fact_result(_unwrap(val), "macOS")
            if key == "tomorrow":
                val = sp.calendar.tomorrow()
                return _fact_result(_unwrap(val), "macOS")
            if key == "yesterday":
                val = sp.calendar.yesterday()
                return _fact_result(_unwrap(val), "macOS")
            if key == "battery":
                val = sp.computer.battery()
                return _fact_result(_format_system_value("battery", _unwrap(val)), "macOS")
            if key == "disk":
                val = sp.computer.disk()
                return _fact_result(_format_system_value("disk", _unwrap(val)), "macOS")
            if key == "uptime":
                val = sp.computer.uptime()
                return _fact_result(_format_system_value("uptime", _unwrap(val)), "macOS")
            if key == "math_pct":
                # WO-B1-0117: pass the FULL request so system_primitives._clean_expr
                # can expand "15% of 340" → "(15/100)*340" before bc evaluates it.
                val = sp.math.calculate(request)
                if _unwrap(val) is not None:
                    return _fact_result(_unwrap(val), "macOS")
            if key == "math":
                expr = _extract_math_expr(request)
                if expr:
                    val = sp.math.calculate(expr)
                    return _fact_result(_unwrap(val), "macOS")
                # B3: spoken sums ("6 times 7", "15% of 80") have no symbol run to
                # extract. system_primitives normalises the words and refuses
                # anything that isn't arithmetic, so the whole request is safe here.
                val = sp.math.calculate(request)
                if _unwrap(val) is not None:
                    return _fact_result(_unwrap(val), "macOS")
            # WO-B1-0117: unit conversions handled inline (no system_primitives needed)
            if key == "convert":
                result = _convert_units(request)
                if result:
                    return _fact_result(result, "macOS")
        except Exception:
            pass

    return None


def _dispatch_fact_builtin(request: str) -> dict[str, Any] | None:
    """
    Minimal builtin FACT dispatch for when system_primitives is unavailable.
    Handles time and date natively (stdlib only) so "what time is it" never
    hits Ollama when system_primitives hasn't arrived yet.
    """
    import datetime as _dt
    low = request.lower()

    for pattern, key in _FACT_PATTERNS:
        if not pattern.search(low):
            continue
        if key == "time":
            now = _dt.datetime.now()
            val = now.strftime("%-I:%M %p").lstrip("0") or now.strftime("%I:%M %p")
            return _fact_result(val, "macOS")
        if key == "date":
            val = _dt.date.today().strftime("%A, %B %-d, %Y")
            return _fact_result(val, "macOS")
        if key == "tomorrow":
            val = (_dt.date.today() + _dt.timedelta(days=1)).strftime("%A, %B %-d, %Y")
            return _fact_result(val, "macOS")
        if key == "yesterday":
            val = (_dt.date.today() - _dt.timedelta(days=1)).strftime("%A, %B %-d, %Y")
            return _fact_result(val, "macOS")
        if key == "math_pct":
            # Builtin fallback: evaluate "15% of 340" via ast
            import re as _re2
            _pct = _re2.compile(r"(\d+(?:\.\d+)?)\s*(?:%|percent|per\s+cent)\s+of\s+(\d+(?:\.\d+)?)", _re2.I)
            pm = _pct.search(request)
            if pm:
                result_val = (float(pm.group(1)) / 100) * float(pm.group(2))
                return _fact_result(_tidy(result_val), "macOS")
        if key == "math":
            expr = _extract_math_expr(request)
            if expr:
                val = _safe_eval_math(expr)
                if val is not None:
                    return _fact_result(str(val), "macOS")
        if key == "convert":
            result = _convert_units(request)
            if result:
                return _fact_result(result, "macOS")

    return None


def _unwrap(val: Any) -> Any:
    """If system_primitives returns a result-metadata dict, extract the value."""
    if isinstance(val, dict) and "value" in val:
        return val["value"]
    return val


def _format_system_value(key: str, val: Any) -> str:
    """
    Format structured system_primitives values into human-readable strings.
    dict values (battery, disk, uptime) need this; scalars pass through as-is.
    """
    if not isinstance(val, dict):
        return str(val)
    if key == "battery":
        pct = val.get("percent")
        if pct is not None:
            source = "charging" if val.get("charging") else val.get("power_source", "")
            return f"{pct}% battery ({source})" if source else f"{pct}% battery"
        power = val.get("power_source", "")
        if not val.get("has_battery", True):
            return f"No battery — running on {power}" if power else "Desktop (no battery)"
        return "Battery status unavailable"
    if key == "disk":
        free = val.get("free", "")
        total = val.get("total", "")
        used_pct = val.get("capacity", "")
        if free and total:
            return f"{free} free of {total} ({used_pct} used)"
        return str(val)
    if key == "uptime":
        # uptime val may be a raw string already (from `uptime` command output)
        return str(val).strip()
    return str(val)


def _fact_result(value: Any, source: str) -> dict[str, Any]:
    return {
        "value":      value,
        "source":     source,
        "authority":  "definitive",
        "confidence": 1.0,
        "freshness":  "live",
    }


def _extract_math_expr(text: str) -> str:
    """Extract the core arithmetic expression from a request string."""
    # Normalize Unicode operators
    text = text.replace("×", "*").replace("÷", "/").replace("^", "**")
    m = re.search(r"(\d[\d\s\+\-\*\/\.\^]+\d)", text)
    return m.group(1).strip() if m else ""


def _safe_eval_math(expr: str) -> float | int | None:
    """
    Evaluate a simple arithmetic expression without using eval() on arbitrary code.
    Only allows digits, whitespace, and +−×÷^. operators.
    """
    cleaned = re.sub(r"[^\d\s\+\-\*\/\.\(\)]", "", expr).strip()
    if not cleaned:
        return None
    try:
        import ast as _ast
        tree = _ast.parse(cleaned, mode="eval")
        # Safety: only allow literals, BinOps, UnaryOps with numeric types
        for node in _ast.walk(tree):
            if not isinstance(node, (
                _ast.Expression, _ast.BinOp, _ast.UnaryOp,
                _ast.Constant, _ast.Num,
                _ast.Add, _ast.Sub, _ast.Mult, _ast.Div,
                _ast.Pow, _ast.FloorDiv, _ast.Mod,
                _ast.USub, _ast.UAdd,
            )):
                return None
        result = eval(compile(tree, "<expr>", "eval"))  # noqa: S307 — gated above
        if isinstance(result, float) and result == int(result):
            return int(result)
        return result
    except Exception:
        return None


def _convert_units(request: str) -> str | None:
    """
    WO-B1-0117: Parse and convert a unit-conversion request.
    Returns a human-readable result string or None if unparseable.

    Supported:
      Distance: km ↔ miles, cm ↔ inches ↔ feet
      Weight:   kg ↔ lbs
      Temp:     °C ↔ °F
      Volume:   litres ↔ gallons (US)
      Speed:    mph ↔ kph
    """
    import re as _re

    # Extract numeric value and from/to units
    # Alternation order: longest/most-specific first so "celsius" is matched
    # before the single-char fallback °?[CF] consumes just the "c" or "f".
    _UNIT_ALTS = (
        r"kilometers?|kilometres?|km"
        r"|miles?\b"
        r"|kilograms?|kg"
        r"|pounds?|lbs?\b"
        r"|centimetres?|centimeters?|cm"
        r"|inches?|in\b"
        r"|feet|ft\b"
        r"|fahrenheit|celsius"  # full words before single-letter C/F
        r"|°?\s*[CF]\b"
        r"|litres?|liters?"
        r"|gallons?"
        r"|km\s*/\s*h|kph|mph"
    )
    _CONV_RE = _re.compile(
        rf"(?:convert\s+)?(\d+(?:\.\d+)?)\s*({_UNIT_ALTS})\s*(?:to|in|into|as)\s*({_UNIT_ALTS})",
        _re.I,
    )
    m = _CONV_RE.search(request)
    if not m:
        return None

    raw_val, from_unit, to_unit = m.group(1), m.group(2).lower().strip(), m.group(3).lower().strip()
    val = float(raw_val)

    def _norm(u: str) -> str:
        u = u.strip().lower()
        aliases = {
            # full word first (before plural strip so "celsius" isn't mangled)
            "kilometer": "km", "kilometre": "km", "kilometers": "km", "kilometres": "km",
            "mile": "mi", "miles": "mi",
            "mph": "mph", "kph": "kph", "km/h": "kph",
            "kilogram": "kg", "kilograms": "kg",
            "lb": "lbs", "lbs": "lbs", "pound": "lbs", "pounds": "lbs",
            "centimeter": "cm", "centimetre": "cm", "centimeters": "cm", "centimetres": "cm",
            "inch": "in", "inches": "in",
            "feet": "ft", "foot": "ft",
            "celsius": "°c", "°c": "°c",
            "fahrenheit": "°f", "°f": "°f",
            "litre": "l", "liter": "l", "litres": "l", "liters": "l",
            "gallon": "gal", "gallons": "gal",
        }
        if u in aliases:
            return aliases[u]
        # fallback: strip trailing plural "s" for any missed variant
        stripped = u.rstrip("s")
        return aliases.get(stripped, stripped)

    fr, to = _norm(from_unit), _norm(to_unit)

    _TABLE: dict[tuple[str, str], tuple[float, str, str]] = {
        # (from, to): (factor or special, from_label, to_label)
        ("km", "mi"):  (0.621371, "km", "miles"),
        ("mi", "km"):  (1.60934, "miles", "km"),
        ("kg", "lbs"): (2.20462, "kg", "lbs"),
        ("lbs", "kg"): (0.453592, "lbs", "kg"),
        ("cm", "in"):  (0.393701, "cm", "inches"),
        ("in", "cm"):  (2.54, "inches", "cm"),
        ("ft", "cm"):  (30.48, "feet", "cm"),
        ("cm", "ft"):  (0.0328084, "cm", "feet"),
        ("ft", "m"):   (0.3048, "feet", "m"),
        ("m", "ft"):   (3.28084, "m", "feet"),
        ("l", "gal"):  (0.264172, "litres", "gallons"),
        ("gal", "l"):  (3.78541, "gallons", "litres"),
        ("mph", "kph"): (1.60934, "mph", "kph"),
        ("kph", "mph"): (0.621371, "kph", "mph"),
        ("km", "m"):   (1000.0, "km", "m"),
        ("m", "km"):   (0.001, "m", "km"),
    }

    # Temperature is special (not a factor)
    if fr == "°c" and to == "°f":
        result = val * 9 / 5 + 32
        return f"{_tidy(val)}°C = {_tidy(result)}°F"
    if fr == "°f" and to == "°c":
        result = (val - 32) * 5 / 9
        return f"{_tidy(val)}°F = {_tidy(result)}°C"

    entry = _TABLE.get((fr, to))
    if entry:
        factor, fl, tl = entry
        result = val * factor
        return f"{_tidy(val)} {fl} = {_tidy(result)} {tl}"

    return None


def _tidy(n: float) -> str:
    """Format a float cleanly — drop trailing zeros, keep up to 4 d.p."""
    s = f"{n:.4f}".rstrip("0").rstrip(".")
    return s if s else "0"


def dispatch_state(request: str) -> dict[str, Any] | None:
    """
    Resolve a STATE-tier request from eLo's known world.
    Returns a result dict or None (fall through to executive).
    Checks blender_state.json and working memory (B2 card 0010 when available).
    """
    from faculties.inner_thought import as_context  # STATE tier reads inner_thought timeline

    low = request.lower()

    # "what am I working on" — check company_state first, then inner_thought context
    if re.search(r"\bwhat\s+(?:am\s+i|are\s+we)\s+(?:working\s+on|building|doing|making)\b", low, re.I):
        try:
            from runtime.capability_registry import read_company_state as _rcs
            cs = _rcs()
            summary = cs.get("summary") or cs.get("active") or ""
            if summary:
                ctx = as_context(5)
                combined = f"{summary}\n\n{ctx}".strip() if ctx.strip() else summary
                return {
                    "value":      combined,
                    "source":     "elo_state",
                    "authority":  "recorded",
                    "confidence": 0.9,
                    "freshness":  "live",
                }
        except Exception:
            pass

    return None
