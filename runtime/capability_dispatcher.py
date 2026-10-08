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
TIER_FACT      = "FACT"
TIER_STATE     = "STATE"
TIER_COGNITION = "COGNITION"
TIER_UNKNOWN   = "UNKNOWN"

# ── FACT patterns (coarse, fast — no LLM) ─────────────────────────────────────
# Each pattern maps to a string key used in dispatch_fact().
_FACT_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\bwhat(?:'s| is| time)?\s+(?:the\s+)?time\b", re.I),  "time"),
    # bare "time?" or "time" alone
    (re.compile(r"^\s*time\s*\??\s*$", re.I),                           "time"),
    (re.compile(r"\bwhat(?:'s| is| are)?\s+(?:today|the\s+date|today'?s?\s+date)\b", re.I), "date"),
    (re.compile(r"\btomorrow(?:'s)?\s+date\b", re.I),                    "tomorrow"),
    (re.compile(r"\byesterday(?:'s)?\s+date\b", re.I),                   "yesterday"),
    (re.compile(r"\bbattery\b",                      re.I),              "battery"),
    (re.compile(r"\bdisk\s*(?:space|usage|free)?\b", re.I),              "disk"),
    (re.compile(r"\buptime\b",                       re.I),              "uptime"),
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
                return _fact_result(_unwrap(val), "macOS")
            if key == "disk":
                val = sp.computer.disk()
                return _fact_result(_unwrap(val), "macOS")
            if key == "uptime":
                val = sp.computer.uptime()
                return _fact_result(_unwrap(val), "macOS")
            if key == "math":
                expr = _extract_math_expr(request)
                if expr:
                    val = sp.math.calculate(expr)
                    return _fact_result(_unwrap(val), "macOS")
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
        if key == "math":
            expr = _extract_math_expr(request)
            if expr:
                val = _safe_eval_math(expr)
                if val is not None:
                    return _fact_result(str(val), "macOS")

    return None


def _unwrap(val: Any) -> Any:
    """If system_primitives returns a result-metadata dict, extract the value."""
    if isinstance(val, dict) and "value" in val:
        return val["value"]
    return val


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


def dispatch_state(request: str) -> dict[str, Any] | None:
    """
    Resolve a STATE-tier request from eLo's known world.
    Returns a result dict or None (fall through to executive).
    Checks blender_state.json and working memory (B2 card 0010 when available).
    """
    low = request.lower()

    # "what am I working on" — check company_state first
    if re.search(r"\bwhat\s+(?:am\s+i|are\s+we)\s+(?:working\s+on|building|doing|making)\b", low, re.I):
        try:
            from runtime.capability_registry import read_company_state as _rcs
            cs = _rcs()
            summary = cs.get("summary") or cs.get("active") or ""
            if summary:
                return {
                    "value":      summary,
                    "source":     "elo_state",
                    "authority":  "recorded",
                    "confidence": 0.9,
                    "freshness":  "live",
                }
        except Exception:
            pass

    return None
